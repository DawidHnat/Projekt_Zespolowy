from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import case, func, select

from app.core.errors import ApiError
from app.core.models import Vehicle
from app.modules.trips.models import Trip
from app.modules.trips.service import WARSAW, calendar_window, polish_day, report_coverages


def local_start_day(session, from_day, through):
    if session.bind.dialect.name == "postgresql":
        return func.date(func.timezone(WARSAW.key, Trip.start_at))
    # SQLite test sessions have no IANA zone conversion. Use the same UTC bounds.
    days = [from_day + timedelta(days=offset) for offset in range((through - from_day).days + 1)]
    return case(*[(Trip.start_at < polish_day(day)[1], day.isoformat()) for day in days])


def totals(rows, *, complete):
    distance = sum((row.distance for row in rows if row.distance is not None), Decimal())
    trip_count = sum(row.trips for row in rows)
    known_distances = sum(row.known_distances for row in rows)
    return {
        "distance_km": float(distance) if known_distances else None,
        "trip_count": trip_count if rows or complete else None,
        "active_days": len({row.day for row in rows}) if rows or complete else None,
        "missing_distance": trip_count - known_distances,
    }


def period_usage(session, source, vehicle_ids, from_day, through):
    lower, upper = calendar_window(from_day, through)
    ids = list(dict.fromkeys(vehicle_ids))
    vehicles = {
        row.id: row.name
        for row in session.execute(
            select(Vehicle.id, Vehicle.name).where(
                Vehicle.source_account == source, Vehicle.id.in_(ids)
            )
        )
    }
    if len(vehicles) != len(ids):
        raise ApiError(404, "NOT_FOUND", "Co najmniej jeden pojazd nie istnieje")

    coverage = report_coverages(session, ids, lower, upper)
    by_vehicle = defaultdict(list)
    day = local_start_day(session, from_day, through).label("day")
    rows = session.execute(
        select(
            Trip.vehicle_id,
            day,
            func.count(Trip.id).label("trips"),
            func.count(Trip.distance_km).label("known_distances"),
            func.sum(Trip.distance_km).label("distance"),
        )
        .where(Trip.vehicle_id.in_(ids), Trip.start_at >= lower, Trip.start_at < upper)
        .group_by(Trip.vehicle_id, day)
    ).all()
    for row in rows:
        by_vehicle[row.vehicle_id].append(row)
    items = [
        {
            "vehicle_id": str(uid),
            "name": vehicles[uid],
            "coverage": coverage[uid],
            **totals(by_vehicle[uid], complete=coverage[uid]["state"] == "complete"),
        }
        for uid in ids
    ]
    complete = all(item["coverage"]["state"] == "complete" for item in items)
    return {
        "source": "webfleet_trip_history",
        "timezone": WARSAW.key,
        "day_basis": "trip_start_day",
        "items": items,
        "summary": {
            **totals(rows, complete=complete),
            "coverage_complete": complete and all(item["missing_distance"] == 0 for item in items),
        },
    }
