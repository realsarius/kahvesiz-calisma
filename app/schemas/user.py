from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserPublicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    username: str
    display_name: Optional[str] = None
    role: str
    avatar_url: Optional[str] = None
    email_verified_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserPIISchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    full_name: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    postal_code: Optional[str] = None
    country_code: str
    consent_given_at: datetime
    consent_version: Optional[str] = None
