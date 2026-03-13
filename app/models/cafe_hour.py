import uuid
from datetime import time
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, SmallInteger, Time, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CafeHour(Base):
    __tablename__ = "cafe_hours"
    __table_args__ = (UniqueConstraint("cafe_id", "day_of_week", name="uq_cafe_hours_cafe_id_day_of_week"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cafe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cafes.id", ondelete="CASCADE"), nullable=False
    )
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    opens_at: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    closes_at: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    is_closed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
