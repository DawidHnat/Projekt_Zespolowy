"""SCRUM-68: full vehicle card on the shared SCRUM-85/SCRUM-70 fields (synthetic data only)."""

import os
import subprocess
import sys
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

from app.core.models import SyncState
from app.modules.fleet.sync import account_key, apply_records

ORIGIN = {"Origin": "http://127.0.0.1:5173"}
FULL_CARD = {
    "ownership_category": "Leasing",
    "leasing_company": "Syntetyczny Leasing",
    "leasing_end_on": "2028-06-30",
    "leasing_buyout_on": "2028-07-15",
    "first_registration_on": "2023-02-10",
    "first_registration_pl_on": "2023-03-01",
    "fuel_type": "diesel",
    "engine_capacity_cc": 1997,
    "power_kw": 110,
    "gross_weight_kg": 3500,
    "curb_weight_kg": 2200,
    "payload_kg": 1300,
    "passenger_seats": 2,
    "axles": 2,
}


def create_vehicle(client, **extra):
    response = client.post(
        "/api/v1/fleet/vehicles",
        headers=ORIGIN,
        json={"name": "Furgon testowy", "license_plate": "SYN 6801", **extra},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_full_card_round_trip_uses_shared_dmc_and_seats(logged_in):
    _, client = logged_in
    created = create_vehicle(client, **FULL_CARD)
    reopened = client.get(f"/api/v1/fleet/vehicles/{created['id']}").json()
    for field, value in FULL_CARD.items():
        assert reopened[field] == value, field
    # DMC and seats are the SCRUM-70 fields, so the licence check sees the card value.
    assert reopened["license_requirement"]["status"] == "determined"
    assert "dmc_kg" not in reopened and "seats" not in reopened

    # Missing values stay missing rather than becoming zero.
    empty = create_vehicle(client, license_plate="SYN 6802")
    for field in ("ownership_category", "power_kw", "curb_weight_kg", "axles"):
        assert empty[field] is None


def test_category_change_keeps_leasing_history(logged_in):
    _, client = logged_in
    vehicle = create_vehicle(client, **FULL_CARD)
    path = f"/api/v1/fleet/vehicles/{vehicle['id']}"
    changed = client.patch(
        path,
        headers=ORIGIN,
        json={"card_version": vehicle["card_version"], "ownership_category": "Firmowe"},
    )
    assert changed.status_code == 200
    body = changed.json()
    assert body["ownership_category"] == "Firmowe"
    assert body["leasing_buyout_on"] == "2028-07-15"
    assert body["leasing_company"] == "Syntetyczny Leasing"

    stale = client.patch(
        path, headers=ORIGIN, json={"card_version": vehicle["card_version"], "axles": 3}
    )
    assert stale.status_code == 409
    assert client.get(path).json()["axles"] == 2


@pytest.mark.parametrize(
    "change",
    [
        {"ownership_category": "Leased"},
        {"power_kw": 0},
        {"curb_weight_kg": "2000"},
        {"axles": 21},
        {"engine_capacity_cc": -1},
        {"payload_kg": 1.5},
    ],
)
def test_invalid_units_are_rejected(logged_in, change):
    _, client = logged_in
    vehicle = create_vehicle(client)
    response = client.patch(
        f"/api/v1/fleet/vehicles/{vehicle['id']}",
        headers=ORIGIN,
        json={"card_version": vehicle["card_version"], **change},
    )
    assert response.status_code == 422


def test_cross_field_rules_use_stored_and_changed_values(logged_in):
    _, client = logged_in
    invalid_create = client.post(
        "/api/v1/fleet/vehicles",
        headers=ORIGIN,
        json={
            "name": "Niespójny",
            "license_plate": "SYN 6803",
            "gross_weight_kg": 2000,
            "curb_weight_kg": 2500,
            "first_registration_on": "2024-05-01",
            "first_registration_pl_on": "2024-04-01",
        },
    )
    assert invalid_create.status_code == 422
    assert {"curb_weight_kg", "first_registration_pl_on"} <= set(
        invalid_create.json()["error"]["fields"]
    )

    vehicle = create_vehicle(client, **FULL_CARD)
    path = f"/api/v1/fleet/vehicles/{vehicle['id']}"
    # Lowering DMC below the stored payload is rejected and nothing is written.
    lowered = client.patch(
        path,
        headers=ORIGIN,
        json={"card_version": vehicle["card_version"], "gross_weight_kg": 1000},
    )
    assert lowered.status_code == 422
    assert set(lowered.json()["error"]["fields"]) == {"curb_weight_kg", "payload_kg"}
    current = client.get(path).json()
    assert current["gross_weight_kg"] == 3500
    assert current["card_version"] == vehicle["card_version"]


def test_webfleet_sync_does_not_overwrite_card_fields(logged_in):
    app, client = logged_in
    now = datetime.now(UTC)
    source = account_key(app.state.settings.webfleet_account)
    master = {"objectname": "WEBFLEET Furgon", "objectno": "WF-68", "vehicletype": "van"}
    with app.state.sessions() as session:
        session.add(SyncState(source_account=source, last_success_at=now))
        apply_records(session, source, {"wf-68": master}, {}, now)
        session.commit()
    listed = client.get("/api/v1/fleet/vehicles").json()["items"]
    vehicle = next(item for item in listed if item["number"] == "WF-68")
    path = f"/api/v1/fleet/vehicles/{vehicle['id']}"
    saved = client.patch(
        path,
        headers=ORIGIN,
        json={
            "card_version": vehicle["card_version"],
            "ownership_category": "Prywatne",
            "axles": 2,
        },
    )
    assert saved.status_code == 200

    with app.state.sessions() as session:
        apply_records(session, source, {"wf-68": master}, {}, now)
        session.commit()
    after = client.get(path).json()
    assert after["ownership_category"] == "Prywatne"
    assert after["axles"] == 2


def test_migration_0016_blocks_lossy_downgrade_on_postgres():
    db_url = os.environ.get("TEST_DATABASE_URL")
    if not db_url or not db_url.startswith("postgresql"):
        pytest.skip("PostgreSQL migration check")
    assert make_url(db_url).database.startswith("fleet_flow_test")
    environment = {**os.environ, "DATABASE_URL": db_url, "SYNC_ENABLED": "false"}
    vehicle_id = "68686868-6868-4868-8868-686868686868"

    def run_alembic(*args):
        return subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            env=environment,
            capture_output=True,
            text=True,
        )

    def delete_vehicle():
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM vehicles WHERE id = :id"), {"id": vehicle_id})

    engine = create_engine(db_url)
    assert run_alembic("downgrade", "base").returncode == 0
    assert run_alembic("upgrade", "head").returncode == 0
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO vehicles (id, source_account, is_manual, name, active, archived, "
                    "locally_edited, manual_name, manual_license_plate, manual_vehicle_type, "
                    "card_version, photo_version, tows_heavy_trailer, ownership_category) "
                    "VALUES (:id, 'syn', true, 'Kartoteka', true, false, true, true, true, "
                    "false, 1, 0, false, 'Leasing')"
                ),
                {"id": vehicle_id},
            )
        # An unknown category is rejected by the database constraint, not only by the API.
        with pytest.raises(IntegrityError):
            with engine.begin() as conn:
                conn.execute(
                    text("UPDATE vehicles SET ownership_category = 'Leased' WHERE id = :id"),
                    {"id": vehicle_id},
                )
        failed = run_alembic("downgrade", "0015_license_compatibility")
        assert failed.returncode != 0
        assert "SCRUM-68" in (failed.stderr + failed.stdout)
        delete_vehicle()
        assert run_alembic("downgrade", "0015_license_compatibility").returncode == 0
        assert run_alembic("upgrade", "head").returncode == 0
    finally:
        delete_vehicle()
        run_alembic("downgrade", "base")
        run_alembic("upgrade", "head")
        engine.dispose()


def test_migration_0016_downgrade_waits_for_a_concurrent_card_write():
    db_url = os.environ.get("TEST_DATABASE_URL")
    if not db_url or not db_url.startswith("postgresql"):
        pytest.skip("PostgreSQL migration check")
    assert make_url(db_url).database.startswith("fleet_flow_test")
    environment = {**os.environ, "DATABASE_URL": db_url, "SYNC_ENABLED": "false"}
    vehicle_id = "68686868-6868-4868-8868-686868686869"

    def run_alembic(*args):
        return subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            env=environment,
            capture_output=True,
            text=True,
        )

    engine = create_engine(db_url)
    assert run_alembic("downgrade", "base").returncode == 0
    assert run_alembic("upgrade", "head").returncode == 0
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO vehicles (id, source_account, is_manual, name, active, archived, "
                    "locally_edited, manual_name, manual_license_plate, manual_vehicle_type, "
                    "card_version, photo_version, tows_heavy_trailer) "
                    "VALUES (:id, 'syn', true, 'Kartoteka', true, false, true, true, true, "
                    "false, 1, 0, false)"
                ),
                {"id": vehicle_id},
            )
        # A card edit is in flight (uncommitted) when the downgrade starts.
        writer = engine.connect()
        transaction = writer.begin()
        writer.execute(text("UPDATE vehicles SET axles = 2 WHERE id = :id"), {"id": vehicle_id})
        downgrade = subprocess.Popen(
            [sys.executable, "-m", "alembic", "downgrade", "0015_license_compatibility"],
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            with pytest.raises(subprocess.TimeoutExpired):
                downgrade.wait(timeout=3)
            transaction.commit()
            output, errors = downgrade.communicate(timeout=60)
        finally:
            writer.close()
            if downgrade.poll() is None:
                downgrade.kill()
        assert downgrade.returncode != 0
        assert "SCRUM-68" in output + errors
        with engine.connect() as conn:
            axles = conn.scalar(
                text("SELECT axles FROM vehicles WHERE id = :id"), {"id": vehicle_id}
            )
        assert axles == 2
    finally:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM vehicles WHERE id = :id"), {"id": vehicle_id})
        run_alembic("downgrade", "base")
        run_alembic("upgrade", "head")
        engine.dispose()
