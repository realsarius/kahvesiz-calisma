import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.user_pii import UserPII
from app.schemas.user import ConsentUpdateRequest, ConsentUpdateResponse
from app.services import account_deletion_service, review_service


router = APIRouter()


def _normalize_role(role: Optional[str]) -> str:
    return (role or "").strip().lower()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@router.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    current_user = await review_service.get_current_user(request, db, required=True)
    await account_deletion_service.delete_user_account(
        actor_user=current_user,
        target_user=current_user,
        db=db,
    )

    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie("session_token")
    return response


@router.delete("/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_as_admin(
    user_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    current_user = await review_service.get_current_user(request, db, required=True)
    role = _normalize_role(getattr(current_user, "role", None))
    if role != "admin":
        raise HTTPException(status_code=403, detail="Bu işlem için admin yetkisi gerekiyor.")

    target_user = await account_deletion_service.get_active_user_or_404(user_id, db)
    await account_deletion_service.delete_user_account(
        actor_user=current_user,
        target_user=target_user,
        db=db,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/users/me/consent", response_model=ConsentUpdateResponse)
async def update_my_consent(
    payload: ConsentUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    current_user = await review_service.get_current_user(request, db, required=True)

    pii_result = await db.execute(
        select(UserPII).where(UserPII.user_id == current_user.id)
    )
    user_pii = pii_result.scalars().first()
    if user_pii is None:
        raise HTTPException(status_code=404, detail="Kullanıcı KVKK kaydı bulunamadı.")

    now = _utcnow()
    user_pii.consent_given_at = now
    user_pii.consent_version = payload.consent_version.strip()
    await db.commit()

    return ConsentUpdateResponse(
        message="Cookie rıza tercihi güncellendi.",
        consent_version=user_pii.consent_version or payload.consent_version.strip(),
        consent_given_at=user_pii.consent_given_at,
        analytics_allowed=payload.analytics_allowed,
        marketing_allowed=payload.marketing_allowed,
    )
