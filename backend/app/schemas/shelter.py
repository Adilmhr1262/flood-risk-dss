"""Emergency shelter schemas."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ShelterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    geographic_id: UUID | None
    capacity: int | None
    facilities: list[str] | None
    contact_phone: str | None
