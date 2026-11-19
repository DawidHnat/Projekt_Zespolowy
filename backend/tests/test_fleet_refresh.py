import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from threading import Event
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import WebfleetSettings
from app.core.models import Base, SyncState
from app.core.settings import Settings
from app.integrations.webfleet.client import WebfleetError
from app.main import create_app
from app.modules.auth.models import User
from app.modules.auth.service import password_hasher
from app.modules.fleet import refresh as refresh_module
from app.modules.fleet.sync import account_key, sync_once

PATH = "/api/v1/fleet/refresh"
ORIGIN = {"Origin": "http://127.0.0.1:5173"}


@pytest.fixture
def refresh_clients(monkeypatch):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires an isolated local PostgreSQL test database")
    parsed = make_url(url)
    assert parsed.database.startswith("fleet_flow_test")
    assert parsed.host in ("127.0.0.1", "localhost")
    schema = "refresh_" + uuid4().hex
    engine = create_engine(url, execution_options={"schema_translate_map": {None: schema}})
    with engine.begin() as connection:
        connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
    Base.metadata.create_all(engine)
    webfleet = WebfleetSettings("synthetic-" + uuid4().hex, "test", "test", "test")
    settings = Settings(url, webfleet_account=webfleet.account)
    app = create_app(settings, engine=engine)
    fixture = SimpleNamespace(calls=[], hold=None, started=Event(), error=None, speed=65)

    class FakeClient:
        def __init__(self, _):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        async def fetch_vehicles(self):
            fixture.calls.append("vehicles")
            if fixture.hold:
                fixture.started.set()
                await asyncio.to_thread(fixture.hold.wait, 5)
            if fixture.error:
                raise fixture.error
            return [{"objectuid": "synthetic-vehicle", "objectname": "Test odświeżenia"}]

        async def fetch_objects(self):
            fixture.calls.append("objects")
            return [
                {
                    "objectuid": "synthetic-vehicle",
                    "latitude_mdeg": 0,
                    "longitude_mdeg": 0,
                    "status": "A",
                    "standstill": "0",
                    "speed": fixture.speed,
                    "pos_time": datetime.now(UTC).isoformat(),
                }
            ]

    monkeypatch.setattr(refresh_module, "WebfleetClient", FakeClient)
    fixture.factory = FakeClient
    fixture.engine, fixture.webfleet, fixture.app = engine, webfleet, app
    with Session(engine) as session:
        session.add(
            User(
                username="refresh-user",
                display_name="Test",
                role="viewer",
                password_hash=password_hasher.hash("synthetic-refresh-password"),
            )
        )
        session.commit()
    try:
        # No background worker or dotenv credentials: only the fake manual source is enabled.
        with TestClient(app) as first, TestClient(app) as second:
            app.state.settings = replace(settings, sync_enabled=True)
            app.state.webfleet_settings = webfleet
            for client in (first, second):
                response = client.post(
                    "/api/v1/auth/login",
                    headers=ORIGIN,
                    json={"username": "refresh-user", "password": "synthetic-refresh-password"},
                )
                assert response.status_code == 200
            fixture.first, fixture.second = first, second
            yield fixture
    finally:
        if fixture.hold:
            fixture.hold.set()
        with engine.begin() as connection:
            connection.exec_driver_sql(f'DROP SCHEMA "{schema}" CASCADE')
        engine.dispose()


def test_refresh_requires_session(application):
    _, anonymous = application
    assert anonymous.get(PATH).status_code == 401
    assert anonymous.post(PATH, headers=ORIGIN).status_code == 401


def test_refresh_requires_origin_and_enabled_source(logged_in, monkeypatch):
    app, client = logged_in
    assert client.post(PATH).status_code == 403
    assert client.post(PATH, headers={"Origin": "https://wrong.example"}).status_code == 403
    monkeypatch.setattr(
        refresh_module, "sync_once", lambda *_args, **_kwargs: pytest.fail("disabled source read")
    )
    assert client.get(PATH).json()["enabled"] is False
    assert client.post(PATH, headers=ORIGIN).json()["result"] == "disabled"
    assert app.state.settings.sync_enabled is False


def test_manual_refresh_and_worker_share_one_account_cooldown(refresh_clients):
    f = refresh_clients
    assert f.first.get(PATH).json()["retry_after_seconds"] == 0
    assert f.first.get("/api/v1/fleet/vehicles").status_code == 503  # cold cache
    result = f.first.post(PATH, headers=ORIGIN).json()
    assert result["result"] == "updated"
    assert 0 < result["retry_after_seconds"] <= 60
    assert f.calls == ["vehicles", "objects"]
    peer = f.second.get(PATH).json()
    assert peer["next_allowed_at"] == result["next_allowed_at"]
    assert f.second.post(PATH, headers=ORIGIN).json()["result"] == "cooldown"
    assert sync_once(f.engine, f.webfleet, client_factory=f.factory) == "rate_limited"
    assert f.calls == ["vehicles", "objects"]
    item = f.first.get("/api/v1/fleet/vehicles").json()["items"][0]
    assert item["speed_kmh"] == 65
    with Session(f.engine) as session:
        state = session.get(SyncState, account_key(f.webfleet.account))
        state.last_attempt_at = datetime.now(UTC) - timedelta(seconds=61)
        session.commit()
    f.speed = 90
    assert f.second.post(PATH, headers=ORIGIN).json()["result"] == "updated"
    assert f.first.get("/api/v1/fleet/vehicles").json()["items"][0]["speed_kmh"] == 90
    assert f.calls == ["vehicles", "objects", "vehicles", "objects"]


def test_concurrent_browser_refresh_is_busy_without_duplicate_provider_calls(refresh_clients):
    f = refresh_clients
    f.hold = Event()
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(f.first.post, PATH, headers=ORIGIN)
        assert f.started.wait(3)
        try:
            assert f.second.get(PATH).json()["running"] is True
            assert f.second.post(PATH, headers=ORIGIN).json()["result"] == "busy"
            assert f.calls == ["vehicles"]
        finally:
            f.hold.set()
        assert pending.result(timeout=5).json()["result"] == "updated"
    assert f.second.get(PATH).json()["running"] is False
    assert f.calls == ["vehicles", "objects"]


def test_provider_backoff_is_shared_and_last_cache_is_preserved(refresh_clients):
    f = refresh_clients
    assert f.first.post(PATH, headers=ORIGIN).json()["result"] == "updated"
    with Session(f.engine) as session:
        state = session.get(SyncState, account_key(f.webfleet.account))
        state.last_attempt_at = datetime.now(UTC) - timedelta(seconds=61)
        session.commit()
    f.error = WebfleetError("provider_rate_limit", retry_after_seconds=1200)
    failed = f.first.post(PATH, headers=ORIGIN).json()
    assert failed["result"] == "failed"
    assert 1190 <= failed["retry_after_seconds"] <= 1200
    assert f.second.post(PATH, headers=ORIGIN).json()["result"] == "cooldown"
    assert f.calls == ["vehicles", "objects", "vehicles"]
    cache = f.second.get("/api/v1/fleet/vehicles").json()
    assert cache["total"] == 1
    assert cache["source"]["status"] == "degraded"
    assert cache["items"][0]["speed_kmh"] is None
    assert "synthetic-" not in str(failed)


def test_unexpected_source_error_is_sanitized_and_consumes_the_interval(refresh_clients):
    f = refresh_clients
    f.error = RuntimeError("synthetic-private-detail")
    response = f.first.post(PATH, headers=ORIGIN)
    assert response.status_code == 503
    assert "synthetic-private-detail" not in response.text
    assert f.second.post(PATH, headers=ORIGIN).json()["result"] == "cooldown"
    assert f.calls == ["vehicles"]
