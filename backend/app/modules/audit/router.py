"""Read-only API for the shared Fleet-Flow audit log (SCRUM-87)."""

from datetime import UTC, date, datetime, time, timedelta
from typing import Annotated, Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.errors import ApiError
from app.core.models import Vehicle
from app.modules.audit.models import AuditEvent
from app.modules.auth.models import User
from app.modules.auth.service import aware, current_user
from app.modules.fleet.sync import account_key

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[User, Depends(current_user)]
WARSAW = ZoneInfo("Europe/Warsaw")

EntityTypeParam = Literal[
    "vehicle",
    "vehicle_odometer",
    "vehicle_document",
    "driver",
    "driver_assignment",
    "trip_annotation",
    "user_account",
    "user_session",
]
ActorTypeParam = Literal["user", "import", "system"]


def _visibility_condition(source: str, user: User):
    security_types = ("user_account", "user_session")
    business_scope = and_(
        AuditEvent.entity_type.not_in(security_types),
        AuditEvent.source_account == source,
    )
    if user.role == "admin":
        security_scope = and_(
            AuditEvent.entity_type.in_(security_types),
            or_(AuditEvent.source_account.is_(None), AuditEvent.source_account == source),
        )
    else:
        security_scope = and_(
            AuditEvent.entity_type.in_(security_types),
            or_(
                AuditEvent.actor_id == user.id,
                AuditEvent.entity_id == str(user.id),
            ),
        )
    return or_(business_scope, security_scope)


@router.get("/actors")
def list_audit_actors(request: Request, session: SessionDep, user: UserDep):
    source = account_key(request.app.state.settings.webfleet_account)
    visible = _visibility_condition(source, user)
    actor_ids = list(
        session.scalars(
            select(AuditEvent.actor_id).where(visible, AuditEvent.actor_id.is_not(None)).distinct()
        ).all()
    )
    if not actor_ids:
        return {"items": []}
    users = session.scalars(
        select(User).where(User.id.in_(actor_ids)).order_by(User.display_name, User.id)
    ).all()
    return {"items": [{"id": str(item.id), "display_name": item.display_name} for item in users]}


@router.get("/events")
def list_audit_events(
    request: Request,
    session: SessionDep,
    user: UserDep,
    vehicle_id: UUID | None = None,
    entity_type: EntityTypeParam | None = None,
    actor_id: UUID | None = None,
    actor_type: ActorTypeParam | None = None,
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
    page: Annotated[int, Query(ge=1, le=100_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
):
    if from_date is not None and to_date is not None and from_date > to_date:
        raise ApiError(
            422, "VALIDATION_ERROR", "Data początkowa nie może być późniejsza niż końcowa"
        )

    source = account_key(request.app.state.settings.webfleet_account)
    if vehicle_id is not None:
        owned = session.scalar(
            select(Vehicle.id).where(Vehicle.id == vehicle_id, Vehicle.source_account == source)
        )
        if owned is None:
            raise ApiError(404, "NOT_FOUND", "Pojazd nie istnieje")

    conditions = [_visibility_condition(source, user)]
    if vehicle_id is not None:
        conditions.append(AuditEvent.vehicle_id == vehicle_id)
    if entity_type is not None:
        conditions.append(AuditEvent.entity_type == entity_type)
    if actor_id is not None:
        conditions.append(AuditEvent.actor_id == actor_id)
    if actor_type is not None:
        conditions.append(AuditEvent.actor_type == actor_type)
    if from_date is not None:
        start_utc = datetime.combine(from_date, time.min, tzinfo=WARSAW).astimezone(UTC)
        conditions.append(AuditEvent.occurred_at >= start_utc)
    if to_date is not None:
        end_utc = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=WARSAW).astimezone(
            UTC
        )
        conditions.append(AuditEvent.occurred_at < end_utc)

    total = session.scalar(select(func.count()).select_from(AuditEvent).where(*conditions)) or 0
    rows = session.scalars(
        select(AuditEvent)
        .where(*conditions)
        .order_by(AuditEvent.occurred_at.desc(), AuditEvent.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    actor_ids = {row.actor_id for row in rows if row.actor_id is not None}
    vehicle_ids = {row.vehicle_id for row in rows if row.vehicle_id is not None}
    actors_by_id = (
        {
            u.id: {"id": str(u.id), "display_name": u.display_name}
            for u in session.scalars(select(User).where(User.id.in_(actor_ids))).all()
        }
        if actor_ids
        else {}
    )
    vehicles_by_id = (
        {
            v.id: {"id": str(v.id), "name": v.name, "license_plate": v.license_plate}
            for v in session.scalars(
                select(Vehicle).where(Vehicle.id.in_(vehicle_ids), Vehicle.source_account == source)
            ).all()
        }
        if vehicle_ids
        else {}
    )

    items = [
        {
            "id": str(row.id),
            "occurred_at": aware(row.occurred_at).isoformat(),
            "actor_type": row.actor_type,
            "actor": actors_by_id.get(row.actor_id) if row.actor_id else None,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "vehicle_id": str(row.vehicle_id) if row.vehicle_id else None,
            "vehicle": vehicles_by_id.get(row.vehicle_id) if row.vehicle_id else None,
            "operation": row.operation,
            "outcome": row.outcome,
            "correlation_id": row.correlation_id,
            "changes": row.changes or {},
        }
        for row in rows
    ]
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
