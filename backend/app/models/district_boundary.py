"""District boundary polygons for GIS rendering.

Mirrors the `district_boundaries` table (migration 0002). One MultiPolygon
per district (UNIQUE on geographic_id); used by the GIS module to draw
district boundary and risk layers.
"""

from datetime import datetime
from uuid import UUID

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DistrictBoundary(Base):
    __tablename__ = "district_boundaries"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    geographic_id: Mapped[UUID] = mapped_column(
        ForeignKey("geographic_data.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    geom: Mapped[str] = mapped_column(Geometry("MULTIPOLYGON", srid=4326), nullable=False)
    source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    geographic: Mapped["GeographicData"] = relationship(back_populates="boundary")
