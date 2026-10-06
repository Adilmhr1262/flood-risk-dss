"""Field response teams managed by disaster authorities.

Teams are typed (rescue / medical / logistics / boat) and carry an
availability status so the command center can see deployable capacity.
"""

from datetime import datetime
from uuid import UUID

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

TEAM_TYPES = ("rescue", "medical", "logistics", "boat")
TEAM_STATUSES = ("available", "deployed", "standby")


class ResponseTeam(Base):
    __tablename__ = "response_teams"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    team_type: Mapped[str] = mapped_column(String(30), nullable=False)
    geographic_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("geographic_data.id", ondelete="SET NULL"), nullable=True, index=True
    )
    members_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="available")
    contact_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    geom: Mapped[str | None] = mapped_column(Geometry("POINT", srid=4326), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    geographic: Mapped["GeographicData | None"] = relationship(back_populates="response_teams")
