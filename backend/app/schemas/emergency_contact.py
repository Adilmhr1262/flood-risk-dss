"""Emergency contact directory schemas."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EmergencyContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    organization: str | None
    phone: str
    district_name: str | None
