import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CafeSeat(Base):
    __tablename__ = "cafe_seats"
    __table_args__ = (Index("idx_cafe_seats_cafe_id", "cafe_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cafe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cafes.id", ondelete="CASCADE"), nullable=False
    )
    seat_type: Mapped[str] = mapped_column(String(30), nullable=False)
    total_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    has_outlet: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
