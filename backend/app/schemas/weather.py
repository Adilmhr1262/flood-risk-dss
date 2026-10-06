"""Weather observation schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WeatherObservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    geographic_id: UUID
    district_name: str | None = None
    observed_at: datetime
    rainfall_mm: float | None
    temperature_c: float | None
    humidity_pct: float | None
    source: str
