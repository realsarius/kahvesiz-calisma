import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CafeAmenity(Base):
    __tablename__ = "cafe_amenities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cafe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cafes.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    wifi_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    wifi_speed_mbps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    outlet_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    outlet_accessibility: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    noise_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    has_natural_light: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_ac: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_heating: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_parking: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_accessible_entry: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allows_laptop: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    min_spend_try: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    has_food: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_alcohol: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pet_friendly: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
