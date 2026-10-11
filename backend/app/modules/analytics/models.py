"""Local rules and immutable alert evidence, separate from provider telemetry."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base


class Rule(Base):
    __tablename__ = "alert_rules"
    __table_args__ = (
        CheckConstraint("threshold_km > 0", name="ck_alert_rules_positive_threshold"),
        CheckConstraint("type = 'daily_distance_threshold'", name="ck_alert_rules_supported_type"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_account: Mapped[str] = mapped_column(String(64), index=True)
    type: Mapped[str] = mapped_column(String(40), default="daily_distance_threshold")
    threshold_km: Mapped[Decimal] = mapped_column(Numeric(14, 1))
    vehicle_id: Mapped[UUID | None] = mapped_column(ForeignKey("vehicles.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (UniqueConstraint("rule_id", "vehicle_id", "event_day"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    rule_id: Mapped[UUID] = mapped_column(ForeignKey("alert_rules.id"), index=True)
    vehicle_id: Mapped[UUID] = mapped_column(ForeignKey("vehicles.id"))
    event_day: Mapped[date] = mapped_column(Date)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    threshold_km: Mapped[Decimal] = mapped_column(Numeric(14, 1))
    distance_km: Mapped[Decimal] = mapped_column(Numeric(14, 1))


class DailyDistance(Base):
    """A lower bound from observed intervals, never a claim of complete daily history."""

    __tablename__ = "daily_distances"
    __table_args__ = (CheckConstraint("distance_km >= 0", name="ck_daily_distances_nonnegative"),)
    vehicle_id: Mapped[UUID] = mapped_column(ForeignKey("vehicles.id"), primary_key=True)
    event_day: Mapped[date] = mapped_column(Date, primary_key=True)
    distance_km: Mapped[Decimal] = mapped_column(Numeric(14, 1))
    first_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AlertReceipt(Base):
    __tablename__ = "alert_receipts"
    alert_id: Mapped[UUID] = mapped_column(ForeignKey("alerts.id"), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
