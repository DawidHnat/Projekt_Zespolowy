from datetime import datetime

from sqlalchemy import CheckConstraint, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UTCDateTime


class TripRecord(Base):
    __tablename__ = "trips"
    __table_args__ = (
        CheckConstraint("source IN ('demo', 'webfleet')", name="trips_source_valid"),
        CheckConstraint("distance_km >= 0", name="trips_distance_nonnegative"),
        Index("ix_trips_vehicle_started", "vehicle_id", "started_at"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    vehicle_id: Mapped[str] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"))
    source: Mapped[str] = mapped_column(String(16))
    started_at: Mapped[datetime] = mapped_column(UTCDateTime())
    ended_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    distance_km: Mapped[float] = mapped_column(Float)
    start_address: Mapped[str] = mapped_column(String(500))
    end_address: Mapped[str] = mapped_column(String(500))
    purpose: Mapped[str] = mapped_column(String(200), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
