"""Append-only audit trail SQLAlchemy model and DB-level mutation guards (SCRUM-87)."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DDL, JSON, CheckConstraint, DateTime, Index, String, Uuid, event
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base

ACTOR_TYPES = ("user", "import", "system")
ENTITY_TYPES = (
    "vehicle",
    "vehicle_odometer",
    "vehicle_document",
    "driver",
    "driver_assignment",
    "trip_annotation",
    "user_account",
    "user_session",
)
OUTCOMES = ("succeeded", "denied", "failed")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        CheckConstraint(
            "actor_type IN ('user', 'import', 'system')",
            name="ck_audit_events_actor_type",
        ),
        CheckConstraint(
            "entity_type IN ('vehicle', 'vehicle_odometer', 'vehicle_document', "
            "'driver', 'driver_assignment', 'trip_annotation', 'user_account', 'user_session')",
            name="ck_audit_events_entity_type",
        ),
        CheckConstraint(
            "outcome IN ('succeeded', 'denied', 'failed')",
            name="ck_audit_events_outcome",
        ),
        Index("ix_audit_events_source_occurred", "source_account", "occurred_at"),
        Index("ix_audit_events_vehicle_occurred", "vehicle_id", "occurred_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(), primary_key=True, default=uuid4)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    source_account: Mapped[str | None] = mapped_column(String(64), index=True)
    actor_id: Mapped[UUID | None] = mapped_column(Uuid(), index=True)
    actor_type: Mapped[str] = mapped_column(String(20))
    entity_type: Mapped[str] = mapped_column(String(40), index=True)
    entity_id: Mapped[str] = mapped_column(String(64), index=True)
    vehicle_id: Mapped[UUID | None] = mapped_column(Uuid(), index=True)
    operation: Mapped[str] = mapped_column(String(60))
    outcome: Mapped[str] = mapped_column(String(20))
    correlation_id: Mapped[str] = mapped_column(String(64), index=True)
    changes: Mapped[dict] = mapped_column(JSON, default=dict)


@event.listens_for(AuditEvent, "before_update")
def _forbid_audit_orm_update(mapper, connection, target):
    raise ValueError("SCRUM-87: audit_events is append-only; UPDATE is prohibited")


@event.listens_for(AuditEvent, "before_delete")
def _forbid_audit_orm_delete(mapper, connection, target):
    raise ValueError("SCRUM-87: audit_events is append-only; DELETE is prohibited")


event.listen(
    AuditEvent.__table__,
    "after_create",
    DDL(
        "CREATE TRIGGER IF NOT EXISTS trg_audit_events_no_update "
        "BEFORE UPDATE ON audit_events "
        "BEGIN SELECT RAISE(ABORT, 'SCRUM-87: audit_events is append-only'); END;"
    ).execute_if(dialect="sqlite"),
)
event.listen(
    AuditEvent.__table__,
    "after_create",
    DDL(
        "CREATE TRIGGER IF NOT EXISTS trg_audit_events_no_delete "
        "BEFORE DELETE ON audit_events "
        "BEGIN SELECT RAISE(ABORT, 'SCRUM-87: audit_events is append-only'); END;"
    ).execute_if(dialect="sqlite"),
)
