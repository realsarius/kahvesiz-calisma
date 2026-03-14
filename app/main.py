from fastapi import FastAPI

from app.core.config import settings
from app.middleware.csrf import ensure_csrf_cookie_for_request, validate_csrf_request
from app.routers import admin, auth, cafes, health, reviews, users


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(cafes.router, prefix="/api/v1/cafes", tags=["cafes"])
    app.include_router(reviews.router, prefix="/api/v1", tags=["reviews"])
    app.include_router(users.router, prefix="/api/v1", tags=["users"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])

    @app.middleware("http")
    async def csrf_middleware(request, call_next):
        csrf_error = validate_csrf_request(request)
        if csrf_error is not None:
            return csrf_error

        response = await call_next(request)
        ensure_csrf_cookie_for_request(request, response)
        return response

    return app


app = create_app()
