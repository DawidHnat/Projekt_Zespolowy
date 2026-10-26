import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.engine import make_url

from app.core.settings import Settings
from app.main import create_app
from app.modules.auth import profile
from app.modules.auth.models import LoginSession, PasswordReset, User
from app.modules.auth.service import (
    COOKIE_NAME,
    current_user,
    digest,
    now_utc,
    password_hasher,
)

ORIGIN = {"Origin": "http://127.0.0.1:5173"}
OLD = "synthetic-test-password"
NEW = "synthetic-new-profile-password"


def login(client, password=OLD, username="test-user"):
    return client.post(
        "/api/v1/auth/login", headers=ORIGIN, json={"username": username, "password": password}
    )


def change(client, **fields):
    return client.post(
        "/api/v1/auth/password/change",
        headers=ORIGIN,
        json={"current_password": OLD, "new_password": NEW, **fields},
    )


def test_profile_is_own_read_only_data_and_requires_a_session(application):
    app, client = application
    assert client.get("/api/v1/auth/profile").status_code == 401
    assert login(client).status_code == 200
    with app.state.sessions() as session:
        user = session.scalar(select(User))
        user.email, user.role = "owner@example.com", "viewer"
        session.commit()
    response = client.get("/api/v1/auth/profile?user_id=someone-else")
    assert response.json() == {
        "username": "test-user",
        "display_name": "Osoba testowa",
        "email": "owner@example.com",
        "role": "viewer",
    }
    assert set(response.json()) == {"username", "display_name", "email", "role"}
    assert "no-store" in response.headers["cache-control"]
    assert (
        client.patch(
            "/api/v1/auth/profile", headers=ORIGIN, json={"role": "admin", "active": False}
        ).status_code
        == 405
    )


def test_password_change_rotates_session_revokes_others_and_reset_tokens(logged_in):
    app, client = logged_in
    other = TestClient(app)
    assert login(other).status_code == 200
    old_cookie = client.cookies.get(COOKIE_NAME)
    with app.state.sessions() as session:
        user = session.scalar(select(User))
        session.add(
            PasswordReset(
                token_hash=digest("synthetic-token"),
                user_id=user.id,
                expires_at=now_utc() + timedelta(minutes=10),
            )
        )
        session.add(
            User(
                username="other-user",
                display_name="Other",
                role="viewer",
                password_hash=password_hasher.hash(OLD),
            )
        )
        session.commit()
    independent = TestClient(app)
    assert login(independent, username="other-user").status_code == 200
    response = change(client)
    assert response.status_code == 200 and response.json() == {"ok": True}
    assert "httponly" in response.headers["set-cookie"].lower()
    assert "samesite=strict" in response.headers["set-cookie"].lower()
    assert client.cookies.get(COOKIE_NAME) != old_cookie
    assert client.get("/api/v1/auth/me").status_code == 200
    assert other.get("/api/v1/auth/me").status_code == 401
    assert independent.get("/api/v1/auth/me").status_code == 200
    with app.state.sessions() as session:
        user = session.scalar(select(User).where(User.username == "test-user"))
        assert password_hasher.verify(NEW, user.password_hash)
        assert user.password_hash != NEW
        assert session.scalar(select(PasswordReset)) is None
        assert session.get(LoginSession, digest(old_cookie)) is None
    assert login(TestClient(app), password=OLD).status_code == 401
    assert login(TestClient(app), password=NEW).status_code == 200


def test_bad_current_password_and_origin_do_not_revoke_sessions(logged_in):
    app, client = logged_in
    cookie = client.cookies.get(COOKIE_NAME)
    assert change(client, current_password="wrong-synthetic-password").status_code == 400
    assert client.get("/api/v1/auth/me").status_code == 200
    for path in ("/api/v1/auth/password/change", "/api/v1/auth/sessions/logout-all"):
        for origin in ({}, {"Origin": "https://evil.example"}):
            r = client.post(
                path, headers=origin, json={"current_password": OLD, "new_password": NEW}
            )
            assert r.status_code == 403
    assert client.cookies.get(COOKIE_NAME) == cookie
    with app.state.sessions() as session:
        assert password_hasher.verify(OLD, session.scalar(select(User)).password_hash)


@pytest.mark.parametrize(
    "fields",
    [
        {"new_password": "short"},
        {"new_password": "x" * 1025},
        {"current_password": ""},
        {"current_password": "x" * 1025},
        {"new_password": OLD},
        {"new_password": False},
        {"role": "admin"},
        {"user_id": str(uuid4())},
    ],
)
def test_password_validation_does_not_reflect_secrets(logged_in, fields):
    app, client = logged_in
    r = change(client, **fields)
    assert r.status_code == 422
    assert OLD not in r.text and NEW not in r.text
    with app.state.sessions() as session:
        assert password_hasher.verify(OLD, session.scalar(select(User)).password_hash)


def test_rate_limit_keeps_existing_session_and_password(logged_in):
    _, client = logged_in
    for _ in range(5):
        assert change(client, current_password="wrong-password").status_code == 400
    assert change(client).status_code == 429
    assert client.get("/api/v1/auth/me").status_code == 200


def test_viewer_can_change_own_password_and_logout_every_device(logged_in):
    app, client = logged_in
    with app.state.sessions() as session:
        session.scalar(select(User)).role = "viewer"
        session.commit()
    other = TestClient(app)
    assert login(other).status_code == 200
    assert change(client).status_code == 200
    assert login(other, password=NEW).status_code == 200
    response = client.post("/api/v1/auth/sessions/logout-all", headers=ORIGIN)
    assert response.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401
    assert other.get("/api/v1/auth/profile").status_code == 401
    assert change(other, current_password=NEW).status_code == 401
    assert login(client, password=NEW).status_code == 200


def test_notification_uses_configured_address_and_failures_do_not_undo_change(
    logged_in, monkeypatch
):
    app, client = logged_in
    sent = []
    with app.state.sessions() as session:
        session.scalar(select(User)).email = "owner@example.com"
        session.commit()
    monkeypatch.setattr(
        profile.SmtpSettings,
        "from_environment",
        lambda _: profile.SmtpSettings("sender@example.com", "synthetic"),
    )
    monkeypatch.setattr(
        profile, "send_password_changed", lambda settings, recipient: sent.append(recipient)
    )
    assert change(client).status_code == 200
    assert sent == ["owner@example.com"]

    def fail(*_):
        raise OSError("synthetic-private-smtp-error")

    monkeypatch.setattr(profile, "send_password_changed", fail)
    response = change(client, current_password=NEW, new_password="another-synthetic-password")
    assert response.json() == {"ok": True}
    assert login(TestClient(app), password="another-synthetic-password").status_code == 200
    assert "smtp" not in response.text


def test_missing_email_does_not_attempt_smtp(logged_in, monkeypatch):
    _, client = logged_in

    def unexpected(*_):
        pytest.fail("SMTP must not be called without an account email")

    monkeypatch.setattr(profile, "send_password_changed", unexpected)
    assert change(client).status_code == 200


def test_password_notification_contains_no_credential_or_reset_link(monkeypatch):
    import ssl

    from app.integrations.mail import client as mail

    sent = []

    class FakeSmtp:
        def __init__(self, host, port, *, timeout, context):
            assert port == 465 and context.verify_mode == ssl.CERT_REQUIRED
            assert context.check_hostname

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def login(self, user, password):
            assert user == "sender@example.com" and password == "synthetic-mail-secret"

        def send_message(self, message, *, from_addr, to_addrs):
            assert from_addr == "sender@example.com" and to_addrs == ["owner@example.com"]
            sent.append(message)

    monkeypatch.setattr(mail.smtplib, "SMTP_SSL", FakeSmtp)
    mail.send_password_changed(
        mail.SmtpSettings("sender@example.com", "synthetic-mail-secret"), "owner@example.com"
    )
    assert len(sent) == 1
    assert "zmienione" in sent[0].get_content()
    assert "synthetic-mail-secret" not in str(sent[0])
    assert "token=" not in str(sent[0])


def test_postgres_two_password_changes_with_same_session_have_one_winner():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires an isolated PostgreSQL test database")
    assert make_url(url).database.startswith("fleet_flow_test"), "Refusing a non-test database"
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        env={**os.environ, "DATABASE_URL": url, "SYNC_ENABLED": "false"},
        capture_output=True,
    )
    assert result.returncode == 0, "Failed to initialize isolated test schema"
    app = create_app(Settings(url))
    token = "synthetic-profile-session-" + uuid4().hex
    with app.state.sessions() as session:
        user = User(
            username=uuid4().hex,
            display_name="Test",
            role="editor",
            password_hash=password_hasher.hash(OLD),
        )
        session.add(user)
        session.flush()
        user_id = user.id
        session.add(
            LoginSession(
                token_hash=digest(token), user_id=user.id, expires_at=now_utc() + timedelta(hours=1)
            )
        )
        session.commit()
    barrier = Barrier(2)

    def simultaneous_authenticated_user():
        with app.state.sessions() as session:
            user = session.get(User, user_id)
        barrier.wait(timeout=10)
        return user

    app.dependency_overrides[current_user] = simultaneous_authenticated_user

    def write(index):
        with TestClient(app) as client:
            client.cookies.set(COOKIE_NAME, token)
            return change(client, new_password=f"synthetic-password-{index}").status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(write, range(2))) == [200, 401]
    with app.state.sessions() as session:
        user = session.get(User, user_id)
        assert any(
            password_hasher.verify(f"synthetic-password-{i}", user.password_hash) for i in range(2)
        )
        assert session.get(LoginSession, digest(token)) is None
