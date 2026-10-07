from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.core.config import DataSource

VehicleStatus = Literal["driving", "parked", "offline", "unknown"]


class Vehicle(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    registration: str
    name: str
    status: VehicleStatus
    speed_kmh: float | None
    odometer_km: float | None
    latitude: float | None
    longitude: float | None
    updated_at: datetime


class VehicleList(BaseModel):
    items: list[Vehicle]
    total: int
    source: DataSource
