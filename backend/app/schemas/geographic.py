"""Geographic assessment-point schemas."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GeographicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    district_name: str
    province: str
    lat: float | None = Field(default=None, alias="latitude")
    lon: float | None = Field(default=None, alias="longitude")
    elevation_m: float | None
    river_distance_km: float | None
    slope_deg: float | None
    vulnerability_index: float | None
