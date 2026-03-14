import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, Union

from fastapi import HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import AuthToken, UserSession
from app.models.review import Review
from app.models.user import User
from app.models.user_pii import UserPII


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_role(role: Optional[str]) -> str:
    return (role or "").strip().lower()


async def get_active_user_or_404(user_id: uuid.UUID, db: AsyncSession) -> User:
    stmt = select(User).where(
        User.id == user_id,
        User.is_active.is_(True),
        User.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    return user


async def delete_user_account(
    actor_user: User,
    target_user: User,
    db: AsyncSession,
) -> Dict[str, Union[int, bool, str]]:
    actor_role = _normalize_role(getattr(actor_user, "role", None))
    is_self_delete = actor_user.id == target_user.id
    is_admin = actor_role == "admin"

    if not is_self_delete and not is_admin:
        raise HTTPException(status_code=403, detail="Bu kullanıcıyı silme yetkiniz yok.")

    now = _utcnow()

    target_user.is_active = False
    target_user.deleted_at = now

    pii_delete_result = await db.execute(
        delete(UserPII).where(UserPII.user_id == target_user.id)
    )

    review_anonymize_result = await db.execute(
        update(Review)
        .where(Review.user_id == target_user.id)
        .values(user_id=None, updated_at=now)
    )

    session_delete_result = await db.execute(
        delete(UserSession).where(UserSession.user_id == target_user.id)
    )

    token_revoke_result = await db.execute(
        update(AuthToken)
        .where(
            AuthToken.user_id == target_user.id,
            AuthToken.used_at.is_(None),
        )
        .values(used_at=now)
    )

    await db.commit()

    return {
        "user_soft_deleted": True,
        "pii_deleted": int(pii_delete_result.rowcount or 0),
        "reviews_anonymized": int(review_anonymize_result.rowcount or 0),
        "sessions_invalidated": int(session_delete_result.rowcount or 0),
        "tokens_revoked": int(token_revoke_result.rowcount or 0),
        "mode": "self" if is_self_delete else "admin",
    }
