from datetime import timedelta
from urllib.parse import parse_qs, urlsplit

from sqlalchemy import select

from app.core.config import SmtpSettings
from app.modules.auth import reset
from app.modules.auth.models import PasswordReset, User
from app.modules.auth.service import now_utc

ORIGIN = {"Origin": "http://127.0.0.1:5173"}


def configure_email(app, monkeypatch):
    sent = []
    with app.state.sessions() as session:
        user = session.scalar(select(User))
        user.email = "owner@example.com"
        session.commit()
    monkeypatch.setattr(
        reset.SmtpSettings,
        "from_environment",
        lambda _: SmtpSettings("sender@example.com", "synthetic"),
    )
    monkeypatch.setattr(
        reset, "send_password_reset", lambda settings, to, url: sent.append((to, url))
    )
    return sent


def token_from(message):
    return parse_qs(urlsplit(message[1]).fragment.split("?", 1)[1])["token"][0]


def test_reset_is_single_use_and_revokes_sessions(logged_in, monkeypatch):
    app, client = logged_in
    sent = configure_email(app, monkeypatch)
    assert client.post(
        "/api/v1/auth/password/request", headers=ORIGIN, json={"username": "test-user"}
    ).json() == {"ok": True}
    token = token_from(sent[0])
    assert sent[0][0] == "owner@example.com"
    assert sent[0][1].startswith("http://127.0.0.1:5173/#reset-password?token=")
    with app.state.sessions() as session:
        row = session.scalar(select(PasswordReset))
        assert row.token_hash != token
    body = {"token": token, "password": "synthetic-new-password"}
    assert (
        client.post("/api/v1/auth/password/confirm", headers=ORIGIN, json=body).status_code == 200
    )
    assert client.get("/api/v1/auth/me").status_code == 401
    assert (
        client.post("/api/v1/auth/password/confirm", headers=ORIGIN, json=body).status_code == 400
    )
    assert (
        client.post(
            "/api/v1/auth/login",
            headers=ORIGIN,
            json={"username": "test-user", "password": "synthetic-test-password"},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/login",
            headers=ORIGIN,
            json={"username": "test-user", "password": "synthetic-new-password"},
        ).status_code
        == 200
    )


def test_neutral_response_rate_limit_expiry_and_no_external_origin(application, monkeypatch):
    app, client = application
    sent = configure_email(app, monkeypatch)
    for name in ("missing", "test-user", "test-user", "test-user", "test-user"):
        assert client.post(
            "/api/v1/auth/password/request", headers=ORIGIN, json={"username": name}
        ).json() == {"ok": True}
    assert len(sent) == 3
    assert (
        client.post(
            "/api/v1/auth/password/request",
            headers={"Origin": "https://evil.example"},
            json={"username": "test-user"},
        ).status_code
        == 403
    )
    token = token_from(sent[-1])
    with app.state.sessions() as session:
        row = session.scalar(select(PasswordReset))
        row.expires_at = now_utc() - timedelta(seconds=1)
        session.commit()
    result = client.post(
        "/api/v1/auth/password/confirm",
        headers=ORIGIN,
        json={"token": token, "password": "synthetic-long-password"},
    )
    assert result.status_code == 400
    assert (
        client.post(
            "/api/v1/auth/password/confirm",
            headers=ORIGIN,
            json={"token": token, "password": "short"},
        ).status_code
        == 422
    )


def test_delivery_failure_and_missing_email_remain_neutral(application, monkeypatch):
    app, client = application
    assert client.post(
        "/api/v1/auth/password/request", headers=ORIGIN, json={"username": "test-user"}
    ).json() == {"ok": True}
    configure_email(app, monkeypatch)

    def fail(*_):
        raise OSError("synthetic-secret-error")

    monkeypatch.setattr(reset, "send_password_reset", fail)
    response = client.post(
        "/api/v1/auth/password/request", headers=ORIGIN, json={"username": "test-user"}
    )
    assert response.json() == {"ok": True} and "synthetic-secret" not in response.text


def test_postgres_concurrent_reset_allows_exactly_one_use():
    import os
    import secrets
    from concurrent.futures import ThreadPoolExecutor
    from uuid import uuid4

    import pytest
    from fastapi.testclient import TestClient
    from sqlalchemy.engine import make_url

    from app.core.settings import Settings
    from app.main import create_app
    from app.modules.auth.service import digest, password_hasher

    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires an isolated PostgreSQL database")
    assert make_url(url).database.startswith("fleet_flow_test")
    app = create_app(Settings(url))
    token = secrets.token_urlsafe(32)
    with app.state.sessions() as session:
        user = User(
            username="synthetic-reset-" + str(uuid4()),
            display_name="Test",
            role="viewer",
            password_hash=password_hasher.hash("synthetic-original-password"),
        )
        session.add(user)
        session.flush()
        session.add(
            PasswordReset(
                token_hash=digest(token),
                user_id=user.id,
                expires_at=now_utc() + timedelta(minutes=20),
            )
        )
        session.commit()
    with TestClient(app) as client:

        def confirm(_):
            return client.post(
                "/api/v1/auth/password/confirm",
                headers=ORIGIN,
                json={"token": token, "password": "synthetic-new-password"},
            ).status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sorted(pool.map(confirm, range(2))) == [200, 400]


def test_smtp_delivery_uses_tls_and_only_the_account_recipient(monkeypatch):
    import ssl

    from app.integrations.mail import client as mail

    sent = []

    class FakeSmtp:
        def __init__(self, host, port, *, timeout, context):
            assert (
                port == 465 and context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
            )

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def login(self, user, password):
            assert user == "sender@example.com" and password == "synthetic"

        def send_message(self, message, *, from_addr, to_addrs):
            sent.append(message)
            assert from_addr == "sender@example.com" and to_addrs == ["owner@example.com"]
            assert message["To"] == "owner@example.com"

    monkeypatch.setattr(mail.smtplib, "SMTP_SSL", FakeSmtp)
    mail.send_password_reset(
        SmtpSettings("sender@example.com", "synthetic"),
        "owner@example.com",
        "https://app.example/#reset-password?token=synthetic",
    )
    assert len(sent) == 1 and "20 minut" in sent[0].get_content()
