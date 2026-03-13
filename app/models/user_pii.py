import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import CHAR, Date, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserPII(Base):
    __tablename__ = "user_pii"
    __table_args__ = {"schema": "pii"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    full_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    country_code: Mapped[str] = mapped_column(CHAR(2), nullable=False, default="TR")
    consent_given_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consent_ip: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    consent_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
