import base64
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.cafe import Cafe
from app.models.cafe_amenity import CafeAmenity
from app.models.cafe_hour import CafeHour
from app.models.cafe_image import CafeImage
from app.models.cafe_seat import CafeSeat
from app.models.neighborhood import Neighborhood
from app.models.review import Review
from app.models.user import User
from app.schemas.cafe import (
    CafeAmenityResponse,
    CafeDetailResponse,
    CafeHourResponse,
    CafeImageResponse,
    CafeListItem,
    CafeListResponse,
    CafeReviewResponse,
    CafeSeatResponse,
)


router = APIRouter()


def _strip_seed_marker(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return value.replace("[seed]", "").strip()


def _encode_cursor(created_at: datetime, cafe_id: uuid.UUID) -> str:
    timestamp = created_at.astimezone(timezone.utc).isoformat()
    raw = f"{timestamp}:{cafe_id}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")


def _decode_cursor(cursor: str) -> Tuple[datetime, uuid.UUID]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        timestamp_raw, id_raw = raw.rsplit(":", 1)
        parsed_dt = datetime.fromisoformat(timestamp_raw)
        if parsed_dt.tzinfo is None:
            parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
        return parsed_dt, uuid.UUID(id_raw)
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Geçersiz cursor formatı.") from exc


def _to_float(value: Optional[Decimal], default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value)


def _serialize_list_item(row) -> CafeListItem:
    cafe = row.Cafe
    return CafeListItem(
        id=cafe.id,
        name=cafe.name,
        slug=cafe.slug,
        address=cafe.address,
        latitude=_to_float(cafe.latitude),
        longitude=_to_float(cafe.longitude),
        avg_rating=_to_float(cafe.avg_rating),
        review_count=cafe.review_count or 0,
        neighborhood=row.neighborhood_name,
        neighborhood_slug=row.neighborhood_slug,
        wifi_available=bool(row.wifi_available) if row.wifi_available is not None else False,
        noise_level=row.noise_level,
        created_at=cafe.created_at,
    )


@router.get("")
async def list_cafes(
    cursor: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    neighborhood: Optional[str] = Query(default=None),
    wifi: Optional[bool] = Query(default=None),
    noise_level: Optional[str] = Query(default=None),
    has_outlet: Optional[bool] = Query(default=None),
    db: AsyncSession = Depends(get_db_session),
):
    base_stmt = (
        select(
            Cafe,
            Neighborhood.name.label("neighborhood_name"),
            Neighborhood.slug.label("neighborhood_slug"),
            CafeAmenity.wifi_available.label("wifi_available"),
            CafeAmenity.noise_level.label("noise_level"),
        )
        .join(Neighborhood, Cafe.neighborhood_id == Neighborhood.id, isouter=True)
        .join(CafeAmenity, CafeAmenity.cafe_id == Cafe.id, isouter=True)
    )
    filters = [Cafe.is_active.is_(True), Cafe.deleted_at.is_(None)]

    if neighborhood:
        filters.append(Neighborhood.slug == neighborhood.strip().lower())
    if wifi is not None:
        filters.append(CafeAmenity.wifi_available.is_(wifi))
    if noise_level:
        filters.append(CafeAmenity.noise_level == noise_level.strip().lower())
    if has_outlet is not None:
        has_outlet_exists = exists(
            select(1).where(
                CafeSeat.cafe_id == Cafe.id,
                CafeSeat.has_outlet.is_(True),
            )
        )
        filters.append(has_outlet_exists if has_outlet else ~has_outlet_exists)

    count_stmt = (
        select(func.count(Cafe.id))
        .select_from(Cafe)
        .join(Neighborhood, Cafe.neighborhood_id == Neighborhood.id, isouter=True)
        .join(CafeAmenity, CafeAmenity.cafe_id == Cafe.id, isouter=True)
        .where(*filters)
    )
    count_result = await db.execute(count_stmt)
    total_count = int(count_result.scalar_one() or 0)

    stmt = base_stmt.where(*filters)

    if cursor:
        cursor_dt, cursor_id = _decode_cursor(cursor)
        stmt = stmt.where(
            or_(
                Cafe.created_at < cursor_dt,
                and_(Cafe.created_at == cursor_dt, Cafe.id < cursor_id),
            )
        )

    stmt = stmt.order_by(Cafe.created_at.desc(), Cafe.id.desc()).limit(limit + 1)
    result = await db.execute(stmt)
    rows = result.all()

    page_rows = rows[:limit]
    items = [_serialize_list_item(row) for row in page_rows]

    next_cursor = None
    if len(rows) > limit and page_rows:
        last_cafe = page_rows[-1].Cafe
        next_cursor = _encode_cursor(last_cafe.created_at, last_cafe.id)

    return CafeListResponse(
        items=items,
        next_cursor=next_cursor,
        limit=limit,
        total_count=total_count,
    )


@router.get("/{slug}", response_model=CafeDetailResponse)
async def get_cafe(slug: str, db: AsyncSession = Depends(get_db_session)):
    detail_stmt = (
        select(
            Cafe,
            Neighborhood.name.label("neighborhood_name"),
            Neighborhood.slug.label("neighborhood_slug"),
            CafeAmenity,
        )
        .join(Neighborhood, Cafe.neighborhood_id == Neighborhood.id, isouter=True)
        .join(CafeAmenity, CafeAmenity.cafe_id == Cafe.id, isouter=True)
        .where(Cafe.slug == slug, Cafe.is_active.is_(True), Cafe.deleted_at.is_(None))
    )
    detail_result = await db.execute(detail_stmt)
    detail_row = detail_result.first()
    if detail_row is None:
        raise HTTPException(status_code=404, detail="Kafe bulunamadı.")

    cafe = detail_row.Cafe
    amenity = detail_row.CafeAmenity

    hours_result = await db.execute(
        select(CafeHour)
        .where(CafeHour.cafe_id == cafe.id)
        .order_by(CafeHour.day_of_week.asc())
    )
    hours_rows = hours_result.scalars().all()

    images_result = await db.execute(
        select(CafeImage)
        .where(CafeImage.cafe_id == cafe.id)
        .order_by(CafeImage.is_primary.desc(), CafeImage.sort_order.asc(), CafeImage.created_at.asc())
    )
    image_rows = images_result.scalars().all()

    seats_result = await db.execute(
        select(CafeSeat)
        .where(CafeSeat.cafe_id == cafe.id)
        .order_by(CafeSeat.seat_type.asc())
    )
    seat_rows = seats_result.scalars().all()

    reviews_result = await db.execute(
        select(Review, User.display_name, User.username)
        .join(User, User.id == Review.user_id, isouter=True)
        .where(
            Review.cafe_id == cafe.id,
            Review.deleted_at.is_(None),
        )
        .order_by(Review.created_at.desc())
        .limit(20)
    )
    review_rows = reviews_result.all()

    amenity_payload = CafeAmenityResponse(
        wifi_available=bool(amenity.wifi_available) if amenity else False,
        wifi_speed_mbps=amenity.wifi_speed_mbps if amenity else None,
        outlet_count=amenity.outlet_count if amenity else None,
        outlet_accessibility=amenity.outlet_accessibility if amenity else None,
        noise_level=amenity.noise_level if amenity else None,
        has_natural_light=bool(amenity.has_natural_light) if amenity else False,
        has_ac=bool(amenity.has_ac) if amenity else False,
        has_heating=bool(amenity.has_heating) if amenity else False,
        has_parking=bool(amenity.has_parking) if amenity else False,
        has_accessible_entry=bool(amenity.has_accessible_entry) if amenity else False,
        allows_laptop=bool(amenity.allows_laptop) if amenity else True,
        min_spend_try=_to_float(amenity.min_spend_try, None) if amenity else None,
        has_food=bool(amenity.has_food) if amenity else False,
        has_alcohol=bool(amenity.has_alcohol) if amenity else False,
        pet_friendly=bool(amenity.pet_friendly) if amenity else False,
    )

    hours_payload = [
        CafeHourResponse(
            day_of_week=item.day_of_week,
            opens_at=item.opens_at,
            closes_at=item.closes_at,
            is_closed=item.is_closed,
        )
        for item in hours_rows
    ]
    images_payload = [
        CafeImageResponse(
            url=item.url,
            alt_text=_strip_seed_marker(item.alt_text),
            is_primary=item.is_primary,
            sort_order=item.sort_order,
        )
        for item in image_rows
    ]
    seats_payload = [
        CafeSeatResponse(
            seat_type=item.seat_type,
            total_count=item.total_count,
            available_count=item.available_count,
            has_outlet=item.has_outlet,
            notes=_strip_seed_marker(item.notes),
        )
        for item in seat_rows
    ]
    reviews_payload = [
        CafeReviewResponse(
            id=row.Review.id,
            rating=row.Review.rating,
            title=_strip_seed_marker(row.Review.title),
            body=_strip_seed_marker(row.Review.body),
            reviewer_name=row.display_name or row.username or "Anonim kullanıcı",
            visited_at=row.Review.visited_at,
            created_at=row.Review.created_at,
        )
        for row in review_rows
    ]

    return CafeDetailResponse(
        id=cafe.id,
        name=cafe.name,
        slug=cafe.slug,
        description=_strip_seed_marker(cafe.description),
        address=cafe.address,
        latitude=_to_float(cafe.latitude),
        longitude=_to_float(cafe.longitude),
        phone=cafe.phone,
        website=cafe.website,
        instagram=cafe.instagram,
        google_maps_url=cafe.google_maps_url,
        is_verified=cafe.is_verified,
        is_active=cafe.is_active,
        status=cafe.status,
        total_capacity=cafe.total_capacity,
        indoor_capacity=cafe.indoor_capacity,
        outdoor_capacity=cafe.outdoor_capacity,
        avg_rating=_to_float(cafe.avg_rating),
        review_count=cafe.review_count or 0,
        neighborhood=detail_row.neighborhood_name,
        neighborhood_slug=detail_row.neighborhood_slug,
        amenities=amenity_payload,
        hours=hours_payload,
        images=images_payload,
        seats=seats_payload,
        reviews=reviews_payload,
        created_at=cafe.created_at,
        updated_at=cafe.updated_at,
    )
