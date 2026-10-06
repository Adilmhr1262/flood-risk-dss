"""Pydantic schemas for Phase 4 GIS decision support tables."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class InfrastructureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    type: str
    district_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    capacity: int | None = None
    contact_phone: str | None = None
    operational_status: str
    is_sample_data: bool


class VulnerabilityIndicatorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    district_name: str
    population_density: float | None = None
    vulnerability_index: float
    poverty_proxy: float | None = None
    healthcare_access_score: float | None = None
    computed_at: datetime | None = None


class ResourceAllocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    district_name: str | None = None
    resource_type: str
    quantity: int
    status: str
    allocated_at: datetime | None = None
    notes: str | None = None


class ResourceAllocationCreate(BaseModel):
    district_name: str
    resource_type: str
    quantity: int
    status: str = "planned"
    notes: str | None = None
