"""SCRUM-85: manual vehicles without WEBFLEET locator, dated odometer, sync safety and linking."""

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
from app.modules.analytics.models import Alert, AlertReceipt, DailyDistance, Rule
from app.modules.auth.models import LoginSession, User
from app.modules.auth.service import password_hasher
from app.modules.fleet.sync import account_key, apply_records, sync_once

ORIGIN = {"Origin": "http://127.0.0.1:5173"}


def test_manual_vehicle_lifecycle_validation_conflicts_sync_and_explicit_link(logged_in):
    app, client = logged_in
    now = datetime.now(UTC)
    source = account_key(app.state.settings.webfleet_account)

    # Even before any WEBFLEET SyncState exists, creating a manual vehicle works and enables reads.
    with app.state.sessions() as session:
        driver = Driver(
            source_account=source,
            first_name="Marek",
            last_name="Nowak",
            display_name="Marek Nowak",
            identifier="DRV-MAN-1",
            active=True,
        )
        session.add(driver)
        session.commit()
        driver_id = str(driver.id)

    # Field-level validation on missing license_plate and mismatched manual odometer pair.
    invalid = client.post(
        "/api/v1/fleet/vehicles",
        headers=ORIGIN,
        json={"name": "", "license_plate": "", "manual_odometer_km": 100.0},
    )
    assert invalid.status_code == 422
    err = invalid.json()["error"]
    assert err["code"] == "VALIDATION_ERROR"
    assert {"name", "license_plate", "manual_odometer_date"} <= set(err["fields"])

    # Viewer cannot create manual vehicles.
    with app.state.sessions() as session:
        user = session.scalar(select(User).where(User.username == "test-user"))
        user.role = "viewer"
        session.commit()
    assert (
        client.post(
            "/api/v1/fleet/vehicles",
            headers=ORIGIN,
            json={"name": "Viewer Auto", "license_plate": "GD 999VV"},
        ).status_code
        == 403
    )
    with app.state.sessions() as session:
        user = session.scalar(select(User).where(User.username == "test-user"))
        user.role = "admin"
        session.commit()

    created_resp = client.post(
        "/api/v1/fleet/vehicles",
        headers=ORIGIN,
        json={
            "name": "Skoda Fabia Serwis",
            "license_plate": "GD 700XY",
            "make": "Skoda",
            "model": "Fabia",
            "year": 2024,
            "vin": "TMBJB7NJ000123456",
            "vehicle_type": "osobowy",
            "fuel_type": "benzyna",
            "leasing_company": "PKO Leasing",
            "leasing_contract_no": "LS/2024/700",
            "leasing_end_on": "2028-06-30",
            "inspection_due_on": "2027-06-15",
            "insurance_due_on": "2027-06-01",
            "manual_odometer_km": 18450.5,
            "manual_odometer_date": "2026-11-25",
            "driver_id": driver_id,
        },
    )
    assert created_resp.status_code == 201
    created = created_resp.json()
    manual_id = created["id"]
    assert created["origin"] == "manual"
    assert created["number"] is None
    assert created["latitude"] is None and created["longitude"] is None
    assert created["position_at"] is None and created["received_at"] is None
    assert created["speed_kmh"] is None and created["status"] == "unknown"
    assert created["odometer_km"] == 18450.5
    assert created["manual_odometer_km"] == 18450.5
    assert created["manual_odometer_date"] == "2026-11-25"
    assert created["driver"]["id"] == driver_id

    # Re-opening preserves card fields, dates, and manual odometer; map excludes GPS-less vehicle.
    reopened = client.get(f"/api/v1/fleet/vehicles/{manual_id}").json()
    assert reopened["leasing_company"] == "PKO Leasing"
    assert reopened["inspection_due_on"] == "2027-06-15"
    assert reopened["insurance_due_on"] == "2027-06-01"
    map_payload = client.get("/api/v1/fleet/map").json()
    assert map_payload["located"] == 0 and map_payload["total"] == 1

    # Duplicate plate or VIN returns 409 DUPLICATE_VEHICLE_IDENTITY with field-level errors.
    dup = client.post(
        "/api/v1/fleet/vehicles",
        headers=ORIGIN,
        json={"name": "Duplikat", "license_plate": "gd-700xy", "vin": "TMBJB7NJ000123456"},
    )
    assert dup.status_code == 409
    assert dup.json()["error"]["code"] == "DUPLICATE_VEHICLE_IDENTITY"
    assert {"license_plate", "vin"} <= set(dup.json()["error"]["fields"])

    # Dated manual odometer endpoint updates mileage cleanly.
    odo_updated = client.put(
        f"/api/v1/fleet/vehicles/{manual_id}/odometer",
        headers=ORIGIN,
        json={
            "card_version": reopened["card_version"],
            "odometer_km": 19100.0,
            "recorded_on": "2026-11-26",
        },
    )
    assert odo_updated.status_code == 200
    assert odo_updated.json()["odometer_km"] == 19100.0
    assert odo_updated.json()["manual_odometer_date"] == "2026-11-26"

    # WEBFLEET sync neither overwrites manual vehicle nor auto-merges when matching plate appears.
    with app.state.sessions() as session:
        session.add(SyncState(source_account=source, last_success_at=now))
        apply_records(
            session,
            source,
            {
                "wf-discovered-700": {
                    "objectname": "WEBFLEET Fabia",
                    "objectno": "WF-700",
                    "licenseplatenumber": "GD700XY",
                    "vehicletype": "van",
                }
            },
            {},
            now,
        )
        wf_car = session.scalar(
            select(Vehicle).where(
                Vehicle.source_account == source, Vehicle.external_uid == "wf-discovered-700"
            )
        )
        session.add(
            Measurement(
                vehicle_id=wf_car.id,
                latitude=54.352,
                longitude=18.646,
                gps_quality="A",
                standing_still=True,
                position_at=now,
                received_at=now,
                odometer_km=Decimal("19500.2"),
            )
        )
        wf_car_id = str(wf_car.id)
        session.commit()

    # Both records exist separately until explicitly linked; detail exposes link_candidates.
    fleet_both = client.get("/api/v1/fleet/vehicles").json()
    assert fleet_both["total"] == 2
    detail_with_candidate = client.get(f"/api/v1/fleet/vehicles/{manual_id}").json()
    assert detail_with_candidate["origin"] == "manual"
    assert [c["id"] for c in detail_with_candidate["link_candidates"]] == [wf_car_id]

    # Explicit linking keeps manual UUID, card fields, and driver while adopting telemetry.
    linked_resp = client.post(
        f"/api/v1/fleet/vehicles/{manual_id}/link-source",
        headers=ORIGIN,
        json={
            "card_version": detail_with_candidate["card_version"],
            "source_vehicle_id": wf_car_id,
        },
    )
    assert linked_resp.status_code == 200
    linked = linked_resp.json()
    assert linked["id"] == manual_id
    assert linked["origin"] == "webfleet"
    assert linked["number"] == "WF-700"
    assert linked["name"] == "Skoda Fabia Serwis"
    assert linked["leasing_company"] == "PKO Leasing"
    assert linked["driver"]["id"] == driver_id
    assert linked["latitude"] == 54.352 and linked["odometer_km"] == 19500.2
    assert client.get("/api/v1/fleet/vehicles").json()["total"] == 1


def test_postgres_manual_vehicle_sync_isolation_and_migration_downgrade_guard():
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
    account = f"manual-pg-{suffix}"
    webfleet = WebfleetSettings(account, "u", "p", "k")
    source = account_key(account)
    now = datetime.now(UTC).replace(microsecond=0)

    class EmptyProvider:
        def __init__(self, _settings):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        async def fetch_vehicles(self):
            return []

        async def fetch_objects(self):
            return []

    try:
        with Session(engine) as session:
            manual_car = Vehicle(
                source_account=source,
                external_uid=None,
                is_manual=True,
                name="Ręczny PG",
                license_plate="GDA 12345",
                manual_name=True,
                manual_license_plate=True,
                locally_edited=True,
            )
            session.add(manual_car)
            session.commit()
            manual_id = manual_car.id

        # Downgrade refuses discarding manual vehicles and warns against pre-SCRUM-85 rollback.
        blocked = migrate("downgrade", "0012_vehicle_archive")
        assert blocked.returncode != 0
        assert "INCOMPLETE_REPORT" in blocked.stderr
        assert "forward fix" in blocked.stderr

        # Empty WEBFLEET report does NOT fail with INCOMPLETE_REPORT or touch the manual vehicle.
        assert (
            sync_once(
                engine, webfleet, client_factory=EmptyProvider, now=now + timedelta(minutes=1)
            )
            == "ok"
        )
        with Session(engine) as session:
            reloaded = session.get(Vehicle, manual_id)
            assert reloaded is not None and reloaded.is_manual is True and reloaded.active is True
    finally:
        with Session(engine) as session:
            for v in session.scalars(select(Vehicle).where(Vehicle.source_account == source)):
                session.delete(v)
            state = session.get(SyncState, source)
            if state:
                session.delete(state)
            session.commit()
        engine.dispose()


def test_link_source_rejects_identity_mismatch_and_merges_alerts_by_event_day(logged_in):
    app, client = logged_in
    now = datetime.now(UTC).replace(microsecond=0)
    day_1 = (now - timedelta(days=2)).date()
    day_2 = (now - timedelta(days=1)).date()
    source = account_key(app.state.settings.webfleet_account)

    created = client.post(
        "/api/v1/fleet/vehicles",
        headers=ORIGIN,
        json={
            "name": "Ręczny Ford",
            "license_plate": "GD 800MM",
            "vin": "WF0XXXTTGX1111111",
        },
    )
    assert created.status_code == 201
    manual_id = created.json()["id"]

    with app.state.sessions() as session:
        editor_user = session.scalar(select(User).where(User.username == "test-user"))
        session.add(SyncState(source_account=source, last_success_at=now))
        unrelated_wf = Vehicle(
            source_account=source,
            external_uid="wf-unrelated-999",
            is_manual=False,
            name="Obcy WEBFLEET",
            license_plate="GD 999ZZ",
            vin="WF0XXXTTGX9999999",
            active=True,
        )
        conflicting_vin_wf = Vehicle(
            source_account=source,
            external_uid="wf-conflict-vin-800",
            is_manual=False,
            name="Sprzeczny VIN WEBFLEET",
            license_plate="GD800MM",
            vin="WF0XXXTTGX2222222",
            active=True,
        )
        matching_wf = Vehicle(
            source_account=source,
            external_uid="wf-match-800",
            is_manual=False,
            name="Zgodny WEBFLEET Ford",
            number="WF-800",
            license_plate="gd-800mm",
            vin=None,
            active=True,
        )
        session.add_all([unrelated_wf, conflicting_vin_wf, matching_wf])
        session.flush()

        manual_veh = session.scalar(
            select(Vehicle).where(Vehicle.source_account == source, Vehicle.is_manual.is_(True))
        )
        manual_uuid = manual_veh.id

        rule = Rule(source_account=source, threshold_km=Decimal("50.0"), vehicle_id=None)
        session.add(rule)
        session.flush()

        # Alert on day_1 already exists on manual vehicle (unread, distance 65 km).
        manual_alert_d1 = Alert(
            rule_id=rule.id,
            vehicle_id=manual_uuid,
            event_day=day_1,
            occurred_at=now - timedelta(days=2, hours=2),
            created_at=now - timedelta(days=2, hours=2),
            threshold_km=Decimal("50.0"),
            distance_km=Decimal("65.0"),
        )
        # Colliding alert on same (rule_id, day_1) on matching_wf WITH AlertReceipt and 120 km,
        # PLUS another alert on day_2 for the SAME rule_id on matching_wf!
        src_alert_d1 = Alert(
            rule_id=rule.id,
            vehicle_id=matching_wf.id,
            event_day=day_1,
            occurred_at=now - timedelta(days=2, hours=1),
            created_at=now - timedelta(days=2, hours=1),
            threshold_km=Decimal("50.0"),
            distance_km=Decimal("120.0"),
        )
        src_alert_d2 = Alert(
            rule_id=rule.id,
            vehicle_id=matching_wf.id,
            event_day=day_2,
            occurred_at=now - timedelta(days=1, hours=1),
            created_at=now - timedelta(days=1, hours=1),
            threshold_km=Decimal("50.0"),
            distance_km=Decimal("88.5"),
        )
        session.add_all([manual_alert_d1, src_alert_d1, src_alert_d2])
        session.flush()
        session.add(
            AlertReceipt(
                alert_id=src_alert_d1.id,
                user_id=editor_user.id,
                read_at=now - timedelta(days=2),
            )
        )
        session.add_all(
            [
                DailyDistance(
                    vehicle_id=manual_uuid,
                    event_day=day_1,
                    distance_km=Decimal("65.0"),
                    first_observed_at=now - timedelta(days=2, hours=3),
                    last_observed_at=now - timedelta(days=2, hours=2),
                ),
                DailyDistance(
                    vehicle_id=matching_wf.id,
                    event_day=day_1,
                    distance_km=Decimal("120.0"),
                    first_observed_at=now - timedelta(days=2, hours=4),
                    last_observed_at=now - timedelta(days=2, hours=1),
                ),
                DailyDistance(
                    vehicle_id=matching_wf.id,
                    event_day=day_2,
                    distance_km=Decimal("88.5"),
                    first_observed_at=now - timedelta(days=1, hours=3),
                    last_observed_at=now - timedelta(days=1, hours=1),
                ),
            ]
        )
        unrelated_id = str(unrelated_wf.id)
        conflicting_vin_id = str(conflicting_vin_wf.id)
        matching_id = str(matching_wf.id)
        session.commit()

    # Candidate list omits both unrelated and conflicting-VIN WEBFLEET vehicles.
    detail = client.get(f"/api/v1/fleet/vehicles/{manual_id}").json()
    assert [c["id"] for c in detail["link_candidates"]] == [matching_id]

    # Unrelated source vehicle is rejected with 409 IDENTITY_MISMATCH before any data changes.
    bad_unrelated = client.post(
        f"/api/v1/fleet/vehicles/{manual_id}/link-source",
        headers=ORIGIN,
        json={"card_version": detail["card_version"], "source_vehicle_id": unrelated_id},
    )
    assert bad_unrelated.status_code == 409
    assert bad_unrelated.json()["error"]["code"] == "IDENTITY_MISMATCH"

    # Conflicting non-null VIN on same plate is rejected with 409 IDENTITY_MISMATCH.
    bad_vin = client.post(
        f"/api/v1/fleet/vehicles/{manual_id}/link-source",
        headers=ORIGIN,
        json={"card_version": detail["card_version"], "source_vehicle_id": conflicting_vin_id},
    )
    assert bad_vin.status_code == 409
    assert bad_vin.json()["error"]["code"] == "IDENTITY_MISMATCH"

    # Both mismatched source vehicles and manual vehicle remain untouched.
    assert client.get(f"/api/v1/fleet/vehicles/{unrelated_id}").status_code == 200
    assert client.get(f"/api/v1/fleet/vehicles/{conflicting_vin_id}").status_code == 200
    assert client.get(f"/api/v1/fleet/vehicles/{manual_id}").json()["origin"] == "manual"

    # Matching source vehicle links cleanly, preserving alerts from BOTH days and AlertReceipt.
    ok_link = client.post(
        f"/api/v1/fleet/vehicles/{manual_id}/link-source",
        headers=ORIGIN,
        json={"card_version": detail["card_version"], "source_vehicle_id": matching_id},
    )
    assert ok_link.status_code == 200
    assert ok_link.json()["origin"] == "webfleet"
    assert ok_link.json()["vin"] == "WF0XXXTTGX1111111"

    alerts_payload = client.get("/api/v1/analytics/alerts").json()
    manual_alerts = [a for a in alerts_payload["items"] if a["vehicle_id"] == manual_id]
    by_day = {a["event_day"]: a for a in manual_alerts}
    assert set(by_day) == {day_1.isoformat(), day_2.isoformat()}
    assert by_day[day_1.isoformat()]["distance_km"] == 120.0
    assert by_day[day_1.isoformat()]["read_at"] is not None
    assert by_day[day_2.isoformat()]["distance_km"] == 88.5


def test_postgres_concurrent_manual_vehicle_duplicate_identity_returns_single_201_and_409():
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
    account = f"manual-race-{suffix}"
    source = account_key(account)
    username = f"manual-race-ed-{suffix}"

    try:
        with Session(engine) as session:
            session.add(
                User(
                    username=username,
                    display_name="Edytor Ręczny PG",
                    role="editor",
                    password_hash=password_hasher.hash("synthetic-manual-race-pass"),
                )
            )
            session.add(
                Vehicle(
                    source_account=source,
                    external_uid="wf-pair-555",
                    is_manual=False,
                    name="WEBFLEET Pair",
                    license_plate="GD 555WF",
                    active=True,
                )
            )
            session.commit()

        app = create_app(Settings(database_url=url, webfleet_account=account), engine=engine)
        with TestClient(app) as client_a, TestClient(app) as client_b:
            for cli in (client_a, client_b):
                res = cli.post(
                    "/api/v1/auth/login",
                    headers=ORIGIN,
                    json={"username": username, "password": "synthetic-manual-race-pass"},
                )
                assert res.status_code == 200

            # 1) Concurrent normalized plate race: "GD 700XY" vs "gd-700xy".
            plate_gate = threading.Barrier(2)

            def post_plate_a():
                plate_gate.wait(timeout=5)
                return client_a.post(
                    "/api/v1/fleet/vehicles",
                    headers=ORIGIN,
                    json={"name": "Auto A", "license_plate": "GD 700XY"},
                )

            def post_plate_b():
                plate_gate.wait(timeout=5)
                return client_b.post(
                    "/api/v1/fleet/vehicles",
                    headers=ORIGIN,
                    json={"name": "Auto B", "license_plate": "gd-700xy"},
                )

            with ThreadPoolExecutor(max_workers=2) as pool:
                fut_a = pool.submit(post_plate_a)
                fut_b = pool.submit(post_plate_b)
                r1, r2 = fut_a.result(10), fut_b.result(10)
            assert sorted([r1.status_code, r2.status_code]) == [201, 409]
            conflict_r = r1 if r1.status_code == 409 else r2
            assert conflict_r.json()["error"]["code"] == "DUPLICATE_VEHICLE_IDENTITY"

            # 2) Concurrent normalized VIN race with distinct plates.
            vin_gate = threading.Barrier(2)

            def post_vin_a():
                vin_gate.wait(timeout=5)
                return client_a.post(
                    "/api/v1/fleet/vehicles",
                    headers=ORIGIN,
                    json={
                        "name": "VIN A",
                        "license_plate": "GA 101AA",
                        "vin": "WVW-ZZZ-1JZ3W000111",
                    },
                )

            def post_vin_b():
                vin_gate.wait(timeout=5)
                return client_b.post(
                    "/api/v1/fleet/vehicles",
                    headers=ORIGIN,
                    json={
                        "name": "VIN B",
                        "license_plate": "GA 202BB",
                        "vin": "wvwzzz1jz3w000111",
                    },
                )

            with ThreadPoolExecutor(max_workers=2) as pool:
                fut_va = pool.submit(post_vin_a)
                fut_vb = pool.submit(post_vin_b)
                v1, v2 = fut_va.result(10), fut_vb.result(10)
            assert sorted([v1.status_code, v2.status_code]) == [201, 409]
            vin_conflict = v1 if v1.status_code == 409 else v2
            assert vin_conflict.json()["error"]["code"] == "DUPLICATE_VEHICLE_IDENTITY"

            # 3) Manual–WEBFLEET pair exception still works with allow_source_duplicate=True.
            pair_ok = client_a.post(
                "/api/v1/fleet/vehicles",
                headers=ORIGIN,
                json={
                    "name": "Ręczny odpowiednik WEBFLEET",
                    "license_plate": "gd-555wf",
                    "allow_source_duplicate": True,
                },
            )
            assert pair_ok.status_code == 201

            with Session(engine) as session:
                manual_rows = session.scalars(
                    select(Vehicle).where(
                        Vehicle.source_account == source, Vehicle.is_manual.is_(True)
                    )
                ).all()
                assert len(manual_rows) == 3
    finally:
        with Session(engine) as session:
            session.execute(delete(Vehicle).where(Vehicle.source_account == source))
            session.execute(delete(SyncState).where(SyncState.source_account == source))
            uid = session.scalar(select(User.id).where(User.username == username))
            if uid:
                session.execute(delete(LoginSession).where(LoginSession.user_id == uid))
                session.execute(delete(User).where(User.id == uid))
            session.commit()
        engine.dispose()


def test_postgres_active_manual_and_active_source_vehicle_forward_fix_sync_probe():
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

    engine = create_engine(url)
    suffix = uuid4().hex
    account = f"manual-probe-{suffix}"
    webfleet = WebfleetSettings(account, "u", "p", "k")
    source = account_key(account)
    now = datetime.now(UTC).replace(microsecond=0)

    class ProbeProvider:
        def __init__(self, _settings):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        async def fetch_vehicles(self):
            return [
                {
                    "objectuid": "wf-probe-active-1",
                    "objectname": "Renault Master WEBFLEET",
                    "licenseplatenumber": "GD 400WF",
                }
            ]

        async def fetch_objects(self):
            return [
                {
                    "objectuid": "wf-probe-active-1",
                    "pos_time": (now + timedelta(minutes=3)).isoformat(),
                    "status": "A",
                    "latitude_mdeg": 54361000,
                    "longitude_mdeg": 18652000,
                    "odometer": 102505,  # WEBFLEET reports 100 m units -> 10250.5 km
                }
            ]

    try:
        with Session(engine) as session:
            manual_car = Vehicle(
                source_account=source,
                external_uid=None,
                is_manual=True,
                name="Dacia Dokker Bez GPS",
                license_plate="GD 401MN",
                leasing_company="mLeasing",
                manual_odometer_km=Decimal("41200.0"),
                manual_odometer_date=now.date(),
                manual_name=True,
                manual_license_plate=True,
                locally_edited=True,
                active=True,
            )
            source_car = Vehicle(
                source_account=source,
                external_uid="wf-probe-active-1",
                is_manual=False,
                name="Renault Master WEBFLEET",
                license_plate="GD 400WF",
                active=True,
            )
            session.add_all([manual_car, source_car])
            session.flush()
            session.add(
                Measurement(
                    vehicle_id=source_car.id,
                    latitude=54.35,
                    longitude=18.64,
                    gps_quality="A",
                    standing_still=True,
                    position_at=now,
                    received_at=now,
                    odometer_km=Decimal("10000.0"),
                )
            )
            session.commit()
            manual_id, source_id = manual_car.id, source_car.id

        assert (
            sync_once(
                engine, webfleet, client_factory=ProbeProvider, now=now + timedelta(minutes=3)
            )
            == "ok"
        )

        with Session(engine) as session:
            refreshed_manual = session.get(Vehicle, manual_id)
            refreshed_source = session.get(Vehicle, source_id)
            refreshed_meas = session.get(Measurement, source_id)
            sync_state = session.get(SyncState, source)

            assert refreshed_manual is not None
            assert refreshed_manual.is_manual is True
            assert refreshed_manual.active is True
            assert refreshed_manual.external_uid is None
            assert refreshed_manual.leasing_company == "mLeasing"
            assert refreshed_manual.manual_odometer_km == Decimal("41200.0")

            assert refreshed_source is not None and refreshed_source.active is True
            assert refreshed_meas is not None
            assert refreshed_meas.latitude == pytest.approx(54.361)
            assert refreshed_meas.odometer_km == Decimal("10250.5")
            assert sync_state is not None and sync_state.error_code is None
    finally:
        with Session(engine) as session:
            session.execute(delete(DailyDistance).where(DailyDistance.vehicle_id == source_id))
            session.execute(delete(Measurement).where(Measurement.vehicle_id == source_id))
            session.execute(delete(Vehicle).where(Vehicle.source_account == source))
            session.execute(delete(SyncState).where(SyncState.source_account == source))
            session.commit()
        engine.dispose()
