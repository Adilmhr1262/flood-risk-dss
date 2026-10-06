"""User accounts with role-based access control.

NOTE on the `role` column: the authoritative PostgreSQL schema
(database/schema.sql) defines a native `user_role` enum with the values
'authority', 'ngo', 'public' and 'volunteer'. The ORM maps `role` as a
plain String and constrains assignments to VALID_ROLES, keeping behaviour
identical to the enum without requiring enum-type management in migrations.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

ROLE_AUTHORITY = "authority"
ROLE_NGO = "ngo"
ROLE_PUBLIC = "public"
ROLE_VOLUNTEER = "volunteer"

VALID_ROLES = (ROLE_AUTHORITY, ROLE_NGO, ROLE_PUBLIC, ROLE_VOLUNTEER)


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # user_role enum ('authority','ngo','public') is defined in schema.sql;
    # the ORM stores the value as text constrained by VALID_ROLES.
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=ROLE_PUBLIC)
    location_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    predictions: Mapped[list["Prediction"]] = relationship(back_populates="creator")
    resource_allocations: Mapped[list["ResourceAllocation"]] = relationship(back_populates="allocator")
    citizen_reports: Mapped[list["CitizenReport"]] = relationship(
        back_populates="reporter", foreign_keys="CitizenReport.reporter_id"
    )
    device_tokens: Mapped[list["DeviceToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
