from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.models import Driver, Measurement, SyncState, Vehicle
from app.modules.auth.models import User
from app.modules.fleet.sync import account_key

ORIGIN = {"Origin": "http://127.0.0.1:5173"}


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
    assert (
        client.patch(
            "/api/v1/fleet/vehicles/11111111-1111-4111-8111-111111111111",
            headers=ORIGIN,
            json={"make": "Test"},
        ).status_code
        == 401
    )


def test_lists_filters_missing_gps_map_and_private_fields(logged_in):
    app, client = logged_in
    identities = add_fleet(app)
    result = client.get("/api/v1/fleet/vehicles?page_size=2").json()
    assert result["total"] == 3 and len(result["items"]) == 2
    first = result["items"][0]
    assert first["status"] == "moving" and first["speed_kmh"] is None
    assert first["make"] is None and first["model"] is None
    assert first["year"] is None and first["vin"] is None
    assert first["position_address"] is None
    assert first["odometer_km"] == 1234.5
    assert first["driver"]["display_name"] == "Ręczny kierowca testowy"
    without_gps = client.get("/api/v1/fleet/vehicles?q=TEST%202").json()["items"][0]
    assert without_gps["latitude"] is None and without_gps["longitude"] is None
    assert "secret-source" not in str(result)
    assert client.get("/api/v1/fleet/vehicles?status=offline").json()["total"] == 1
    assert client.get("/api/v1/fleet/vehicles?q=TEST%202").json()["items"][0]["status"] == "unknown"
    assert client.get("/api/v1/fleet/vehicles?page_size=101").status_code == 422
    geo = client.get("/api/v1/fleet/map").json()
    assert geo["total"] == 3 and geo["located"] == 2
    assert geo["features"][0]["geometry"]["coordinates"] == [21.0, 52.0]
    assert client.get("/api/v1/fleet/map?status=unknown").json()["features"] == []
    filtered_list = client.get("/api/v1/fleet/vehicles?q=TEST%200&status=moving").json()
    filtered_map = client.get("/api/v1/fleet/map?q=TEST%200&status=moving").json()
    assert [vehicle["id"] for vehicle in filtered_list["items"]] == [
        feature["properties"]["id"] for feature in filtered_map["features"]
    ]
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


def test_vehicle_card_patch_telemetry_and_stale_address(logged_in):
    app, client = logged_in
    now = datetime.now(UTC)
    source = account_key(app.state.settings.webfleet_account)
    with app.state.sessions() as session:
        session.add(SyncState(source_account=source, last_attempt_at=now, last_success_at=now))
        vehicle = Vehicle(
            source_account=source,
            external_uid="card-test-uid",
            name="Pojazd bazowy",
            license_plate="GD 12345",
        )
        session.add(vehicle)
        session.flush()
        vehicle_id = str(vehicle.id)
        measurement = Measurement(
            vehicle_id=vehicle.id,
            latitude=54.35,
            longitude=18.64,
            position_at=now,
            received_at=now,
            gps_quality="A",
            standing_still=False,
            odometer_km=Decimal("5000.0"),
            speed_kmh=Decimal("60.0"),
            position_address="Gdańsk, Targ Węglowy",
        )
        session.add(measurement)
        session.commit()

    detail = client.get(f"/api/v1/fleet/vehicles/{vehicle_id}").json()
    assert detail["speed_kmh"] is None
    assert detail["position_address"] == "Gdańsk, Targ Węglowy"
    assert detail["is_stale"] is False

    # Simulate stale telemetry: address remains visible as last known, is_stale is True
    with app.state.sessions() as session:
        m = session.get(Measurement, vehicle.id)
        m.position_at = now - timedelta(hours=2)
        session.commit()

    detail_stale = client.get(f"/api/v1/fleet/vehicles/{vehicle_id}").json()
    assert detail_stale["position_address"] == "Gdańsk, Targ Węglowy"
    assert detail_stale["is_stale"] is True
    assert detail_stale["status"] == "offline"

    path = f"/api/v1/fleet/vehicles/{vehicle_id}"

    # Missing Origin header -> 403
    assert client.patch(path, json={"make": "Renault"}).status_code == 403

    # Foreign Origin header -> 403
    assert (
        client.patch(
            path, headers={"Origin": "https://other.example"}, json={"make": "Renault"}
        ).status_code
        == 403
    )

    # Viewer role cannot edit card -> 403
    with app.state.sessions() as session:
        user = session.scalar(select(User))
        user.role = "viewer"
        session.commit()
    assert client.patch(path, headers=ORIGIN, json={"make": "Renault"}).status_code == 403

    # Editor and Admin roles can edit card -> 200
    with app.state.sessions() as session:
        user = session.scalar(select(User))
        user.role = "editor"
        session.commit()

    # Invalid names: null, empty string, whitespace-only -> 422
    assert client.patch(path, headers=ORIGIN, json={"name": None}).status_code == 422
    assert client.patch(path, headers=ORIGIN, json={"name": ""}).status_code == 422
    assert client.patch(path, headers=ORIGIN, json={"name": "   "}).status_code == 422

    # Patch card metadata with valid fields and trimmed name
    patch_res = client.patch(
        path,
        headers=ORIGIN,
        json={
            "name": "  Nowa Nazwa Pojazdu  ",
            "make": "  Renault  ",
            "model": "Master",
            "year": 2023,
            "vin": "VF1MA000000000001",
        },
    )
    assert patch_res.status_code == 200
    patched = patch_res.json()
    assert patched["name"] == "Nowa Nazwa Pojazdu"
    assert patched["make"] == "Renault"
    assert patched["model"] == "Master"
    assert patched["year"] == 2023
    assert patched["vin"] == "VF1MA000000000001"

    # Search matches make, model, vin
    for query in ("Renault", "Master", "VF1MA"):
        res = client.get(f"/api/v1/fleet/vehicles?q={query}").json()
        assert res["total"] == 1
        assert res["items"][0]["id"] == vehicle_id

    # Validation errors
    bad_year = client.patch(path, headers=ORIGIN, json={"year": 1850})
    assert bad_year.status_code == 422
    extra_field = client.patch(path, headers=ORIGIN, json={"extra": "val"})
    assert extra_field.status_code == 422
    not_found = client.patch(
        "/api/v1/fleet/vehicles/11111111-1111-4111-8111-111111111111",
        headers=ORIGIN,
        json={"make": "Test"},
    )
    assert not_found.status_code == 404
