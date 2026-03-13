from datetime import datetime, time
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class CafeListItem(BaseModel):
    id: UUID
    name: str
    slug: str
    address: str
    latitude: float
    longitude: float
    avg_rating: float
    review_count: int
    neighborhood: Optional[str] = None
    neighborhood_slug: Optional[str] = None
    wifi_available: bool = False
    noise_level: Optional[str] = None
    created_at: datetime


class CafeListResponse(BaseModel):
    items: List[CafeListItem]
    next_cursor: Optional[str] = None
    limit: int
    total_count: int


class CafeAmenityResponse(BaseModel):
    wifi_available: bool = False
    wifi_speed_mbps: Optional[int] = None
    outlet_count: Optional[int] = None
    outlet_accessibility: Optional[str] = None
    noise_level: Optional[str] = None
    has_natural_light: bool = False
    has_ac: bool = False
    has_heating: bool = False
    has_parking: bool = False
    has_accessible_entry: bool = False
    allows_laptop: bool = True
    min_spend_try: Optional[float] = None
    has_food: bool = False
    has_alcohol: bool = False
    pet_friendly: bool = False


class CafeHourResponse(BaseModel):
    day_of_week: int
    opens_at: Optional[time] = None
    closes_at: Optional[time] = None
    is_closed: bool


class CafeImageResponse(BaseModel):
    url: str
    alt_text: Optional[str] = None
    is_primary: bool
    sort_order: int


class CafeSeatResponse(BaseModel):
    seat_type: str
    total_count: int
    available_count: int
    has_outlet: bool
    notes: Optional[str] = None


class CafeDetailResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    address: str
    latitude: float
    longitude: float
    phone: Optional[str] = None
    website: Optional[str] = None
    instagram: Optional[str] = None
    google_maps_url: Optional[str] = None
    is_verified: bool
    is_active: bool
    status: str
    total_capacity: Optional[int] = None
    indoor_capacity: Optional[int] = None
    outdoor_capacity: Optional[int] = None
    avg_rating: float
    review_count: int
    neighborhood: Optional[str] = None
    neighborhood_slug: Optional[str] = None
    amenities: CafeAmenityResponse
    hours: List[CafeHourResponse]
    images: List[CafeImageResponse]
    seats: List[CafeSeatResponse]
    created_at: datetime
    updated_at: datetime
