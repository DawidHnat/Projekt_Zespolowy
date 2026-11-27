"""SCRUM-87: shared append-only audit trail tests (transactions, rollback, scoping, redaction)."""

import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

from app.core.models import SyncState, Vehicle
from app.modules.audit.service import record_audit_event, sanitize_changes
from app.modules.auth.models import User
from app.modules.auth.service import password_hasher
from app.modules.fleet.sync import account_key, apply_records
from app.modules.trips.models import Trip

ORIGIN = {"Origin": "http://127.0.0.1:5173"}


def test_business_operations_record_audit_trail_and_import_is_distinguished(logged_in):
    app, client = logged_in
    now = datetime.now(UTC)
    source = account_key(app.state.settings.webfleet_account)

    # 1. WEBFLEET import creates actor_type == "import" without raw GPS coordinates.
    with app.state.sessions() as session:
        session.add(SyncState(source_account=source, last_success_at=now))
        apply_records(
            session,
            source,
            {
                "wf-secret-object-uid": {
                    "objectuid": "wf-secret-object-uid",
                    "objectname": "Renault Import",
                    "objectno": "WF-01",
                    "licenseplatenumber": "GD 100WF",
                    "vehicletype": "van",
                }
            },
            {},
            now,
        )
        imported = session.scalar(
            select(Vehicle).where(Vehicle.external_uid == "wf-secret-object-uid")
        )
        trip = Trip(
            vehicle_id=imported.id,
            external_uid="wf-trip-audit",
            start_at=now - timedelta(hours=2),
            end_at=now - timedelta(hours=1),
            distance_km=Decimal("31.4"),
        )
        session.add(trip)
        session.commit()
        imported_id = str(imported.id)
        trip_id = str(trip.id)

    # 2. Manual vehicle creation + odometer update + card edit with explicit correlation ID.
    manual = client.post(
        "/api/v1/fleet/vehicles",
        headers={**ORIGIN, "X-Correlation-ID": "corr-manual-create-01"},
        json={
            "name": "Skoda Ręczna Audyt",
            "license_plate": "GD 777AU",
            "gross_weight_kg": 2200,
        },
    )
    assert manual.status_code == 201
    manual_id = manual.json()["id"]

    odo = client.put(
        f"/api/v1/fleet/vehicles/{manual_id}/odometer",
        headers=ORIGIN,
        json={
            "card_version": manual.json()["card_version"],
            "odometer_km": 12500.5,
            "recorded_on": "2026-11-25",
        },
    )
    assert odo.status_code == 200

    card_patch = client.patch(
        f"/api/v1/fleet/vehicles/{imported_id}",
        headers=ORIGIN,
        json={"card_version": 1, "make": "Renault", "gross_weight_kg": 3500},
    )
    assert card_patch.status_code == 200

    # 3. Driver creation, assignment to imported vehicle, trip annotation update, assignment close.
    drv = client.post(
        "/api/v1/drivers",
        headers=ORIGIN,
        json={
            "first_name": "Kamil",
            "last_name": "Audytowy",
            "identifier": "SYN-AUD-1",
            "phone": "+48 600 700 800",
            "email": "kamil.private@example.com",
            "categories": ["B"],
        },
    ).json()
    assign_res = client.post(
        f"/api/v1/drivers/{drv['id']}/assignments",
        headers=ORIGIN,
        json={"version": drv["version"], "vehicle_id": imported_id},
    )
    assert assign_res.status_code == 201

    trip_res = client.patch(
        f"/api/v1/trips/{trip_id}/annotation",
        headers=ORIGIN,
        json={"version": 1, "purpose": " Serwis klienta ", "driver_id": drv["id"]},
    )
    assert trip_res.status_code == 200

    close_res = client.patch(
        f"/api/v1/drivers/{drv['id']}/assignments/{assign_res.json()['assignment']['id']}/close",
        headers=ORIGIN,
        json={"version": assign_res.json()["driver_version"]},
    )
    assert close_res.status_code == 200

    # 4. Per-vehicle audit query returns imported + card + assignment + trip annotation events!
    veh_events = client.get(f"/api/v1/audit/events?vehicle_id={imported_id}").json()
    ops = [item["operation"] for item in veh_events["items"]]
    assert "vehicle.imported" in ops
    assert "vehicle.updated" in ops
    assert "driver_assignment.created" in ops
    assert "trip_annotation.updated" in ops
    assert "driver_assignment.closed" in ops

    import_ev = next(
        item for item in veh_events["items"] if item["operation"] == "vehicle.imported"
    )
    assert import_ev["actor_type"] == "import"
    assert import_ev["actor"] is None
    assert "wf-secret-object-uid" not in json.dumps(veh_events)

    # 5. Correlation ID propagation & privacy redaction (no raw phone/email in driver audit).
    manual_events = client.get(f"/api/v1/audit/events?vehicle_id={manual_id}").json()
    created_ev = next(
        item for item in manual_events["items"] if item["operation"] == "vehicle.created"
    )
    assert created_ev["correlation_id"] == "corr-manual-create-01"
    assert any(item["operation"] == "vehicle.odometer_updated" for item in manual_events["items"])

    driver_events = client.get("/api/v1/audit/events?entity_type=driver").json()
    serialized_drv_audit = json.dumps(driver_events)
    assert "+48 600 700 800" not in serialized_drv_audit
    assert "kamil.private@example.com" not in serialized_drv_audit
    assert driver_events["items"][0]["changes"]["phone_configured"]["after"] is True

    # 6. Filter by actor_type=import vs actor_type=user and actor_id.
    only_imports = client.get("/api/v1/audit/events?actor_type=import").json()
    assert only_imports["total"] == 1
    assert only_imports["items"][0]["operation"] == "vehicle.imported"

    actors = client.get("/api/v1/audit/actors").json()["items"]
    assert len(actors) == 1
    by_actor = client.get(f"/api/v1/audit/events?actor_id={actors[0]['id']}").json()
    assert by_actor["total"] >= 5
    assert all(item["actor_type"] == "user" for item in by_actor["items"])


def test_atomic_rollback_leaves_no_audit_trace_and_mutations_are_forbidden(logged_in):
    app, client = logged_in
    source = account_key(app.state.settings.webfleet_account)

    # Atomic rollback in business session leaves zero orphan audit events.
    with app.state.sessions() as session:
        user = session.scalar(select(User).where(User.username == "test-user"))
        temp_vehicle = Vehicle(
            source_account=source,
            is_manual=True,
            name="Niezapisany",
            license_plate="SYN ROLL 1",
        )
        session.add(temp_vehicle)
        session.flush()
        record_audit_event(
            session,
            entity_type="vehicle",
            entity_id=temp_vehicle.id,
            vehicle_id=temp_vehicle.id,
            operation="vehicle.created",
            actor_id=user.id,
            source_account=source,
            changes={"name": {"before": None, "after": "Niezapisany"}},
        )
        session.flush()
        session.rollback()

    events = client.get("/api/v1/audit/events?entity_type=vehicle").json()
    assert events["total"] == 0

    # Create one real event, then verify HTTP write methods and DB UPDATE/DELETE are blocked!
    created = client.post(
        "/api/v1/fleet/vehicles",
        headers=ORIGIN,
        json={"name": "Trwały ślad", "license_plate": "SYN IMM 01"},
    )
    assert created.status_code == 201
    event_list = client.get("/api/v1/audit/events?entity_type=vehicle").json()
    assert event_list["total"] == 1
    event_id = event_list["items"][0]["id"]

    for method in ("POST", "PUT", "PATCH", "DELETE"):
        assert client.request(method, "/api/v1/audit/events", headers=ORIGIN).status_code == 405
        assert client.request(
            method, f"/api/v1/audit/events/{event_id}", headers=ORIGIN
        ).status_code in (404, 405)

    # SQLite DB trigger blocks raw SQL UPDATE and DELETE.
    with app.state.sessions() as session:
        with pytest.raises(DBAPIError, match="append-only"):
            session.execute(
                text("UPDATE audit_events SET operation = 'tampered' WHERE id = :id"),
                {"id": event_id.replace("-", "")},
            )
        session.rollback()
        with pytest.raises(DBAPIError, match="append-only"):
            session.execute(text("DELETE FROM audit_events"))
        session.rollback()


def test_sensitive_fields_and_card_numbers_never_enter_audit_log(logged_in):
    _, client = logged_in

    for forbidden_field in (
        "password",
        "password_hash",
        "token",
        "token_hash",
        "api_key",
        "pin",
        "card_number",
        "latitude",
        "longitude",
        "storage_key",
        "external_uid",
    ):
        with pytest.raises(ValueError, match="not permitted"):
            sanitize_changes("vehicle", {forbidden_field: {"before": None, "after": "secret"}})

    # Accidental PAN-like string inside a free-text description is masked.
    masked = sanitize_changes(
        "trip_annotation",
        {"description": {"before": None, "after": "Karta 1234 5678 9012 3456 PIN"}},
    )
    assert "1234 5678 9012 3456" not in json.dumps(masked)
    assert "[REDACTED_CARD]" in masked["description"]["after"]

    # Password change and failed login record security events without storing secrets/tokens.
    bad_login = client.post(
        "/api/v1/auth/login",
        headers=ORIGIN,
        json={"username": "test-user", "password": "wrong-super-secret-password"},
    )
    assert bad_login.status_code == 401

    pwd_change = client.post(
        "/api/v1/auth/password/change",
        headers=ORIGIN,
        json={
            "current_password": "synthetic-test-password",
            "new_password": "new-synthetic-password-123",
        },
    )
    assert pwd_change.status_code == 200

    all_events = client.get("/api/v1/audit/events").json()
    raw_dump = json.dumps(all_events)
    assert "wrong-super-secret-password" not in raw_dump
    assert "synthetic-test-password" not in raw_dump
    assert "new-synthetic-password-123" not in raw_dump
    ops = {item["operation"] for item in all_events["items"]}
    assert "auth.login_succeeded" in ops
    assert "auth.login_failed" in ops
    assert "auth.password_changed" in ops


def test_access_control_and_source_scoping_hide_foreign_and_other_users_events(logged_in):
    app, client = logged_in

    with app.state.sessions() as session:
        me = session.scalar(select(User).where(User.username == "test-user"))
        me.role = "editor"
        other_user = User(
            username="other-editor",
            display_name="Inny Edytor",
            role="editor",
            password_hash=password_hasher.hash("other-synthetic-password"),
        )
        foreign_vehicle = Vehicle(
            source_account=account_key("foreign-webfleet-tenant"),
            is_manual=True,
            name="Obcy Pojazd",
            license_plate="OBCY 001",
        )
        session.add_all([other_user, foreign_vehicle])
        session.flush()
        record_audit_event(
            session,
            entity_type="vehicle",
            entity_id=foreign_vehicle.id,
            vehicle_id=foreign_vehicle.id,
            operation="vehicle.created",
            actor_id=other_user.id,
            source_account=foreign_vehicle.source_account,
            changes={"name": {"before": None, "after": "Obcy Pojazd"}},
        )
        record_audit_event(
            session,
            entity_type="user_session",
            entity_id=other_user.id,
            operation="auth.login_succeeded",
            actor_id=other_user.id,
            changes={"action": {"before": None, "after": "login_succeeded"}},
        )
        session.commit()
        foreign_vid = str(foreign_vehicle.id)
        other_uid = str(other_user.id)

    # Current user (editor) must NOT see foreign-source vehicle events or other_user's auth events!
    visible = client.get("/api/v1/audit/events").json()
    dump = json.dumps(visible)
    assert "Obcy Pojazd" not in dump
    assert other_uid not in dump
    assert client.get(f"/api/v1/audit/events?vehicle_id={foreign_vid}").status_code == 404

    # Admin sees security events across accounts, still never foreign fleet sources!
    with app.state.sessions() as session:
        me = session.scalar(select(User).where(User.username == "test-user"))
        me.role = "admin"
        session.commit()
    admin_visible = client.get("/api/v1/audit/events?entity_type=user_session").json()
    assert any(item["entity_id"] == other_uid for item in admin_visible["items"])
    assert client.get(f"/api/v1/audit/events?vehicle_id={foreign_vid}").status_code == 404

    # Unauthenticated access is denied (401).
    client.post("/api/v1/auth/logout", headers=ORIGIN)
    assert client.get("/api/v1/audit/events").status_code == 401
    assert client.get("/api/v1/audit/actors").status_code == 401


def test_postgres_migration_0016_append_only_trigger_and_controlled_retention():
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

    assert run_alembic("downgrade", "0015_license_compatibility").returncode == 0
    assert run_alembic("upgrade", "head").returncode == 0
    engine = create_engine(db_url)
    event_uuid = uuid4()
    event_id_str = str(event_uuid)
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO audit_events (id, occurred_at, source_account, actor_id, "
                    "actor_type, entity_type, entity_id, vehicle_id, operation, outcome, "
                    "correlation_id, changes) VALUES (:id, now(), 'syn', NULL, 'import', "
                    "'vehicle', :entity_id, NULL, 'vehicle.imported', 'succeeded', 'corr-pg', '{}')"
                ),
                {"id": event_uuid, "entity_id": event_id_str},
            )

        # PostgreSQL trigger blocks both UPDATE and DELETE for normal application sessions!
        with pytest.raises(DBAPIError, match="append-only"):
            with engine.begin() as conn:
                conn.execute(
                    text("UPDATE audit_events SET operation = 'hacked' WHERE id = :id"),
                    {"id": event_uuid},
                )
        with pytest.raises(DBAPIError, match="append-only"):
            with engine.begin() as conn:
                conn.execute(
                    text("DELETE FROM audit_events WHERE id = :id"),
                    {"id": event_uuid},
                )

        # Controlled maintenance parameter allows legal retention cleanup in an admin transaction.
        with engine.begin() as conn:
            conn.execute(text("SET LOCAL fleet_flow.audit_maintenance = 'allow'"))
            conn.execute(
                text("DELETE FROM audit_events WHERE id = :id"),
                {"id": event_uuid},
            )
    finally:
        run_alembic("downgrade", "base")
        run_alembic("upgrade", "head")
        engine.dispose()
