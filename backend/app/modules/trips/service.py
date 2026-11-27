from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.modules.auth.service import aware
from app.modules.trips.models import TripHistoryDay

WARSAW = ZoneInfo("Europe/Warsaw")


def polish_day(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, WARSAW)
    end = datetime.combine(day + timedelta(days=1), time.min, WARSAW)
    return start.astimezone(UTC), end.astimezone(UTC)


def report_coverage(session, vehicle_id, lower, upper):
    first = lower.astimezone(WARSAW).date()
    last = (upper - timedelta(microseconds=1)).astimezone(WARSAW).date()
    rows = session.scalars(
        select(TripHistoryDay).where(
            TripHistoryDay.vehicle_id == vehicle_id,
            TripHistoryDay.report_day.between(first, last),
        )
    ).all()
    covered = sorted(row.report_day.isoformat() for row in rows if row.imported_at)
    failed = sorted(row.report_day.isoformat() for row in rows if row.error_code)
    last_success = max((aware(row.imported_at) for row in rows if row.imported_at), default=None)
    requested = (last - first).days + 1
    state = "unavailable"
    if len(covered) == requested and not failed:
        state = "complete"
    elif covered or failed:
        state = "partial"
    return {
        "basis": "report_end_day",
        "state": state,
        "requested_days": requested,
        "covered_days": covered,
        "failed_days": failed,
        "last_success_at": last_success.isoformat() if last_success else None,
    }


def annotation_payload(annotation, author):
    if annotation is None:
        return {
            "purpose": None,
            "description": None,
            "version": 1,
            "updated_at": None,
            "updated_by": None,
        }
    return {
        "purpose": annotation.purpose,
        "description": annotation.description,
        "version": annotation.version,
        "updated_at": aware(annotation.updated_at).isoformat(),
        "updated_by": {"id": str(author.id), "display_name": author.display_name},
    }


def trip_payload(trip, annotation, author, vehicle_name=None):
    start = aware(trip.start_at)
    end = aware(trip.end_at) if trip.end_at else None
    return {
        "id": str(trip.id),
        "vehicle_id": str(trip.vehicle_id),
        "start_at": start.isoformat(),
        "end_at": end.isoformat() if end else None,
        "distance_km": float(trip.distance_km) if trip.distance_km is not None else None,
        "duration_seconds": int((end - start).total_seconds()) if end else None,
        "vehicle_name": vehicle_name,
        "start_address": trip.start_address,
        "end_address": trip.end_address,
        "driver_id": str(trip.driver_id) if trip.driver_id else None,
        "withdrawn_at": aware(trip.withdrawn_at).isoformat() if trip.withdrawn_at else None,
        "annotation": annotation_payload(annotation, author),
        "geometry": None,
    }
