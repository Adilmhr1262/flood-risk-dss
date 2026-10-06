"""Operational incident records for the authority command center.

An incident moves through a controlled workflow:
detected -> verified -> response_started -> resolved.
Incidents may be raised manually, or escalated from an alert or a citizen
report (``source`` / ``source_id`` record the provenance).
"""

from datetime import datetime
from uuid import UUID

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

INCIDENT_STATUSES = ("detected", "verified", "response_started", "resolved")
INCIDENT_SOURCES = ("manual", "alert", "report")

# Allowed forward transitions. Reopening is not permitted: a new incident
# is raised if a situation recurs, keeping the audit trail linear.
INCIDENT_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "detected": ("verified",),
    "verified": ("response_started",),
    "response_started": ("resolved",),
    "resolved": (),
}


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    geographic_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("geographic_data.id", ondelete="SET NULL"), nullable=True, index=True
    )
    geom: Mapped[str | None] = mapped_column(Geometry("POINT", srid=4326), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="detected")
    severity: Mapped[int] = mapped_column(Integer, nullable=False, default=3)  # 1-5
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="manual")
    source_id: Mapped[UUID | None] = mapped_column(nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assigned_to: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    geographic: Mapped["GeographicData | None"] = relationship(back_populates="incidents")
    notes: Mapped[list["IncidentNote"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan",
        order_by="IncidentNote.created_at",
    )


class IncidentNote(Base):
    __tablename__ = "incident_notes"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    incident_id: Mapped[UUID] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    incident: Mapped["Incident"] = relationship(back_populates="notes")
