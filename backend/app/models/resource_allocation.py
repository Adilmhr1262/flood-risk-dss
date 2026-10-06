"""Relief resource allocations per district.

Mirrors the `resource_allocations` table created by Alembic migration 0003.
Tracks planned / dispatched / delivered relief resources (relief kits, medical
teams, boats, ...) allocated by authority users.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ResourceAllocation(Base):
    __tablename__ = "resource_allocations"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    geographic_id: Mapped[UUID] = mapped_column(
        ForeignKey("geographic_data.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    allocated_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="planned")
    allocated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    geographic: Mapped["GeographicData"] = relationship(back_populates="resource_allocations")
    allocator: Mapped["User | None"] = relationship(back_populates="resource_allocations")
