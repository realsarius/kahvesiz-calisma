import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating_range"),
        CheckConstraint("noise_rating BETWEEN 1 AND 5", name="ck_reviews_noise_rating_range"),
        CheckConstraint("wifi_rating BETWEEN 1 AND 5", name="ck_reviews_wifi_rating_range"),
        CheckConstraint("outlet_rating BETWEEN 1 AND 5", name="ck_reviews_outlet_rating_range"),
        UniqueConstraint("user_id", "cafe_id", name="uq_reviews_user_id_cafe_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    cafe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cafes.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    noise_rating: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    wifi_rating: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    outlet_rating: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    visited_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_verified_visit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
