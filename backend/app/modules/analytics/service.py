from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.models import Vehicle
from app.modules.analytics.models import Alert, DailyDistance, Rule
from app.modules.auth.service import aware

WARSAW = ZoneInfo("Europe/Warsaw")


def record_distance_interval(session, vehicle_id, previous, reading, now, *, max_gap_seconds=900):
    """Persist only a known, nonnegative interval wholly inside one Polish calendar day.

    Call before replacing the previous Measurement, in the synchronization transaction.
    Duplicate/out-of-order samples, counter resets and gaps do not invent distance.
    The existing shared synchronization lock serializes updates to a vehicle's baseline.
    """
    if previous is None or not previous.position_at or not reading.position_at:
        return
    start, end = aware(previous.position_at), aware(reading.position_at)
    before, after = previous.odometer_km, reading.odometer_km
    if (
        not start < end <= aware(now)
        or end - start > timedelta(seconds=max_gap_seconds)
        or start.astimezone(WARSAW).date() != end.astimezone(WARSAW).date()
        or before is None
        or after is None
        or not before.is_finite()
        or not after.is_finite()
        or before < 0
        or after < before
    ):
        return
    statement = insert_for(session, DailyDistance).values(
        vehicle_id=vehicle_id,
        event_day=end.astimezone(WARSAW).date(),
        distance_km=after - before,
        first_observed_at=start,
        last_observed_at=end,
    )
    session.execute(
        statement.on_conflict_do_update(
            index_elements=[DailyDistance.vehicle_id, DailyDistance.event_day],
            set_={
                "distance_km": DailyDistance.distance_km + statement.excluded.distance_km,
                "last_observed_at": end,
            },
        )
    )


def insert_for(session, model):
    if session.bind.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:  # Isolated SQLite tests; deployment uses PostgreSQL.
        from sqlalchemy.dialects.sqlite import insert
    return insert(model)


def require_vehicle(session: Session, source: str, vehicle_id):
    if vehicle_id is not None and not session.scalar(
        select(Vehicle.id).where(
            Vehicle.id == vehicle_id, Vehicle.source_account == source, Vehicle.active.is_(True)
        )
    ):
        raise ApiError(404, "NOT_FOUND", "Pojazd nie istnieje lub jest nieaktywny")


def rule_payload(rule: Rule):
    return {
        "id": str(rule.id),
        "type": rule.type,
        "threshold_km": float(rule.threshold_km),
        "vehicle_id": str(rule.vehicle_id) if rule.vehicle_id else None,
        "active": rule.active,
    }


def evaluate_distance_rules(
    session: Session, source: str, *, now: datetime | None = None, stale_seconds=900, rule_id=None
) -> int:
    """Evaluate the observed daily distance, not the absolute odometer.

    Called in the caller's transaction after a successful synchronization or rule edit.
    A PostgreSQL unique key + UPSERT also protects parallel workers and repeated imports.
    """
    now = aware(now or datetime.now(UTC))
    query = select(Rule).where(Rule.source_account == source, Rule.active.is_(True))
    if rule_id is not None:
        query = query.where(Rule.id == rule_id)
    # Serializes edits/disabling with evaluation; stable ordering prevents lock inversion.
    rules = session.scalars(query.order_by(Rule.id).with_for_update()).all()
    if not rules:
        return 0
    readings = session.execute(
        select(Vehicle, DailyDistance)
        .join(DailyDistance, DailyDistance.vehicle_id == Vehicle.id)
        .where(Vehicle.source_account == source, Vehicle.active.is_(True))
        .where(
            DailyDistance.last_observed_at >= now - timedelta(seconds=stale_seconds),
            DailyDistance.last_observed_at <= now,
        )
    ).all()
    created = 0
    for vehicle, distance in readings:
        value = distance.distance_km
        for rule in rules:
            if rule.vehicle_id is not None and rule.vehicle_id != vehicle.id:
                continue
            if value <= rule.threshold_km:
                continue
            statement = (
                insert_for(session, Alert)
                .values(
                    rule_id=rule.id,
                    vehicle_id=vehicle.id,
                    event_day=distance.event_day,
                    occurred_at=aware(distance.last_observed_at),
                    created_at=now,
                    threshold_km=rule.threshold_km,
                    distance_km=value,
                )
                .on_conflict_do_nothing(
                    index_elements=[Alert.rule_id, Alert.vehicle_id, Alert.event_day]
                )
                .returning(Alert.id)
            )
            created += session.scalar(statement) is not None
    return created
