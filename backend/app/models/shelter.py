"""Emergency shelter / relief centre locations.

Mirrors the `shelters` table in database/schema.sql. Facilities are stored as
a native TEXT[] array.
"""

from datetime import datetime
from uuid import UUID

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Shelter(Base):
    __tablename__ = "shelters"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    geographic_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("geographic_data.id", ondelete="SET NULL"), nullable=True, index=True
    )
    geom: Mapped[str | None] = mapped_column(Geometry("POINT", srid=4326), nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_occupancy: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    facilities: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    geographic: Mapped["GeographicData | None"] = relationship(back_populates="shelters")
