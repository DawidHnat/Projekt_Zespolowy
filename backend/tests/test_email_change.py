from datetime import timedelta
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.integrations.mail import client as mail
from app.modules.auth import profile
from app.modules.auth.models import EmailChange, PasswordReset, User
from app.modules.auth.service import COOKIE_NAME, aware, digest, now_utc, password_hasher

ORIGIN = {"Origin": "http://127.0.0.1:5173"}
PROFILE = "/api/v1/auth/profile"
REQUEST = "/api/v1/auth/email/change/request"
CONFIRM = "/api/v1/auth/email/change/confirm"
PASSWORD = "synthetic-test-password"
OLD_EMAIL = "old-address@example.com"
NEW_EMAIL = "new-address@example.com"


def login(client, username="test-user"):
    return client.post(
        "/api/v1/auth/login", headers=ORIGIN, json={"username": username, "password": PASSWORD}
    )


def request_change(client, email=NEW_EMAIL, *, password=PASSWORD, headers=ORIGIN):
    return client.post(
        REQUEST, headers=headers, json={"current_password": password, "new_email": email}
    )


def confirm(client, token, *, headers=ORIGIN):
    return client.post(CONFIRM, headers=headers, json={"token": token})


def token_from(delivery):
    return parse_qs(urlsplit(delivery[1]).fragment.partition("?")[2])["token"][0]


@pytest.fixture
def email_change(logged_in, monkeypatch):
    app, client = logged_in
    with app.state.sessions() as session:
        owner = session.scalar(select(User))
        owner.email = OLD_EMAIL
        owner.first_name = "Anna"
        owner.last_name = "Próba"
        owner.role = "viewer"
        session.commit()
    sent = []
    monkeypatch.setattr(
        profile,
        "load_environment",
        lambda: {"SMTP_USERNAME": "sender@example.com", "SMTP_PASSWORD": "synthetic"},
    )
    monkeypatch.setattr(
        profile, "send_email_confirmation", lambda _, to, url: sent.append((to, url))
    )
    monkeypatch.setattr(profile, "send_password_changed", lambda *_: None)
    return app, client, sent


def test_email_change_requires_new_mailbox_and_same_accounts_session(email_change):
    app, owner, sent = email_change
    other_device = TestClient(app)
    stranger = TestClient(app)
    signed_out = TestClient(app)
    assert login(other_device, OLD_EMAIL).status_code == 200
    with app.state.sessions() as session:
        user = session.scalar(select(User))
        session.add(
            PasswordReset(
                token_hash=digest("synthetic-reset-token"),
                user_id=user.id,
                expires_at=now_utc() + timedelta(minutes=10),
            )
        )
        session.add(
            User(
                username="other-user",
                display_name="Other",
                role="viewer",
                password_hash=password_hasher.hash(PASSWORD),
            )
        )
        session.commit()
    assert login(stranger, "other-user").status_code == 200

    response = request_change(owner)
    assert response.status_code == 200 and response.json() == {"ok": True}
    [(recipient, link)] = sent
    assert recipient == NEW_EMAIL and link.startswith(ORIGIN["Origin"] + "/#confirm-email?")
    token = token_from(sent[0])
    with app.state.sessions() as session:
        pending = session.get(EmailChange, digest(token))
        assert pending.new_email == NEW_EMAIL
        assert pending.account_version == 1
        assert (
            timedelta(minutes=19) < aware(pending.expires_at) - now_utc() <= timedelta(minutes=20)
        )
        assert session.get(EmailChange, token) is None
    assert login(signed_out, NEW_EMAIL).status_code == 401
    assert confirm(signed_out, token).status_code == 401
    assert confirm(stranger, token).status_code == 400
    assert confirm(other_device, token, headers={}).status_code == 403
    assert owner.get(PROFILE).json()["email"] == OLD_EMAIL

    cookie = other_device.cookies.get(COOKIE_NAME)
    response = confirm(other_device, token)
    assert response.status_code == 200 and response.json() == {"ok": True}
    assert "httponly" in response.headers["set-cookie"].lower()
    assert other_device.cookies.get(COOKIE_NAME) != cookie
    data = other_device.get(PROFILE).json()
    assert (data["email"], data["role"], data["first_name"], data["last_name"]) == (
        NEW_EMAIL,
        "viewer",
        "Anna",
        "Próba",
    )
    assert confirm(other_device, token).status_code == 400
    assert owner.get(PROFILE).status_code == 401
    assert stranger.get(PROFILE).status_code == 200
    assert login(signed_out, OLD_EMAIL).status_code == 401
    assert login(signed_out, NEW_EMAIL).status_code == 200
    with app.state.sessions() as session:
        assert session.scalar(select(EmailChange)) is None
        assert session.scalar(select(PasswordReset)) is None
        assert session.scalar(select(User.version).where(User.username == "test-user")) == 2


@pytest.mark.parametrize("stored_format", ["invalid-argon2", "unsupported-hash"])
def test_malformed_stored_password_hash_rejects_email_change(email_change, stored_format):
    app, owner, sent = email_change
    with app.state.sessions() as session:
        user = session.scalar(select(User))
        if stored_format == "unsupported-hash":
            user.password_hash = "not-a-supported-hash"
        else:
            hash_parts = user.password_hash.split("$")
            hash_parts[-2] = "invalid%base64"
            user.password_hash = "$".join(hash_parts)
        session.commit()

    cookie = owner.cookies.get(COOKIE_NAME)
    response = request_change(owner)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_CURRENT_PASSWORD"
    assert "set-cookie" not in response.headers
    assert owner.cookies.get(COOKIE_NAME) == cookie
    assert owner.get(PROFILE).json()["email"] == OLD_EMAIL
    assert not sent
    with app.state.sessions() as session:
        assert session.scalar(select(EmailChange)) is None


def test_request_checks_origin_current_password_and_throttles_without_sending(email_change):
    app, owner, sent = email_change
    assert request_change(TestClient(app)).status_code == 401
    assert (
        request_change(owner, headers={"Origin": "https://outside.example.com"}).status_code == 403
    )
    invalid = request_change(owner, "invalid-address")
    assert invalid.status_code == 422 and PASSWORD not in invalid.text
    for _ in range(3):
        response = request_change(owner, password="wrong-synthetic-password")
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_CURRENT_PASSWORD"
    assert request_change(owner).status_code == 429
    assert sent == []
    assert owner.get(PROFILE).json()["email"] == OLD_EMAIL


def test_request_rejects_same_email_case_insensitively(email_change):
    _, owner, sent = email_change
    response = request_change(owner, OLD_EMAIL.upper())
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMAIL_UNCHANGED"
    assert sent == []


def test_expired_or_replaced_links_leave_existing_address_intact(email_change):
    app, owner, sent = email_change
    assert request_change(owner).status_code == 200
    expired = token_from(sent[-1])
    with app.state.sessions() as session:
        session.get(EmailChange, digest(expired)).expires_at = now_utc() - timedelta(seconds=1)
        session.commit()
    response = confirm(owner, expired)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_EMAIL_CONFIRMATION"
    assert request_change(owner).status_code == 200
    first = token_from(sent[-1])
    assert request_change(owner, "replacement@example.com").status_code == 200
    assert confirm(owner, first).status_code == 400
    assert owner.get(PROFILE).json()["email"] == OLD_EMAIL
    assert confirm(owner, token_from(sent[-1])).status_code == 200
    assert owner.get(PROFILE).json()["email"] == "replacement@example.com"


def test_missing_config_or_smtp_failure_preserves_previous_link(email_change, monkeypatch):
    app, owner, sent = email_change
    assert request_change(owner).status_code == 200
    token = token_from(sent[0])
    with monkeypatch.context() as unconfigured:
        unconfigured.setattr(profile, "load_environment", dict)
        response = request_change(owner, "another@example.com")
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "EMAIL_CONFIRMATION_UNAVAILABLE"
        assert len(sent) == 1

    def fail(*_):
        raise mail.SmtpError("private synthetic transport error")

    monkeypatch.setattr(profile, "send_email_confirmation", fail)
    response = request_change(owner, "another@example.com")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "EMAIL_CONFIRMATION_FAILED"
    assert "private synthetic" not in response.text
    assert owner.get(PROFILE).json()["email"] == OLD_EMAIL
    with app.state.sessions() as session:
        assert session.scalars(select(EmailChange.token_hash)).all() == [digest(token)]
    assert confirm(owner, token).status_code == 200


@pytest.mark.parametrize("duplicate", [{"username": NEW_EMAIL}, {"email": NEW_EMAIL.upper()}])
def test_email_confirmation_rechecks_login_and_email_collisions(email_change, duplicate):
    app, owner, sent = email_change
    assert request_change(owner).status_code == 200
    fields = {"username": "competing-account", **duplicate}
    with app.state.sessions() as session:
        session.add(
            User(
                **fields,
                display_name="Other",
                role="viewer",
                password_hash=password_hasher.hash(PASSWORD),
            )
        )
        session.commit()
    response = confirm(owner, token_from(sent[0]))
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ACCOUNT_IDENTIFIER_TAKEN"
    assert owner.get(PROFILE).json()["email"] == OLD_EMAIL


def test_password_change_invalidates_a_pending_email_link(email_change):
    app, owner, sent = email_change
    assert request_change(owner).status_code == 200
    response = owner.post(
        "/api/v1/auth/password/change",
        headers=ORIGIN,
        json={"current_password": PASSWORD, "new_password": "synthetic-new-password"},
    )
    assert response.status_code == 200
    assert confirm(owner, token_from(sent[0])).status_code == 400
    assert owner.get(PROFILE).json()["email"] == OLD_EMAIL
    with app.state.sessions() as session:
        assert session.scalar(select(EmailChange)) is None


def test_confirmation_mail_addresses_new_mailbox_without_password(monkeypatch):
    sent = []
    link = "https://localhost/#confirm-email?token=synthetic-confirmation-token"
    monkeypatch.setattr(
        mail, "_send", lambda _, recipient, message: sent.append((recipient, message))
    )
    mail.send_email_confirmation(
        mail.SmtpSettings("sender@example.com", "synthetic-mail-secret"), NEW_EMAIL, link
    )
    [(recipient, message)] = sent
    assert recipient == message["To"] == NEW_EMAIL
    assert message["From"] == "sender@example.com"
    assert link in message.get_content()
    assert "20 minut" in message.get_content()
    assert OLD_EMAIL not in str(message) and "synthetic-mail-secret" not in str(message)
