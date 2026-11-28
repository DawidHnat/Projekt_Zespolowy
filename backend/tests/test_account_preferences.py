import base64
import io
import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
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


# Valid 1×1 lossless WebP (widely used feature-detection sample).
VALID_WEBP = base64.b64decode("UklGRhoAAABXRUJQVlA4TA0AAAAvAAAAEAcQERGIiP4HAA==")


def test_custom_background_is_private_bounded_and_deletable(logged_in):
    pytest.importorskip("PIL")
    app, client = logged_in
    image_id = uuid4()
    image = VALID_WEBP
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
    # Stored bytes are a fresh WebP re-encoding, not the uploaded file.
    assert downloaded.content[:4] == b"RIFF" and downloaded.content[8:12] == b"WEBP"

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


def _webp(size=(4, 3), **save):
    from PIL import Image

    output = io.BytesIO()
    Image.new("RGB", size, (20, 120, 230)).save(output, format="WEBP", **save)
    return output.getvalue()


def test_custom_background_is_decoded_reencoded_and_stripped_of_metadata(logged_in):
    PIL = pytest.importorskip("PIL")
    from PIL import Image

    _, client = logged_in
    headers = {**_origin(), "Content-Type": "image/webp"}
    exif = Image.Exif()
    exif[0x010E] = "synthetic description"  # ImageDescription
    exif[0x8825] = {0x0002: (52.0, 13.0, 0.0)}  # GPS block
    original = _webp(exif=exif.tobytes(), icc_profile=b"synthetic-icc")
    with Image.open(io.BytesIO(original)) as check:
        assert check.info.get("exif")  # The fixture really carries metadata.

    image_id = uuid4()
    assert (
        client.put(
            f"/api/v1/preferences/background/{image_id}", headers=headers, content=original
        ).status_code
        == 200
    )
    stored = client.get(f"/api/v1/preferences/background/{image_id}").content
    with Image.open(io.BytesIO(stored)) as result:
        assert result.format == "WEBP" and result.size == (4, 3)
        assert not result.info.get("exif") and not result.info.get("icc_profile")
        assert not result.info.get("xmp")
    assert PIL is not None


@pytest.mark.parametrize(
    "content, status",
    [
        # Valid RIFF/WEBP header followed by garbage: not an image.
        (b"RIFF" + (24).to_bytes(4, "little") + b"WEBPVP8 " + b"\x00" * 16, 415),
        (b"RIFF" + (8).to_bytes(4, "little") + b"WEBP", 415),
    ],
)
def test_custom_background_rejects_corrupt_webp_with_a_valid_header(logged_in, content, status):
    pytest.importorskip("PIL")
    _, client = logged_in
    image_id = uuid4()
    response = client.put(
        f"/api/v1/preferences/background/{image_id}",
        headers={**_origin(), "Content-Type": "image/webp"},
        content=content,
    )
    assert response.status_code == status
    assert client.get(f"/api/v1/preferences/background/{image_id}").status_code == 404


def test_custom_background_rejects_truncated_and_oversized_dimensions(logged_in):
    pytest.importorskip("PIL")
    _, client = logged_in
    headers = {**_origin(), "Content-Type": "image/webp"}
    whole = _webp(size=(64, 64), lossless=True)
    truncated = client.put(
        f"/api/v1/preferences/background/{uuid4()}", headers=headers, content=whole[:-20]
    )
    assert truncated.status_code == 415
    too_wide = client.put(
        f"/api/v1/preferences/background/{uuid4()}", headers=headers, content=_webp(size=(2561, 1))
    )
    assert too_wide.status_code == 413
    assert too_wide.json()["error"]["code"] == "IMAGE_TOO_LARGE"


def test_custom_background_delete_only_removes_the_current_image(logged_in):
    pytest.importorskip("PIL")
    _, client = logged_in
    headers = {**_origin(), "Content-Type": "image/webp"}
    first, second = uuid4(), uuid4()
    assert (
        client.put(
            f"/api/v1/preferences/background/{first}", headers=headers, content=VALID_WEBP
        ).status_code
        == 200
    )
    assert (
        client.put(
            f"/api/v1/preferences/background/{second}", headers=headers, content=VALID_WEBP
        ).status_code
        == 200
    )
    # A stale delete for the replaced image must not remove the current one.
    assert (
        client.delete(f"/api/v1/preferences/background/{first}", headers=_origin()).status_code
        == 404
    )
    assert client.get(f"/api/v1/preferences/background/{second}").status_code == 200


def test_postgres_concurrent_accounts_cannot_share_an_image_id():
    pytest.importorskip("PIL")
    url = os.environ.get("TEST_DATABASE_URL")
    if not url or not url.startswith("postgresql"):
        pytest.skip("PostgreSQL concurrency check")
    from sqlalchemy import create_engine, delete
    from sqlalchemy.engine import make_url
    from sqlalchemy.orm import Session

    from app.core.settings import Settings
    from app.main import create_app
    from app.modules.auth.models import LoginSession
    from app.modules.preferences.models import AccountBackgroundImage

    assert make_url(url).database.startswith("fleet_flow_test")
    import subprocess
    import sys

    # This file runs before the migration tests, so bring the schema up explicitly.
    upgrade = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        env={**os.environ, "DATABASE_URL": url, "SYNC_ENABLED": "false"},
        capture_output=True,
        text=True,
    )
    assert upgrade.returncode == 0, "alembic upgrade head failed"
    engine = create_engine(url)
    suffix = uuid4().hex[:8]
    names = [f"bg-race-{suffix}-{index}" for index in range(2)]
    ids = [uuid4(), uuid4()]
    with Session(engine) as session:
        for user_id, name in zip(ids, names, strict=True):
            session.add(
                User(
                    id=user_id,
                    username=name,
                    display_name=name,
                    role="editor",
                    password_hash=password_hasher.hash("synthetic-test-password"),
                )
            )
        session.commit()
    app = create_app(Settings(database_url=url))
    clients = [TestClient(app) for _ in names]
    try:
        for client, name in zip(clients, names, strict=True):
            assert _login(client, name).status_code == 200
        headers = {**_origin(), "Content-Type": "image/webp"}
        for _ in range(10):
            image_id = uuid4()

            def upload(client, image_id=image_id):
                return client.put(
                    f"/api/v1/preferences/background/{image_id}",
                    headers=headers,
                    content=VALID_WEBP,
                ).status_code

            with ThreadPoolExecutor(max_workers=2) as pool:
                statuses = sorted(pool.map(upload, clients))
            assert statuses == [200, 409], statuses
    finally:
        for client in clients:
            client.close()
        with Session(engine) as session:
            for model, column in (
                (AccountBackgroundImage, AccountBackgroundImage.user_id),
                (LoginSession, LoginSession.user_id),
                (User, User.id),
            ):
                session.execute(delete(model).where(column.in_(ids)))
            session.commit()
        engine.dispose()


def test_migration_0012_account_background_images_blocks_lossy_downgrade():
    import subprocess
    import sys

    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url

    url = os.environ.get("TEST_DATABASE_URL")
    if not url or not url.startswith("postgresql"):
        pytest.skip("PostgreSQL migration check")
    assert make_url(url).database.startswith("fleet_flow_test")
    environment = {**os.environ, "DATABASE_URL": url, "SYNC_ENABLED": "false"}

    def alembic(*args):
        return subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            env=environment,
            capture_output=True,
            text=True,
        )

    engine = create_engine(url)
    user_id = uuid4()
    assert alembic("downgrade", "base").returncode == 0
    assert alembic("upgrade", "head").returncode == 0
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO users (id, username, display_name, password_hash, role, active) "
                    "VALUES (:id, :name, 'Tło', 'synthetic', 'editor', true)"
                ),
                {"id": user_id, "name": f"bg-downgrade-{user_id.hex[:8]}"},
            )
            conn.execute(
                text(
                    "INSERT INTO account_background_images (user_id, image_id, image, updated_at) "
                    "VALUES (:id, :image_id, :image, now())"
                ),
                {"id": user_id, "image_id": uuid4(), "image": VALID_WEBP},
            )
        failed = alembic("downgrade", "0015_merge_accounts_and_trips")
        assert failed.returncode != 0 and "SCRUM-148" in failed.stdout + failed.stderr
        with engine.begin() as conn:
            assert conn.scalar(text("SELECT count(*) FROM account_background_images")) == 1
            conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
        assert alembic("downgrade", "0015_merge_accounts_and_trips").returncode == 0
        assert alembic("upgrade", "head").returncode == 0
    finally:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
        alembic("downgrade", "base")
        alembic("upgrade", "head")
        engine.dispose()
