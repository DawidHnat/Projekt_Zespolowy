from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import and_, delete, func, select
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.errors import ApiError
from app.modules.analytics.models import Alert, AlertReceipt, Rule
from app.modules.analytics.schemas import ReceiptBody, RuleCreate, RuleUpdate
from app.modules.analytics.service import (
    evaluate_distance_rules,
    insert_for,
    require_vehicle,
    rule_payload,
)
from app.modules.auth.models import User
from app.modules.auth.service import aware, check_origin, current_user, editor, now_utc
from app.modules.fleet.sync import account_key

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[User, Depends(current_user)]
EditorDep = Annotated[User, Depends(editor)]
Page = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]


def source_key(request: Request):
    return account_key(request.app.state.settings.webfleet_account)


def find_rule(session, source, rule_id, *, lock=False):
    statement = select(Rule).where(Rule.id == rule_id, Rule.source_account == source)
    if lock:
        statement = statement.with_for_update()
    rule = session.scalar(statement)
    if not rule:
        raise ApiError(404, "NOT_FOUND", "Reguła nie istnieje")
    return rule


@router.get("/rules")
def rules(
    request: Request, session: SessionDep, _: UserDep, page: Page = 1, page_size: PageSize = 25
):
    query = select(Rule).where(Rule.source_account == source_key(request))
    total = session.scalar(select(func.count()).select_from(query.subquery()))
    rows = session.scalars(query.order_by(Rule.id).offset((page - 1) * page_size).limit(page_size))
    return {
        "items": [rule_payload(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/rules", status_code=201)
def create_rule(body: RuleCreate, request: Request, session: SessionDep, _: EditorDep):
    source = source_key(request)
    require_vehicle(session, source, body.vehicle_id)
    rule = Rule(source_account=source, **body.model_dump())
    session.add(rule)
    session.flush()
    evaluate_distance_rules(
        session, source, rule_id=rule.id, stale_seconds=request.app.state.settings.stale_seconds
    )
    session.commit()
    return rule_payload(rule)


@router.patch("/rules/{rule_id}")
def update_rule(
    rule_id: UUID, body: RuleUpdate, request: Request, session: SessionDep, _: EditorDep
):
    source = source_key(request)
    rule = find_rule(session, source, rule_id, lock=True)
    changes = body.model_dump(exclude_unset=True)
    if "vehicle_id" in changes:
        require_vehicle(session, source, changes["vehicle_id"])
    for key, value in changes.items():
        setattr(rule, key, value)
    session.flush()
    evaluate_distance_rules(
        session, source, rule_id=rule.id, stale_seconds=request.app.state.settings.stale_seconds
    )
    session.commit()
    return rule_payload(rule)


@router.get("/alerts")
def alerts(
    request: Request,
    session: SessionDep,
    user: UserDep,
    read: bool | None = None,
    page: Page = 1,
    page_size: PageSize = 25,
):
    query = (
        select(Alert, AlertReceipt.read_at)
        .join(Rule, Rule.id == Alert.rule_id)
        .outerjoin(
            AlertReceipt, and_(AlertReceipt.alert_id == Alert.id, AlertReceipt.user_id == user.id)
        )
        .where(Rule.source_account == source_key(request))
    )
    if read is not None:
        query = query.where(
            AlertReceipt.read_at.is_not(None) if read else AlertReceipt.read_at.is_(None)
        )
    total = session.scalar(select(func.count()).select_from(query.subquery()))
    rows = session.execute(
        query.order_by(Alert.occurred_at.desc(), Alert.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return {
        "items": [
            {
                "id": str(alert.id),
                "vehicle_id": str(alert.vehicle_id),
                "rule_id": str(alert.rule_id),
                "event_day": alert.event_day.isoformat(),
                "occurred_at": aware(alert.occurred_at).isoformat(),
                "threshold_km": float(alert.threshold_km),
                "distance_km": float(alert.distance_km),
                "coverage": "partial",
                "read_at": aware(read_at).isoformat() if read_at else None,
            }
            for alert, read_at in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.patch("/alerts/{alert_id}/receipt", dependencies=[Depends(check_origin)])
def receipt(
    alert_id: UUID, body: ReceiptBody, request: Request, session: SessionDep, user: UserDep
):
    alert = session.scalar(
        select(Alert.id)
        .join(Rule, Rule.id == Alert.rule_id)
        .where(Alert.id == alert_id, Rule.source_account == source_key(request))
    )
    if not alert:
        raise ApiError(404, "NOT_FOUND", "Alert nie istnieje")
    read_at = None
    if body.read:
        statement = (
            insert_for(session, AlertReceipt)
            .values(alert_id=alert_id, user_id=user.id, read_at=now_utc())
            .on_conflict_do_nothing(index_elements=[AlertReceipt.alert_id, AlertReceipt.user_id])
        )
        session.execute(statement)
        read_at = session.get(AlertReceipt, (alert_id, user.id)).read_at
    else:
        session.execute(
            delete(AlertReceipt).where(
                AlertReceipt.alert_id == alert_id, AlertReceipt.user_id == user.id
            )
        )
    session.commit()
    return {"read_at": aware(read_at).isoformat() if read_at else None}
