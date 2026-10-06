"""District boundary schemas."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DistrictBoundaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    geographic_id: UUID
    district_name: str | None = None
    source: str | None
    # Geometry is serialized to GeoJSON by the GIS endpoints; the raw
    # PostGIS element is not JSON-serializable on its own.
    geojson: dict | None = None
