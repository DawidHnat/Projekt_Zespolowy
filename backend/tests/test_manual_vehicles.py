"""SCRUM-85: manual vehicles without WEBFLEET locator, dated odometer, sync safety and linking."""

import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import WebfleetSettings
from app.core.models import Driver, Measurement, SyncState, Vehicle
from app.modules.auth.models import User
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

        # Downgrade refuses silently discarding manual vehicles.
        blocked = migrate("downgrade", "0012_vehicle_archive")
        assert blocked.returncode != 0

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
