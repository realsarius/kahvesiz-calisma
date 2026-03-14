import os
from dataclasses import dataclass
from dataclasses import field


def _csv_to_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Kahvesiz Calisma API")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    environment: str = os.getenv("ENVIRONMENT", "development")
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://user:pass@db:5432/kahvesiz"
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    secret_key: str = os.getenv("SECRET_KEY", "change-me")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    session_expire_days: int = int(os.getenv("SESSION_EXPIRE_DAYS", "30"))
    magic_link_expire_minutes: int = int(os.getenv("MAGIC_LINK_EXPIRE_MINUTES", "15"))
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    allowed_origins: list[str] = field(
        default_factory=lambda: _csv_to_list(
            os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
        )
    )
    resend_api_key: str = os.getenv("RESEND_API_KEY", "")
    resend_from_email: str = os.getenv("RESEND_FROM_EMAIL", "")
    kvkk_encryption_key: str = os.getenv("KVKK_ENCRYPTION_KEY", "")
    kvkk_hash_pepper: str = os.getenv("KVKK_HASH_PEPPER", "")


settings = Settings()
