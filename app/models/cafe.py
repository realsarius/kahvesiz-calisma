import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Cafe(Base):
    __tablename__ = "cafes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    neighborhood_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("neighborhoods.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    map_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    img_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latitude: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(11, 8), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    instagram: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    google_maps_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    seats: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    coffee_price: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    total_capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    indoor_capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    outdoor_capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    avg_rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False, default=Decimal("0.00"))
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
