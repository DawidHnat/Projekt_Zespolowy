from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.models import Driver, Measurement, Vehicle
from app.integrations.webfleet.client import WebfleetError
from app.modules.fleet.sync import apply_records, validate_records


def sample(now):
    master = [
        {
            "objectuid": "synthetic-id",
            "objectname": "Test vehicle",
            "objectno": "TEST",
            "licenseplatenumber": "TEST 001",
            "drivername": "must-not-import",
        }
    ]
    snapshot = [
        {
            "objectuid": "synthetic-id",
            "pos_time": now.isoformat(),
            "latitude_mdeg": 52000000,
            "longitude_mdeg": 21000000,
            "standstill": "1",
            "status": "A",
            "odometer": "12345",
        }
    ]
    return master, snapshot


def test_repeated_import_preserves_id_manual_driver_and_newer_measurement(application):
    app, _ = application
    now = datetime.now(UTC)
    masters, readings = validate_records(*sample(now))
    with app.state.sessions() as session:
        apply_records(session, "test-source", masters, readings, now)
        session.commit()
        vehicle = session.scalar(select(Vehicle))
        identity = vehicle.id
        driver = Driver(display_name="Ręcznie wpisany kierowca")
        session.add(driver)
        session.flush()
        vehicle.driver_id = driver.id
        driver_id = driver.id
        session.commit()
        apply_records(session, "test-source", masters, readings, now)
        older_masters, older_readings = validate_records(*sample(now - timedelta(hours=1)))
        apply_records(session, "test-source", older_masters, older_readings, now)
        session.commit()
        assert len(list(session.scalars(select(Vehicle)))) == 1
        assert vehicle.id == identity and vehicle.driver_id == driver_id
        assert len(list(session.scalars(select(Driver)))) == 1
        measurement = session.get(Measurement, identity)
        assert measurement.position_at.replace(tzinfo=UTC) == now
        assert float(measurement.odometer_km) == 1234.5


def test_incomplete_or_duplicate_reports_cannot_deactivate_cached_vehicles():
    with pytest.raises(WebfleetError):
        validate_records([], [{"objectuid": "orphan"}])
    master, snapshots = sample(datetime.now(UTC))
    with pytest.raises(WebfleetError):
        validate_records(master + master, snapshots)
    with pytest.raises(WebfleetError):
        validate_records(master, snapshots + snapshots)


def test_postgres_shared_limiter_failure_cache_and_lock():
    import os
    from uuid import uuid4

    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url

    from app.core.config import WebfleetSettings
    from app.core.models import Base, SyncState
    from app.modules.fleet.sync import account_key, sync_once

    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires an isolated PostgreSQL database")
    assert make_url(url).database.startswith("fleet_flow_test")
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    settings = WebfleetSettings("synthetic-" + str(uuid4()), "test", "test", "test")
    now = datetime.now(UTC)
    calls = []

    class FakeClient:
        def __init__(self, _):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        async def fetch_vehicles(self):
            calls.append("vehicles")
            return sample(now)[0]

        async def fetch_objects(self):
            calls.append("objects")
            return sample(now)[1]

    class FailedClient(FakeClient):
        async def fetch_vehicles(self):
            raise WebfleetError("timeout")

    assert sync_once(engine, settings, client_factory=FakeClient, now=now) == "ok"
    assert (
        sync_once(engine, settings, client_factory=FakeClient, now=now + timedelta(seconds=30))
        == "rate_limited"
    )
    assert calls == ["vehicles", "objects"]
    assert (
        sync_once(engine, settings, client_factory=FailedClient, now=now + timedelta(seconds=60))
        == "degraded"
    )
    from sqlalchemy.orm import Session

    with Session(engine) as session:
        source = account_key(settings.account)
        state = session.get(SyncState, source)
        assert state.error_code == "timeout"
        assert state.last_success_at == now
        assert (
            len(list(session.scalars(select(Vehicle).where(Vehicle.source_account == source)))) == 1
        )
    key = int.from_bytes(bytes.fromhex(source)[:8], signed=True)
    with engine.connect() as connection:
        connection.execute(text("SELECT pg_advisory_lock(:key)"), {"key": key})
        connection.commit()
        try:
            assert (
                sync_once(
                    engine, settings, client_factory=FakeClient, now=now + timedelta(seconds=120)
                )
                == "busy"
            )
            assert calls == ["vehicles", "objects"]
        finally:
            connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": key})
            connection.commit()
    engine.dispose()
