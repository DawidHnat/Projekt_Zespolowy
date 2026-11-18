from datetime import UTC, datetime, timedelta

import pytest

from app.core.models import Measurement, SyncState
from app.modules.fleet.sync import account_key, apply_records, validate_records


def add_speed_snapshot(app, raw_speed=72.5):
    now = datetime.now(UTC)
    source = account_key(app.state.settings.webfleet_account)
    masters, readings = validate_records(
        [{"objectuid": "synthetic-speed", "objectname": "Test prędkości"}],
        [
            {
                "objectuid": "synthetic-speed",
                "latitude_mdeg": 0,
                "longitude_mdeg": 0,
                "status": "A",
                "standstill": "0",
                "pos_time": now.isoformat(),
                "speed": raw_speed,
            }
        ],
    )
    with app.state.sessions() as session:
        session.add(SyncState(source_account=source, last_attempt_at=now, last_success_at=now))
        apply_records(session, source, masters, readings, now)
        session.commit()
        measurement = session.query(Measurement).one()
        return str(measurement.vehicle_id), now


@pytest.mark.parametrize(
    ("raw_speed", "expected"),
    [
        (0, 0.0),
        (65, 65.0),
        (86.4, 86.4),
        ("72.5", 72.5),
        (300, 300.0),
        (None, None),
        (301, None),
        ("NaN", None),
    ],
)
def test_provider_speed_reaches_list_and_detail_in_kmh(logged_in, raw_speed, expected):
    app, client = logged_in
    vehicle_id, _ = add_speed_snapshot(app, raw_speed)
    detail = client.get(f"/api/v1/fleet/vehicles/{vehicle_id}").json()
    listing = client.get("/api/v1/fleet/vehicles").json()["items"][0]
    assert detail["speed_kmh"] == listing["speed_kmh"] == expected
    assert detail["status"] == "moving"
    assert detail["is_stale"] is False


@pytest.mark.parametrize(
    "case", ["old", "missing_time", "future", "no_gps", "last_fix", "uncertain_fix", "source_error"]
)
def test_unconfirmed_measurement_does_not_expose_current_speed(logged_in, case):
    app, client = logged_in
    vehicle_id, now = add_speed_snapshot(app)
    with app.state.sessions() as session:
        measurement = session.query(Measurement).one()
        if case == "old":
            measurement.position_at = now - timedelta(minutes=16)
        elif case == "missing_time":
            measurement.position_at = None
        elif case == "future":
            measurement.position_at = now + timedelta(minutes=1)
        elif case == "no_gps":
            measurement.latitude = None
        elif case == "last_fix":
            measurement.gps_quality = "L"
        elif case == "uncertain_fix":
            measurement.gps_quality = "V"
        else:
            state = session.get(SyncState, account_key(app.state.settings.webfleet_account))
            state.error_code = "timeout"
        session.commit()
    detail = client.get(f"/api/v1/fleet/vehicles/{vehicle_id}").json()
    listing = client.get("/api/v1/fleet/vehicles").json()["items"][0]
    assert detail["speed_kmh"] is None
    assert listing["speed_kmh"] is None
