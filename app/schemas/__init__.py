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
from app.schemas.cafe import (
    CafeAmenityResponse,
    CafeDetailResponse,
    CafeHourResponse,
    CafeImageResponse,
    CafeListItem,
    CafeListResponse,
    CafeSeatResponse,
)
from app.schemas.user import UserPIISchema, UserPublicSchema
from app.schemas.review import ReviewCreate, ReviewListResponse, ReviewResponse, VoteCreate

__all__ = [
    "AuthUserResponse",
    "CafeAmenityResponse",
    "CafeDetailResponse",
    "CafeHourResponse",
    "CafeImageResponse",
    "CafeListItem",
    "CafeListResponse",
    "CafeSeatResponse",
    "LogoutRequest",
    "LogoutResponse",
    "MagicLinkRequest",
    "MagicLinkResponse",
    "RegisterRequest",
    "RegisterResponse",
    "ReviewCreate",
    "ReviewListResponse",
    "ReviewResponse",
    "UserPIISchema",
    "UserPublicSchema",
    "VerifyRequest",
    "VerifyResponse",
    "VoteCreate",
]
