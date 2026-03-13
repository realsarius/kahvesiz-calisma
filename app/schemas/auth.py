from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RegisterRequest(BaseModel):
    email: str
    username: str
    display_name: Optional[str] = None


class MagicLinkRequest(BaseModel):
    email: str


class VerifyRequest(BaseModel):
    token: str


class LogoutRequest(BaseModel):
    session_token: Optional[str] = None


class AuthUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    username: str
    display_name: Optional[str] = None
    role: str
    is_active: bool
    email_verified_at: Optional[datetime] = None


class RegisterResponse(BaseModel):
    message: str
    user: AuthUserResponse


class MagicLinkResponse(BaseModel):
    message: str
    status: str
    expires_in_minutes: int
    debug_token: Optional[str] = None


class VerifyResponse(BaseModel):
    message: str
    session_token: str
    session_expires_at: datetime
    user: AuthUserResponse


class LogoutResponse(BaseModel):
    message: str
