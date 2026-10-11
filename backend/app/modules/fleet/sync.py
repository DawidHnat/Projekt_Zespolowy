"""One shared, rate-limited owner for vehicle reads; never imports drivers."""

import asyncio
import hashlib
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.models import Measurement, SyncState, Vehicle
from app.integrations.webfleet.client import WebfleetClient, WebfleetError
from app.integrations.webfleet.models import ObjectSnapshot
from app.modules.analytics.service import evaluate_distance_rules, record_distance_interval
from app.modules.auth.service import aware


def account_key(account: str) -> str:
    return hashlib.sha256(account.strip().lower().encode()).hexdigest()


async def read_vehicle_data(settings, client_factory):
    async with client_factory(settings) as client:
        masters = await client.fetch_vehicles()
        snapshots = await client.fetch_objects()
        return masters, snapshots


def validate_records(masters, snapshots):
    indexed = {}
    for row in masters:
        uid = row.get("objectuid")
        if not isinstance(uid, str) or not uid.strip() or len(uid) > 200 or uid in indexed:
            raise WebfleetError("INVALID_RECORDS")
        indexed[uid] = row
    readings = {}
    for row in snapshots:
        try:
            reading = ObjectSnapshot.from_record(row)
        except ValueError:
            raise WebfleetError("INVALID_RECORDS") from None
        if reading.uid not in indexed or reading.uid in readings:
            raise WebfleetError("INCOMPLETE_REPORT")
        readings[reading.uid] = reading
    return indexed, readings


def apply_records(session, source, masters, readings, now):
    vehicles = {
        v.external_uid: v
        for v in session.scalars(select(Vehicle).where(Vehicle.source_account == source))
    }
    for uid, row in masters.items():
        vehicle = vehicles.get(uid)
        if not vehicle:
            vehicle = Vehicle(source_account=source, external_uid=uid, name="Bez nazwy")
            session.add(vehicle)
            session.flush()
        # Explicit allowlist. driver_id and all future annotations are local ownership.
        vehicle.name = str(row.get("objectname") or row.get("objectno") or "Bez nazwy")[:200]
        vehicle.number = str(row["objectno"])[:200] if row.get("objectno") else None
        vehicle.license_plate = (
            str(row["licenseplatenumber"])[:100] if row.get("licenseplatenumber") else None
        )
        vehicle.vehicle_type = str(row["vehicletype"])[:100] if row.get("vehicletype") else None
        vehicle.active = True
        reading = readings.get(uid)
        if reading:
            measurement = session.get(Measurement, vehicle.id)
            if measurement and measurement.position_at:
                if not reading.position_at or reading.position_at < aware(measurement.position_at):
                    continue  # Out-of-order telemetry must not move the vehicle backwards.
            if not measurement:
                measurement = Measurement(vehicle_id=vehicle.id, received_at=now)
                session.add(measurement)
            record_distance_interval(session, vehicle.id, measurement, reading, now)
            for field in (
                "latitude",
                "longitude",
                "odometer_km",
                "ignition_on",
                "standing_still",
                "gps_quality",
                "position_at",
            ):
                setattr(measurement, field, getattr(reading, field))
            measurement.received_at = now
    for uid, vehicle in vehicles.items():
        if uid not in masters:
            vehicle.active = False


def sync_once(engine, settings, *, client_factory=WebfleetClient, now=None):
    now = now or datetime.now(UTC)
    source = account_key(settings.account)
    lock_id = int.from_bytes(bytes.fromhex(source)[:8], signed=True)
    with engine.connect() as connection:
        locked = connection.execute(
            text("SELECT pg_try_advisory_lock(:key)"), {"key": lock_id}
        ).scalar()
        connection.commit()
        if not locked:
            return "busy"
        try:
            with Session(connection, expire_on_commit=False) as session:
                state = session.get(SyncState, source)
                if (
                    state
                    and state.last_attempt_at
                    and now - aware(state.last_attempt_at) < timedelta(seconds=60)
                ):
                    return "rate_limited"
                if not state:
                    state = SyncState(source_account=source)
                    session.add(state)
                state.last_attempt_at = now
                session.commit()  # Failed attempts also consume the shared interval.
                try:
                    masters, snapshots = asyncio.run(read_vehicle_data(settings, client_factory))
                    indexed, readings = validate_records(masters, snapshots)
                    apply_records(session, source, indexed, readings, now)
                    session.flush()
                    evaluate_distance_rules(session, source, now=now)
                    state.last_success_at = now
                    state.error_code = None
                    session.commit()
                    return "ok"
                except WebfleetError as error:
                    session.rollback()
                    state = session.get(SyncState, source)
                    state.error_code = error.code
                    session.commit()
                    return "degraded"
        finally:
            connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": lock_id})
            connection.commit()


async def sync_worker(engine, settings, interval):
    while True:
        try:
            await asyncio.to_thread(sync_once, engine, settings)
        except Exception:
            # No provider/SQL exceptions in logs: may contain credentials or telemetry.
            # Readiness and last-success timestamps expose availability to the UI.
            pass
        await asyncio.sleep(interval)
