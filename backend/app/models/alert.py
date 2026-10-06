"""Early warning flood alert records.

Mirrors the `alerts` table in database/schema.sql. Alerts are issued per
assessment point through `geographic_id` (FK to geographic_data).
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

ALERT_SEVERITIES = ("info", "watch", "warning", "emergency")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    geographic_id: Mapped[UUID] = mapped_column(
        ForeignKey("geographic_data.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="info")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Phase 6 early-warning provenance: which model scored the district and
    # what evidence triggered the alert. Plain columns so the alerts table
    # stays queryable without a join to predictions.
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    factors: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    geographic: Mapped["GeographicData"] = relationship(back_populates="alerts")
