import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import MetaData, Table, create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import WebfleetSettings
from app.core.models import Driver, SyncState, Vehicle
from app.core.settings import Settings
from app.main import create_app
from app.modules.auth.models import LoginAttempt, LoginSession, User
from app.modules.auth.service import digest, password_hasher
from app.modules.drivers.models import DriverAssignment, DriverCategory
from app.modules.fleet import sync


def database():
    value = os.environ.get("TEST_DATABASE_URL")
    if not value:
        pytest.skip("Requires an isolated PostgreSQL database")
    url = make_url(value)
    assert url.host in ("127.0.0.1", "localhost") and url.database.startswith("fleet_flow_test")
    return value


def migrate(url, *command, success=True):
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *command],
        env={**os.environ, "DATABASE_URL": url, "SYNC_ENABLED": "false"},
        capture_output=True,
        text=True,
    )
    assert (result.returncode == 0) is success, "Unexpected manual-driver migration result"
    return result


def test_legacy_migration_keeps_names_ids_unknown_dates_and_blocks_lossy_downgrade():
    url = database()
    migrate(url, "upgrade", "head")
    migrate(url, "downgrade", "0007_user_roles")
    engine = create_engine(url)
    legacy, ambiguous, unlinked = uuid4(), uuid4(), uuid4()
    cars = [uuid4() for _ in range(4)]
    old_drivers = Table("drivers", MetaData(), autoload_with=engine)
    old_cars = Table("vehicles", MetaData(), autoload_with=engine)
    try:
        with engine.begin() as connection:
            for identity, name in (
                (legacy, "Jean Marie Kowalski"),
                (ambiguous, "Synthetic ambiguous"),
                (unlinked, "Synthetic unlinked"),
            ):
                connection.execute(
                    old_drivers.insert().values(id=identity, display_name=name, active=True)
                )
            for identity, driver_id, source in zip(
                cars,
                (legacy, legacy, ambiguous, ambiguous),
                ("a" * 64, "a" * 64, "b" * 64, "c" * 64),
                strict=True,
            ):
                connection.execute(
                    old_cars.insert().values(
                        id=identity,
                        source_account=source,
                        external_uid=identity.hex,
                        name="Synthetic",
                        active=True,
                        driver_id=driver_id,
                    )
                )
        migrate(url, "upgrade", "head")
        with Session(engine) as session:
            person = session.get(Driver, legacy)
            assert (
                person.display_name == "Jean Marie Kowalski" and person.source_account == "a" * 64
            )
            assert (
                person.first_name is None and person.last_name is None and person.identifier is None
            )
            assert session.get(Driver, ambiguous).source_account is None
            assert session.get(Driver, unlinked).source_account is None
            history = session.scalars(
                select(DriverAssignment).where(DriverAssignment.driver_id == legacy)
            ).all()
            assert len(history) == 2
            assert all(row.started_at is None and row.recorded_at and row.active for row in history)
            assert session.get(Vehicle, cars[0]).driver_id == legacy
            person.first_name = "Synthetic"
            person.version = 2
            session.commit()
        failed = migrate(url, "downgrade", "0007_user_roles", success=False)
        assert "keep schema and roll back application" in failed.stderr
        with Session(engine) as session:
            assert session.get(Driver, legacy).first_name == "Synthetic"
            assert (
                len(
                    session.scalars(
                        select(DriverAssignment).where(DriverAssignment.driver_id == legacy)
                    ).all()
                )
                == 2
            )
            person = session.get(Driver, legacy)
            person.first_name, person.version = None, 1
            session.commit()
        migrate(url, "downgrade", "0007_user_roles")
        with engine.connect() as connection:
            row = (
                connection.execute(select(old_drivers).where(old_drivers.c.id == legacy))
                .mappings()
                .one()
            )
            assert row["id"] == legacy and row["display_name"] == "Jean Marie Kowalski"
    finally:
        migrate(url, "upgrade", "head")
        with Session(engine) as session:
            session.query(DriverAssignment).filter(
                DriverAssignment.driver_id.in_((legacy, ambiguous, unlinked))
            ).delete(synchronize_session=False)
            session.query(Vehicle).filter(Vehicle.id.in_(cars)).delete(synchronize_session=False)
            session.query(Driver).filter(Driver.id.in_((legacy, ambiguous, unlinked))).delete(
                synchronize_session=False
            )
            session.commit()
        engine.dispose()


def test_postgres_concurrent_versions_multiple_drivers_and_repeat_sync_preserve_local_data(
    monkeypatch,
):
    url = database()
    migrate(url, "upgrade", "head")
    engine = create_engine(url)
    account = "synthetic-driver-" + uuid4().hex
    source = sync.account_key(account)
    username = "synthetic-driver-" + uuid4().hex
    user_id = uuid4()
    cars = [uuid4() for _ in range(3)]
    with Session(engine) as session:
        session.add(
            User(
                id=user_id,
                username=username,
                display_name="Synthetic",
                role="editor",
                password_hash=password_hasher.hash("synthetic-postgres-password"),
            )
        )
        for identity in cars:
            session.add(
                Vehicle(
                    id=identity, source_account=source, external_uid=identity.hex, name="Synthetic"
                )
            )
        session.commit()
    app = create_app(Settings(url, webfleet_account=account), engine=engine)
    origin = {"Origin": "http://127.0.0.1:5173"}
    try:
        with TestClient(app, client=("driver-concurrency-fixture", 50000)) as client:
            assert (
                client.post(
                    "/api/v1/auth/login",
                    headers=origin,
                    json={"username": username, "password": "synthetic-postgres-password"},
                ).status_code
                == 200
            )

            def person(index):
                response = client.post(
                    "/api/v1/drivers",
                    headers=origin,
                    json={
                        "first_name": "Synthetic",
                        "last_name": "Driver",
                        "identifier": "driver-" + str(index),
                        "categories": ["B"],
                    },
                )
                assert response.status_code == 201
                return response.json()

            first, second, third = [person(index) for index in range(3)]

            def assign(driver, car):
                return client.post(
                    f"/api/v1/drivers/{driver['id']}/assignments",
                    headers=origin,
                    json={"version": driver["version"], "vehicle_id": str(car)},
                )

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda car: assign(first, car), cars[:2]))
            assert sorted(row.status_code for row in results) == [201, 409]
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda driver: assign(driver, cars[2]), (second, third)))
            assert [row.status_code for row in results] == [201, 201]
            with Session(engine) as session:
                assert session.get(Vehicle, cars[2]).driver_id is None
                before = {
                    row.id: (row.driver_id, row.vehicle_id, row.started_at, row.active)
                    for row in session.scalars(
                        select(DriverAssignment)
                        .join(Driver, Driver.id == DriverAssignment.driver_id)
                        .where(Driver.source_account == source)
                    )
                }

            async def source_read(*_):
                return (
                    [
                        {
                            "objectuid": identity.hex,
                            "objectname": "Imported synthetic",
                            "drivername": "Must not import",
                        }
                        for identity in cars
                    ],
                    [],
                )

            monkeypatch.setattr(sync, "read_vehicle_data", source_read)
            settings = WebfleetSettings(account, "synthetic", "synthetic", "synthetic")
            assert sync.sync_once(engine, settings, now=datetime.now(UTC)) == "ok"
            with Session(engine) as session:
                after = {
                    row.id: (row.driver_id, row.vehicle_id, row.started_at, row.active)
                    for row in session.scalars(
                        select(DriverAssignment)
                        .join(Driver, Driver.id == DriverAssignment.driver_id)
                        .where(Driver.source_account == source)
                    )
                }
                assert before == after and len(after) == 3
                assert all(
                    row.first_name == "Synthetic"
                    for row in session.scalars(
                        select(Driver).where(Driver.source_account == source)
                    )
                )
                assert session.get(Vehicle, cars[2]).driver_id is None
    finally:
        with Session(engine) as session:
            identities = select(Driver.id).where(Driver.source_account == source)
            session.query(DriverCategory).filter(DriverCategory.driver_id.in_(identities)).delete(
                synchronize_session=False
            )
            session.query(DriverAssignment).filter(
                DriverAssignment.driver_id.in_(identities)
            ).delete(synchronize_session=False)
            session.query(Vehicle).filter(Vehicle.id.in_(cars)).delete(synchronize_session=False)
            session.query(Driver).filter(Driver.source_account == source).delete(
                synchronize_session=False
            )
            session.query(SyncState).filter(SyncState.source_account == source).delete(
                synchronize_session=False
            )
            session.query(LoginSession).filter(LoginSession.user_id == user_id).delete(
                synchronize_session=False
            )
            session.query(User).filter(User.id == user_id).delete(synchronize_session=False)
            session.query(LoginAttempt).filter(
                LoginAttempt.key.in_(
                    (digest("ip:driver-concurrency-fixture"), digest("account:" + username))
                )
            ).delete(synchronize_session=False)
            session.commit()
        engine.dispose()
