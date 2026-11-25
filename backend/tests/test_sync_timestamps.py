import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import WebfleetSettings
from app.core.models import Base, Measurement, Vehicle
from app.modules.analytics.models import DailyDistance
from app.modules.fleet.sync import account_key, sync_once


@pytest.mark.parametrize("legacy_future", [False, True])
def test_provider_timestamps_do_not_overwrite_or_poison_last_good_sample(legacy_future):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires an isolated PostgreSQL database")
    parsed = make_url(url)
    assert parsed.host in ("127.0.0.1", "localhost")
    assert parsed.database.startswith("fleet_flow_test")
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    settings = WebfleetSettings(f"synthetic-time-{uuid4()}", "test", "test", "test")
    source = account_key(settings.account)
    start = datetime(2026, 1, 8, 11, tzinfo=UTC)

    def run(elapsed_minutes, sample_seconds, latitude, odometer):
        class FakeWebfleet:
            def __init__(self, _):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_):
                pass

            async def fetch_vehicles(self):
                return [{"objectuid": "timestamp-test"}]

            async def fetch_objects(self):
                return [
                    {
                        "objectuid": "timestamp-test",
                        "pos_time": (start + timedelta(seconds=sample_seconds)).isoformat()
                        if sample_seconds is not None
                        else None,
                        "status": "A",
                        "latitude_mdeg": latitude * 1000000,
                        "longitude_mdeg": 0,
                        "odometer": odometer,
                    }
                ]

        return sync_once(
            engine,
            settings,
            client_factory=FakeWebfleet,
            now=start + timedelta(minutes=elapsed_minutes),
        )

    try:
        assert run(0, 0, 1, "10000") == "ok"
        with Session(engine) as session:
            vehicle_id = session.scalar(select(Vehicle.id).where(Vehicle.source_account == source))
            if legacy_future:
                measurement = session.get(Measurement, vehicle_id)
                measurement.position_at = start + timedelta(seconds=600)
                session.commit()

        assert run(1, 61, 2, "20000") == "ok"  # One second in the future.
        with Session(engine) as session:
            measurement = session.get(Measurement, vehicle_id)
            assert measurement.latitude == 1
            assert measurement.received_at == start

        assert run(2, 120, 3, "10100") == "ok"
        assert run(3, 120, 4, "20000") == "ok"  # Same timestamp, conflicting values.
        assert run(4, 119, 5, "20000") == "ok"
        assert run(5, None, 6, "20000") == "ok"
        with Session(engine) as session:
            measurement = session.get(Measurement, vehicle_id)
            assert measurement.latitude == 3
            assert (
                measurement.received_at == measurement.position_at == start + timedelta(minutes=2)
            )
            assert measurement.odometer_km == 1010
            interval = session.scalar(
                select(DailyDistance).where(DailyDistance.vehicle_id == vehicle_id)
            )
            if legacy_future:
                assert interval is None
            else:
                assert interval.distance_km == 10
    finally:
        engine.dispose()
