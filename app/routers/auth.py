import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from requests import RequestException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.database import get_db_session
from app.core.security import generate_plain_token, hash_token
from app.models.auth import AuthToken, UserSession
from app.models.user import User
from app.schemas.auth import (
    AuthUserResponse,
    LogoutRequest,
    LogoutResponse,
    MagicLinkRequest,
    MagicLinkResponse,
    RegisterRequest,
    RegisterResponse,
    VerifyRequest,
    VerifyResponse,
)
from app.services.email import render_magic_link_email, send_email_via_resend


router = APIRouter()
logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_email(email: str) -> str:
    value = (email or "").strip().lower()
    if "@" not in value or "." not in value.split("@")[-1]:
        raise HTTPException(status_code=422, detail="Geçerli bir email girin.")
    return value


def _normalize_username(username: str) -> str:
    value = (username or "").strip()
    if len(value) < 3 or len(value) > 50:
        raise HTTPException(status_code=422, detail="Kullanıcı adı 3-50 karakter olmalı.")
    return value


def _extract_session_token(request: Request, payload: Optional[LogoutRequest]) -> Optional[str]:
    if payload and payload.session_token:
        return payload.session_token.strip()
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    cookie_token = request.cookies.get("session_token")
    if cookie_token:
        return cookie_token.strip()
    return None


def _user_to_auth_response(user: User) -> AuthUserResponse:
    return AuthUserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        is_active=user.is_active,
        email_verified_at=user.email_verified_at,
    )


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db_session),
):
    email = _normalize_email(payload.email)
    username = _normalize_username(payload.username)

    existing_stmt = select(User).where((User.email == email) | (User.username == username))
    existing = await db.execute(existing_stmt)
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Email veya kullanıcı adı zaten kayıtlı.")

    user = User(
        email=email,
        username=username,
        display_name=(payload.display_name or "").strip() or None,
        role="user",
        is_active=True,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email veya kullanıcı adı zaten kayıtlı.")

    await db.refresh(user)
    return RegisterResponse(
        message="Kayıt başarılı. Magic link ile giriş yapabilirsiniz.",
        user=_user_to_auth_response(user),
    )


@router.post("/magic-link", response_model=MagicLinkResponse, status_code=status.HTTP_202_ACCEPTED)
async def request_magic_link(
    payload: MagicLinkRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    email = _normalize_email(payload.email)
    user_stmt = select(User).where(User.email == email, User.is_active.is_(True), User.deleted_at.is_(None))
    user_result = await db.execute(user_stmt)
    user = user_result.scalars().first()

    debug_token = None
    if user is not None:
        plain_token = generate_plain_token()
        debug_token = plain_token if settings.environment == "development" else None

        auth_token = AuthToken(
            user_id=user.id,
            token_hash=hash_token(plain_token),
            token_type="magic_link",
            ip_address=request.client.host if request.client else None,
            expires_at=_utcnow() + timedelta(minutes=settings.magic_link_expire_minutes),
        )
        db.add(auth_token)
        await db.commit()

        subject, html, text = render_magic_link_email(plain_token)
        try:
            await run_in_threadpool(
                send_email_via_resend,
                email,
                subject,
                html,
                text,
            )
        except RequestException:
            logger.exception("Magic link email gönderimi başarısız oldu: %s", email)
        else:
            logger.info("Magic link email gönderim denemesi tamamlandı: %s", email)

    return MagicLinkResponse(
        message="Eğer hesap mevcutsa magic link gönderilecektir.",
        status="queued",
        expires_in_minutes=settings.magic_link_expire_minutes,
        debug_token=debug_token,
    )


@router.post("/verify", response_model=VerifyResponse)
async def verify_magic_link(
    payload: VerifyRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    raw_token = (payload.token or "").strip()
    if not raw_token:
        raise HTTPException(status_code=422, detail="Token boş olamaz.")

    now = _utcnow()
    token_hash = hash_token(raw_token)

    token_stmt = select(AuthToken).where(
        AuthToken.token_hash == token_hash,
        AuthToken.used_at.is_(None),
        AuthToken.expires_at > now,
    )
    token_result = await db.execute(token_stmt)
    auth_token = token_result.scalars().first()
    if auth_token is None:
        raise HTTPException(status_code=401, detail="Token geçersiz veya süresi dolmuş.")

    user_result = await db.execute(select(User).where(User.id == auth_token.user_id))
    user = user_result.scalars().first()
    if user is None or not user.is_active or user.deleted_at is not None:
        raise HTTPException(status_code=401, detail="Kullanıcı aktif değil.")

    auth_token.used_at = now
    if user.email_verified_at is None:
        user.email_verified_at = now

    session_plain = generate_plain_token()
    session_expires_at = now + timedelta(days=settings.session_expire_days)
    session = UserSession(
        user_id=user.id,
        session_token_hash=hash_token(session_plain),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        last_active_at=now,
        expires_at=session_expires_at,
    )
    db.add(session)
    await db.commit()

    response.set_cookie(
        key="session_token",
        value=session_plain,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=settings.session_expire_days * 24 * 60 * 60,
    )
    return VerifyResponse(
        message="Giriş başarılı.",
        session_token=session_plain,
        session_expires_at=session_expires_at,
        user=_user_to_auth_response(user),
    )


@router.get("/session")
async def get_session(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    session_token = (request.cookies.get("session_token") or "").strip()
    if not session_token:
        return {"user": None}

    now = _utcnow()
    session_hash = hash_token(session_token)
    session_stmt = select(UserSession).where(
        UserSession.session_token_hash == session_hash,
        UserSession.expires_at > now,
    )
    session_result = await db.execute(session_stmt)
    session = session_result.scalars().first()
    if session is None:
        return {"user": None}

    user_stmt = select(User).where(
        User.id == session.user_id,
        User.is_active.is_(True),
        User.deleted_at.is_(None),
    )
    user_result = await db.execute(user_stmt)
    user = user_result.scalars().first()
    if user is None:
        return {"user": None}

    if session.last_active_at is None or (now - session.last_active_at) >= timedelta(minutes=5):
        session.last_active_at = now
        await db.commit()

    return {
        "user": {
            "id": str(user.id),
            "name": user.display_name or user.username,
            "email": user.email,
            "is_admin": user.role == "admin",
        }
    }


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    response: Response,
    payload: Optional[LogoutRequest] = None,
    db: AsyncSession = Depends(get_db_session),
):
    provided_token = _extract_session_token(request, payload)
    if not provided_token:
        raise HTTPException(status_code=401, detail="Aktif oturum bulunamadı.")

    session_hash = hash_token(provided_token)
    stmt = select(UserSession).where(UserSession.session_token_hash == session_hash)
    result = await db.execute(stmt)
    session = result.scalars().first()
    if session is None:
        raise HTTPException(status_code=401, detail="Aktif oturum bulunamadı.")

    await db.delete(session)
    await db.commit()
    response.delete_cookie("session_token")
    return LogoutResponse(message="Çıkış yapıldı.")
