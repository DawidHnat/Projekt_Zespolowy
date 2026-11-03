from datetime import UTC, datetime, timedelta

from sqlalchemy import case, false, func, or_, select

from app.core.errors import ApiError
from app.core.models import Driver, Measurement, SyncState, Vehicle
from app.modules.auth.service import aware


def timestamp(value):
    return aware(value).isoformat() if value else None


def source_payload(session, source):
    state = session.get(SyncState, source)
    if not state or not state.last_success_at:
        raise ApiError(503, "SOURCE_UNAVAILABLE", "Oczekiwanie na dane WEBFLEET")
    return {
        "status": "degraded" if state.error_code else "ok",
        "last_success_at": timestamp(state.last_success_at),
        "error_code": state.error_code,
    }


def serialize_vehicle(vehicle, measurement, driver, now, stale_seconds):
    time = aware(measurement.position_at) if measurement and measurement.position_at else None
    age = (now - time).total_seconds() if time else None
    stale = age is None or age > stale_seconds or age < -300
    status = "unknown"
    if measurement:
        if stale:
            status = "offline"
        elif measurement.standing_still is not None:
            status = "stopped" if measurement.standing_still else "moving"
    located = bool(
        measurement
        and measurement.gps_quality == "A"
        and time
        and age >= -300
        and measurement.latitude is not None
        and measurement.longitude is not None
    )
    return {
        "id": str(vehicle.id),
        "name": vehicle.name,
        "number": vehicle.number,
        "license_plate": vehicle.license_plate,
        "vehicle_type": vehicle.vehicle_type,
        "status": status,
        "driver": {"id": str(driver.id), "display_name": driver.display_name} if driver else None,
        "latitude": measurement.latitude if located else None,
        "longitude": measurement.longitude if located else None,
        "position_at": timestamp(time),
        "received_at": timestamp(measurement.received_at) if measurement else None,
        "is_stale": stale,
        "odometer_km": float(measurement.odometer_km)
        if measurement and measurement.odometer_km is not None
        else None,
        "speed_kmh": None,  # Snapshot units remain unconfirmed in SCRUM-14.
        "ignition_on": measurement.ignition_on if measurement else None,
        "standing_still": measurement.standing_still if measurement else None,
    }


def fleet_status(now, stale_seconds):
    """Use the same time boundaries as the detail serializer, including future GPS."""
    stale = or_(
        Measurement.position_at.is_(None),
        Measurement.position_at < now - timedelta(seconds=stale_seconds),
        Measurement.position_at > now + timedelta(seconds=300),
    )
    return case(
        (Measurement.vehicle_id.is_(None), "unknown"),
        (stale, "offline"),
        (Measurement.standing_still.is_(True), "stopped"),
        (Measurement.standing_still.is_(False), "moving"),
        else_="unknown",
    )


def fleet_filters(source, q, status, status_expression):
    conditions = [Vehicle.source_account == source, Vehicle.active.is_(True)]
    needle = q.strip().casefold()
    if "\x00" in needle:
        # PostgreSQL text cannot contain NUL; avoid sending an invalid SQL parameter.
        conditions.append(false())
    elif needle:
        # Escape LIKE metacharacters: user input is a literal substring, not a pattern.
        conditions.append(
            or_(
                *(
                    field.contains(needle, autoescape=True)
                    for field in (
                        Vehicle.search_name,
                        Vehicle.search_number,
                        Vehicle.search_license_plate,
                    )
                )
            )
        )
    if status:
        conditions.append(status_expression == status)
    return conditions


def fleet_count(session, conditions):
    return session.scalar(
        select(func.count())
        .select_from(Vehicle)
        .outerjoin(Measurement, Measurement.vehicle_id == Vehicle.id)
        .where(*conditions)
    )


def fleet_page(session, source, stale_seconds, q, status, page, page_size):
    now = datetime.now(UTC)
    conditions = fleet_filters(source, q, status, fleet_status(now, stale_seconds))
    total = fleet_count(session, conditions)
    rows = session.execute(
        select(Vehicle, Measurement, Driver)
        .outerjoin(Measurement, Measurement.vehicle_id == Vehicle.id)
        .outerjoin(Driver, Driver.id == Vehicle.driver_id)
        .where(*conditions)
        .order_by(Vehicle.name, Vehicle.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return [serialize_vehicle(*row, now, stale_seconds) for row in rows], total


def fleet_markers(session, source, stale_seconds, q, status):
    now = datetime.now(UTC)
    status_expression = fleet_status(now, stale_seconds)
    conditions = fleet_filters(source, q, status, status_expression)
    total = fleet_count(session, conditions)
    # Coordinates of stale positions remain useful; only invalid/missing/future GPS is hidden.
    rows = session.execute(
        select(
            Vehicle.id,
            Vehicle.name,
            Measurement.longitude,
            Measurement.latitude,
            Measurement.position_at,
            status_expression.label("status"),
        )
        .join(Measurement, Measurement.vehicle_id == Vehicle.id)
        .where(
            *conditions,
            Measurement.gps_quality == "A",
            Measurement.position_at <= now + timedelta(seconds=300),
            Measurement.latitude.is_not(None),
            Measurement.longitude.is_not(None),
        )
        .order_by(Vehicle.name, Vehicle.id)
    ).all()
    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [row.longitude, row.latitude]},
            "properties": {
                "id": str(row.id),
                "name": row.name,
                "status": row.status,
                "is_stale": (now - aware(row.position_at)).total_seconds() > stale_seconds,
                "position_at": timestamp(row.position_at),
            },
        }
        for row in rows
    ]
    return features, total


def fleet_summary(session, source, stale_seconds):
    now = datetime.now(UTC)
    status_expression = fleet_status(now, stale_seconds)
    rows = session.execute(
        select(status_expression, func.count())
        .select_from(Vehicle)
        .outerjoin(Measurement, Measurement.vehicle_id == Vehicle.id)
        .where(Vehicle.source_account == source, Vehicle.active.is_(True))
        .group_by(status_expression)
    ).all()
    counts = dict.fromkeys(("moving", "stopped", "offline", "unknown"), 0)
    counts.update(rows)
    return {"total": sum(counts.values()), **counts}
