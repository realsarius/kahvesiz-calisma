import re
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models import Cafe, CafeModerator, User
from app.schemas.admin import (
    AdminCafeCreate,
    AdminCafeResponse,
    AdminCafeUpdate,
    AdminModeratorAssignRequest,
    AdminModeratedCafe,
    AdminModeratedCafesResponse,
    AdminUserResponse,
)
from app.services.review_service import get_current_user


router = APIRouter()


def _slugify(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = normalized.strip("-")
    return normalized or "cafe"


async def _ensure_admin(request: Request, db: AsyncSession):
    user = await get_current_user(request, db)
    role = (user.role or "").strip().lower()
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekiyor.")
    return user


async def _ensure_unique_slug(name: str, db: AsyncSession, exclude_id: Optional[UUID] = None) -> str:
    base = _slugify(name)
    candidate = base
    suffix = 1
    while True:
        slug_stmt = select(Cafe.id).where(Cafe.slug == candidate)
        if exclude_id is not None:
            slug_stmt = slug_stmt.where(Cafe.id != exclude_id)
        existing = await db.execute(slug_stmt)
        if existing.scalar_one_or_none() is None:
            return candidate
        suffix += 1
        candidate = f"{base}-{suffix}"


def _map_cafe_response(cafe: Cafe) -> AdminCafeResponse:
    return AdminCafeResponse(
        id=cafe.id,
        name=cafe.name,
        slug=cafe.slug,
        map_url=cafe.map_url,
        img_url=cafe.img_url,
        location=cafe.location,
        has_sockets=cafe.has_sockets,
        has_toilet=cafe.has_toilet,
        has_wifi=cafe.has_wifi,
        can_take_calls=cafe.can_take_calls,
        seats=cafe.seats,
        coffee_price=cafe.coffee_price,
        details=cafe.details,
        created_at=cafe.created_at,
        updated_at=cafe.updated_at,
    )


@router.get("/cafes")
async def list_admin_cafes(
    request: Request,
    search: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db_session),
):
    await _ensure_admin(request, db)
    stmt = select(Cafe).where(Cafe.deleted_at.is_(None))
    if search:
        like_pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            (Cafe.name.ilike(like_pattern)) | (Cafe.location.ilike(like_pattern))
        )
    result = await db.execute(stmt.order_by(Cafe.created_at.desc()))
    cafes = result.scalars().all()
    return {"cafes": [_map_cafe_response(cafe) for cafe in cafes]}


@router.post("/cafes", status_code=status.HTTP_201_CREATED)
async def create_admin_cafe(
    request: Request,
    payload: AdminCafeCreate,
    db: AsyncSession = Depends(get_db_session),
):
    await _ensure_admin(request, db)
    slug = await _ensure_unique_slug(payload.name, db)
    cafe = Cafe(
        name=payload.name,
        slug=slug,
        address=payload.location or payload.name,
        location=payload.location,
        map_url=payload.map_url,
        img_url=payload.img_url,
        has_sockets=payload.has_sockets,
        has_toilet=payload.has_toilet,
        has_wifi=payload.has_wifi,
        can_take_calls=payload.can_take_calls,
        seats=payload.seats,
        coffee_price=payload.coffee_price,
        details=payload.details,
    )
    db.add(cafe)
    await db.commit()
    await db.refresh(cafe)
    return _map_cafe_response(cafe)


@router.put("/cafes/{cafe_id}")
async def update_admin_cafe(
    request: Request,
    cafe_id: UUID,
    payload: AdminCafeUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    await _ensure_admin(request, db)
    cafe = await db.get(Cafe, cafe_id)
    if cafe is None or cafe.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Kafe bulunamadı.")

    if cafe.name != payload.name:
        cafe.slug = await _ensure_unique_slug(payload.name, db, exclude_id=cafe_id)

    cafe.name = payload.name
    cafe.address = payload.location or payload.name
    cafe.location = payload.location
    cafe.map_url = payload.map_url
    cafe.img_url = payload.img_url
    cafe.has_sockets = payload.has_sockets
    cafe.has_toilet = payload.has_toilet
    cafe.has_wifi = payload.has_wifi
    cafe.can_take_calls = payload.can_take_calls
    cafe.seats = payload.seats
    cafe.coffee_price = payload.coffee_price
    cafe.details = payload.details
    await db.commit()
    await db.refresh(cafe)
    return _map_cafe_response(cafe)


@router.delete("/cafes/{cafe_id}")
async def delete_admin_cafe(
    request: Request,
    cafe_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    await _ensure_admin(request, db)
    cafe = await db.get(Cafe, cafe_id)
    if cafe is None or cafe.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Kafe bulunamadı.")

    cafe.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Kafe silindi."}


@router.post("/moderators")
async def assign_admin_moderator(
    request: Request,
    payload: AdminModeratorAssignRequest,
    db: AsyncSession = Depends(get_db_session),
):
    await _ensure_admin(request, db)
    user = await db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    cafe = await db.get(Cafe, payload.cafe_id)
    if cafe is None or cafe.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Kafe bulunamadı.")

    existing_stmt = select(CafeModerator).where(
        CafeModerator.user_id == payload.user_id,
        CafeModerator.cafe_id == payload.cafe_id,
    )
    existing = await db.execute(existing_stmt)
    if existing.scalars().first():
        return {"assigned": False, "message": "Kullanıcı zaten moderatör."}

    moderator = CafeModerator(user_id=payload.user_id, cafe_id=payload.cafe_id)
    db.add(moderator)
    await db.commit()
    return {"assigned": True, "message": "Moderatör atandı."}


@router.delete("/moderators/{user_id}/{cafe_id}")
async def remove_admin_moderator(
    request: Request,
    user_id: UUID,
    cafe_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    await _ensure_admin(request, db)

    stmt = select(CafeModerator).where(
        CafeModerator.user_id == user_id,
        CafeModerator.cafe_id == cafe_id,
    )
    result = await db.execute(stmt)
    moderator = result.scalars().first()
    if moderator is None:
        raise HTTPException(status_code=404, detail="Moderatör kaydı bulunamadı.")

    await db.delete(moderator)
    await db.commit()
    return {"message": "Moderatör kaldırıldı."}


@router.get("/moderators/{user_id}")
async def list_admin_moderated_cafes(
    request: Request,
    user_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    await _ensure_admin(request, db)
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    stmt = (
        select(Cafe)
        .join(CafeModerator, CafeModerator.cafe_id == Cafe.id)
        .where(CafeModerator.user_id == user_id, Cafe.deleted_at.is_(None))
    )
    result = await db.execute(stmt)
    cafes = result.scalars().all()
    return AdminModeratedCafesResponse(
        cafes=[AdminModeratedCafe(id=cafe.id, name=cafe.name) for cafe in cafes]
    )


@router.get("/users")
async def list_admin_users(
    request: Request,
    search: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db_session),
):
    await _ensure_admin(request, db)
    stmt = select(User).where(User.deleted_at.is_(None))
    if search:
        like_pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            (User.email.ilike(like_pattern)) | (User.name.ilike(like_pattern))
        )
    result = await db.execute(stmt.order_by(User.created_at.desc()))
    users = result.scalars().all()
    return {
        "users": [
            AdminUserResponse(
                id=user.id,
                name=user.display_name or user.username or user.email,
                email=user.email,
                is_admin=((user.role or "user").strip().lower() == "admin"),
                created_at=user.created_at,
            )
            for user in users
        ]
    }
