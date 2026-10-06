"""User schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str
    role: str
    location_name: str | None
    phone: str | None
    created_at: datetime


class UserUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    location_name: str | None = None
    phone: str | None = None
