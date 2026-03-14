from fastapi import FastAPI

from app.core.config import settings
from app.routers import auth, cafes, health, reviews


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
    return app


app = create_app()
