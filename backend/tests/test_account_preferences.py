from uuid import uuid4

from fastapi.testclient import TestClient

from app.modules.auth.models import User
from app.modules.auth.service import password_hasher


def _dashboard_value():
    widgets = ["metrics", "map", "activity", "vehicles", "utilization", "trips"]
    item = {"x": 0, "y": 0, "w": 12, "h": 8}
    return {
        "visibleWidgets": widgets,
        "layouts": {
            "dashboard": {
                profile: [
                    {
                        **item,
                        "x": 0,
                        "w": 12 if profile == "desktop" else 1,
                        "i": widget,
                    }
                    for widget in widgets
                ]
                for profile in ("desktop", "compact")
            }
        },
    }


def _login(client, username):
    return client.post(
        "/api/v1/auth/login",
        headers={"Origin": "http://127.0.0.1:5173"},
        json={"username": username, "password": "synthetic-test-password"},
    )


def _origin():
    return {"Origin": "http://127.0.0.1:5173"}


def test_preferences_are_private_per_user_and_module(logged_in):
    app, client = logged_in
    with app.state.sessions() as session:
        session.add(
            User(
                id=uuid4(),
                username="other-user",
                display_name="Other",
                role="editor",
                password_hash=password_hasher.hash("synthetic-test-password"),
            )
        )
        session.commit()

    dashboard = _dashboard_value()
    saved = client.put(
        "/api/v1/preferences/dashboard",
        headers=_origin(),
        json={"version": 0, "value": dashboard},
    )
    assert saved.status_code == 200 and saved.json()["version"] == 1
    assert client.get("/api/v1/preferences/vehicles").json()["value"] is None

    other = TestClient(app)
    try:
        assert _login(other, "other-user").status_code == 200
        assert other.get("/api/v1/preferences/dashboard").json() == {
            "module": "dashboard",
            "version": 0,
            "value": None,
            "updated_at": None,
        }
        assert (
            other.put(
                "/api/v1/preferences/dashboard",
                headers=_origin(),
                json={"version": 0, "value": dashboard},
            ).status_code
            == 200
        )
    finally:
        other.close()

    assert client.get("/api/v1/preferences/dashboard").json()["version"] == 1


def test_preference_writes_use_compare_and_swap_for_two_browsers(logged_in):
    app, first = logged_in
    second = TestClient(app)
    try:
        assert _login(second, "test-user").status_code == 200
        initial = first.get("/api/v1/preferences/dashboard").json()
        assert second.get("/api/v1/preferences/dashboard").json()["version"] == 0

        payload = {"version": initial["version"], "value": _dashboard_value()}
        assert (
            first.put(
                "/api/v1/preferences/dashboard",
                headers=_origin(),
                json=payload,
            ).json()["version"]
            == 1
        )

        conflict = second.put(
            "/api/v1/preferences/dashboard",
            headers=_origin(),
            json=payload,
        )
        assert conflict.status_code == 409
        assert conflict.json()["error"]["code"] == "VERSION_CONFLICT"
        latest = second.get("/api/v1/preferences/dashboard").json()
        assert latest["version"] == 1
        assert latest["value"] == _dashboard_value()

        saved = second.put(
            "/api/v1/preferences/dashboard",
            headers=_origin(),
            json={"version": latest["version"], "value": _dashboard_value()},
        )
        assert saved.status_code == 200 and saved.json()["version"] == 2
    finally:
        second.close()


def test_preference_endpoint_requires_auth_and_rejects_invalid_values(logged_in):
    _, client = logged_in
    assert client.get("/api/v1/preferences/dashboard").status_code == 200
    assert client.get("/api/v1/preferences/unsupported").status_code == 422
    response = client.put(
        "/api/v1/preferences/dashboard",
        headers=_origin(),
        json={"version": 0, "value": {"visibleWidgets": ["unknown"], "layouts": {}}},
    )
    assert response.status_code == 422


def test_preference_writes_require_an_allowed_origin_and_do_not_mutate(logged_in):
    _, client = logged_in
    payload = {"version": 0, "value": _dashboard_value()}

    for headers in ({}, {"Origin": "https://foreign.example"}):
        response = client.put(
            "/api/v1/preferences/dashboard",
            headers=headers,
            json=payload,
        )
        assert response.status_code == 403

    assert client.get("/api/v1/preferences/dashboard").json()["version"] == 0
    saved = client.put(
        "/api/v1/preferences/dashboard",
        headers=_origin(),
        json=payload,
    )
    assert saved.status_code == 200
    assert saved.json()["version"] == 1


def test_unbounded_integer_dimensions_are_rejected_without_mutation(logged_in):
    _, client = logged_in
    huge = 10**400
    dashboard = _dashboard_value()
    dashboard["layouts"]["dashboard"]["desktop"][0]["x"] = huge
    response = client.put(
        "/api/v1/preferences/dashboard",
        headers=_origin(),
        json={"version": 0, "value": dashboard},
    )
    assert response.status_code == 422
    assert client.get("/api/v1/preferences/dashboard").json()["version"] == 0

    vehicle_id = "11111111-1111-4111-8111-111111111111"
    vehicles = {
        "layout": {
            "version": 2,
            "defaultSize": {"width": 320, "height": 480},
            "sizes": {vehicle_id: {"width": 320, "height": -huge}},
        },
        "sort": "name-asc",
        "filters": {"q": "", "status": ""},
        "pageSize": 25,
    }
    response = client.put(
        "/api/v1/preferences/vehicles",
        headers=_origin(),
        json={"version": 0, "value": vehicles},
    )
    assert response.status_code == 422
    assert client.get("/api/v1/preferences/vehicles").json()["version"] == 0


def test_dashboard_preferences_accept_account_appearance_and_map_layouts(logged_in):
    _, client = logged_in
    value = _dashboard_value()
    value.update(
        {
            "theme": "dark",
            "accent": "#123456",
            "material": "solid",
            "background": {
                "kind": "custom",
                "preset": "city",
                "veil": 28,
                "blur": 0,
                "customId": str(uuid4()),
            },
        }
    )
    map_widgets = ["map", "vehicles"]
    value["layouts"]["map"] = {
        profile: [
            {
                "i": widget,
                "x": index * 6 if profile == "desktop" else 0,
                "y": 0,
                "w": 6 if profile == "desktop" else 1,
                "h": 12,
            }
            for index, widget in enumerate(map_widgets)
        ]
        for profile in ("desktop", "compact")
    }

    saved = client.put(
        "/api/v1/preferences/dashboard",
        headers=_origin(),
        json={"version": 0, "value": value},
    )
    assert saved.status_code == 200
    assert saved.json()["value"] == value

    invalid = {**value, "layouts": {**value["layouts"]}}
    invalid["layouts"]["map"] = {
        "desktop": [{"i": "metrics", "x": 0, "y": 0, "w": 6, "h": 12}],
        "compact": [{"i": "metrics", "x": 0, "y": 0, "w": 1, "h": 12}],
    }
    response = client.put(
        "/api/v1/preferences/dashboard",
        headers=_origin(),
        json={"version": 1, "value": invalid},
    )
    assert response.status_code == 422
    assert client.get("/api/v1/preferences/dashboard").json()["version"] == 1


def test_custom_background_is_private_bounded_and_deletable(logged_in):
    app, client = logged_in
    image_id = uuid4()
    image = b"RIFF" + (8).to_bytes(4, "little") + b"WEBP"
    headers = {**_origin(), "Content-Type": "image/webp"}
    uploaded = client.put(
        f"/api/v1/preferences/background/{image_id}",
        headers=headers,
        content=image,
    )
    assert uploaded.status_code == 200
    assert uploaded.json() == {"id": str(image_id)}

    downloaded = client.get(f"/api/v1/preferences/background/{image_id}")
    assert downloaded.status_code == 200
    assert downloaded.headers["content-type"] == "image/webp"
    assert downloaded.content == image

    with app.state.sessions() as session:
        session.add(
            User(
                id=uuid4(),
                username="other-background-user",
                display_name="Other",
                role="editor",
                password_hash=password_hasher.hash("synthetic-test-password"),
            )
        )
        session.commit()
    other = TestClient(app)
    try:
        assert _login(other, "other-background-user").status_code == 200
        assert other.get(f"/api/v1/preferences/background/{image_id}").status_code == 404
        assert (
            other.put(
                f"/api/v1/preferences/background/{image_id}",
                headers=headers,
                content=image,
            ).status_code
            == 409
        )
    finally:
        other.close()

    assert (
        client.delete(
            f"/api/v1/preferences/background/{image_id}",
            headers=_origin(),
        ).status_code
        == 204
    )
    assert client.get(f"/api/v1/preferences/background/{image_id}").status_code == 404


def test_custom_background_rejects_wrong_content_and_oversized_upload_without_mutation(logged_in):
    _, client = logged_in
    image_id = uuid4()
    wrong_type = client.put(
        f"/api/v1/preferences/background/{image_id}",
        headers={**_origin(), "Content-Type": "image/png"},
        content=b"not-webp",
    )
    assert wrong_type.status_code == 415

    oversized = client.put(
        f"/api/v1/preferences/background/{image_id}",
        headers={**_origin(), "Content-Type": "image/webp"},
        content=b"RIFF" + (8).to_bytes(4, "little") + b"WEBP" + b"x" * (8 * 1024 * 1024),
    )
    assert oversized.status_code == 413
    assert client.get(f"/api/v1/preferences/background/{image_id}").status_code == 404
