"""Critical infrastructure locations: hospitals, rescue centres, emergency facilities.

Mirrors the `infrastructure` table created by Alembic migration 0003.
Shelters live in the separate `shelters` table and are not duplicated here.
Seed rows carry ``is_sample_data=True`` to mark them as illustrative data
that must be replaced with authoritative registries before operational use.
"""

from datetime import datetime
from uuid import UUID

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

INFRASTRUCTURE_TYPES = ("shelter", "hospital", "rescue_center", "emergency_facility")


class Infrastructure(Base):
    __tablename__ = "infrastructure"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    geographic_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("geographic_data.id", ondelete="SET NULL"), nullable=True, index=True
    )
    geom: Mapped[str | None] = mapped_column(Geometry("POINT", srid=4326), nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    operational_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="operational")
    is_sample_data: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    geographic: Mapped["GeographicData | None"] = relationship(back_populates="infrastructure")
