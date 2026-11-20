import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import MetaData, Table, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.models import SyncState, Vehicle
from app.core.settings import Settings
from app.main import create_app
from app.modules.auth.models import User
from app.modules.auth.service import password_hasher
from app.modules.fleet.sync import account_key, apply_records

ORIGIN = {"Origin": "http://127.0.0.1:5173"}


def test_migrated_card_ownership_and_concurrent_stale_update():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires an isolated PostgreSQL database")
    parsed = make_url(url)
    assert parsed.host in ("127.0.0.1", "localhost")
    assert parsed.database.startswith("fleet_flow_test")
    engine = create_engine(url)
    suffix = uuid4().hex
    account = "card-tests-" + suffix
    source = account_key(account)
    legacy_id, fresh_id = uuid4(), uuid4()
    username = f"card-{suffix}"
    password = "synthetic-card-test-password"
    now = datetime.now(UTC)

    def migrate(*ordered):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *ordered],
            env={**os.environ, "DATABASE_URL": url, "SYNC_ENABLED": "false"},
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "Synthetic vehicle-card migration failed"

    try:
        migrate("downgrade", "0010_manual_drivers")
        vehicles = Table("vehicles", MetaData(), autoload_with=engine)
        with engine.begin() as connection:
            connection.execute(
                vehicles.insert().values(
                    id=legacy_id,
                    external_uid="legacy",
                    source_account=source,
                    active=True,
                    locally_edited=True,
                    name="Local legacy name",
                    number="Stary numer",
                )
            )
        migrate("upgrade", "head")
        with Session(engine) as session:
            session.add_all(
                [
                    SyncState(source_account=source, last_success_at=now),
                    User(
                        username=username,
                        display_name="Synthetic editor",
                        password_hash=password_hasher.hash(password),
                        role="editor",
                    ),
                    Vehicle(
                        id=fresh_id, source_account=source, external_uid="fresh", name="Before"
                    ),
                ]
            )
            session.commit()

        app = create_app(Settings(database_url=url, webfleet_account=account))
        gate = Barrier(2)
        path = f"/api/v1/fleet/vehicles/{fresh_id}"

        def save(name):
            with TestClient(app) as client:
                response = client.post(
                    "/api/v1/auth/login",
                    headers=ORIGIN,
                    json={"username": username, "password": password},
                )
                assert response.status_code == 200
                response = client.get(path)
                version = response.json()["card_version"]
                gate.wait(timeout=15)
                return client.patch(
                    path, headers=ORIGIN, json={"card_version": version, "name": name}
                )

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(save, ("Local one", "Local two")))
        assert sorted(response.status_code for response in results) == [200, 409]
        winner = next(response.json() for response in results if response.status_code == 200)
        loser = next(response.json() for response in results if response.status_code == 409)
        assert loser["error"]["code"] == "VERSION_CONFLICT"
        assert winner["card_version"] == 2

        with Session(engine) as session:
            apply_records(
                session,
                source,
                {
                    uid: {
                        "objectname": "Provider name",
                        "objectno": "Nowy numer",
                        "licenseplatenumber": "SYN 001",
                        "vehicletype": "van",
                    }
                    for uid in ("legacy", "fresh")
                },
                {},
                now,
            )
            session.commit()
            fresh = session.get(Vehicle, fresh_id)
            assert fresh.card_version == 2 and fresh.name == winner["name"]
            assert fresh.number == "Nowy numer"
            assert fresh.license_plate == "SYN 001" and fresh.vehicle_type == "van"
            legacy = session.get(Vehicle, legacy_id)
            assert legacy.card_version == 1 and legacy.name == "Local legacy name"
            assert legacy.number == "Nowy numer"
            assert legacy.license_plate is None and legacy.vehicle_type is None

        migrate("downgrade", "0010_manual_drivers")
        with engine.connect() as connection:
            rolled_back = connection.execute(
                vehicles.select().where(vehicles.c.id == fresh_id)
            ).one()
            assert rolled_back.locally_edited and rolled_back.name == winner["name"]
            assert rolled_back.license_plate == "SYN 001"
        migrate("upgrade", "head")
    finally:
        engine.dispose()
