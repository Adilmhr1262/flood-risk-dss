"""Geographic reference data for assessed locations.

Each row is a district-level assessment point with PostGIS geometry.
Mirrors the `geographic_data` table in database/schema.sql.
"""

from datetime import datetime
from uuid import UUID

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GeographicData(Base):
    __tablename__ = "geographic_data"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    district_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    province: Mapped[str] = mapped_column(String(100), nullable=False)
    geom: Mapped[str] = mapped_column(Geometry("POINT", srid=4326), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    elevation_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    river_distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    slope_deg: Mapped[float | None] = mapped_column(Float, nullable=True)
    population_density_per_km2: Mapped[float | None] = mapped_column(Float, nullable=True)
    vulnerability_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    events: Mapped[list["FloodEvent"]] = relationship(back_populates="geographic")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="geographic")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="geographic")
    shelters: Mapped[list["Shelter"]] = relationship(back_populates="geographic")
    infrastructure: Mapped[list["Infrastructure"]] = relationship(back_populates="geographic")
    vulnerability: Mapped["VulnerabilityIndicator | None"] = relationship(
        back_populates="geographic", cascade="all, delete-orphan", uselist=False
    )
    resource_allocations: Mapped[list["ResourceAllocation"]] = relationship(back_populates="geographic")
    citizen_reports: Mapped[list["CitizenReport"]] = relationship(back_populates="geographic")
    incidents: Mapped[list["Incident"]] = relationship(back_populates="geographic")
    response_teams: Mapped[list["ResponseTeam"]] = relationship(back_populates="geographic")
    weather_observations: Mapped[list["WeatherObservation"]] = relationship(
        back_populates="geographic", cascade="all, delete-orphan"
    )
    boundary: Mapped["DistrictBoundary | None"] = relationship(
        back_populates="geographic", cascade="all, delete-orphan", uselist=False
    )
