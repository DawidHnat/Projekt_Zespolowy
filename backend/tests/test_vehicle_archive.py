"""SCRUM-88: vehicle archiving, restoration, history preservation and WEBFLEET sync separation."""

import os
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import WebfleetSettings
from app.core.models import Driver, Measurement, SyncState, Vehicle
from app.core.settings import Settings
from app.main import create_app
from app.modules.analytics.models import Alert, DailyDistance, Rule
from app.modules.auth.models import LoginSession, User
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
    assert restored.json()["source_active"] is True
    assert client.get("/api/v1/fleet/vehicles").json()["total"] == 2


def test_restore_source_inactive_vehicle_keeps_detail_and_all_filter_accessible(logged_in):
    app, client = logged_in
    now = datetime.now(UTC)
    source = account_key(app.state.settings.webfleet_account)

    with app.state.sessions() as session:
        session.add(SyncState(source_account=source, last_success_at=now))
        keep_a = Vehicle(
            source_account=source,
            external_uid="wf-keep-a",
            name="Aktywny A",
            license_plate="GD 101AA",
        )
        keep_b = Vehicle(
            source_account=source,
            external_uid="wf-keep-b",
            name="Aktywny B",
            license_plate="GD 102BB",
        )
        deactivated = Vehicle(
            source_account=source,
            external_uid="wf-gone-1",
            name="Wycofany ze źródła",
            license_plate="GD 909ZZ",
        )
        session.add_all([keep_a, keep_b, deactivated])
        session.flush()
        trip = Trip(
            vehicle_id=deactivated.id,
            external_uid="trip-gone-1",
            start_at=now - timedelta(hours=4),
            end_at=now - timedelta(hours=3),
            distance_km=Decimal("18.4"),
        )
        session.add(trip)
        deactivated_id = str(deactivated.id)
        session.commit()

    archived = client.post(
        f"/api/v1/fleet/vehicles/{deactivated_id}/archive",
        headers=ORIGIN,
        json={"card_version": 1, "reason": "Zakończona umowa"},
    )
    assert archived.status_code == 200
    assert archived.json()["archived"] is True
    assert archived.json()["source_active"] is True

    # Source record becomes inactive in DB and subsequent sync without wf-gone-1 keeps active=False.
    with app.state.sessions() as session:
        session.scalar(select(Vehicle).where(Vehicle.external_uid == "wf-gone-1")).active = False
        apply_records(
            session,
            source,
            {
                "wf-keep-a": {"objectname": "Aktywny A", "licenseplatenumber": "GD 101AA"},
                "wf-keep-b": {"objectname": "Aktywny B", "licenseplatenumber": "GD 102BB"},
            },
            {},
            now + timedelta(minutes=5),
        )
        session.commit()

    archived_inactive = client.get(f"/api/v1/fleet/vehicles/{deactivated_id}")
    assert archived_inactive.status_code == 200
    assert archived_inactive.json()["archived"] is True
    assert archived_inactive.json()["source_active"] is False

    # Restore clears archived without faking WEBFLEET source presence; card remains reachable.
    restored = client.post(
        f"/api/v1/fleet/vehicles/{deactivated_id}/restore",
        headers=ORIGIN,
        json={"card_version": archived_inactive.json()["card_version"]},
    )
    assert restored.status_code == 200
    assert restored.json()["archived"] is False
    assert restored.json()["source_active"] is False

    detail_after = client.get(f"/api/v1/fleet/vehicles/{deactivated_id}")
    assert detail_after.status_code == 200
    assert detail_after.json()["archived"] is False
    assert detail_after.json()["source_active"] is False

    patched = client.patch(
        f"/api/v1/fleet/vehicles/{deactivated_id}",
        headers=ORIGIN,
        json={"card_version": detail_after.json()["card_version"], "make": "Ford"},
    )
    assert patched.status_code == 200
    assert patched.json()["make"] == "Ford"
    assert patched.json()["source_active"] is False

    # Hidden from active WEBFLEET fleet and archive-only filter, but exposed under archive=all.
    active_ids = {item["id"] for item in client.get("/api/v1/fleet/vehicles").json()["items"]}
    assert deactivated_id not in active_ids
    archived_ids = {
        item["id"] for item in client.get("/api/v1/fleet/vehicles?archive=archived").json()["items"]
    }
    assert deactivated_id not in archived_ids
    all_items = {
        item["id"]: item
        for item in client.get("/api/v1/fleet/vehicles?archive=all").json()["items"]
    }
    assert deactivated_id in all_items
    assert all_items[deactivated_id]["source_active"] is False
    assert all_items[deactivated_id]["archived"] is False

    trips = client.get(
        "/api/v1/trips",
        params={
            "vehicle_id": deactivated_id,
            "from": (now - timedelta(days=1)).isoformat(),
            "to": now.isoformat(),
        },
    ).json()
    assert trips["total"] == 1


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
    username = f"arch-editor-{suffix}"
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
            veh_ids = session.scalars(
                select(Vehicle.id).where(Vehicle.source_account == source)
            ).all()
            if veh_ids:
                session.execute(
                    delete(DriverAssignment).where(DriverAssignment.vehicle_id.in_(veh_ids))
                )
                session.execute(delete(Measurement).where(Measurement.vehicle_id.in_(veh_ids)))
            session.execute(delete(Vehicle).where(Vehicle.source_account == source))
            session.execute(delete(Driver).where(Driver.source_account == source))
            session.execute(delete(SyncState).where(SyncState.source_account == source))
            test_user_id = session.scalar(select(User.id).where(User.username == username))
            if test_user_id:
                session.execute(delete(LoginSession).where(LoginSession.user_id == test_user_id))
                session.execute(delete(User).where(User.id == test_user_id))
            session.commit()
        engine.dispose()


def test_postgres_concurrent_archive_with_driver_assign_and_close():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires an isolated PostgreSQL database")
    parsed = make_url(url)
    assert parsed.host in ("127.0.0.1", "localhost")
    assert parsed.database.startswith("fleet_flow_test")

    migrate = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        env={**os.environ, "DATABASE_URL": url, "SYNC_ENABLED": "false"},
        capture_output=True,
        text=True,
    )
    assert migrate.returncode == 0, migrate.stderr

    engine = create_engine(url, pool_size=8, max_overflow=8)
    suffix = uuid4().hex
    account = f"archive-race-{suffix}"
    source = account_key(account)
    username = f"race-editor-{suffix}"
    now = datetime.now(UTC).replace(microsecond=0)

    try:
        with Session(engine) as session:
            session.add(
                User(
                    username=username,
                    display_name="Edytor współbieżny",
                    role="editor",
                    password_hash=password_hasher.hash("synthetic-race-password"),
                )
            )
            session.add(SyncState(source_account=source, last_success_at=now))
            session.commit()

        app = create_app(Settings(database_url=url, webfleet_account=account), engine=engine)
        with TestClient(app) as client_a, TestClient(app) as client_b:
            for cli in (client_a, client_b):
                res = cli.post(
                    "/api/v1/auth/login",
                    headers=ORIGIN,
                    json={"username": username, "password": "synthetic-race-password"},
                )
                assert res.status_code == 200

            # 1) Archive concurrently with POST /drivers/{id}/assignments across two DB sessions.
            for idx in range(5):
                with Session(engine) as session:
                    drv = Driver(
                        source_account=source,
                        first_name="Jan",
                        last_name=f"Assign{idx}",
                        display_name=f"Jan Assign{idx}",
                        identifier=f"RACE-A-{idx}-{suffix[:6]}",
                        active=True,
                    )
                    veh = Vehicle(
                        source_account=source,
                        external_uid=f"wf-race-a-{idx}",
                        name=f"Pojazd A{idx}",
                        license_plate=f"GDA{idx}00",
                    )
                    session.add_all([drv, veh])
                    session.commit()
                    drv_id, veh_id = str(drv.id), str(veh.id)
                    veh_uuid, drv_uuid = veh.id, drv.id

                barrier = threading.Barrier(2)

                def do_archive(vid=veh_id, gate=barrier):
                    gate.wait(timeout=5)
                    return client_a.post(
                        f"/api/v1/fleet/vehicles/{vid}/archive",
                        headers=ORIGIN,
                        json={"card_version": 1, "reason": "Test współbieżny assign"},
                    )

                def do_assign(did=drv_id, vid=veh_id, gate=barrier):
                    gate.wait(timeout=5)
                    return client_b.post(
                        f"/api/v1/drivers/{did}/assignments",
                        headers=ORIGIN,
                        json={"version": 1, "vehicle_id": vid},
                    )

                with ThreadPoolExecutor(max_workers=2) as pool:
                    fut_arch = pool.submit(do_archive)
                    fut_assign = pool.submit(do_assign)
                    arch_res = fut_arch.result(timeout=10)
                    assign_res = fut_assign.result(timeout=10)

                assert arch_res.status_code == 200, arch_res.text
                assert assign_res.status_code in (201, 409), assign_res.text
                if assign_res.status_code == 409:
                    assert assign_res.json()["error"]["code"] == "VEHICLE_ARCHIVED"

                with Session(engine) as session:
                    refreshed_veh = session.get(Vehicle, veh_uuid)
                    refreshed_drv = session.get(Driver, drv_uuid)
                    rows = session.scalars(
                        select(DriverAssignment).where(DriverAssignment.vehicle_id == veh_uuid)
                    ).all()
                    assert refreshed_veh.archived is True
                    assert refreshed_veh.driver_id is None
                    assert all(not r.active and r.ended_at is not None for r in rows)
                    if assign_res.status_code == 201:
                        assert len(rows) == 1
                        assert refreshed_drv.version == 3
                    else:
                        assert len(rows) == 0
                        assert refreshed_drv.version == 1

            # 2) Archive concurrently with PATCH /drivers/{id}/assignments/{aid}/close.
            for idx in range(5):
                with Session(engine) as session:
                    drv = Driver(
                        source_account=source,
                        first_name="Ewa",
                        last_name=f"Close{idx}",
                        display_name=f"Ewa Close{idx}",
                        identifier=f"RACE-C-{idx}-{suffix[:6]}",
                        active=True,
                    )
                    session.add(drv)
                    session.flush()
                    veh = Vehicle(
                        source_account=source,
                        external_uid=f"wf-race-c-{idx}",
                        name=f"Pojazd C{idx}",
                        license_plate=f"GDC{idx}00",
                        driver_id=drv.id,
                    )
                    session.add(veh)
                    session.flush()
                    asgn = DriverAssignment(
                        driver_id=drv.id,
                        vehicle_id=veh.id,
                        active=True,
                        started_at=now - timedelta(days=1),
                        recorded_at=now - timedelta(days=1),
                    )
                    session.add(asgn)
                    session.commit()
                    drv_id, veh_id, asgn_id = str(drv.id), str(veh.id), str(asgn.id)
                    veh_uuid, drv_uuid = veh.id, drv.id

                barrier = threading.Barrier(2)

                def do_archive_c(vid=veh_id, gate=barrier):
                    gate.wait(timeout=5)
                    return client_a.post(
                        f"/api/v1/fleet/vehicles/{vid}/archive",
                        headers=ORIGIN,
                        json={"card_version": 1, "reason": "Test współbieżny close"},
                    )

                def do_close_c(did=drv_id, aid=asgn_id, gate=barrier):
                    gate.wait(timeout=5)
                    return client_b.patch(
                        f"/api/v1/drivers/{did}/assignments/{aid}/close",
                        headers=ORIGIN,
                        json={"version": 1},
                    )

                with ThreadPoolExecutor(max_workers=2) as pool:
                    fut_arch = pool.submit(do_archive_c)
                    fut_close = pool.submit(do_close_c)
                    arch_res = fut_arch.result(timeout=10)
                    close_res = fut_close.result(timeout=10)

                assert arch_res.status_code == 200, arch_res.text
                assert close_res.status_code in (200, 409), close_res.text
                if close_res.status_code == 409:
                    assert close_res.json()["error"]["code"] == "CONFLICT"

                with Session(engine) as session:
                    refreshed_veh = session.get(Vehicle, veh_uuid)
                    refreshed_drv = session.get(Driver, drv_uuid)
                    rows = session.scalars(
                        select(DriverAssignment).where(DriverAssignment.vehicle_id == veh_uuid)
                    ).all()
                    assert refreshed_veh.archived is True
                    assert refreshed_veh.driver_id is None
                    assert len(rows) == 1
                    assert rows[0].active is False and rows[0].ended_at is not None
                    assert refreshed_drv.version == 2
    finally:
        with Session(engine) as session:
            veh_ids = session.scalars(
                select(Vehicle.id).where(Vehicle.source_account == source)
            ).all()
            if veh_ids:
                session.execute(
                    delete(DriverAssignment).where(DriverAssignment.vehicle_id.in_(veh_ids))
                )
                session.execute(delete(Measurement).where(Measurement.vehicle_id.in_(veh_ids)))
            session.execute(delete(Vehicle).where(Vehicle.source_account == source))
            session.execute(delete(Driver).where(Driver.source_account == source))
            session.execute(delete(SyncState).where(SyncState.source_account == source))
            test_user_id = session.scalar(select(User.id).where(User.username == username))
            if test_user_id:
                session.execute(delete(LoginSession).where(LoginSession.user_id == test_user_id))
                session.execute(delete(User).where(User.id == test_user_id))
            session.commit()
        engine.dispose()
