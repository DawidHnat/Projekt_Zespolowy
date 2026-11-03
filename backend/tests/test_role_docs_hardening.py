from dataclasses import replace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import ConfigurationError
from app.core.settings import Settings
from app.main import create_app
from app.modules.auth.models import User


@pytest.mark.parametrize("role,write_status", [("admin", 404), ("editor", 404), ("viewer", 403)])
def test_existing_role_policy_is_enforced_before_resource_lookup(logged_in, role, write_status):
    app, client = logged_in
    with app.state.sessions() as session:
        user = session.scalar(select(User))
        user.role = role
        session.commit()
    assert client.get("/api/v1/auth/me").json()["user"]["role"] == role
    response = client.patch(
        f"/api/v1/trips/{uuid4()}/annotation",
        headers={"Origin": "http://127.0.0.1:5173"},
        json={"version": 1, "purpose": "synthetic"},
    )
    assert response.status_code == write_status
    assert (
        client.patch(
            f"/api/v1/trips/{uuid4()}/annotation",
            headers={"Origin": "https://untrusted.invalid"},
            json={"version": 1, "purpose": "synthetic"},
        ).status_code
        == 403
    )


def test_unauthenticated_write_is_rejected(application):
    _, client = application
    assert (
        client.patch(
            f"/api/v1/trips/{uuid4()}/annotation",
            headers={"Origin": "http://127.0.0.1:5173"},
            json={"version": 1, "purpose": "synthetic"},
        ).status_code
        == 401
    )


@pytest.mark.parametrize(
    "local,enabled", [(True, True), (True, False), (False, True), (False, False)]
)
def test_docs_routes_are_local_only_even_for_constructed_settings(application, local, enabled):
    original, _ = application
    settings = replace(
        original.state.settings,
        origins=("http://127.0.0.1:5173",) if local else ("https://fleet.example.invalid",),
        cookie_secure=not local,
        api_docs_enabled=enabled,
    )
    app = create_app(settings, engine=original.state.engine)
    with TestClient(app) as client:
        for path in ("/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"):
            assert client.get(path).status_code == (200 if local and enabled else 404)
        assert app.openapi()["paths"]["/api/v1/auth/login"]


@pytest.mark.parametrize(
    "origins,secure,flag,expected",
    [
        ("http://localhost:5173", "false", None, True),
        ("http://127.0.0.1:5173", "false", "false", False),
        ("https://fleet.example.invalid", "true", None, False),
        ("http://localhost:5173,https://fleet.example.invalid", "true", None, False),
        ("https://fleet.example.invalid", "true", "true", None),
        ("http://localhost:5173", "false", "maybe", None),
    ],
)
def test_environment_docs_configuration(monkeypatch, origins, secure, flag, expected):
    values = {
        "DATABASE_URL": "postgresql+psycopg://test@localhost/fleet_flow_test",
        "CORS_ORIGINS": origins,
        "COOKIE_SECURE": secure,
    }
    if flag is not None:
        values["API_DOCS_ENABLED"] = flag
    monkeypatch.setattr("app.core.settings.load_environment", lambda: values)
    if expected is None:
        with pytest.raises(ConfigurationError):
            Settings.from_environment()
    else:
        assert Settings.from_environment().local_api_docs is expected
