"""Imported trip facts and local annotations have separate owners and storage."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base


class Trip(Base):
    __tablename__ = "trips"
    __table_args__ = (
        UniqueConstraint("vehicle_id", "external_uid"),
        Index("ix_trips_vehicle_start", "vehicle_id", "start_at"),
        CheckConstraint("end_at IS NULL OR end_at >= start_at", name="ck_trips_time_order"),
        CheckConstraint(
            "distance_km IS NULL OR (distance_km >= 0 AND distance_km <= 99999999999.999)",
            name="ck_trips_distance",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    vehicle_id: Mapped[UUID] = mapped_column(ForeignKey("vehicles.id"))
    external_uid: Mapped[str] = mapped_column(String(200))
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    distance_km: Mapped[Decimal | None] = mapped_column(Numeric(14, 3))


class TripAnnotation(Base):
    __tablename__ = "trip_annotations"
    __table_args__ = (CheckConstraint("version >= 2", name="ck_trip_annotations_version"),)
    trip_id: Mapped[UUID] = mapped_column(ForeignKey("trips.id"), primary_key=True)
    purpose: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(2000))
    version: Mapped[int]
    updated_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
