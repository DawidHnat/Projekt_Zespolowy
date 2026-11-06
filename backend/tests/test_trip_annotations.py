import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.engine import make_url

from app.core.models import Vehicle
from app.core.settings import Settings
from app.main import create_app
from app.modules.auth.models import User
from app.modules.auth.service import aware, current_user
from app.modules.fleet.sync import account_key
from app.modules.trips.models import Trip, TripAnnotation

ORIGIN = {"Origin": "http://127.0.0.1:5173"}
START = datetime(2026, 1, 10, 10, tzinfo=UTC)


def add_trip(session, source, *, vehicle=None, start=START, end=START + timedelta(hours=1)):
    if vehicle is None:
        vehicle = Vehicle(source_account=source, external_uid=uuid4().hex, name="Pojazd testowy")
        session.add(vehicle)
        session.flush()
    trip = Trip(
        vehicle_id=vehicle.id,
        external_uid=uuid4().hex,
        start_at=start,
        end_at=end,
        distance_km=Decimal("12.345"),
    )
    session.add(trip)
    session.flush()
    return vehicle, trip


@pytest.fixture
def stored_trip(logged_in):
    app, client = logged_in
    with app.state.sessions() as session:
        vehicle, trip = add_trip(session, account_key(app.state.settings.webfleet_account))
        ids = str(vehicle.id), str(trip.id)
        session.commit()
    return app, client, *ids


def patch(client, trip_id, **fields):
    return client.patch(
        f"/api/v1/trips/{trip_id}/annotation",
        headers={**ORIGIN, "Content-Type": "application/json"},
        content=json.dumps(fields),
    )


def test_annotation_is_durable_audited_and_separate_from_source(stored_trip):
    app, client, vehicle_id, trip_id = stored_trip
    original = client.get(f"/api/v1/trips/{trip_id}").json()
    assert original["annotation"] == {
        "purpose": None,
        "description": None,
        "version": 1,
        "updated_at": None,
        "updated_by": None,
    }
    saved = patch(
        client, trip_id, version=1, purpose="  Odbiór testowy  ", description="Opis\nDrugi wiersz"
    )
    assert saved.status_code == 200
    note = saved.json()
    assert note["purpose"] == "Odbiór testowy" and note["version"] == 2
    assert note["updated_by"]["display_name"] == "Osoba testowa"
    assert datetime.fromisoformat(note["updated_at"]).tzinfo is not None
    after = client.get(f"/api/v1/trips/{trip_id}").json()
    assert {k: v for k, v in after.items() if k != "annotation"} == {
        k: v for k, v in original.items() if k != "annotation"
    }
    # Re-importing source facts updates the same Trip; local annotations are untouched.
    with app.state.sessions() as session:
        trip = session.get(Trip, UUID(trip_id))
        trip.distance_km = Decimal("15.000")
        trip.end_at = START + timedelta(hours=2)
        session.commit()
    reimported = client.get(f"/api/v1/trips/{trip_id}").json()
    assert reimported["annotation"] == note
    assert reimported["distance_km"] == 15 and reimported["duration_seconds"] == 7200
    with app.state.sessions() as session:
        persisted = session.get(TripAnnotation, UUID(trip_id))
        assert persisted.description == "Opis\nDrugi wiersz" and persisted.version == 2
    assert after["vehicle_id"] == vehicle_id and "external_uid" not in after


def test_partial_patch_clear_and_optimistic_conflict(stored_trip):
    _, client, _, trip_id = stored_trip
    first = patch(client, trip_id, version=1, purpose="Cel", description="Opis").json()
    conflict = patch(client, trip_id, version=1, purpose="Spóźniona zmiana")
    assert conflict.status_code == 409 and conflict.json()["error"]["code"] == "VERSION_CONFLICT"
    assert client.get(f"/api/v1/trips/{trip_id}").json()["annotation"] == first
    second = patch(client, trip_id, version=2, purpose=None).json()
    assert second["purpose"] is None and second["description"] == "Opis" and second["version"] == 3
    third = patch(client, trip_id, version=3, description=" \n ").json()
    assert third["description"] is None and third["version"] == 4


@pytest.mark.parametrize(
    "fields",
    [
        {},
        {"version": 1},
        {"version": True, "purpose": "Cel"},
        {"version": "1", "purpose": "Cel"},
        {"version": 1.5, "purpose": "Cel"},
        {"version": 0, "purpose": "Cel"},
        {"version": 1, "purpose": "x" * 201},
        {"version": 1, "description": "x" * 2001},
        {"version": 1, "purpose": "a\nb"},
        {"version": 1, "description": "a\x00b"},
        {"version": 1, "description": "a\ud800b"},
        {"version": 1, "purpose": False},
        {"version": 1, "distance_km": 0},
        {"version": 1, "updated_by": str(uuid4()), "purpose": "Cel"},
    ],
)
def test_invalid_patch_does_not_write_or_reflect_input(stored_trip, fields):
    _, client, _, trip_id = stored_trip
    assert patch(client, trip_id, **fields).status_code == 422
    assert client.get(f"/api/v1/trips/{trip_id}").json()["annotation"]["version"] == 1


def test_authentication_origin_roles_and_account_isolation(stored_trip):
    app, client, vehicle_id, trip_id = stored_trip
    path = f"/api/v1/trips/{trip_id}/annotation"
    assert client.patch(path, json={"version": 1, "purpose": "Cel"}).status_code == 403
    assert (
        client.patch(
            path, headers={"Origin": "https://other.example"}, json={"version": 1, "purpose": "Cel"}
        ).status_code
        == 403
    )
    with app.state.sessions() as session:
        _, foreign = add_trip(session, "different-source")
        foreign_id = str(foreign.id)
        user = session.scalar(select(User))
        user.role = "viewer"
        session.commit()
    assert client.get(f"/api/v1/trips/{trip_id}").status_code == 200
    assert patch(client, trip_id, version=1, purpose="Cel").status_code == 403
    assert client.get(f"/api/v1/trips/{foreign_id}").status_code == 404
    with app.state.sessions() as session:
        session.scalar(select(User)).role = "editor"
        session.commit()
    assert patch(client, foreign_id, version=1, purpose="Cel").status_code == 404
    assert patch(client, str(uuid4()), version=1, purpose="Cel").status_code == 404
    assert patch(client, trip_id, version=1, purpose="Cel").status_code == 200
    client.post("/api/v1/auth/logout", headers=ORIGIN)
    assert client.get(f"/api/v1/trips/{trip_id}").status_code == 401
    assert (
        client.get(
            "/api/v1/trips",
            params={
                "vehicle_id": vehicle_id,
                "from": START.isoformat(),
                "to": (START + timedelta(days=1)).isoformat(),
            },
        ).status_code
        == 401
    )
    assert patch(client, trip_id, version=2, purpose="Cel").status_code == 401


def test_trip_list_ranges_pagination_and_unknown_values(stored_trip):
    app, client, vehicle_id, trip_id = stored_trip
    with app.state.sessions() as session:
        vehicle = session.get(Vehicle, UUID(vehicle_id))
        _, before = add_trip(
            session,
            vehicle.source_account,
            vehicle=vehicle,
            start=START - timedelta(hours=1),
            end=START,
        )
        _, overlap = add_trip(
            session,
            vehicle.source_account,
            vehicle=vehicle,
            start=START - timedelta(hours=1),
            end=START + timedelta(minutes=1),
        )
        _, point = add_trip(session, vehicle.source_account, vehicle=vehicle, start=START, end=None)
        point.distance_km = None
        _, zero = add_trip(session, vehicle.source_account, vehicle=vehicle, start=START, end=START)
        _, after = add_trip(
            session,
            vehicle.source_account,
            vehicle=vehicle,
            start=START + timedelta(days=1),
            end=None,
        )
        included = {trip_id, str(overlap.id), str(point.id), str(zero.id)}
        excluded = {str(before.id), str(after.id)}
        session.commit()
    params = {
        "vehicle_id": vehicle_id,
        "from": START.isoformat(),
        "to": (START + timedelta(days=1)).isoformat(),
        "page_size": 2,
    }
    first = client.get("/api/v1/trips", params=params).json()
    second = client.get("/api/v1/trips", params={**params, "page": 2}).json()
    items = first["items"] + second["items"]
    assert first["total"] == second["total"] == 4
    assert {item["id"] for item in items} == included
    assert not ({item["id"] for item in items} & excluded)
    assert any(item["distance_km"] is None and item["end_at"] is None for item in items)
    assert all(item["geometry"] is None for item in items)
    assert (
        client.get("/api/v1/trips", params={**params, "from": "2026-01-10T00:00:00"}).status_code
        == 422
    )
    assert (
        client.get("/api/v1/trips", params={**params, "to": START.isoformat()}).status_code == 422
    )
    assert (
        client.get(
            "/api/v1/trips", params={**params, "to": (START + timedelta(days=94)).isoformat()}
        ).status_code
        == 422
    )
    assert client.get("/api/v1/trips", params={**params, "page_size": 101}).status_code == 422
    assert (
        client.get("/api/v1/trips", params={**params, "vehicle_id": str(uuid4())}).status_code
        == 404
    )


@pytest.mark.parametrize("initial_version", [1, 2])
def test_postgres_two_editors_cannot_silently_overwrite_each_other(initial_version):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires an isolated PostgreSQL test database")
    assert make_url(url).database.startswith("fleet_flow_test"), "Refusing a non-test database"
    migration = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        env={**os.environ, "DATABASE_URL": url, "SYNC_ENABLED": "false"},
        capture_output=True,
        text=True,
    )
    assert migration.returncode == 0, "Failed to initialize the isolated test schema"
    app = create_app(Settings(url, webfleet_account=uuid4().hex))
    with app.state.sessions() as session:
        user = User(
            username=uuid4().hex,
            display_name="Test",
            role="editor",
            password_hash="unused-synthetic",
        )
        session.add(user)
        _, trip = add_trip(session, account_key(app.state.settings.webfleet_account))
        session.flush()
        trip_id, user_id = str(trip.id), user.id
        if initial_version == 2:
            session.add(
                TripAnnotation(
                    trip_id=trip.id,
                    purpose="Pierwsza",
                    version=2,
                    updated_by=user.id,
                    updated_at=START,
                )
            )
        session.commit()

    def authenticated_test_user():
        with app.state.sessions() as session:
            return session.get(User, user_id)

    app.dependency_overrides[current_user] = authenticated_test_user
    with TestClient(app) as client:

        def write(index):
            return patch(
                client, trip_id, version=initial_version, purpose=f"Edytor {index}"
            ).status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sorted(pool.map(write, range(2))) == [200, 409]
        with app.state.sessions() as session:
            annotation = session.get(TripAnnotation, UUID(trip_id))
            assert annotation.version == initial_version + 1
            assert annotation.purpose in {"Edytor 0", "Edytor 1"}
            assert aware(annotation.updated_at) > START
