from datetime import datetime

from sqlalchemy import CheckConstraint, Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UTCDateTime


class VehicleRecord(Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        CheckConstraint("source IN ('demo', 'webfleet')", name="vehicles_source_valid"),
        CheckConstraint(
            "status IN ('driving', 'parked', 'offline', 'unknown')", name="vehicles_status_valid"
        ),
        Index("ix_vehicles_source_status", "source", "status"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    source: Mapped[str] = mapped_column(String(16))
    registration: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(16))
    speed_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)
    odometer_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime())
