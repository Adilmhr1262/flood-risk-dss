"""Alert request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AlertCreate(BaseModel):
    district_name: str = Field(min_length=2, max_length=150)
    title: str = Field(min_length=2, max_length=255)
    message: str = Field(min_length=2)
    severity: str = Field(default="info")


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    message: str
    severity: str
    is_active: bool
    geographic_id: UUID
    issued_at: datetime
    expires_at: datetime | None = None
    model_version: str | None = None
    probability: float | None = None
    factors: list | None = None
