import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from requests import RequestException
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.database import get_db_session
from app.core.pii_protection import protect_user_pii_payload
from app.core.security import generate_plain_token, hash_token
from app.middleware.csrf import (
    CSRF_COOKIE_NAME,
    clear_csrf_cookie,
    generate_csrf_token,
    set_csrf_cookie,
)
from app.models.auth import AuthToken, UserSession
from app.models.user import User
from app.models.user_pii import UserPII
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
from app.services.email import (
    render_email_verify_email,
    render_magic_link_email,
    send_email_via_resend,
)


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


def _get_client_ip(request: Optional[object]) -> Optional[str]:
    client = getattr(request, "client", None)
    return getattr(client, "host", None) if client else None


def _get_user_agent(request: Optional[object]) -> Optional[str]:
    headers = getattr(request, "headers", None)
    if not headers:
        return None
    return headers.get("user-agent")


async def _verify_token_and_open_session(
    raw_token: str,
    request: Optional[Request],
    response: Optional[Response],
    db: AsyncSession,
) -> VerifyResponse:
    token = (raw_token or "").strip()
    if not token:
        raise HTTPException(status_code=422, detail="Token boş olamaz.")

    now = _utcnow()
    token_hash = hash_token(token)

    token_stmt = select(AuthToken).where(
        AuthToken.token_hash == token_hash,
        AuthToken.used_at.is_(None),
        AuthToken.expires_at > now,
    )
    token_result = await db.execute(token_stmt)
    auth_token = token_result.scalars().first()
    if auth_token is None or auth_token.token_type not in {"magic_link", "email_verify"}:
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
    ip_address = _get_client_ip(request)
    user_agent = _get_user_agent(request)
    session = UserSession(
        user_id=user.id,
        session_token_hash=hash_token(session_plain),
        ip_address=ip_address,
        user_agent=user_agent,
        last_active_at=now,
        expires_at=session_expires_at,
    )
    db.add(session)
    await db.commit()

    if response is None:
        raise HTTPException(status_code=500, detail="Response nesnesi bulunamadı.")

    response.set_cookie(
        key="session_token",
        value=session_plain,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=settings.session_expire_days * 24 * 60 * 60,
    )
    set_csrf_cookie(response, generate_csrf_token())
    return VerifyResponse(
        message="Giriş başarılı.",
        session_expires_at=session_expires_at,
        user=_user_to_auth_response(user),
    )


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    email = _normalize_email(payload.email)
    username = _normalize_username(payload.username)
    if not payload.consent_given:
        raise HTTPException(status_code=422, detail="KVKK onayı olmadan kayıt tamamlanamaz.")

    existing_stmt = select(User).where((User.email == email) | (User.username == username))
    existing = await db.execute(existing_stmt)
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Email veya kullanıcı adı zaten kayıtlı.")

    now = _utcnow()
    consent_ip = _get_client_ip(request)
    country_code = (payload.country_code or "TR").strip().upper()
    if len(country_code) != 2:
        raise HTTPException(status_code=422, detail="country_code 2 karakter olmalı.")

    user = User(
        id=uuid.uuid4(),
        email=email,
        username=username,
        display_name=(payload.display_name or "").strip() or None,
        role="user",
        is_active=True,
    )
    protected_pii = protect_user_pii_payload(
        user.id,
        {
            "full_name": (payload.full_name or "").strip() or None,
            "phone": (payload.phone or "").strip() or None,
            "address_line1": (payload.address_line1 or "").strip() or None,
            "address_line2": (payload.address_line2 or "").strip() or None,
            "city": (payload.city or "").strip() or None,
            "district": (payload.district or "").strip() or None,
            "postal_code": (payload.postal_code or "").strip() or None,
        },
    )
    user_pii = UserPII(
        user_id=user.id,
        full_name=protected_pii.get("full_name"),
        phone=protected_pii.get("phone"),
        birth_date=payload.birth_date,
        address_line1=protected_pii.get("address_line1"),
        address_line2=protected_pii.get("address_line2"),
        city=protected_pii.get("city"),
        district=protected_pii.get("district"),
        postal_code=protected_pii.get("postal_code"),
        country_code=country_code,
        consent_given_at=now,
        consent_ip=consent_ip,
        consent_version=(payload.consent_version or "").strip() or "v1",
    )

    verify_plain_token = generate_plain_token()
    verify_token = AuthToken(
        user_id=user.id,
        token_hash=hash_token(verify_plain_token),
        token_type="email_verify",
        ip_address=consent_ip,
        expires_at=now + timedelta(minutes=settings.magic_link_expire_minutes),
    )

    db.add(user)
    flush = getattr(db, "flush", None)
    if callable(flush):
        await flush()
    db.add(user_pii)
    db.add(verify_token)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        logger.exception("Register transaction failed for email=%s username=%s", email, username)
        raise HTTPException(status_code=409, detail="Email veya kullanıcı adı zaten kayıtlı.")

    subject, html, text = render_email_verify_email(verify_plain_token)
    try:
        await run_in_threadpool(
            send_email_via_resend,
            email,
            subject,
            html,
            text,
        )
    except RequestException:
        logger.exception("Email verify gönderimi başarısız oldu: %s", email)
    else:
        logger.info("Email verify gönderim denemesi tamamlandı: %s", email)

    return RegisterResponse(
        message="Kayıt başarılı. Email doğrulama ve magic link ile giriş yapabilirsiniz.",
        user=_user_to_auth_response(user),
        debug_email_verify_token=verify_plain_token if settings.environment == "development" else None,
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
    return await _verify_token_and_open_session(payload.token, request, response, db)


@router.get("/verify", response_model=VerifyResponse)
async def verify_magic_link_get(
    request: Request,
    response: Response,
    token: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db_session),
):
    return await _verify_token_and_open_session(token, request, response, db)


@router.get("/csrf")
async def get_csrf_token(
    request: Request,
    response: Response,
):
    csrf_token = (request.cookies.get(CSRF_COOKIE_NAME) or "").strip()
    if not csrf_token:
        csrf_token = generate_csrf_token()
        set_csrf_cookie(response, csrf_token)
    return {"csrf_token": csrf_token}


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
            "role": user.role,
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

    if payload and payload.logout_all:
        await db.execute(
            delete(UserSession).where(
                UserSession.user_id == session.user_id,
            )
        )
    else:
        await db.delete(session)
    await db.commit()
    response.delete_cookie("session_token")
    clear_csrf_cookie(response)
    return LogoutResponse(message="Çıkış yapıldı.")


@router.post("/bridge-session")
async def bridge_session(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    """Create a FastAPI session from an active legacy (Flask) session.

    The endpoint forwards the caller's cookies to the legacy
    ``/api/auth/session`` endpoint (reachable via the nginx-dev container)
    to verify the legacy session.  When valid it looks up (or auto-creates)
    the corresponding FastAPI user and issues a ``session_token`` cookie so
    that FastAPI-only endpoints (e.g. admin panel) work seamlessly.
    """

    import httpx

    # If the caller already has a valid FastAPI session, skip.
    existing_session_token = (request.cookies.get("session_token") or "").strip()
    if existing_session_token:
        session_hash = hash_token(existing_session_token)
        stmt = select(UserSession).where(
            UserSession.session_token_hash == session_hash,
            UserSession.expires_at > _utcnow(),
        )
        result = await db.execute(stmt)
        if result.scalars().first() is not None:
            return {"message": "FastAPI oturumu zaten mevcut."}

    # Forward cookies to legacy session endpoint via nginx.
    cookie_header = request.headers.get("cookie", "")
    if not cookie_header:
        raise HTTPException(status_code=401, detail="Legacy oturum cookie'si bulunamadı.")

    legacy_base_url = "http://nginx-dev:80"
    try:
        async with httpx.AsyncClient(base_url=legacy_base_url, timeout=5.0) as client:
            legacy_resp = await client.get(
                "/api/auth/session",
                headers={"cookie": cookie_header},
            )
    except Exception:
        logger.exception("Legacy session doğrulaması sırasında bağlantı hatası.")
        raise HTTPException(status_code=502, detail="Legacy servisine bağlanılamadı.")

    if legacy_resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Legacy oturum geçersiz.")

    try:
        legacy_payload = legacy_resp.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Legacy yanıtı ayrıştırılamadı.")

    # The legacy response may be wrapped in {'data': {'user': {...}}} or {'user': {...}}.
    legacy_data = legacy_payload.get("data", legacy_payload) if isinstance(legacy_payload, dict) else {}
    legacy_user = legacy_data.get("user") if isinstance(legacy_data, dict) else None
    if not legacy_user or not isinstance(legacy_user, dict):
        raise HTTPException(status_code=401, detail="Legacy oturumda kullanıcı bilgisi bulunamadı.")

    legacy_email = (legacy_user.get("email") or "").strip().lower()
    legacy_name = (legacy_user.get("name") or "").strip()
    legacy_is_admin = bool(legacy_user.get("is_admin", False))

    if not legacy_email:
        raise HTTPException(status_code=401, detail="Legacy kullanıcısında email bilgisi yok.")

    # Find or create the corresponding FastAPI user.
    user_stmt = select(User).where(User.email == legacy_email)
    user_result = await db.execute(user_stmt)
    user = user_result.scalars().first()

    if user is None:
        user = User(
            id=uuid.uuid4(),
            email=legacy_email,
            username=legacy_email.split("@")[0],
            display_name=legacy_name or None,
            role="admin" if legacy_is_admin else "user",
            is_active=True,
            email_verified_at=_utcnow(),
        )
        db.add(user)
        try:
            await db.commit()
            await db.refresh(user)
        except IntegrityError:
            await db.rollback()
            # Username collision — retry lookup.
            user_result = await db.execute(select(User).where(User.email == legacy_email))
            user = user_result.scalars().first()
            if user is None:
                raise HTTPException(status_code=500, detail="Kullanıcı eşleştirilemedi.")
    else:
        # Sync role from legacy if needed.
        target_role = "admin" if legacy_is_admin else "user"
        if user.role != target_role:
            user.role = target_role
            await db.commit()

    if not user.is_active or user.deleted_at is not None:
        raise HTTPException(status_code=403, detail="Kullanıcı aktif değil.")

    # Create a FastAPI session.
    now = _utcnow()
    session_plain = generate_plain_token()
    session_expires_at = now + timedelta(days=settings.session_expire_days)
    ip_address = _get_client_ip(request)
    user_agent = _get_user_agent(request)
    session = UserSession(
        user_id=user.id,
        session_token_hash=hash_token(session_plain),
        ip_address=ip_address,
        user_agent=user_agent,
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
    set_csrf_cookie(response, generate_csrf_token())

    return {
        "message": "FastAPI oturumu oluşturuldu.",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.display_name or user.username,
            "role": user.role,
            "is_admin": user.role == "admin",
        },
    }
