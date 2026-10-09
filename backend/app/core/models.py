from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Driver(Base):
    __tablename__ = "drivers"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    display_name: Mapped[str] = mapped_column(String(120))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (UniqueConstraint("source_account", "external_uid"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_account: Mapped[str] = mapped_column(String(64), index=True)
    external_uid: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(200))
    number: Mapped[str | None] = mapped_column(String(200))
    license_plate: Mapped[str | None] = mapped_column(String(100))
    vehicle_type: Mapped[str | None] = mapped_column(String(100))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    # This local field belongs to Fleet-Flow and is never written by WEBFLEET.
    driver_id: Mapped[UUID | None] = mapped_column(ForeignKey("drivers.id"))


class Measurement(Base):
    __tablename__ = "measurements"
    vehicle_id: Mapped[UUID] = mapped_column(ForeignKey("vehicles.id"), primary_key=True)
    latitude: Mapped[float | None]
    longitude: Mapped[float | None]
    odometer_km: Mapped[Decimal | None] = mapped_column(Numeric(14, 1))
    ignition_on: Mapped[bool | None]
    standing_still: Mapped[bool | None]
    gps_quality: Mapped[str | None] = mapped_column(String(1))
    position_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SyncState(Base):
    __tablename__ = "sync_states"
    source_account: Mapped[str] = mapped_column(String(64), primary_key=True)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(80))
