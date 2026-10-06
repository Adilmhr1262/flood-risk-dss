"""Historical flood event records.

Mirrors the `flood_events` table in database/schema.sql. Events are linked to
their assessment point through `geographic_id` (FK to geographic_data).
"""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FloodEvent(Base):
    __tablename__ = "flood_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    geographic_id: Mapped[UUID] = mapped_column(
        ForeignKey("geographic_data.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    rainfall_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    severity: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1 (minor) .. 5 (catastrophic)
    flood_status: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    damage_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    affected_population: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    geographic: Mapped["GeographicData"] = relationship(back_populates="events")
