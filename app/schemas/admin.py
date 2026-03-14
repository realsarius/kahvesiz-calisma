from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AdminCafeBase(BaseModel):
    name: str
    map_url: str
    img_url: str
    location: str
    has_sockets: bool = Field(False, alias="has_sockets")
    has_toilet: bool = Field(False, alias="has_toilet")
    has_wifi: bool = Field(False, alias="has_wifi")
    can_take_calls: bool = Field(False, alias="can_take_calls")
    seats: str
    coffee_price: str
    details: Optional[str] = None


class AdminCafeCreate(AdminCafeBase):
    pass


class AdminCafeUpdate(AdminCafeBase):
    pass


class AdminCafeResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    map_url: Optional[str] = None
    img_url: Optional[str] = None
    location: Optional[str] = None
    has_sockets: bool
    has_toilet: bool
    has_wifi: bool
    can_take_calls: bool
    seats: Optional[str] = None
    coffee_price: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AdminUserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    is_admin: bool
    created_at: datetime


class AdminModeratedCafe(BaseModel):
    id: UUID
    name: str


class AdminModeratedCafesResponse(BaseModel):
    cafes: List[AdminModeratedCafe]


class AdminModeratorsResponse(BaseModel):
    moderators: List[AdminModeratedCafe]


class AdminModeratorAssignRequest(BaseModel):
    user_id: UUID
    cafe_id: UUID


class AdminAssignmentsResponse(BaseModel):
    assigned: bool
    message: Optional[str]
