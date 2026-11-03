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
        session.add(SyncState(source_account=source, last_success_at=now, error_code="timeout"))
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
    assert geo["source"]["status"] == "degraded"
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
