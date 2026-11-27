"""One shared, rate-limited owner for vehicle reads; never imports drivers."""

import asyncio
import hashlib
import json
import logging
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.models import Measurement, SyncState, Vehicle
from app.core.settings import DEFAULT_STALE_SECONDS
from app.integrations.webfleet.client import REQUEST_INTERVALS, WebfleetClient, WebfleetError
from app.integrations.webfleet.models import MAX_ODOMETER_KM, ObjectSnapshot
from app.modules.analytics.service import evaluate_distance_rules, record_distance_interval
from app.modules.audit.service import build_diff, record_audit_event
from app.modules.auth.service import aware

MAX_READ_ATTEMPTS = 3
MAX_AUTOMATIC_RETRY_WAIT_SECONDS = 60
RETRYABLE_ERROR_CODES = {
    "timeout",
    "connection_failed",
    "provider_rate_limit",
    "local_rate_limit",
}
logger = logging.getLogger("fleet_flow.sync")


def log_sync_failure(code):
    # Fixed codes only. Never log exceptions, SQL, source accounts or provider payloads.
    logger.error(
        json.dumps({"event": "webfleet_sync_failed", "code": code, "event_id": uuid4().hex})
    )


def account_key(account: str) -> str:
    return hashlib.sha256(account.strip().lower().encode()).hexdigest()


def source_lock_id(source: str) -> int:
    return int.from_bytes(bytes.fromhex(source)[:8], signed=True)


def minimum_sync_interval(interval: int) -> int:
    return max(
        interval,
        REQUEST_INTERVALS["showVehicleReportExtern"],
        REQUEST_INTERVALS["showObjectReportExtern"],
    )


class RetryTracker:
    def __init__(self, sleep_fn=asyncio.sleep):
        self.sleep_fn = sleep_fn
        self.elapsed_seconds = 0.0

    async def sleep(self, delay: float):
        self.elapsed_seconds += delay
        await self.sleep_fn(delay)


async def _read_with_retries(action, fetch, tracker):
    for attempt in range(MAX_READ_ATTEMPTS):
        try:
            return await fetch()
        except WebfleetError as error:
            retryable = error.retryable or error.code in RETRYABLE_ERROR_CODES
            if not retryable or attempt == MAX_READ_ATTEMPTS - 1:
                error.elapsed_seconds = tracker.elapsed_seconds
                raise
            delay = max(
                REQUEST_INTERVALS[action],
                2**attempt,
                error.retry_after_seconds or 0,
            )
            if delay > MAX_AUTOMATIC_RETRY_WAIT_SECONDS:
                error.elapsed_seconds = tracker.elapsed_seconds
                raise
            await tracker.sleep(delay)


async def read_vehicle_data(settings, client_factory, *, sleep=asyncio.sleep, tracker=None):
    if tracker is None:
        tracker = RetryTracker(sleep)
    async with client_factory(settings) as client:
        masters = await _read_with_retries(
            "showVehicleReportExtern",
            client.fetch_vehicles,
            tracker,
        )
        snapshots = await _read_with_retries(
            "showObjectReportExtern",
            client.fetch_objects,
            tracker,
        )
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
        for v in session.scalars(
            select(Vehicle)
            .where(Vehicle.source_account == source, Vehicle.is_manual.is_(False))
            .order_by(Vehicle.id)
            .with_for_update()
        )
    }
    # The provider reports no authoritative deletion signal. A shrinking report
    # cannot replace a known roster, even if its telemetry is internally consistent.
    if any(vehicle.active and uid not in masters for uid, vehicle in vehicles.items()):
        raise WebfleetError("INCOMPLETE_REPORT")
    sync_correlation_id = uuid4().hex
    for uid, row in masters.items():
        vehicle = vehicles.get(uid)
        is_new = vehicle is None
        before_roster = (
            {
                "origin": "webfleet",
                "name": vehicle.name,
                "number": vehicle.number,
                "license_plate": vehicle.license_plate,
                "vehicle_type": vehicle.vehicle_type,
            }
            if vehicle is not None
            else {
                "origin": None,
                "name": None,
                "number": None,
                "license_plate": None,
                "vehicle_type": None,
            }
        )
        if not vehicle:
            vehicle = Vehicle(source_account=source, external_uid=uid, name="Bez nazwy")
            session.add(vehicle)
            session.flush()
        if not vehicle.manual_name:
            vehicle.name = str(row.get("objectname") or row.get("objectno") or "Bez nazwy")[:200]
        vehicle.number = str(row["objectno"])[:200] if row.get("objectno") else None
        if not vehicle.manual_license_plate:
            vehicle.license_plate = (
                str(row["licenseplatenumber"])[:100] if row.get("licenseplatenumber") else None
            )
        if not vehicle.manual_vehicle_type:
            vehicle.vehicle_type = str(row["vehicletype"])[:100] if row.get("vehicletype") else None
        vehicle.active = True
        after_roster = {
            "origin": "webfleet",
            "name": vehicle.name,
            "number": vehicle.number,
            "license_plate": vehicle.license_plate,
            "vehicle_type": vehicle.vehicle_type,
        }
        roster_diff = build_diff("vehicle", before_roster, after_roster)
        if is_new or roster_diff:
            record_audit_event(
                session,
                entity_type="vehicle",
                entity_id=vehicle.id,
                vehicle_id=vehicle.id,
                operation="vehicle.imported",
                actor_id=None,
                actor_type="import",
                source_account=source,
                changes=roster_diff,
                correlation_id=sync_correlation_id,
                occurred_at=now,
            )
        reading = readings.get(uid)
        if reading:
            position_at = reading.position_at
            if position_at and position_at > now:
                continue
            measurement = session.get(Measurement, vehicle.id)
            previous = measurement
            if measurement and measurement.position_at:
                stored_at = aware(measurement.position_at)
                if not position_at:
                    continue
                if stored_at > min(aware(measurement.received_at), now):
                    # Old code could store a future timestamp. It is not a distance baseline.
                    previous = None
                elif position_at <= stored_at:
                    continue
            if not measurement:
                measurement = Measurement(vehicle_id=vehicle.id, received_at=now)
                session.add(measurement)
            if reading.odometer_km is not None and (
                reading.odometer_km < 0 or reading.odometer_km > MAX_ODOMETER_KM
            ):
                raise WebfleetError("INVALID_RECORDS")
            record_distance_interval(session, vehicle.id, previous, reading, now)
            for field in (
                "latitude",
                "longitude",
                "odometer_km",
                "ignition_on",
                "standing_still",
                "gps_quality",
                "position_at",
                "speed_kmh",
                "position_address",
            ):
                setattr(measurement, field, getattr(reading, field))
            measurement.received_at = now


def sync_once(
    engine,
    settings,
    *,
    client_factory=WebfleetClient,
    now=None,
    sync_interval_seconds=60,
    stale_seconds=DEFAULT_STALE_SECONDS,
    sleep=asyncio.sleep,
):
    supplied_now = now is not None
    now = aware(now) if supplied_now else datetime.now(UTC)
    minimum_interval = minimum_sync_interval(sync_interval_seconds)
    source = account_key(settings.account)
    lock_id = source_lock_id(source)
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
                    and now - aware(state.last_attempt_at) < timedelta(seconds=minimum_interval)
                ):
                    return "rate_limited"
                if not state:
                    state = SyncState(source_account=source)
                    session.add(state)
                state.last_attempt_at = now
                session.commit()  # Failed attempts also consume the shared interval.
                tracker = RetryTracker(sleep)
                try:
                    masters, snapshots = asyncio.run(
                        read_vehicle_data(settings, client_factory, sleep=sleep, tracker=tracker)
                    )
                    indexed, readings = validate_records(masters, snapshots)
                    completed_at = (
                        datetime.now(UTC)
                        if not supplied_now
                        else (now + timedelta(seconds=tracker.elapsed_seconds))
                    )
                    apply_records(session, source, indexed, readings, completed_at)
                    session.flush()
                    evaluate_distance_rules(
                        session, source, now=completed_at, stale_seconds=stale_seconds
                    )
                    state.last_attempt_at = completed_at
                    state.last_success_at = completed_at
                    state.error_code = None
                    session.commit()
                    return "ok"
                except WebfleetError as error:
                    session.rollback()
                    state = session.get(SyncState, source)
                    if not state:
                        state = SyncState(source_account=source)
                        session.add(state)
                    elapsed = getattr(error, "elapsed_seconds", tracker.elapsed_seconds)
                    failed_at = (
                        datetime.now(UTC)
                        if not supplied_now
                        else (now + timedelta(seconds=elapsed))
                    )
                    retry_wait = max(
                        minimum_interval,
                        error.retry_after_seconds or 0,
                    )
                    state.last_attempt_at = failed_at + timedelta(
                        seconds=retry_wait - minimum_interval
                    )
                    state.error_code = error.code
                    session.commit()
                    return "degraded"
                except Exception:
                    session.rollback()
                    state = session.get(SyncState, source)
                    state.error_code = "SYNC_INTERNAL_ERROR"
                    session.commit()
                    raise
        finally:
            connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": lock_id})
            connection.commit()


async def sync_worker(engine, settings, interval, *, stale_seconds=DEFAULT_STALE_SECONDS):
    while True:
        try:
            result = await asyncio.to_thread(
                sync_once,
                engine,
                settings,
                sync_interval_seconds=interval,
                stale_seconds=stale_seconds,
            )
            if result == "degraded":
                log_sync_failure("SOURCE_DEGRADED")
        except Exception:
            log_sync_failure("SYNC_INTERNAL_ERROR")
        await asyncio.sleep(interval)
