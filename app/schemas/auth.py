from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RegisterRequest(BaseModel):
    email: str
    username: str
    display_name: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    postal_code: Optional[str] = None
    country_code: Optional[str] = "TR"
    consent_given: bool = True
    consent_version: Optional[str] = None


class MagicLinkRequest(BaseModel):
    email: str


class VerifyRequest(BaseModel):
    token: str


class LogoutRequest(BaseModel):
    session_token: Optional[str] = None
    logout_all: bool = False


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
    debug_email_verify_token: Optional[str] = None


class MagicLinkResponse(BaseModel):
    message: str
    status: str
    expires_in_minutes: int
    debug_token: Optional[str] = None


class VerifyResponse(BaseModel):
    message: str
    session_expires_at: datetime
    user: AuthUserResponse


class LogoutResponse(BaseModel):
    message: str
