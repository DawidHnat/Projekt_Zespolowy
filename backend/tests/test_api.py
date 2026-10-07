from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.seed import seed_demo
from app.main import create_app


def test_health_is_independent_of_database_and_ready_redacts_errors():
    engine = Mock()
    engine.connect.side_effect = OperationalError("postgres://secret", {}, Exception("password"))
    settings = Settings(_env_file=None, database_url="sqlite://", data_source="demo")
    with TestClient(create_app(settings, engine)) as client:
        assert client.get("/health").json() == {"status": "ok"}
        engine.connect.assert_not_called()
        response = client.get("/ready")
        assert response.status_code == 503
        assert response.json() == {"detail": "Database unavailable."}
        assert "secret" not in response.text and "password" not in response.text


def test_filter_pagination_and_aggregate_use_matching_data(client):
    response = client.get("/api/v1/vehicles", params={"status": "driving", "limit": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "demo"
    assert data["total"] == 2 and len(data["items"]) == 1
    assert data["items"][0]["status"] == "driving"
    assert data["items"][0]["updated_at"].endswith("Z")
    assert client.get("/api/v1/vehicles?query=gdańsk").json()["total"] == 1
    assert client.get("/api/v1/vehicles?query=gd%2012").json()["total"] == 1
    assert client.get("/api/v1/vehicles?query=%25").json()["total"] == 0
    summary = client.get("/api/v1/analytics/summary").json()
    assert summary == {
        "total_vehicles": 4,
        "driving_vehicles": 2,
        "distance_km": 161,
        "trips_count": 4,
        "source": "demo",
    }
    alerts = client.get("/api/v1/analytics/alerts").json()
    assert alerts["total"] == 2
    assert {alert["severity"] for alert in alerts["items"]} == {"warning", "info"}


def test_patch_persists_only_provided_annotation_fields(client):
    trips = client.get("/api/v1/vehicles/demo-1/trips").json()
    trip = next(trip for trip in trips["items"] if trip["id"] == "demo-trip-1")
    before_notes = trip["notes"]
    response = client.patch("/api/v1/trips/demo-trip-1", json={"purpose": "Wizyta serwisowa"})
    assert response.status_code == 200
    assert response.json()["purpose"] == "Wizyta serwisowa"
    assert response.json()["notes"] == before_notes
    persisted = client.get("/api/v1/vehicles/demo-1/trips").json()["items"]
    assert (
        next(item for item in persisted if item["id"] == trip["id"])["purpose"]
        == "Wizyta serwisowa"
    )
    cleared = client.patch("/api/v1/trips/demo-trip-1", json={"notes": ""})
    assert cleared.json()["notes"] == ""
    assert cleared.json()["purpose"] == "Wizyta serwisowa"


@pytest.mark.parametrize(
    "payload",
    [{}, {"purpose": None}, {"purpose": "x" * 201}, {"notes": "x" * 2001}, {"distance_km": 0}],
)
def test_patch_rejects_invalid_or_protected_fields(client, payload):
    assert client.patch("/api/v1/trips/demo-trip-1", json=payload).status_code == 422


@pytest.mark.parametrize("path", ["/api/v1/vehicles/missing", "/api/v1/vehicles/missing/trips"])
def test_unknown_vehicle_returns_404(client, path):
    assert client.get(path).status_code == 404


def test_unknown_trip_and_invalid_filters(client):
    assert client.patch("/api/v1/trips/missing", json={"notes": "a"}).status_code == 404
    for query in ["limit=0", "limit=501", "offset=-1", "status=made-up"]:
        assert client.get(f"/api/v1/vehicles?{query}").status_code == 422


def test_switch_to_webfleet_never_labels_demo_as_live(engine):
    settings = Settings(_env_file=None, database_url="sqlite://", data_source="webfleet")
    with TestClient(create_app(settings, engine)) as live:
        assert live.get("/api/v1/vehicles").json() == {
            "items": [],
            "total": 0,
            "source": "webfleet",
        }
        assert live.get("/api/v1/vehicles/demo-1").status_code == 404
        assert live.get("/api/v1/vehicles/demo-1/trips").status_code == 404
        assert live.patch("/api/v1/trips/demo-trip-1", json={"notes": "edit"}).status_code == 404
        assert live.get("/api/v1/analytics/summary").json() == {
            "total_vehicles": 0,
            "driving_vehicles": 0,
            "distance_km": 0,
            "trips_count": 0,
            "source": "webfleet",
        }
        assert live.get("/api/v1/analytics/alerts").json()["items"] == []


def test_repeated_seed_preserves_annotations(client, engine):
    client.patch("/api/v1/trips/demo-trip-1", json={"notes": "Keep this"})
    with Session(engine) as session:
        assert seed_demo(session) == 0
    trips = client.get("/api/v1/vehicles/demo-1/trips").json()["items"]
    assert next(item for item in trips if item["id"] == "demo-trip-1")["notes"] == "Keep this"
