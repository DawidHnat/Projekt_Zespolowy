import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.models import Driver, Measurement, Vehicle
from app.integrations.webfleet.client import WebfleetError
from app.modules.fleet.sync import apply_records, read_vehicle_data, validate_records


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


def test_source_reads_retry_transient_failures_with_bounded_delays():
    now = datetime.now(UTC)
    expected = sample(now)
    attempts = {"vehicles": 0, "objects": 0}
    delays = []

    class RetryingClient:
        def __init__(self, _):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        async def fetch_vehicles(self):
            attempts["vehicles"] += 1
            if attempts["vehicles"] == 1:
                raise WebfleetError("timeout")
            return expected[0]

        async def fetch_objects(self):
            attempts["objects"] += 1
            if attempts["objects"] < 3:
                raise WebfleetError("provider_rate_limit", retry_after_seconds=20)
            return expected[1]

    async def no_wait(delay):
        delays.append(delay)

    result = asyncio.run(read_vehicle_data(None, RetryingClient, sleep=no_wait))

    assert result == expected
    assert attempts == {"vehicles": 2, "objects": 3}
    assert delays == [10, 20, 20]


def test_source_reads_stop_after_three_transient_failures():
    calls = []
    delays = []

    class UnavailableClient:
        def __init__(self, _):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        async def fetch_vehicles(self):
            calls.append("vehicles")
            raise WebfleetError("connection_failed")

    async def no_wait(delay):
        delays.append(delay)

    with pytest.raises(WebfleetError, match="connection_failed"):
        asyncio.run(read_vehicle_data(None, UnavailableClient, sleep=no_wait))

    assert calls == ["vehicles"] * 3
    assert delays == [10, 10]


def test_source_does_not_retry_beyond_retry_after_cap():
    calls = []
    delays = []

    class RateLimitedClient:
        def __init__(self, _):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        async def fetch_vehicles(self):
            calls.append("vehicles")
            raise WebfleetError("provider_rate_limit", retry_after_seconds=61)

    async def no_wait(delay):
        delays.append(delay)

    with pytest.raises(WebfleetError, match="provider_rate_limit"):
        asyncio.run(read_vehicle_data(None, RateLimitedClient, sleep=no_wait))

    assert calls == ["vehicles"]
    assert delays == []


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

    assert (
        sync_once(
            engine,
            settings,
            client_factory=FakeClient,
            now=now,
            sync_interval_seconds=30,
        )
        == "ok"
    )
    assert (
        sync_once(
            engine,
            settings,
            client_factory=FakeClient,
            now=now + timedelta(seconds=10),
            sync_interval_seconds=30,
        )
        == "rate_limited"
    )
    assert calls == ["vehicles", "objects"]
    assert (
        sync_once(
            engine,
            settings,
            client_factory=FakeClient,
            now=now + timedelta(seconds=30),
            sync_interval_seconds=30,
        )
        == "ok"
    )
    assert calls == ["vehicles", "objects", "vehicles", "objects"]
    assert (
        sync_once(
            engine,
            settings,
            client_factory=FailedClient,
            now=now + timedelta(seconds=39),
            sync_interval_seconds=1,
        )
        == "rate_limited"
    )
    assert (
        sync_once(
            engine,
            settings,
            client_factory=FailedClient,
            now=now + timedelta(seconds=40),
            sync_interval_seconds=1,
        )
        == "degraded"
    )
    from sqlalchemy.orm import Session

    with Session(engine) as session:
        source = account_key(settings.account)
        state = session.get(SyncState, source)
        assert state.error_code == "timeout"
        assert state.last_success_at == now + timedelta(seconds=30)
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
            assert calls == ["vehicles", "objects", "vehicles", "objects"]
        finally:
            connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": key})
            connection.commit()
    engine.dispose()


def test_two_cycles_rate_limit_blocks_second_cycle_after_retry_exhaustion():
    from sqlalchemy import create_engine, event
    from sqlalchemy.pool import StaticPool

    from app.core.config import WebfleetSettings
    from app.core.models import Base
    from app.modules.fleet.sync import sync_once

    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )

    @event.listens_for(engine, "connect")
    def register_advisory_functions(dbapi_connection, _):
        dbapi_connection.create_function("pg_try_advisory_lock", 1, lambda key: 1)
        dbapi_connection.create_function("pg_advisory_unlock", 1, lambda key: 1)

    Base.metadata.create_all(engine)

    t0 = datetime(2026, 11, 10, 12, 0, 0, tzinfo=UTC)
    settings = WebfleetSettings("regress-account", "u", "p", "k")

    request_times = []
    delays = []

    class VirtualClock:
        def __init__(self, current):
            self.current = current

        async def sleep(self, seconds):
            delays.append(seconds)
            self.current += timedelta(seconds=seconds)

    clock = VirtualClock(t0)

    class RateLimitedClient:
        def __init__(self, _):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        async def fetch_vehicles(self):
            request_times.append((clock.current - t0).total_seconds())
            raise WebfleetError("provider_rate_limit", retry_after_seconds=60)

    result1 = sync_once(
        engine,
        settings,
        client_factory=RateLimitedClient,
        now=clock.current,
        sync_interval_seconds=60,
        sleep=clock.sleep,
    )
    assert result1 == "degraded"
    assert request_times == [0, 60, 120]
    assert delays == [60, 60]
    assert clock.current == t0 + timedelta(seconds=120)

    # Cycle 2 immediately at t0 + 120s must be blocked by rate limiting
    result2 = sync_once(
        engine,
        settings,
        client_factory=RateLimitedClient,
        now=clock.current,
        sync_interval_seconds=60,
        sleep=clock.sleep,
    )
    assert result2 == "rate_limited"
    assert request_times == [0, 60, 120]

    # Still rate-limited at 179s
    result_179 = sync_once(
        engine,
        settings,
        client_factory=RateLimitedClient,
        now=t0 + timedelta(seconds=179),
        sync_interval_seconds=60,
        sleep=clock.sleep,
    )
    assert result_179 == "rate_limited"
    assert request_times == [0, 60, 120]

    # At 180s, cooldown expires and next cycle runs
    clock.current = t0 + timedelta(seconds=180)
    result3 = sync_once(
        engine,
        settings,
        client_factory=RateLimitedClient,
        now=clock.current,
        sync_interval_seconds=60,
        sleep=clock.sleep,
    )
    assert result3 == "degraded"
    assert request_times == [0, 60, 120, 180, 240, 300]
    engine.dispose()


def test_validate_records_rejects_odometer_overflow():
    master = [{"objectuid": "v-1", "objectname": "Test"}]
    snapshot = [{"objectuid": "v-1", "odometer": "1000000000000000"}]
    with pytest.raises(WebfleetError) as exc_info:
        validate_records(master, snapshot)
    assert exc_info.value.code == "INVALID_RECORDS"


def test_corrupt_odometer_marks_sync_degraded_and_recovers_on_next_cycle():
    """SCRUM-131: An out-of-range odometer must not throw DataError or leave status ok."""
    import os
    from uuid import uuid4

    from sqlalchemy import create_engine
    from sqlalchemy.engine import make_url
    from sqlalchemy.orm import Session

    from app.core.config import WebfleetSettings
    from app.core.models import Base, Measurement, SyncState, Vehicle
    from app.modules.fleet.service import source_payload
    from app.modules.fleet.sync import account_key, sync_once

    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires an isolated PostgreSQL database")
    assert make_url(url).database.startswith("fleet_flow_test")
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    settings = WebfleetSettings("synthetic-" + str(uuid4()), "test", "test", "test")
    source = account_key(settings.account)
    t0 = datetime.now(UTC)

    masters = [
        {
            "objectuid": "v-131",
            "objectname": "Pojazd 131",
            "objectno": "P-131",
            "licenseplatenumber": "GD 131AA",
        }
    ]

    class GoodClient:
        def __init__(self, _):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        async def fetch_vehicles(self):
            return masters

        async def fetch_objects(self):
            return [
                {
                    "objectuid": "v-131",
                    "pos_time": t0.isoformat(),
                    "latitude_mdeg": 54000000,
                    "longitude_mdeg": 18000000,
                    "standstill": "0",
                    "status": "A",
                    "odometer": "12345",
                }
            ]

    class OverflowClient(GoodClient):
        async def fetch_objects(self):
            return [
                {
                    "objectuid": "v-131",
                    "pos_time": (t0 + timedelta(seconds=65)).isoformat(),
                    "latitude_mdeg": 54000000,
                    "longitude_mdeg": 18000000,
                    "standstill": "0",
                    "status": "A",
                    "odometer": "1000000000000000",
                }
            ]

    class RecoveredClient(GoodClient):
        async def fetch_objects(self):
            return [
                {
                    "objectuid": "v-131",
                    "pos_time": (t0 + timedelta(seconds=130)).isoformat(),
                    "latitude_mdeg": 54000000,
                    "longitude_mdeg": 18000000,
                    "standstill": "0",
                    "status": "A",
                    "odometer": "12400",
                }
            ]

    # Cycle 1: initial valid sync
    assert (
        sync_once(
            engine, settings, client_factory=GoodClient, now=t0, sync_interval_seconds=60
        )
        == "ok"
    )
    with Session(engine) as session:
        state = session.get(SyncState, source)
        assert state.error_code is None
        assert state.last_success_at == t0
        payload = source_payload(session, source)
        assert payload["status"] == "ok"
        assert payload["error_code"] is None
        vehicle = session.scalar(select(Vehicle).where(Vehicle.external_uid == "v-131"))
        assert vehicle is not None
        measurement = session.get(Measurement, vehicle.id)
        assert float(measurement.odometer_km) == 1234.5

    # Cycle 2: corrupted odometer (10^15)
    t1 = t0 + timedelta(seconds=65)
    result = sync_once(
        engine, settings, client_factory=OverflowClient, now=t1, sync_interval_seconds=60
    )
    assert result == "degraded"
    with Session(engine) as session:
        state = session.get(SyncState, source)
        assert state.error_code == "INVALID_RECORDS"
        assert state.last_success_at == t0
        payload = source_payload(session, source)
        assert payload["status"] == "degraded"
        assert payload["error_code"] == "INVALID_RECORDS"
        measurement = session.get(Measurement, vehicle.id)
        assert float(measurement.odometer_km) == 1234.5

    # Cycle 3: recovery with valid data
    t2 = t0 + timedelta(seconds=130)
    result = sync_once(
        engine, settings, client_factory=RecoveredClient, now=t2, sync_interval_seconds=60
    )
    assert result == "ok"
    with Session(engine) as session:
        state = session.get(SyncState, source)
        assert state.error_code is None
        assert state.last_success_at == t2
        payload = source_payload(session, source)
        assert payload["status"] == "ok"
        assert payload["error_code"] is None
        measurement = session.get(Measurement, vehicle.id)
        assert float(measurement.odometer_km) == 1240.0

    engine.dispose()
