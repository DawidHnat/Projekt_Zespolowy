"""SCRUM-70: Polish driving license category compatibility, API blocks, and history safety."""

import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.core.models import SyncState, Vehicle
from app.modules.drivers.compatibility import (
    HISTORICAL_ASSIGNMENT_WARNING,
    MATRIX_VERSION,
    PO_CONFIRMED,
    evaluate_driver_vehicle,
    expand_driver_categories,
    vehicle_license_requirement,
)
from app.modules.fleet.sync import account_key
from app.modules.trips.models import Trip

ORIGIN = {"Origin": "http://127.0.0.1:5173"}


def test_statutory_matrix_is_non_alphabetical_and_pending_po_confirmation():
    assert MATRIX_VERSION == "pl-ustawa-o-kierujacych-v1-pending-po"
    assert PO_CONFIRMED is False

    # Higher alphabetical letters do NOT imply lower unrelated categories (D !=> C or B).
    d_entitled = expand_driver_categories(["D"])
    assert d_entitled == {"D", "D1"}
    assert "C" not in d_entitled
    assert "B" not in d_entitled

    # C implies C1, A implies A2/A1/AM, C+E implies C/C1+E/C1/B+E/T.
    assert expand_driver_categories(["C"]) == {"C", "C1"}
    assert expand_driver_categories(["A"]) == {"A", "A2", "A1", "AM"}
    assert {"C", "C1+E", "C1", "B+E", "T"} <= expand_driver_categories(["C+E"])

    # Art. 6 ust. 2 pkt 3: C+E together with D implies D+E and D1+E.
    assert {"D+E", "D1+E"} <= expand_driver_categories(["C+E", "D"])
    assert "D+E" not in expand_driver_categories(["C+E", "D1"])
    assert "D1+E" in expand_driver_categories(["C+E", "D1"])


@pytest.mark.parametrize(
    ("kwargs", "expected_status", "expected_cat", "expected_reason"),
    [
        # "ciężarowy" label alone NEVER implies C and NEVER guesses compatible without DMC!
        (
            {"vehicle_type": "ciężarowy", "gross_weight_kg": None},
            "unverified",
            None,
            "missing_vehicle_dmc",
        ),
        # N1 "ciężarowy" up to 3500 kg requires B, not C.
        (
            {"vehicle_type": "ciężarowy", "gross_weight_kg": 3500},
            "determined",
            "B",
            None,
        ),
        # DMC boundaries: 3500 -> B, 3501 -> C1, 7500 -> C1, 7501 -> C.
        ({"gross_weight_kg": 3500}, "determined", "B", None),
        ({"gross_weight_kg": 3501}, "determined", "C1", None),
        ({"gross_weight_kg": 7500}, "determined", "C1", None),
        ({"gross_weight_kg": 7501}, "determined", "C", None),
        # Heavy trailer upgrades (+E).
        (
            {"gross_weight_kg": 3500, "tows_heavy_trailer": True},
            "determined",
            "B+E",
            None,
        ),
        (
            {"gross_weight_kg": 7500, "tows_heavy_trailer": True},
            "determined",
            "C1+E",
            None,
        ),
        (
            {"gross_weight_kg": 18000, "tows_heavy_trailer": True},
            "determined",
            "C+E",
            None,
        ),
        # Buses require passenger_seats.
        (
            {"vehicle_type": "autobus", "passenger_seats": None},
            "unverified",
            None,
            "missing_passenger_seats",
        ),
        (
            {"vehicle_type": "autobus", "passenger_seats": 12},
            "determined",
            "D1",
            None,
        ),
        (
            {"vehicle_type": "autobus", "passenger_seats": 24, "tows_heavy_trailer": True},
            "determined",
            "D+E",
            None,
        ),
        # Tractor and motorcycle/override rules.
        ({"vehicle_type": "ciągnik rolniczy"}, "determined", "T", None),
        (
            {"vehicle_type": "motocykl"},
            "unverified",
            None,
            "missing_vehicle_requirements",
        ),
        (
            {"vehicle_type": "motocykl", "required_category_override": "A2"},
            "determined",
            "A2",
            None,
        ),
    ],
)
def test_vehicle_license_requirement_boundaries_and_exceptions(
    kwargs, expected_status, expected_cat, expected_reason
):
    base = {
        "name": "Syntetyczny",
        "vehicle_type": None,
        "gross_weight_kg": None,
        "passenger_seats": None,
        "tows_heavy_trailer": False,
        "required_category_override": None,
    }
    base.update(kwargs)
    dummy = Vehicle(**base)
    req = vehicle_license_requirement(dummy)
    assert req["status"] == expected_status
    assert req["required_category"] == expected_cat
    assert req["reason"] == expected_reason


def test_missing_data_is_never_compatible():
    truck_no_dmc = Vehicle(
        name="Ciężarowy bez DMC",
        vehicle_type="ciężarowy",
        gross_weight_kg=None,
        tows_heavy_trailer=False,
    )
    res_no_dmc = evaluate_driver_vehicle(["B", "C", "C+E"], truck_no_dmc)
    assert res_no_dmc["status"] == "unverified"
    assert res_no_dmc["reason"] == "missing_vehicle_dmc"

    van_3500 = Vehicle(
        name="Dostawczy N1",
        vehicle_type="ciężarowy",
        gross_weight_kg=3500,
        tows_heavy_trailer=False,
    )
    res_no_cats = evaluate_driver_vehicle([], van_3500)
    assert res_no_cats["status"] == "unverified"
    assert res_no_cats["reason"] == "missing_driver_categories"

    res_n1_b = evaluate_driver_vehicle(["B"], van_3500)
    assert res_n1_b["status"] == "compatible"
    assert res_n1_b["required_category"] == "B"


def test_api_blocks_incompatible_assignments_trip_annotations_and_manual_vehicle_driver(logged_in):
    app, client = logged_in
    now = datetime.now(UTC)
    source = account_key(app.state.settings.webfleet_account)

    with app.state.sessions() as session:
        session.add(SyncState(source_account=source, last_success_at=now))
        heavy_truck = Vehicle(
            source_account=source,
            external_uid="syn-heavy-truck",
            name="Ciężarówka 18t",
            license_plate="SYN 18T",
            vehicle_type="ciężarowy",
            gross_weight_kg=18000,
        )
        unverified_van = Vehicle(
            source_account=source,
            external_uid="syn-van-no-dmc",
            name="Auto bez DMC",
            license_plate="SYN NODMC",
            vehicle_type="ciężarowy",
            gross_weight_kg=None,
        )
        session.add_all([heavy_truck, unverified_van])
        session.flush()
        trip = Trip(
            vehicle_id=heavy_truck.id,
            external_uid="syn-heavy-trip",
            start_at=now - timedelta(hours=2),
            end_at=now - timedelta(hours=1),
            distance_km=Decimal("48.0"),
        )
        session.add(trip)
        session.commit()
        heavy_truck_id = str(heavy_truck.id)
        unverified_van_id = str(unverified_van.id)
        trip_id = str(trip.id)

    b_driver = client.post(
        "/api/v1/drivers",
        headers=ORIGIN,
        json={
            "first_name": "Marek",
            "last_name": "TylkoB",
            "identifier": "SYN-DRV-B",
            "categories": ["B"],
        },
    ).json()
    c_driver = client.post(
        "/api/v1/drivers",
        headers=ORIGIN,
        json={
            "first_name": "Piotr",
            "last_name": "ZawodowyC",
            "identifier": "SYN-DRV-C",
            "categories": ["B", "C"],
        },
    ).json()

    # 1. Direct API block on POST /drivers/{id}/assignments for incompatible driver.
    blocked_assign = client.post(
        f"/api/v1/drivers/{b_driver['id']}/assignments",
        headers=ORIGIN,
        json={"version": b_driver["version"], "vehicle_id": heavy_truck_id},
    )
    assert blocked_assign.status_code == 409
    assert blocked_assign.json()["error"]["code"] == "LICENSE_INCOMPATIBLE"

    # 2. Direct API block on PATCH /trips/{id}/annotation for incompatible driver.
    blocked_trip = client.patch(
        f"/api/v1/trips/{trip_id}/annotation",
        headers=ORIGIN,
        json={"version": 1, "purpose": "Dostawa", "driver_id": b_driver["id"]},
    )
    assert blocked_trip.status_code == 409
    assert blocked_trip.json()["error"]["code"] == "LICENSE_INCOMPATIBLE"

    # 3. Direct API block on POST /fleet/vehicles with an incompatible driver.
    blocked_manual = client.post(
        "/api/v1/fleet/vehicles",
        headers=ORIGIN,
        json={
            "name": "Ręczna ciężarówka",
            "license_plate": "SYN MAN 18T",
            "gross_weight_kg": 18000,
            "driver_id": b_driver["id"],
        },
    )
    assert blocked_manual.status_code == 409
    assert blocked_manual.json()["error"]["code"] == "LICENSE_INCOMPATIBLE"

    # Unverified vehicle (missing DMC) is NOT treated as compatible, yet not blocked;
    # it appears in assignments_to_check with reason missing_vehicle_dmc!
    unverified_assign = client.post(
        f"/api/v1/drivers/{b_driver['id']}/assignments",
        headers=ORIGIN,
        json={"version": b_driver["version"], "vehicle_id": unverified_van_id},
    )
    assert unverified_assign.status_code == 201
    assert unverified_assign.json()["assignment"]["compatibility"]["status"] == "unverified"
    assert (
        unverified_assign.json()["assignment"]["compatibility"]["reason"] == "missing_vehicle_dmc"
    )

    # Compatible C driver succeeds on both assignment and trip annotation.
    ok_assign = client.post(
        f"/api/v1/drivers/{c_driver['id']}/assignments",
        headers=ORIGIN,
        json={"version": c_driver["version"], "vehicle_id": heavy_truck_id},
    )
    assert ok_assign.status_code == 201
    assert ok_assign.json()["assignment"]["compatibility"]["status"] == "compatible"
    assert ok_assign.json()["assignment"]["compatibility"]["required_category"] == "C"

    ok_trip = client.patch(
        f"/api/v1/trips/{trip_id}/annotation",
        headers=ORIGIN,
        json={"version": 1, "purpose": "Trasa krajowa", "driver_id": c_driver["id"]},
    )
    assert ok_trip.status_code == 200
    assert ok_trip.json()["driver_id"] == c_driver["id"]
    assert ok_trip.json()["driver"]["historical_warning"] == HISTORICAL_ASSIGNMENT_WARNING

    # Check summary widget breakdown before category change: 1 unverified, 0 incompatible.
    summary_before = client.get("/api/v1/drivers/summary").json()
    assert summary_before["assignments_to_check"] == {
        "status": "evaluated",
        "total": 1,
        "incompatible": 0,
        "unverified": 1,
        "by_reason": {
            "category_mismatch": 0,
            "missing_driver_categories": 0,
            "missing_vehicle_dmc": 1,
            "missing_passenger_seats": 0,
            "missing_vehicle_requirements": 0,
        },
        "matrix_version": MATRIX_VERSION,
        "po_confirmed": False,
    }

    # If vehicle DMC is updated on unverified_van to 12000 kg while b_driver is still assigned,
    # active relationship becomes incompatible and is counted in category_mismatch!
    van_detail = client.get(f"/api/v1/fleet/vehicles/{unverified_van_id}").json()
    patched_van = client.patch(
        f"/api/v1/fleet/vehicles/{unverified_van_id}",
        headers=ORIGIN,
        json={"card_version": van_detail["card_version"], "gross_weight_kg": 12000},
    )
    assert patched_van.status_code == 200
    assert patched_van.json()["license_requirement"]["required_category"] == "C"

    summary_after_dmc = client.get("/api/v1/drivers/summary").json()
    assert summary_after_dmc["assignments_to_check"]["total"] == 1
    assert summary_after_dmc["assignments_to_check"]["incompatible"] == 1
    assert summary_after_dmc["assignments_to_check"]["by_reason"]["category_mismatch"] == 1

    attention = client.post(
        "/api/v1/drivers/search",
        headers=ORIGIN,
        json={"compatibility_status": "attention"},
    ).json()
    assert [item["id"] for item in attention["items"]] == [b_driver["id"]]

    # Close c_driver's assignment and then remove category C from c_driver:
    # historical closed assignment and trip annotation MUST remain intact with warning!
    closed = client.patch(
        f"/api/v1/drivers/{c_driver['id']}/assignments/{ok_assign.json()['assignment']['id']}/close",
        headers=ORIGIN,
        json={"version": ok_assign.json()["driver_version"]},
    )
    assert closed.status_code == 200
    assert closed.json()["assignment"]["active"] is False
    assert (
        closed.json()["assignment"]["compatibility"]["historical_warning"]
        == HISTORICAL_ASSIGNMENT_WARNING
    )

    downgraded_driver = client.patch(
        f"/api/v1/drivers/{c_driver['id']}",
        headers=ORIGIN,
        json={"version": closed.json()["driver_version"], "categories": ["B"]},
    )
    assert downgraded_driver.status_code == 200

    history = client.get(f"/api/v1/drivers/{c_driver['id']}/assignments?active=false").json()
    assert history["total"] == 1
    hist_item = history["items"][0]
    assert hist_item["compatibility"]["status"] == "incompatible"
    assert hist_item["compatibility"]["historical_warning"] == HISTORICAL_ASSIGNMENT_WARNING

    persisted_trip = client.get(f"/api/v1/trips/{trip_id}").json()
    assert persisted_trip["annotation"]["driver_id"] == c_driver["id"]
    assert (
        persisted_trip["annotation"]["driver"]["historical_warning"]
        == HISTORICAL_ASSIGNMENT_WARNING
    )


def test_migration_0015_blocks_lossy_downgrade_on_postgres():
    db_url = os.environ.get("TEST_DATABASE_URL")
    if not db_url or not db_url.startswith("postgresql"):
        pytest.skip("PostgreSQL migration check")
    assert make_url(db_url).database.startswith("fleet_flow_test")
    environment = {**os.environ, "DATABASE_URL": db_url, "SYNC_ENABLED": "false"}

    def run_alembic(*args):
        return subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            env=environment,
            capture_output=True,
            text=True,
        )

    engine = create_engine(db_url)
    try:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM vehicles WHERE id = '99999999-9999-4999-8999-999999999999'")
            )
    except Exception:
        pass
    assert run_alembic("downgrade", "base").returncode == 0
    assert run_alembic("upgrade", "head").returncode == 0
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO vehicles (id, source_account, is_manual, name, active, archived, "
                    "locally_edited, manual_name, manual_license_plate, manual_vehicle_type, "
                    "card_version, photo_version, gross_weight_kg, tows_heavy_trailer) "
                    "VALUES ('99999999-9999-4999-8999-999999999999', 'syn', true, 'Ciężarówka', "
                    "true, false, true, true, true, false, 1, 0, 12000, false)"
                )
            )
        failed = run_alembic("downgrade", "0014_vehicle_documents")
        assert failed.returncode != 0
        assert "SCRUM-70" in (failed.stderr + failed.stdout)
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM vehicles WHERE id = '99999999-9999-4999-8999-999999999999'")
            )
        assert run_alembic("downgrade", "0014_vehicle_documents").returncode == 0
        assert run_alembic("upgrade", "head").returncode == 0
    finally:
        try:
            with engine.begin() as conn:
                conn.execute(
                    text("DELETE FROM vehicles WHERE id = '99999999-9999-4999-8999-999999999999'")
                )
        except Exception:
            pass
        run_alembic("downgrade", "base")
        run_alembic("upgrade", "head")
        engine.dispose()
