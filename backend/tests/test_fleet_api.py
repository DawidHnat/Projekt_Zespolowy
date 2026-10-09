from datetime import UTC, datetime, timedelta

from app.core.models import Driver, Measurement, SyncState, Vehicle
from app.modules.fleet.sync import account_key


def add_fleet(app):
    now = datetime.now(UTC)
    with app.state.sessions() as session:
        source = account_key(app.state.settings.webfleet_account)
        session.add(SyncState(source_account=source, last_attempt_at=now, last_success_at=now))
        driver = Driver(display_name="Ręczny kierowca testowy")
        session.add(driver)
        session.flush()
        identities = []
        for index in range(3):
            vehicle = Vehicle(
                source_account=source,
                external_uid=f"secret-source-{index}",
                name=f"Test {index}",
                license_plate=f"TEST {index}",
                driver_id=driver.id,
            )
            session.add(vehicle)
            session.flush()
            identities.append(str(vehicle.id))
            if index < 2:
                session.add(
                    Measurement(
                        vehicle_id=vehicle.id,
                        latitude=52.0,
                        longitude=21.0,
                        position_at=now - timedelta(hours=index),
                        received_at=now,
                        gps_quality="A",
                        standing_still=False,
                        odometer_km=1234.5,
                    )
                )
        session.add(Vehicle(source_account="other-account", external_uid="other", name="OTHER"))
        session.commit()
    return identities


def test_every_fleet_endpoint_requires_session(application):
    _, client = application
    for route in ("vehicles", "map", "summary", "vehicles/11111111-1111-4111-8111-111111111111"):
        assert client.get("/api/v1/fleet/" + route).status_code == 401


def test_lists_filters_missing_gps_map_and_private_fields(logged_in):
    app, client = logged_in
    identities = add_fleet(app)
    result = client.get("/api/v1/fleet/vehicles?page_size=2").json()
    assert result["total"] == 3 and len(result["items"]) == 2
    first = result["items"][0]
    assert first["status"] == "moving" and first["speed_kmh"] is None
    assert first["driver"]["display_name"] == "Ręczny kierowca testowy"
    assert "secret-source" not in str(result)
    assert client.get("/api/v1/fleet/vehicles?status=offline").json()["total"] == 1
    assert client.get("/api/v1/fleet/vehicles?q=TEST%202").json()["items"][0]["status"] == "unknown"
    assert client.get("/api/v1/fleet/vehicles?page_size=101").status_code == 422
    geo = client.get("/api/v1/fleet/map").json()
    assert geo["total"] == 3 and geo["located"] == 2
    assert geo["features"][0]["geometry"]["coordinates"] == [21.0, 52.0]
    assert client.get("/api/v1/fleet/map?status=unknown").json()["features"] == []
    assert client.get("/api/v1/fleet/vehicles/" + identities[2]).status_code == 200
    summary = client.get("/api/v1/fleet/summary").json()
    assert summary["moving"] == summary["offline"] == summary["unknown"] == 1


def test_cold_source_and_degraded_cache_are_explicit(logged_in):
    app, client = logged_in
    assert client.get("/api/v1/fleet/vehicles").status_code == 503
    add_fleet(app)
    with app.state.sessions() as session:
        state = session.get(SyncState, account_key(app.state.settings.webfleet_account))
        state.error_code = "timeout"
        session.commit()
    result = client.get("/api/v1/fleet/vehicles").json()
    assert result["source"]["status"] == "degraded" and result["total"] == 3
