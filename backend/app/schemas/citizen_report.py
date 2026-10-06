"""Schemas for citizen flood sighting reports (mobile app)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.citizen_report import REPORT_CATEGORIES, REPORT_PRIORITIES, REPORT_STATUSES


class CitizenReportCreate(BaseModel):
    district_name: str = Field(min_length=1, max_length=150)
    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)
    severity: int = Field(ge=1, le=5, description="Observed flood severity: 1=Minor … 5=Catastrophic")
    description: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(
        default=None,
        description=f"Report category, one of: {', '.join(REPORT_CATEGORIES)}",
    )


class CitizenReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reporter_id: UUID | None
    geographic_id: UUID
    district_name: str | None = None
    severity: int
    description: str | None
    status: str
    category: str | None = None
    image_path: str | None = None
    verified_by: UUID | None = None
    verified_at: datetime | None = None
    verification_note: str | None = None
    priority: str = "medium"
    created_at: datetime


class CitizenReportVerify(BaseModel):
    """Authority triage decision on a citizen report."""

    status: str = Field(description=f"One of: {', '.join(REPORT_STATUSES)}")
    note: str | None = Field(default=None, max_length=2000)
    priority: str | None = Field(
        default=None, description=f"Optional new priority, one of: {', '.join(REPORT_PRIORITIES)}"
    )


class DeviceTokenCreate(BaseModel):
    fcm_token: str = Field(min_length=10, max_length=512)
    platform: str = Field(default="android", max_length=20)


class DeviceTokenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    platform: str
    created_at: datetime
