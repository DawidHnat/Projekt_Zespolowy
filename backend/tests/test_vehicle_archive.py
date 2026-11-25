"""SCRUM-88: vehicle archiving, restoration, history preservation and WEBFLEET sync separation."""

import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import WebfleetSettings
from app.core.models import Driver, Measurement, SyncState, Vehicle
from app.core.settings import Settings
from app.main import create_app
from app.modules.analytics.models import Alert, DailyDistance, Rule
from app.modules.auth.models import User
from app.modules.auth.service import password_hasher
from app.modules.drivers.models import DriverAssignment
from app.modules.fleet.sync import account_key, apply_records, sync_once
from app.modules.trips.models import Trip, TripAnnotation

ORIGIN = {"Origin": "http://127.0.0.1:5173"}


def test_archive_restore_permissions_filters_and_assignment_handling(logged_in):
    app, client = logged_in
    now = datetime.now(UTC)
    source = account_key(app.state.settings.webfleet_account)

    with app.state.sessions() as session:
        editor_user = session.scalar(select(User).where(User.username == "test-user"))
        viewer_user = User(
            username="viewer-archive",
            display_name="Viewer testowy",
            role="viewer",
            password_hash=password_hasher.hash("synthetic-viewer-password"),
        )
        session.add_all([SyncState(source_account=source, last_success_at=now), viewer_user])
        driver = Driver(
            source_account=source,
            first_name="Anna",
            last_name="Kowalska",
            display_name="Anna Kowalska",
            identifier="DRV-ARCH-1",
            active=True,
        )
        session.add(driver)
        session.flush()
        active_car = Vehicle(
            source_account=source,
            external_uid="wf-active-1",
            name="Auto aktywne",
            license_plate="GD 100AA",
        )
        sold_car = Vehicle(
            source_account=source,
            external_uid="wf-sold-1",
            name="Auto sprzedane",
            license_plate="GD 200BB",
            driver_id=driver.id,
        )
        session.add_all([active_car, sold_car])
        session.flush()
        session.add_all(
            [
                Measurement(
                    vehicle_id=active_car.id,
                    latitude=54.35,
                    longitude=18.64,
                    gps_quality="A",
                    standing_still=True,
                    position_at=now,
                    received_at=now,
                    odometer_km=Decimal("10000.0"),
                ),
                Measurement(
                    vehicle_id=sold_car.id,
                    latitude=54.40,
                    longitude=18.55,
                    gps_quality="A",
                    standing_still=True,
                    position_at=now,
                    received_at=now,
                    odometer_km=Decimal("85000.0"),
                ),
                DriverAssignment(
                    driver_id=driver.id,
                    vehicle_id=sold_car.id,
                    active=True,
                    started_at=now - timedelta(days=10),
                    recorded_at=now - timedelta(days=10),
                ),
            ]
        )
        trip = Trip(
            vehicle_id=sold_car.id,
            external_uid="trip-sold-1",
            start_at=now - timedelta(hours=3),
            end_at=now - timedelta(hours=2),
            distance_km=Decimal("42.5"),
        )
        session.add(trip)
        session.flush()
        session.add(
            TripAnnotation(
                trip_id=trip.id,
                purpose="Dostawa",
                description="Ostatni kurs przed sprzedażą",
                version=2,
                updated_by=editor_user.id,
                updated_at=now - timedelta(hours=1),
            )
        )
        rule = Rule(source_account=source, threshold_km=Decimal("50.0"), vehicle_id=sold_car.id)
        session.add(rule)
        session.flush()
        session.add_all(
            [
                DailyDistance(
                    vehicle_id=sold_car.id,
                    event_day=now.date(),
                    distance_km=Decimal("75.0"),
                    first_observed_at=now - timedelta(hours=3),
                    last_observed_at=now - timedelta(minutes=5),
                ),
                Alert(
                    rule_id=rule.id,
                    vehicle_id=sold_car.id,
                    event_day=now.date(),
                    occurred_at=now - timedelta(minutes=5),
                    created_at=now - timedelta(minutes=5),
                    threshold_km=Decimal("50.0"),
                    distance_km=Decimal("75.0"),
                ),
            ]
        )
        sold_id, active_id, driver_id, trip_id = (
            str(sold_car.id),
            str(active_car.id),
            str(driver.id),
            str(trip.id),
        )
        session.commit()

    # Viewer cannot archive or restore, and untrusted Origin is rejected.
    bad_origin = client.post(
        f"/api/v1/fleet/vehicles/{sold_id}/archive",
        headers={"Origin": "https://evil.example"},
        json={"card_version": 1},
    )
    assert bad_origin.status_code == 403

    with app.state.sessions() as session:
        user = session.scalar(select(User).where(User.username == "test-user"))
        user.role = "viewer"
        session.commit()
    forbidden = client.post(
        f"/api/v1/fleet/vehicles/{sold_id}/archive",
        headers=ORIGIN,
        json={"card_version": 1, "reason": "Próba viewera"},
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "FORBIDDEN"
    with app.state.sessions() as session:
        user = session.scalar(select(User).where(User.username == "test-user"))
        user.role = "admin"
        session.commit()

    # Stale card_version returns 409 VERSION_CONFLICT.
    conflict = client.post(
        f"/api/v1/fleet/vehicles/{sold_id}/archive",
        headers=ORIGIN,
        json={"card_version": 99, "reason": "Błędna wersja"},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "VERSION_CONFLICT"

    # Editor archives the vehicle with optional reason.
    archived_resp = client.post(
        f"/api/v1/fleet/vehicles/{sold_id}/archive",
        headers=ORIGIN,
        json={"card_version": 1, "reason": "  Sprzedaż pojazdu po leasingu  "},
    )
    assert archived_resp.status_code == 200
    archived_body = archived_resp.json()
    assert archived_body["archived"] is True
    assert archived_body["card_version"] == 2
    assert archived_body["archive"]["reason"] == "Sprzedaż pojazdu po leasingu"
    assert archived_body["archive"]["archived_by"]["display_name"] == "Osoba testowa"
    assert archived_body["driver"] is None and archived_body["driver_count"] == 0

    # Double archive is rejected with 409 ALREADY_ARCHIVED.
    again = client.post(
        f"/api/v1/fleet/vehicles/{sold_id}/archive",
        headers=ORIGIN,
        json={"card_version": 2},
    )
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "ALREADY_ARCHIVED"

    # Default fleet views omit archived vehicles; archive filter exposes them.
    default_list = client.get("/api/v1/fleet/vehicles").json()
    assert [item["id"] for item in default_list["items"]] == [active_id]
    default_map = client.get("/api/v1/fleet/map").json()
    assert [f["properties"]["id"] for f in default_map["features"]] == [active_id]
    summary = client.get("/api/v1/fleet/summary").json()
    assert summary["total"] == 1

    only_archived = client.get("/api/v1/fleet/vehicles?archive=archived").json()
    assert [item["id"] for item in only_archived["items"]] == [sold_id]
    all_vehicles = client.get("/api/v1/fleet/vehicles?archive=all").json()
    assert {item["id"] for item in all_vehicles["items"]} == {active_id, sold_id}

    # Historical details, trips, annotations, alerts, and closed driver assignments remain intact.
    detail = client.get(f"/api/v1/fleet/vehicles/{sold_id}")
    assert detail.status_code == 200 and detail.json()["archived"] is True
    trips = client.get(
        "/api/v1/trips",
        params={
            "vehicle_id": sold_id,
            "from": (now - timedelta(days=1)).isoformat(),
            "to": now.isoformat(),
        },
    ).json()
    assert trips["total"] == 1 and trips["items"][0]["id"] == trip_id
    assert trips["items"][0]["annotation"]["purpose"] == "Dostawa"
    alerts = client.get("/api/v1/analytics/alerts").json()
    assert alerts["total"] == 1 and alerts["items"][0]["vehicle_id"] == sold_id

    assignments = client.get(f"/api/v1/drivers/{driver_id}/assignments").json()
    assert assignments["total"] == 1
    assert assignments["items"][0]["active"] is False
    assert assignments["items"][0]["ended_at"] is not None
    assert assignments["items"][0]["vehicle"]["archived"] is True

    # New regular driver assignment and new alert rule on archived vehicle are blocked.
    driver_detail = client.get(f"/api/v1/drivers/{driver_id}").json()
    blocked_assign = client.post(
        f"/api/v1/drivers/{driver_id}/assignments",
        headers=ORIGIN,
        json={"version": driver_detail["version"], "vehicle_id": sold_id},
    )
    assert blocked_assign.status_code == 409
    assert blocked_assign.json()["error"]["code"] == "VEHICLE_ARCHIVED"

    blocked_rule = client.post(
        "/api/v1/analytics/rules",
        headers=ORIGIN,
        json={"type": "daily_distance_threshold", "threshold_km": 100.0, "vehicle_id": sold_id},
    )
    assert blocked_rule.status_code == 409
    assert blocked_rule.json()["error"]["code"] == "VEHICLE_ARCHIVED"

    # WEBFLEET sync does not unarchive the vehicle or erase its history.
    with app.state.sessions() as session:
        apply_records(
            session,
            source,
            {
                "wf-active-1": {"objectname": "Auto aktywne", "licenseplatenumber": "GD 100AA"},
                "wf-sold-1": {"objectname": "Auto sprzedane", "licenseplatenumber": "GD 200BB"},
            },
            {},
            now + timedelta(minutes=2),
        )
        session.commit()
    still_archived = client.get(f"/api/v1/fleet/vehicles/{sold_id}").json()
    assert still_archived["archived"] is True
    assert client.get("/api/v1/fleet/vehicles").json()["total"] == 1

    # Restore clears archive state and brings vehicle back to active fleet.
    restored = client.post(
        f"/api/v1/fleet/vehicles/{sold_id}/restore",
        headers=ORIGIN,
        json={"card_version": still_archived["card_version"]},
    )
    assert restored.status_code == 200
    assert restored.json()["archived"] is False and restored.json()["archive"] is None
    assert client.get("/api/v1/fleet/vehicles").json()["total"] == 2


def test_postgres_archive_sync_restore_and_migration_downgrade_guard():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires an isolated PostgreSQL database")
    parsed = make_url(url)
    assert parsed.host in ("127.0.0.1", "localhost")
    assert parsed.database.startswith("fleet_flow_test")

    def migrate(*args):
        return subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            env={**os.environ, "DATABASE_URL": url, "SYNC_ENABLED": "false"},
            capture_output=True,
            text=True,
        )

    assert migrate("upgrade", "head").returncode == 0
    engine = create_engine(url)
    suffix = uuid4().hex
    account = f"archive-pg-{suffix}"
    webfleet = WebfleetSettings(account, "u", "p", "k")
    source = account_key(account)
    now = datetime.now(UTC).replace(microsecond=0)

    class FakeProvider:
        def __init__(self, _settings):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        async def fetch_vehicles(self):
            return [{"objectuid": "pg-arch-uid", "objectname": "Dostawczy PG"}]

        async def fetch_objects(self):
            return [
                {
                    "objectuid": "pg-arch-uid",
                    "pos_time": (now + timedelta(minutes=2)).isoformat(),
                    "status": "A",
                    "latitude_mdeg": 54350000,
                    "longitude_mdeg": 18640000,
                }
            ]

    try:
        assert sync_once(engine, webfleet, client_factory=FakeProvider, now=now) == "ok"
        with Session(engine) as session:
            user = User(
                username=f"arch-editor-{suffix}",
                display_name="Edytor PG",
                role="editor",
                password_hash=password_hasher.hash("synthetic-pg-password"),
            )
            session.add(user)
            session.commit()
            vehicle_id = session.scalar(
                select(Vehicle.id).where(
                    Vehicle.source_account == source, Vehicle.external_uid == "pg-arch-uid"
                )
            )

        app = create_app(Settings(database_url=url, webfleet_account=account), engine=engine)
        with TestClient(app) as client:
            login = client.post(
                "/api/v1/auth/login",
                headers=ORIGIN,
                json={"username": f"arch-editor-{suffix}", "password": "synthetic-pg-password"},
            )
            assert login.status_code == 200
            arch = client.post(
                f"/api/v1/fleet/vehicles/{vehicle_id}/archive",
                headers=ORIGIN,
                json={"card_version": 1, "reason": "Wycofany po kolizji"},
            )
            assert arch.status_code == 200 and arch.json()["archived"] is True

            # Downgrade to 0011 refuses silently dropping archived state.
            blocked_downgrade = migrate("downgrade", "0011_vehicle_card_ownership")
            assert blocked_downgrade.returncode != 0

            # Subsequent sync_once keeps vehicle archived while source remains healthy.
            assert (
                sync_once(
                    engine,
                    webfleet,
                    client_factory=FakeProvider,
                    now=now + timedelta(minutes=2),
                )
                == "ok"
            )
            assert client.get("/api/v1/fleet/vehicles").json()["total"] == 0
            assert client.get("/api/v1/fleet/vehicles?archive=archived").json()["total"] == 1

            rest = client.post(
                f"/api/v1/fleet/vehicles/{vehicle_id}/restore",
                headers=ORIGIN,
                json={"card_version": 2},
            )
            assert rest.status_code == 200 and rest.json()["archived"] is False
            assert client.get("/api/v1/fleet/vehicles").json()["total"] == 1
    finally:
        with Session(engine) as session:
            for v in session.scalars(select(Vehicle).where(Vehicle.source_account == source)):
                v.archived = False
                v.archived_at = None
                v.archived_by = None
                v.archived_reason = None
            session.commit()
        engine.dispose()
