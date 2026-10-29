from uuid import UUID, uuid4

import pytest
from sqlalchemy import event, select

from app.core.models import Driver, Vehicle
from app.modules.auth.models import User
from app.modules.fleet.sync import account_key

ROOT = "/api/v1/drivers"
ORIGIN = {"Origin": "http://127.0.0.1:5173"}


def create(client, **changes):
    return client.post(
        ROOT,
        headers=ORIGIN,
        json={
            "first_name": "Jan",
            "last_name": "Żółć",
            "identifier": "SYNTHETIC-" + uuid4().hex,
            "phone": "+48 123 456 789",
            "email": "synthetic@example.com",
            "categories": ["B", "C+E"],
            **changes,
        },
    )


def vehicle(app, source=None, name="Syntetyczny pojazd"):
    with app.state.sessions() as session:
        row = Vehicle(
            source_account=source or account_key(app.state.settings.webfleet_account),
            external_uid=uuid4().hex,
            name=name,
        )
        session.add(row)
        session.commit()
        return str(row.id)


def assign(client, driver, identity):
    return client.post(
        f"{ROOT}/{driver['id']}/assignments",
        headers=ORIGIN,
        json={"version": driver["version"], "vehicle_id": identity},
    )


def test_profiles_validation_unicode_identity_and_optimistic_edit(logged_in):
    _, client = logged_in
    first = create(client, identifier="Straße").json()
    assert first["display_name"] == "Jan Żółć" and first["version"] == 1
    assert first["categories"] == ["B", "C+E"] and first["vehicles_total"] == 0
    assert first["first_vehicle"] is None and not first["needs_completion"]
    assert first["compatibility"]["status"] == "not_evaluated"
    assert create(client, identifier="STRASSE").status_code == 409
    assert create(client).status_code == 201  # Shared contact is allowed.
    changed = client.patch(
        f"{ROOT}/{first['id']}",
        headers=ORIGIN,
        json={"version": 1, "last_name": "Nowak", "phone": None, "email": "", "categories": []},
    )
    assert changed.status_code == 200
    assert changed.json()["display_name"] == "Jan Nowak" and changed.json()["version"] == 2
    assert changed.json()["phone"] is None and changed.json()["email"] is None
    assert changed.json()["categories"] == []
    assert (
        client.patch(
            f"{ROOT}/{first['id']}", headers=ORIGIN, json={"version": 1, "last_name": "Obsolete"}
        ).status_code
        == 409
    )
    assert client.get(f"{ROOT}/{first['id']}").json()["last_name"] == "Nowak"


@pytest.mark.parametrize(
    "changes",
    [
        {"first_name": "  "},
        {"last_name": "bad\x00text"},
        {"identifier": ""},
        {"phone": "abc"},
        {"phone": "123"},
        {"phone": "++48 123 456 789"},
        {"phone": "123+456789"},
        {"email": "invalid"},
        {"categories": ["B", "B"]},
        {"categories": ["invented"]},
        {"active": "false"},
        {"source_account": "other"},
        {"pesel": "no-identifiers"},
    ],
)
def test_invalid_profile_is_not_saved_or_reflected(logged_in, changes):
    _, client = logged_in
    response = create(client, **changes)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert client.get(ROOT).json()["total"] == 0


def test_many_to_many_history_deactivation_and_compatibility_pointer(logged_in):
    app, client = logged_in
    car, other_car = vehicle(app), vehicle(app)
    first, second = create(client).json(), create(client).json()
    one = assign(client, first, car)
    assert one.status_code == 201
    first["version"] = one.json()["driver_version"]
    assert assign(client, first, car).status_code == 409
    assert assign(client, first, other_car).status_code == 201
    assert assign(client, second, car).status_code == 201
    first = client.get(f"{ROOT}/{first['id']}").json()
    assert first["vehicles_total"] == 2
    with app.state.sessions() as session:
        assert session.get(Vehicle, UUID(car)).driver_id is None
    history = client.get(f"{ROOT}/{first['id']}/assignments").json()
    assert history["total"] == 2 and all(row["start_known"] for row in history["items"])
    page = client.get(f"{ROOT}/{first['id']}/assignments", params={"page_size": 1}).json()
    assert page["total"] == 2 and len(page["items"]) == 1
    assert client.get(f"{ROOT}/{first['id']}").json()["vehicles_total"] == 2
    closed = client.patch(
        f"{ROOT}/{first['id']}", headers=ORIGIN, json={"version": first["version"], "active": False}
    )
    assert closed.status_code == 200 and closed.json()["vehicles_total"] == 0
    history = client.get(f"{ROOT}/{first['id']}/assignments").json()
    assert history["total"] == 2 and all(
        not row["active"] and row["ended_at"] for row in history["items"]
    )
    with app.state.sessions() as session:
        assert session.get(Vehicle, UUID(car)).driver_id == UUID(second["id"])
        assert session.get(Vehicle, UUID(other_car)).driver_id is None
    resumed = client.patch(
        f"{ROOT}/{first['id']}",
        headers=ORIGIN,
        json={"version": closed.json()["version"], "active": True},
    )
    assert resumed.json()["vehicles_total"] == 0
    assert client.get(f"{ROOT}/{first['id']}/assignments").json()["total"] == 2


def test_close_checks_version_and_preserves_history(logged_in):
    app, client = logged_in
    driver = create(client).json()
    result = assign(client, driver, vehicle(app)).json()
    path = f"{ROOT}/{driver['id']}/assignments/{result['assignment']['id']}/close"
    assert client.patch(path, headers=ORIGIN, json={"version": 1}).status_code == 409
    closed = client.patch(path, headers=ORIGIN, json={"version": result["driver_version"]})
    assert closed.status_code == 200 and not closed.json()["assignment"]["active"]
    assert closed.json()["assignment"]["ended_at"] >= closed.json()["assignment"]["started_at"]
    assert client.get(f"{ROOT}/{driver['id']}/assignments").json()["total"] == 1


def test_search_filters_summary_pagination_and_source_scope(logged_in):
    app, client = logged_in
    first = create(client, first_name="Anna", last_name="Straße").json()
    second = create(client, first_name="Zofia", categories=[]).json()
    assign(client, first, vehicle(app, name="Specjalny pojazd"))
    assert assign(client, second, vehicle(app, source="foreign-source")).status_code == 404
    with app.state.sessions() as session:
        session.add(
            Driver(source_account="foreign-source", display_name="Foreign", identifier="foreign")
        )
        session.commit()
    for query in ("STRASSE", "Specjalny", "+48", "synthetic@example.com"):
        assert client.get(ROOT, params={"q": query}).json()["total"] >= 1
    for query in ("%_", "\x00"):
        assert client.get(ROOT, params={"q": query}).json()["total"] == 0
    assert client.get(ROOT, params={"assigned": True}).json()["total"] == 1
    assert client.get(ROOT, params={"category": "C+E"}).json()["total"] == 1
    assert client.get(ROOT, params={"category": "unsupported"}).status_code == 422
    assert (
        client.get(ROOT, params={"sort": "vehicles_desc"}).json()["items"][0]["id"] == first["id"]
    )
    summary = client.get(ROOT + "/summary").json()
    assert (
        summary["total"],
        summary["active"],
        summary["active_unassigned"],
        summary["active_missing_categories"],
    ) == (2, 2, 1, 1)
    assert summary["assignments_to_check"]["total"] is None
    search = client.post(ROOT + "/search", headers=ORIGIN, json={"q": "STRASSE"})
    assert search.status_code == 200 and search.json()["total"] == 1
    assert search.json()["summary"]["total"] == 1
    assert client.post(ROOT + "/search", json={"q": "contact"}).status_code == 403
    for index in range(25):
        assert create(client, last_name=f"Synthetic {index}").status_code == 201
    selects = []

    def record_query(connection, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            selects.append(1)

    event.listen(app.state.engine, "before_cursor_execute", record_query)
    try:
        one = client.get(ROOT).json()
        first_queries = len(selects)
        two = client.get(ROOT, params={"page": 2}).json()
        second_queries = len(selects) - first_queries
    finally:
        event.remove(app.state.engine, "before_cursor_execute", record_query)
    assert first_queries == second_queries and first_queries <= 8
    assert one["total"] == two["total"] == 27
    assert len(one["items"]) == 25 and len(two["items"]) == 2
    assert {item["id"] for item in one["items"]}.isdisjoint({item["id"] for item in two["items"]})


def test_roles_origin_and_expiry(logged_in):
    app, client = logged_in
    driver = create(client).json()
    assert client.post(ROOT, json={}).status_code == 403
    with app.state.sessions() as session:
        session.scalar(select(User)).role = "viewer"
        session.commit()
    assert client.get(ROOT).status_code == 200
    assert create(client).status_code == 403
    assert (
        client.patch(
            f"{ROOT}/{driver['id']}", headers=ORIGIN, json={"version": 1, "active": False}
        ).status_code
        == 403
    )
    assert assign(client, driver, str(uuid4())).status_code == 403
    client.cookies.clear()
    assert client.get(ROOT).status_code == 401


def test_custom_order_is_global_bounded_and_source_scoped_with_missing_category_filter(logged_in):
    app, client = logged_in
    people = [
        create(client, last_name=name, categories=cats).json()
        for name, cats in (("Alpha", ["B"]), ("Bravo", []), ("Charlie", []), ("Delta", ["C"]))
    ]
    foreign = UUID("53000000-0000-4000-8000-000000000099")
    with app.state.sessions() as session:
        session.add(Driver(id=foreign, source_account="another-source", display_name="Foreign"))
        session.commit()
    order = [str(foreign), people[2]["id"], people[0]["id"]]
    body = {"sort": "custom", "custom_order": order, "page_size": 2}
    first = client.post(f"{ROOT}/search", headers=ORIGIN, json=body).json()
    second = client.post(f"{ROOT}/search", headers=ORIGIN, json={**body, "page": 2}).json()
    assert [p["id"] for p in first["items"] + second["items"]] == [
        people[i]["id"] for i in (2, 0, 1, 3)
    ]
    assert first["summary"]["total"] == 4 and first["summary"]["active_missing_categories"] == 2
    filtered = client.post(
        f"{ROOT}/search", headers=ORIGIN, json={**body, "missing_categories": True}
    ).json()
    assert [p["id"] for p in filtered["items"]] == [people[i]["id"] for i in (2, 1)]
    assert filtered["total"] == 2 and filtered["summary"]["total"] == 2
    assert client.get(ROOT, params={"missing_categories": False}).json()["total"] == 2
    assert (
        client.post(
            f"{ROOT}/search", headers=ORIGIN, json={"custom_order": [people[0]["id"]] * 2}
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"{ROOT}/search",
            headers=ORIGIN,
            json={"custom_order": [str(UUID(int=i + 1)) for i in range(2001)]},
        ).status_code
        == 422
    )
