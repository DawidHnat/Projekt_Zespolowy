import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import WebfleetSettings
from app.core.models import Vehicle
from app.core.settings import Settings
from app.main import create_app
from app.modules.analytics.models import Alert, DailyDistance, Rule
from app.modules.auth.models import User
from app.modules.auth.service import password_hasher
from app.modules.fleet.sync import account_key, sync_once

ORIGIN = {"Origin": "http://127.0.0.1:5173"}


@pytest.mark.parametrize(("stale_seconds", "expected_total"), [(15, 0), (300, 2)])
def test_rule_edit_and_sync_agree_on_configured_freshness(stale_seconds, expected_total):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires an isolated PostgreSQL database")
    parsed = make_url(url)
    assert parsed.host in ("127.0.0.1", "localhost")
    assert parsed.database.startswith("fleet_flow_test")
    migration = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        env={**os.environ, "DATABASE_URL": url, "SYNC_ENABLED": "false"},
        capture_output=True,
        text=True,
    )
    assert migration.returncode == 0, "Synthetic alert migration failed"
    engine = create_engine(url)
    suffix = uuid4().hex
    account = "alert-freshness-" + suffix
    source = account_key(account)
    now = datetime.now(UTC)
    observed = now - timedelta(minutes=1)
    username, password = f"alerts-{suffix}", "synthetic-freshness-password"

    class Provider:
        def __init__(self, _):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        async def fetch_vehicles(self):
            return [{"objectuid": "synthetic-alert-car"}]

        async def fetch_objects(self):
            return []

    try:
        with Session(engine) as session:
            vehicle = Vehicle(
                source_account=source, external_uid="synthetic-alert-car", name="Synthetic vehicle"
            )
            session.add_all(
                [
                    vehicle,
                    User(
                        username=username,
                        display_name="Synthetic editor",
                        password_hash=password_hasher.hash(password),
                        role="editor",
                    ),
                ]
            )
            session.flush()
            worker_rule = Rule(
                source_account=source, vehicle_id=vehicle.id, threshold_km=Decimal("10")
            )
            manual_rule = Rule(
                source_account=source,
                vehicle_id=vehicle.id,
                threshold_km=Decimal("10"),
                active=False,
            )
            session.add_all(
                [
                    worker_rule,
                    manual_rule,
                    DailyDistance(
                        vehicle_id=vehicle.id,
                        event_day=observed.astimezone(ZoneInfo("Europe/Warsaw")).date(),
                        first_observed_at=observed - timedelta(minutes=1),
                        last_observed_at=observed,
                        distance_km=Decimal("15"),
                    ),
                ]
            )
            session.flush()
            rule_ids = {worker_rule.id, manual_rule.id}
            manual_id = manual_rule.id
            session.commit()

        assert (
            sync_once(
                engine,
                WebfleetSettings(account, "synthetic", "synthetic", "synthetic"),
                client_factory=Provider,
                now=now,
                stale_seconds=stale_seconds,
            )
            == "ok"
        )
        settings = Settings(database_url=url, webfleet_account=account, stale_seconds=stale_seconds)
        with TestClient(create_app(settings)) as client:
            response = client.post(
                "/api/v1/auth/login",
                headers=ORIGIN,
                json={
                    "username": username,
                    "password": password,
                },
            )
            assert response.status_code == 200
            path = f"/api/v1/analytics/rules/{manual_id}"
            assert client.patch(path, headers=ORIGIN, json={"active": True}).status_code == 200
            assert client.patch(path, headers=ORIGIN, json={"active": True}).status_code == 200

        with Session(engine) as session:
            actual = list(session.scalars(select(Alert.rule_id).where(Alert.rule_id.in_(rule_ids))))
            assert len(actual) == expected_total
            if expected_total:
                assert set(actual) == rule_ids
    finally:
        engine.dispose()
