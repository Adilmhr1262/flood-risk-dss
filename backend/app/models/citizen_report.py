"""Community flood sighting reports submitted from the mobile app.

Mirrors the `citizen_reports` table in database/schema.sql (migrations
0004/0005). Reports are triaged by authority users:
pending -> verified | rejected | resolved (legacy: dismissed).
"""

from datetime import datetime
from uuid import UUID

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

REPORT_STATUSES = ("pending", "verified", "rejected", "resolved", "dismissed")

REPORT_CATEGORIES = (
    "flood_water",
    "road_blockage",
    "rescue_request",
    "medical_emergency",
)

REPORT_PRIORITIES = ("low", "medium", "high", "urgent")


class CitizenReport(Base):
    __tablename__ = "citizen_reports"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    reporter_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    geographic_id: Mapped[UUID] = mapped_column(
        ForeignKey("geographic_data.id", ondelete="CASCADE"), nullable=False, index=True
    )
    geom: Mapped[str | None] = mapped_column(Geometry("POINT", srid=4326), nullable=True)
    severity: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5, CHECK in DB
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    category: Mapped[str | None] = mapped_column(String(30), nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    verified_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    reporter: Mapped["User | None"] = relationship(
        back_populates="citizen_reports", foreign_keys=[reporter_id]
    )
    geographic: Mapped["GeographicData"] = relationship(back_populates="citizen_reports")
    verifier: Mapped["User | None"] = relationship(foreign_keys=[verified_by])
