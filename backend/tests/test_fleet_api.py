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
    assert client.get("/api/v1/fleet/vehicles?page=100001").status_code == 422
    assert client.get("/api/v1/fleet/vehicles?page=" + "9" * 100).status_code == 422
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


def test_vehicle_sorting_applies_before_pagination(logged_in):
    app, client = logged_in
    add_fleet(app)
    source = account_key(app.state.settings.webfleet_account)
    with app.state.sessions() as session:
        vehicles = session.query(Vehicle).filter_by(source_account=source).all()
        odometers = {"Test 0": 100, "Test 1": 300}
        for vehicle in vehicles:
            if vehicle.name in odometers:
                measurement = session.query(Measurement).filter_by(vehicle_id=vehicle.id).one()
                measurement.odometer_km = odometers[vehicle.name]
        session.commit()

    descending = client.get("/api/v1/fleet/vehicles?sort=odometer-desc&page_size=1").json()
    assert descending["items"][0]["name"] == "Test 1"
    second_page = client.get("/api/v1/fleet/vehicles?sort=odometer-desc&page_size=1&page=2").json()
    assert second_page["items"][0]["name"] == "Test 0"
    third_page = client.get("/api/v1/fleet/vehicles?sort=odometer-desc&page_size=1&page=3").json()
    assert third_page["items"][0]["name"] == "Test 2"
    assert client.get("/api/v1/fleet/vehicles?sort=unsupported").status_code == 422
    for invalid_page in (0, 10**100, 100_001):
        response = client.get("/api/v1/fleet/vehicles", params={"page": invalid_page})
        assert response.status_code == 422


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
    assert result["source"]["last_success_at"]
    stale_vehicles = [item for item in result["items"] if item["position_at"]]
    assert all(item["is_stale"] and item["status"] == "offline" for item in stale_vehicles)
    geo = client.get("/api/v1/fleet/map").json()
    assert geo["source"] == result["source"]
    assert all(feature["properties"]["is_stale"] for feature in geo["features"])


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
    assert detail["speed_kmh"] == 60.0
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
    assert detail_stale["speed_kmh"] is None

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
    assert (
        client.patch(path, headers=ORIGIN, json={"card_version": 1, "name": None}).status_code
        == 422
    )
    assert (
        client.patch(path, headers=ORIGIN, json={"card_version": 1, "name": ""}).status_code == 422
    )
    assert (
        client.patch(path, headers=ORIGIN, json={"card_version": 1, "name": "   "}).status_code
        == 422
    )

    # Patch card metadata with valid fields and trimmed name
    patch_res = client.patch(
        path,
        headers=ORIGIN,
        json={
            "card_version": 1,
            "name": "  Nowa Nazwa Pojazdu  ",
            "make": "  Renault  ",
            "model": "Master",
            "year": 2023,
            "vin": "VF1MA000000000001",
            "ownership_category": "Leasing",
            "purchase_date": "2026-01-15",
            "first_registration": "2023-02-10",
            "first_registration_poland": "2023-03-01",
            "fuel_type": "Diesel",
            "engine_capacity_cc": 1997,
            "power_kw": 110,
            "dmc_kg": 3500,
            "curb_weight_kg": 2200,
            "payload_kg": 1300,
            "seats": 3,
            "axles": 2,
        },
    )
    assert patch_res.status_code == 200
    patched = patch_res.json()
    assert patched["name"] == "Nowa Nazwa Pojazdu"
    assert patched["card_version"] == 2
    assert client.patch(path, headers=ORIGIN, json={"make": "Old client"}).status_code == 422
    assert client.patch(path, headers=ORIGIN, json={"card_version": 2}).status_code == 422
    stale = client.patch(path, headers=ORIGIN, json={"card_version": 1, "make": "Stale"})
    assert stale.status_code == 409 and stale.json()["error"]["code"] == "VERSION_CONFLICT"
    assert patched["make"] == "Renault"
    assert patched["model"] == "Master"
    assert patched["year"] == 2023
    assert patched["vin"] == "VF1MA000000000001"
    assert patched["ownership_category"] == "Leasing"
    assert patched["purchase_date"] == "2026-01-15"
    assert patched["dmc_kg"] == 3500
    assert patched["payload_kg"] == 1300

    # Search matches make, model, vin
    for query in ("Renault", "Master", "VF1MA"):
        res = client.get(f"/api/v1/fleet/vehicles?q={query}").json()
        assert res["total"] == 1
        assert res["items"][0]["id"] == vehicle_id

    # Validation errors
    bad_year = client.patch(path, headers=ORIGIN, json={"card_version": 2, "year": 1850})
    assert bad_year.status_code == 422
    bad_category = client.patch(
        path, headers=ORIGIN, json={"card_version": 2, "ownership_category": "Leased"}
    )
    assert bad_category.status_code == 422
    bad_weight = client.patch(path, headers=ORIGIN, json={"card_version": 2, "dmc_kg": 0})
    assert bad_weight.status_code == 422
    extra_field = client.patch(path, headers=ORIGIN, json={"card_version": 2, "extra": "val"})
    assert extra_field.status_code == 422
    not_found = client.patch(
        "/api/v1/fleet/vehicles/11111111-1111-4111-8111-111111111111",
        headers=ORIGIN,
        json={"card_version": 1, "make": "Test"},
    )
    assert not_found.status_code == 404


def test_literal_search_pages_and_map_do_not_hide_other_markers(logged_in):
    app, client = logged_in
    add_fleet(app)
    with app.state.sessions() as session:
        source = account_key(app.state.settings.webfleet_account)
        session.add_all(
            [
                Vehicle(source_account=source, external_uid="literal", name="Van 100%_A"),
                Vehicle(source_account=source, external_uid="similar", name="Van 100xxA"),
                Vehicle(source_account=source, external_uid="inactive", name="Test", active=False),
            ]
        )
        session.commit()
    matches = client.get("/api/v1/fleet/vehicles", params={"q": " 100%_a "}).json()
    assert matches["total"] == 1 and matches["items"][0]["name"] == "Van 100%_A"
    first = client.get("/api/v1/fleet/vehicles", params={"page_size": 1}).json()
    second = client.get("/api/v1/fleet/vehicles", params={"page_size": 1, "page": 2}).json()
    assert first["total"] == second["total"] == 5
    assert first["items"][0]["id"] != second["items"][0]["id"]
    assert client.get("/api/v1/fleet/vehicles?page=100").json()["items"] == []
    assert client.get("/api/v1/fleet/map").json()["located"] == 2
    assert client.get("/api/v1/fleet/map", params={"q": "TEST 0"}).json()["total"] == 1


def test_sql_status_boundaries_match_details_and_zero_gps(logged_in, monkeypatch):
    from app.modules.fleet import service

    app, client = logged_in
    now = datetime(2026, 10, 28, 10, tzinfo=UTC)

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return now

    monkeypatch.setattr(service, "datetime", FrozenDatetime)
    source = account_key(app.state.settings.webfleet_account)
    cases = [
        (None, None, "unknown", False),  # No measurement.
        (None, False, "offline", False),
        (-900, False, "moving", True),  # Exact stale boundary is still fresh.
        (-900.001, False, "offline", True),
        (300, True, "stopped", True),  # Exact future boundary is still valid.
        (300.001, True, "offline", False),
        (0, None, "unknown", True),
    ]
    with app.state.sessions() as session:
        session.add(SyncState(source_account=source, last_success_at=now))
        for index, (offset, standing, _, _) in enumerate(cases):
            vehicle = Vehicle(source_account=source, external_uid=str(index), name=f"Edge {index}")
            session.add(vehicle)
            session.flush()
            if index:
                session.add(
                    Measurement(
                        vehicle_id=vehicle.id,
                        latitude=0,
                        longitude=0,
                        gps_quality="A",
                        position_at=now + timedelta(seconds=offset) if offset is not None else None,
                        received_at=now,
                        standing_still=standing,
                    )
                )
        session.commit()
    expected = {status: [] for status in ("unknown", "offline", "moving", "stopped")}
    for index, (_, _, status, _) in enumerate(cases):
        expected[status].append(f"Edge {index}")
    for status, names in expected.items():
        payload = client.get("/api/v1/fleet/vehicles", params={"status": status}).json()
        assert [item["name"] for item in payload["items"]] == names
        assert all(item["status"] == status for item in payload["items"])
        assert payload["total"] == len(names)
        geo = client.get("/api/v1/fleet/map", params={"status": status}).json()
        assert geo["total"] == len(names)
        assert all(feature["properties"]["status"] == status for feature in geo["features"])
    geo = client.get("/api/v1/fleet/map").json()
    assert geo["located"] == 4 and geo["total"] == 7
    assert all(feature["geometry"]["coordinates"] == [0.0, 0.0] for feature in geo["features"])
    assert geo["source"]["status"] == "ok"
    assert client.get("/api/v1/fleet/summary").json() == {
        "total": 7,
        **{status: len(names) for status, names in expected.items()},
        "source": geo["source"],
    }


def test_large_fleet_only_materializes_the_requested_page(logged_in):
    from sqlalchemy import event, insert

    app, client = logged_in
    now = datetime.now(UTC)
    source = account_key(app.state.settings.webfleet_account)
    with app.state.sessions() as session:
        session.add(SyncState(source_account=source, last_success_at=now))
        session.execute(
            insert(Vehicle),
            [
                {"source_account": source, "external_uid": str(index), "name": "Same name"}
                for index in range(10001)
            ],
        )
        session.commit()
    loaded = []

    def track_load(session, instance):
        if isinstance(instance, (Vehicle, Measurement, Driver)):
            loaded.append(instance)

    event.listen(app.state.sessions, "loaded_as_persistent", track_load)
    try:
        first = client.get("/api/v1/fleet/vehicles?page_size=2").json()
        second = client.get("/api/v1/fleet/vehicles?page_size=2&page=2").json()
        assert first["total"] == second["total"] == 10001
        ids = [item["id"] for item in first["items"] + second["items"]]
        assert len(set(ids)) == 4 and ids == sorted(ids)  # Stable tie breaker.
        assert len(loaded) == 4
        assert client.get("/api/v1/fleet/summary").json()["unknown"] == 10001
        assert client.get("/api/v1/fleet/map").json()["total"] == 10001
        assert len(loaded) == 4  # Summary and markers never load vehicle ORM objects.
    finally:
        event.remove(app.state.sessions, "loaded_as_persistent", track_load)


def test_sql_search_preserves_unicode_casefold_and_recomputes_on_edits(logged_in):
    app, client = logged_in
    add_fleet(app)
    names = ["Straße", "ﬃ Truck", "ΟΣ", "İstanbul", "ᏣᎳᎩ", "ŁÓDŹ"]
    needles = ["STRASSE", "FFI", "ος", "i\u0307stanbul", "ᏣᎳᎩ".lower(), "łódź"]
    with app.state.sessions() as session:
        source = account_key(app.state.settings.webfleet_account)
        vehicles = [
            Vehicle(source_account=source, external_uid=f"unicode-{i}", name=name)
            for i, name in enumerate(names)
        ]
        session.add_all(vehicles)
        session.flush()
        identity = vehicles[0].id
        session.commit()
    for name, needle in zip(names, needles, strict=True):
        result = client.get("/api/v1/fleet/vehicles", params={"q": needle}).json()
        assert result["total"] == 1 and result["items"][0]["name"] == name
    assert client.get("/api/v1/fleet/vehicles", params={"q": "\x00"}).json()["total"] == 0
    with app.state.sessions() as session:
        vehicle = session.get(Vehicle, identity)
        vehicle.name = "Renamed"
        vehicle.number = "Straße 100%_"
        session.commit()
    result = client.get("/api/v1/fleet/vehicles", params={"q": "STRASSE 100%_"}).json()
    assert result["total"] == 1 and result["items"][0]["name"] == "Renamed"
    assert "search_name" not in result["items"][0]
