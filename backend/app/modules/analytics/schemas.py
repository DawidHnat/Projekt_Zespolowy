from typing import Literal

from pydantic import BaseModel

from app.core.config import DataSource


class Summary(BaseModel):
    total_vehicles: int
    driving_vehicles: int
    distance_km: float
    trips_count: int
    source: DataSource


class Alert(BaseModel):
    id: str
    vehicle_id: str
    severity: Literal["info", "warning"]
    title: str
    description: str


class AlertList(BaseModel):
    items: list[Alert]
    total: int
    source: DataSource
