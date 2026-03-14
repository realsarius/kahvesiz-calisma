import secrets
from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.core.config import settings


SESSION_COOKIE_NAME = "session_token"
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAMES = ("x-csrftoken", "x-csrf-token")
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
API_PREFIX = "/api/v1"
EXEMPT_PATHS = {
    "/api/v1/auth/register",
    "/api/v1/auth/magic-link",
    "/api/v1/auth/verify",
    "/api/v1/auth/csrf",
    "/api/v1/auth/bridge-session",
}


def _normalize(value: Optional[str]) -> str:
    return (value or "").strip()


def _is_api_v1_path(path: str) -> bool:
    return path == API_PREFIX or path.startswith(f"{API_PREFIX}/")


def _is_exempt_path(path: str) -> bool:
    if path in EXEMPT_PATHS:
        return True
    return path.startswith("/api/v1/auth/verify/")


def _has_session_cookie(request: Request) -> bool:
    return bool(_normalize(request.cookies.get(SESSION_COOKIE_NAME)))


def _get_header_csrf_token(request: Request) -> Optional[str]:
    for header_name in CSRF_HEADER_NAMES:
        token = _normalize(request.headers.get(header_name))
        if token:
            return token
    return None


def should_enforce_csrf(request: Request) -> bool:
    method = request.method.upper()
    path = request.url.path

    if method not in WRITE_METHODS:
        return False
    if not _is_api_v1_path(path):
        return False
    if _is_exempt_path(path):
        return False
    if not _has_session_cookie(request):
        return False
    return True


def validate_csrf_request(request: Request) -> Optional[JSONResponse]:
    if not should_enforce_csrf(request):
        return None

    header_token = _get_header_csrf_token(request)
    cookie_token = _normalize(request.cookies.get(CSRF_COOKIE_NAME))
    if not header_token or not cookie_token:
        return JSONResponse(
            status_code=403,
            content={"detail": "CSRF token eksik."},
        )

    if not secrets.compare_digest(header_token, cookie_token):
        return JSONResponse(
            status_code=403,
            content={"detail": "CSRF token doğrulanamadı."},
        )
    return None


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def set_csrf_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=token,
        httponly=False,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=settings.session_expire_days * 24 * 60 * 60,
        path="/",
    )


def clear_csrf_cookie(response: Response) -> None:
    response.delete_cookie(
        key=CSRF_COOKIE_NAME,
        path="/",
    )


def ensure_csrf_cookie_for_request(request: Request, response: Response) -> None:
    method = request.method.upper()
    path = request.url.path
    if method not in SAFE_METHODS:
        return
    if not _is_api_v1_path(path):
        return
    if not _has_session_cookie(request):
        return
    if _normalize(request.cookies.get(CSRF_COOKIE_NAME)):
        return
    set_csrf_cookie(response, generate_csrf_token())

