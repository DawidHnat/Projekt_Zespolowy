from datetime import UTC, datetime

from sqlalchemy import select

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


def fleet_rows(session, source, stale_seconds, q="", status=None):
    statement = (
        select(Vehicle, Measurement, Driver)
        .outerjoin(Measurement, Measurement.vehicle_id == Vehicle.id)
        .outerjoin(Driver, Driver.id == Vehicle.driver_id)
        .where(Vehicle.source_account == source, Vehicle.active.is_(True))
        .order_by(Vehicle.name, Vehicle.id)
        .limit(10001)
    )
    now = datetime.now(UTC)
    records = session.execute(statement).all()
    if len(records) > 10000:
        raise ApiError(503, "FLEET_TOO_LARGE", "Flota wymaga dodatkowej konfiguracji stronicowania")
    items = [serialize_vehicle(*row, now, stale_seconds) for row in records]
    needle = q.strip().casefold()
    return [
        item
        for item in items
        if (not status or item["status"] == status)
        and (
            not needle
            or any(
                needle in (item[field] or "").casefold()
                for field in ("name", "number", "license_plate")
            )
        )
    ]
