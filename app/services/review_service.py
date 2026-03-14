import base64
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

from fastapi import HTTPException, Request
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_token
from app.models.auth import UserSession
from app.models.cafe import Cafe
from app.models.review import Review
from app.models.review_vote import ReviewVote
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewListResponse, ReviewResponse, VoteCreate


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _extract_session_token(request: Request) -> Optional[str]:
    auth_header = (request.headers.get("authorization") or "").strip()
    if auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip() or None

    cookie_token = (request.cookies.get("session_token") or "").strip()
    return cookie_token or None


async def get_current_user(request: Request, db: AsyncSession, required: bool = True) -> Optional[User]:
    session_token = _extract_session_token(request)
    if not session_token:
        if required:
            raise HTTPException(status_code=401, detail="Giriş yapmanız gerekiyor.")
        return None

    now = _utcnow()
    session_hash = hash_token(session_token)
    session_stmt = select(UserSession).where(
        UserSession.session_token_hash == session_hash,
        UserSession.expires_at > now,
    )
    session_result = await db.execute(session_stmt)
    session = session_result.scalars().first()
    if session is None:
        if required:
            raise HTTPException(status_code=401, detail="Oturum geçersiz veya süresi dolmuş.")
        return None

    user_stmt = select(User).where(
        User.id == session.user_id,
        User.is_active.is_(True),
        User.deleted_at.is_(None),
    )
    user_result = await db.execute(user_stmt)
    user = user_result.scalars().first()
    if user is None:
        if required:
            raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı veya aktif değil.")
        return None

    if session.last_active_at is None or (now - session.last_active_at).total_seconds() >= 300:
        session.last_active_at = now
        await db.commit()

    return user


def _encode_cursor(created_at: datetime, review_id: uuid.UUID) -> str:
    timestamp = created_at.astimezone(timezone.utc).isoformat()
    raw = f"{timestamp}:{review_id}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")


def _decode_cursor(cursor: str) -> Tuple[datetime, uuid.UUID]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        timestamp_raw, id_raw = raw.rsplit(":", 1)
        parsed_dt = datetime.fromisoformat(timestamp_raw)
        if parsed_dt.tzinfo is None:
            parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
        return parsed_dt, uuid.UUID(id_raw)
    except Exception as exc:  # pragma: no cover - defensive parsing
        raise HTTPException(status_code=422, detail="Geçersiz cursor formatı.") from exc


async def _get_active_cafe_or_404(cafe_id: uuid.UUID, db: AsyncSession) -> Cafe:
    cafe_stmt = select(Cafe).where(
        Cafe.id == cafe_id,
        Cafe.is_active.is_(True),
        Cafe.deleted_at.is_(None),
    )
    cafe_result = await db.execute(cafe_stmt)
    cafe = cafe_result.scalars().first()
    if cafe is None:
        raise HTTPException(status_code=404, detail="Kafe bulunamadı.")
    return cafe


def _normalize_vote(vote: str) -> str:
    normalized = (vote or "").strip().lower()
    if normalized == "upvote":
        return "helpful"
    if normalized == "downvote":
        return "unhelpful"
    if normalized in {"helpful", "unhelpful"}:
        return normalized
    raise HTTPException(status_code=422, detail="Geçersiz oy tipi.")


def _normalize_role(role: Optional[str]) -> str:
    return (role or "").strip().lower()


async def list_reviews(
    cafe_id: uuid.UUID,
    db: AsyncSession,
    limit: int,
    cursor: Optional[str] = None,
    current_user: Optional[User] = None,
) -> ReviewListResponse:
    await _get_active_cafe_or_404(cafe_id, db)

    helpful_count_expr = func.sum(case((ReviewVote.vote == "helpful", 1), else_=0)).label("helpful_count")
    unhelpful_count_expr = func.sum(case((ReviewVote.vote == "unhelpful", 1), else_=0)).label("unhelpful_count")

    count_stmt = select(func.count(Review.id)).where(
        Review.cafe_id == cafe_id,
        Review.deleted_at.is_(None),
    )
    count_result = await db.execute(count_stmt)
    total_count = int(count_result.scalar_one() or 0)

    stmt = (
        select(
            Review,
            User.display_name.label("display_name"),
            User.username.label("username"),
            func.coalesce(helpful_count_expr, 0),
            func.coalesce(unhelpful_count_expr, 0),
        )
        .join(User, User.id == Review.user_id, isouter=True)
        .join(ReviewVote, ReviewVote.review_id == Review.id, isouter=True)
        .where(
            Review.cafe_id == cafe_id,
            Review.deleted_at.is_(None),
        )
        .group_by(Review.id, User.display_name, User.username)
    )

    if cursor:
        cursor_dt, cursor_id = _decode_cursor(cursor)
        stmt = stmt.where(
            or_(
                Review.created_at < cursor_dt,
                and_(Review.created_at == cursor_dt, Review.id < cursor_id),
            )
        )

    stmt = stmt.order_by(Review.created_at.desc(), Review.id.desc()).limit(limit + 1)
    result = await db.execute(stmt)
    rows = result.all()

    my_vote_map = {}
    if current_user and rows:
        review_ids = [row[0].id for row in rows[:limit]]
        if review_ids:
            vote_result = await db.execute(
                select(ReviewVote.review_id, ReviewVote.vote).where(
                    ReviewVote.user_id == current_user.id,
                    ReviewVote.review_id.in_(review_ids),
                )
            )
            my_vote_map = {row.review_id: row.vote for row in vote_result.all()}

    page_rows = rows[:limit]
    items = [
        ReviewResponse(
            id=row[0].id,
            user_id=row[0].user_id,
            cafe_id=row[0].cafe_id,
            rating=row[0].rating,
            title=row[0].title,
            body=row[0].body,
            noise_rating=row[0].noise_rating,
            wifi_rating=row[0].wifi_rating,
            outlet_rating=row[0].outlet_rating,
            visited_at=row[0].visited_at,
            is_verified_visit=row[0].is_verified_visit,
            reviewer_name=row.display_name or row.username or "Anonim kullanıcı",
            helpful_count=int(row[3] or 0),
            unhelpful_count=int(row[4] or 0),
            my_vote=my_vote_map.get(row[0].id),
            created_at=row[0].created_at,
            updated_at=row[0].updated_at,
        )
        for row in page_rows
    ]

    next_cursor = None
    if len(rows) > limit and page_rows:
        last_review = page_rows[-1][0]
        next_cursor = _encode_cursor(last_review.created_at, last_review.id)

    return ReviewListResponse(
        items=items,
        next_cursor=next_cursor,
        limit=limit,
        total_count=total_count,
    )


async def create_review(
    cafe_id: uuid.UUID,
    payload: ReviewCreate,
    current_user: User,
    db: AsyncSession,
) -> ReviewResponse:
    await _get_active_cafe_or_404(cafe_id, db)

    existing_stmt = select(Review).where(
        Review.cafe_id == cafe_id,
        Review.user_id == current_user.id,
        Review.deleted_at.is_(None),
    )
    existing_result = await db.execute(existing_stmt)
    existing_review = existing_result.scalars().first()
    if existing_review is not None:
        raise HTTPException(status_code=409, detail="Bu kafe için zaten yorumunuz var.")

    review = Review(
        user_id=current_user.id,
        cafe_id=cafe_id,
        rating=payload.rating,
        title=payload.title,
        body=payload.body,
        noise_rating=payload.noise_rating,
        wifi_rating=payload.wifi_rating,
        outlet_rating=payload.outlet_rating,
        visited_at=payload.visited_at,
        is_verified_visit=False,
    )
    db.add(review)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Bu kafe için zaten yorumunuz var.") from exc

    return ReviewResponse(
        id=review.id,
        user_id=review.user_id,
        cafe_id=review.cafe_id,
        rating=review.rating,
        title=review.title,
        body=review.body,
        noise_rating=review.noise_rating,
        wifi_rating=review.wifi_rating,
        outlet_rating=review.outlet_rating,
        visited_at=review.visited_at,
        is_verified_visit=review.is_verified_visit,
        reviewer_name=current_user.display_name or current_user.username,
        helpful_count=0,
        unhelpful_count=0,
        my_vote=None,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


async def delete_review(
    review_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> None:
    review_stmt = select(Review).where(
        Review.id == review_id,
        Review.deleted_at.is_(None),
    )
    review_result = await db.execute(review_stmt)
    review = review_result.scalars().first()
    if review is None:
        raise HTTPException(status_code=404, detail="Yorum bulunamadı.")

    role = _normalize_role(current_user.role)
    is_owner = review.user_id == current_user.id
    is_staff = role in {"admin", "moderator", "mod"}
    if not is_owner and not is_staff:
        raise HTTPException(status_code=403, detail="Bu yorumu silme yetkiniz yok.")

    review.deleted_at = _utcnow()
    await db.commit()


async def upsert_review_vote(
    review_id: uuid.UUID,
    payload: VoteCreate,
    current_user: User,
    db: AsyncSession,
) -> None:
    normalized_vote = _normalize_vote(payload.vote)

    review_stmt = select(Review).where(
        Review.id == review_id,
        Review.deleted_at.is_(None),
    )
    review_result = await db.execute(review_stmt)
    review = review_result.scalars().first()
    if review is None:
        raise HTTPException(status_code=404, detail="Yorum bulunamadı.")

    existing_stmt = select(ReviewVote).where(
        ReviewVote.review_id == review_id,
        ReviewVote.user_id == current_user.id,
    )
    existing_result = await db.execute(existing_stmt)
    existing_vote = existing_result.scalars().first()

    if existing_vote is None:
        db.add(
            ReviewVote(
                review_id=review_id,
                user_id=current_user.id,
                vote=normalized_vote,
            )
        )
    else:
        existing_vote.vote = normalized_vote

    await db.commit()


async def delete_review_vote(
    review_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> None:
    vote_stmt = select(ReviewVote).where(
        ReviewVote.review_id == review_id,
        ReviewVote.user_id == current_user.id,
    )
    vote_result = await db.execute(vote_stmt)
    vote = vote_result.scalars().first()
    if vote is None:
        raise HTTPException(status_code=404, detail="Geri çekilecek oy bulunamadı.")

    await db.delete(vote)
    await db.commit()
