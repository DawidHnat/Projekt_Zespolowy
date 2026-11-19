from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base


class DriverCategory(Base):
    __tablename__ = "driver_categories"
    driver_id: Mapped[UUID] = mapped_column(ForeignKey("drivers.id"), primary_key=True)
    category: Mapped[str] = mapped_column(String(5), primary_key=True)


class DriverAssignment(Base):
    __tablename__ = "driver_assignments"
    __table_args__ = (
        CheckConstraint(
            "ended_at IS NULL OR started_at IS NULL OR ended_at >= started_at",
            name="ck_driver_assignment_dates",
        ),
        CheckConstraint("NOT active OR ended_at IS NULL", name="ck_driver_assignment_active"),
        Index("ix_driver_assignments_vehicle", "vehicle_id"),
        Index("ix_driver_assignments_driver", "driver_id"),
        Index(
            "uq_driver_assignments_open_pair",
            "driver_id",
            "vehicle_id",
            unique=True,
            postgresql_where=text("active"),
            sqlite_where=text("active = 1"),
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    driver_id: Mapped[UUID] = mapped_column(ForeignKey("drivers.id"))
    vehicle_id: Mapped[UUID] = mapped_column(ForeignKey("vehicles.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Migrated legacy pointers have an unknown start. Never guess historical ownership.
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
