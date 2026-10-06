"""Schemas for the authority command center (Phase W3): incidents, teams, resources."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.incident import INCIDENT_SOURCES, INCIDENT_STATUSES
from app.models.response_team import TEAM_STATUSES, TEAM_TYPES


class IncidentCreate(BaseModel):
    """Raise a new incident, manually or escalated from an alert/report."""

    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    district_name: str | None = Field(default=None, max_length=150)
    severity: int = Field(default=3, ge=1, le=5)
    source: str = Field(default="manual", description=f"One of: {', '.join(INCIDENT_SOURCES)}")
    source_id: UUID | None = None
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)


class IncidentStatusUpdate(BaseModel):
    status: str = Field(description=f"One of: {', '.join(INCIDENT_STATUSES)}")
    note: str | None = Field(default=None, max_length=2000)


class IncidentNoteCreate(BaseModel):
    note: str = Field(min_length=1, max_length=4000)


class IncidentNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    author_id: UUID | None
    note: str
    created_at: datetime


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    district_name: str | None = None
    status: str
    severity: int
    source: str
    created_by: UUID | None
    assigned_to: UUID | None
    notes: list[IncidentNoteOut] = []
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None


class IncidentStats(BaseModel):
    by_status: dict[str, int]
    open_by_severity: dict[str, int]
    avg_hours_to_resolve: float | None
    resolved_last_7d: int


class ResponseTeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    team_type: str = Field(description=f"One of: {', '.join(TEAM_TYPES)}")
    district_name: str | None = Field(default=None, max_length=150)
    members_count: int | None = Field(default=None, ge=1, le=500)
    status: str = Field(default="available", description=f"One of: {', '.join(TEAM_STATUSES)}")
    contact_phone: str | None = Field(default=None, max_length=30)
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)


class ResponseTeamUpdate(BaseModel):
    status: str | None = Field(default=None, description=f"One of: {', '.join(TEAM_STATUSES)}")
    members_count: int | None = Field(default=None, ge=1, le=500)
    contact_phone: str | None = Field(default=None, max_length=30)
    district_name: str | None = Field(default=None, max_length=150)


class ResponseTeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    team_type: str
    district_name: str | None = None
    members_count: int | None
    status: str
    contact_phone: str | None
    latitude: float | None = None
    longitude: float | None = None
    created_at: datetime
    updated_at: datetime


class ShelterResourceOut(BaseModel):
    """Shelter monitoring row for the command center."""

    id: UUID
    name: str
    district_name: str | None
    capacity: int | None
    current_occupancy: int
    availability: int | None  # capacity - occupancy, None when capacity unknown
    occupancy_pct: float | None  # None when capacity unknown
    status: str
    contact_phone: str | None
    latitude: float | None = None
    longitude: float | None = None


class ShelterUpdate(BaseModel):
    current_occupancy: int | None = Field(default=None, ge=0)
    status: str | None = Field(
        default=None, description="One of: open, full, closed, maintenance"
    )


class WeatherLatestOut(BaseModel):
    district_name: str
    observed_at: datetime | None
    rainfall_mm: float | None
    temperature_c: float | None
    humidity_pct: float | None
    source: str | None
