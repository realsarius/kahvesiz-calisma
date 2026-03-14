import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.services import account_deletion_service, review_service


router = APIRouter()


def _normalize_role(role: Optional[str]) -> str:
    return (role or "").strip().lower()


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
