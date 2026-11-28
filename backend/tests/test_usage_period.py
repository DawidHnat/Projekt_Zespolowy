from datetime import date, timedelta
from decimal import Decimal

from app.core.models import Vehicle
from app.modules.fleet.sync import account_key
from app.modules.trips.models import Trip, TripHistoryDay
from app.modules.trips.service import polish_day


def test_usage_metrics_are_scoped_by_vehicle_and_local_start_day(logged_in):
    app, client = logged_in
    source = account_key(app.state.settings.webfleet_account)
    first = date(2026, 10, 24)
    last = first + timedelta(days=1)
    start, midnight = polish_day(first)
    _, end = polish_day(last)
    with app.state.sessions() as session:
        one, two, empty, foreign = [
            Vehicle(
                source_account=source if name != "D" else "separate", external_uid=name, name=name
            )
            for name in "ABCD"
        ]
        session.add_all([one, two, empty, foreign])
        session.flush()
        session.add_all(
            [
                Trip(
                    vehicle_id=one.id,
                    external_uid="11",
                    start_at=start,
                    distance_km=Decimal("10.005"),
                ),
                Trip(
                    vehicle_id=one.id,
                    external_uid="12",
                    start_at=midnight - timedelta(minutes=1),
                    end_at=midnight + timedelta(minutes=1),
                    distance_km=Decimal("2.001"),
                ),
                Trip(vehicle_id=one.id, external_uid="13", start_at=midnight),
                Trip(
                    vehicle_id=two.id,
                    external_uid="21",
                    start_at=start,
                    distance_km=Decimal("1.001"),
                ),
                Trip(
                    vehicle_id=two.id, external_uid="22", start_at=end, distance_km=Decimal("100")
                ),
                TripHistoryDay(vehicle_id=one.id, report_day=first, imported_at=end),
            ]
        )
        ids = [str(vehicle.id) for vehicle in (one, two, empty)]
        isolated_id = str(foreign.id)
        session.commit()
    params = {"vehicle_ids": ids, "from_day": first.isoformat(), "through": last.isoformat()}
    path = "/api/v1/analytics/usage"
    response = client.get(path, params=params)
    assert response.status_code == 200
    data = response.json()
    a, b, unknown = data["items"]
    assert a["coverage"]["state"] == "partial"
    assert a["distance_km"] == 12.006 and a["active_days"] == 2
    assert b["distance_km"] == 1.001 and b["active_days"] == 1 and b["trip_count"] == 1
    assert unknown["distance_km"] is None and unknown["active_days"] is None
    assert data["summary"] == {
        "distance_km": 13.007,
        "trip_count": 4,
        "active_days": 2,
        "missing_distance": 1,
        "coverage_complete": False,
    }
    assert client.get(path, params={**params, "vehicle_ids": [isolated_id]}).status_code == 404
    assert client.get(path, params={**params, "through": "2026-01-01"}).status_code == 422
