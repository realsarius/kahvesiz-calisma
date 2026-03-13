"""Pydantic schema package for API contracts."""

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
from app.schemas.user import UserPIISchema, UserPublicSchema

__all__ = [
    "AuthUserResponse",
    "LogoutRequest",
    "LogoutResponse",
    "MagicLinkRequest",
    "MagicLinkResponse",
    "RegisterRequest",
    "RegisterResponse",
    "UserPIISchema",
    "UserPublicSchema",
    "VerifyRequest",
    "VerifyResponse",
]
