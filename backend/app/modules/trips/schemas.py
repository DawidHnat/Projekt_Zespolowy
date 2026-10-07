from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.config import DataSource


class Trip(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    vehicle_id: str
    started_at: datetime
    ended_at: datetime | None
    distance_km: float
    start_address: str
    end_address: str
    purpose: str
    notes: str


class TripList(BaseModel):
    items: list[Trip]
    total: int
    source: DataSource


class TripUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    purpose: str = Field(default="", max_length=200)
    notes: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def require_change(self) -> "TripUpdate":
        if not self.model_fields_set:
            raise ValueError("Provide purpose or notes.")
        return self
