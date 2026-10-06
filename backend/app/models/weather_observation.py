"""Time-series weather observations per district.

Mirrors the `weather_observations` table (migration 0002). The natural-key
UNIQUE constraint on (geographic_id, observed_at, source) makes bulk imports
duplicate-safe. This table feeds rainfall-trend charts and provides the
environmental inputs for the prediction service.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WeatherObservation(Base):
    __tablename__ = "weather_observations"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    geographic_id: Mapped[UUID] = mapped_column(
        ForeignKey("geographic_data.id", ondelete="CASCADE"), nullable=False, index=True
    )
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rainfall_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    # NOT NULL with default: NULLs never conflict in a UNIQUE constraint, so a
    # nullable source would defeat duplicate detection.
    source: Mapped[str] = mapped_column(String(200), nullable=False, default="unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    geographic: Mapped["GeographicData"] = relationship(back_populates="weather_observations")

    __table_args__ = (
        UniqueConstraint(
            "geographic_id",
            "observed_at",
            "source",
            name="uq_weather_observations_natural",
        ),
    )
