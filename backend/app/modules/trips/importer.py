"""Import a completed Polish calendar day outside the HTTP request path."""

import asyncio
from datetime import UTC, date, datetime, timedelta
from hashlib import sha256
from uuid import UUID

from sqlalchemy import delete, func, or_, select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.models import Vehicle
from app.integrations.webfleet.client import REQUEST_INTERVALS, WebfleetClient, WebfleetError
from app.integrations.webfleet.history import stop_values, trip_values
from app.modules.auth.service import aware
from app.modules.drivers.models import DriverAssignment
from app.modules.fleet.sync import account_key, source_lock_id
from app.modules.trips.models import (
    Trip,
    TripAnnotation,
    TripHistoryDay,
    TripHistorySource,
    TripStop,
)
from app.modules.trips.service import WARSAW, polish_day

REPORT_INTERVAL = timedelta(seconds=REQUEST_INTERVALS["showTripReportExtern"])


async def fetch_day(factory, settings, object_uid, start, end):
    async with factory(settings) as client:
        return await client.fetch_trip_history(object_uid, start, end)


def import_one_day(
    engine,
    settings,
    vehicle_id: UUID,
    first: date,
    last: date,
    *,
    refresh=False,
    client_factory=WebfleetClient,
    clock=lambda: datetime.now(UTC),
):
    if not 0 <= (last - first).days < 93 or last >= clock().astimezone(WARSAW).date():
        raise ValueError("Wybierz do 93 zakończonych dni kalendarzowych")
    if refresh and first != last:
        raise ValueError("Ponowny import obejmuje jeden dzień")
    source = account_key(settings.account)
    lock = source_lock_id(sha256(("trip-history:" + source).encode()).hexdigest())
    with engine.connect() as connection:
        locked = connection.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": lock})
        connection.commit()
        if not locked:
            return "busy"
        try:
            with Session(connection, expire_on_commit=False) as session:
                vehicle = session.get(Vehicle, vehicle_id)
                if vehicle is None or vehicle.source_account != source:
                    return "unknown_vehicle"
                return import_pending_day(
                    session, settings, vehicle, first, last, refresh, client_factory, clock
                )
        finally:
            connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": lock})
            connection.commit()


def import_pending_day(session, settings, vehicle, first, last, refresh, factory, clock):
    done = set(
        session.scalars(
            select(TripHistoryDay.report_day).where(
                TripHistoryDay.vehicle_id == vehicle.id,
                TripHistoryDay.report_day.between(first, last),
                TripHistoryDay.imported_at.is_not(None),
                TripHistoryDay.error_code.is_(None),
            )
        )
    )
    days = (first + timedelta(days=offset) for offset in range((last - first).days + 1))
    day = next((day for day in days if refresh or day not in done), None)
    if day is None:
        return "complete"

    now = clock()
    limiter = session.get(TripHistorySource, vehicle.source_account)
    if limiter and now < aware(limiter.next_attempt_at):
        return "rate_limited"
    if limiter is None:
        limiter = TripHistorySource(
            source_account=vehicle.source_account, next_attempt_at=now + REPORT_INTERVAL
        )
        session.add(limiter)
    status = session.get(TripHistoryDay, (vehicle.id, day))
    if status is None:
        status = TripHistoryDay(vehicle_id=vehicle.id, report_day=day)
        session.add(status)
    limiter.next_attempt_at = now + REPORT_INTERVAL
    status.error_code = "IMPORT_PENDING"
    session.commit()

    start, end = polish_day(day)
    try:
        trips, stops = asyncio.run(fetch_day(factory, settings, vehicle.external_uid, start, end))
        save_day(session, vehicle, start, end, trips, stops, clock())
        status.imported_at = clock()
        status.error_code = None
        session.commit()
    except WebfleetError as error:
        session.rollback()
        status.error_code = error.code
        if error.retry_after_seconds:
            limiter.next_attempt_at = max(
                aware(limiter.next_attempt_at),
                clock() + timedelta(seconds=min(error.retry_after_seconds, 86400)),
            )
        session.commit()
        return "degraded"
    return "imported"


def save_day(session, vehicle, start, end, trips, stops, now):
    trip_rows = {}
    for row in trips:
        if str(row.get("tripmode")) == "4":
            continue  # A manual odometer correction is not a driven trip.
        values = trip_values(row, vehicle.external_uid)
        if start <= (values["end_at"] or values["start_at"]) < end:
            if values["external_uid"] in trip_rows and trip_rows[values["external_uid"]] != values:
                raise WebfleetError("INVALID_HISTORY_RECORDS")
            trip_rows[values["external_uid"]] = values

    stop_rows = {}
    for row in stops:
        values = stop_values(row, vehicle.external_uid)
        if start <= values["end_at"] < end:
            if values["start_at"] in stop_rows and stop_rows[values["start_at"]] != values:
                raise WebfleetError("INVALID_HISTORY_RECORDS")
            stop_rows[values["start_at"]] = values

    for values in trip_rows.values():
        assigned = list(
            session.scalars(
                select(DriverAssignment.driver_id)
                .distinct()
                .where(
                    DriverAssignment.vehicle_id == vehicle.id,
                    DriverAssignment.started_at <= values["start_at"],
                    or_(
                        DriverAssignment.ended_at.is_(None),
                        DriverAssignment.ended_at > values["start_at"],
                    ),
                )
                .limit(2)
            )
        )
        write = insert(Trip).values(
            vehicle_id=vehicle.id, driver_id=assigned[0] if len(assigned) == 1 else None, **values
        )
        session.execute(
            write.on_conflict_do_update(
                index_elements=[Trip.vehicle_id, Trip.external_uid],
                set_={
                    **{field: value for field, value in values.items() if field != "external_uid"},
                    # A trip that is back in the complete report is current again.
                    "withdrawn_at": None,
                },
            )
        )
    for values in stop_rows.values():
        write = insert(TripStop).values(vehicle_id=vehicle.id, **values)
        session.execute(
            write.on_conflict_do_update(
                index_elements=[TripStop.vehicle_id, TripStop.start_at],
                set_={field: value for field, value in values.items() if field != "start_at"},
            )
        )
    reconcile_day(session, vehicle, start, end, set(trip_rows), set(stop_rows), now)


def reconcile_day(session, vehicle, start, end, trip_uids, stop_starts, now):
    """A completed day's report is complete: drop what it no longer lists.

    Stops hold only source data and are removed. Trips without a local annotation
    are removed; annotated trips are kept and marked as withdrawn, so the user's
    purpose and description are never lost.
    """
    trip_day = func.coalesce(Trip.end_at, Trip.start_at)
    missing = select(Trip.id).where(
        Trip.vehicle_id == vehicle.id, trip_day >= start, trip_day < end
    )
    if trip_uids:
        missing = missing.where(Trip.external_uid.not_in(trip_uids))
    annotated = select(TripAnnotation.trip_id).where(TripAnnotation.trip_id.in_(missing))
    session.execute(
        update(Trip)
        .where(Trip.id.in_(annotated), Trip.withdrawn_at.is_(None))
        .values(withdrawn_at=now)
        .execution_options(synchronize_session=False)
    )
    session.execute(
        delete(Trip)
        .where(Trip.id.in_(missing), Trip.id.not_in(annotated))
        .execution_options(synchronize_session=False)
    )
    stale_stops = delete(TripStop).where(
        TripStop.vehicle_id == vehicle.id, TripStop.end_at >= start, TripStop.end_at < end
    )
    if stop_starts:
        stale_stops = stale_stops.where(TripStop.start_at.not_in(stop_starts))
    session.execute(stale_stops.execution_options(synchronize_session=False))
