import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from urllib.parse import parse_qs, urlsplit
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import make_url

from app.core.config import SmtpSettings
from app.core.models import Base
from app.core.settings import Settings
from app.integrations.mail.client import SmtpError
from app.main import create_app
from app.modules.auth import accounts, profile
from app.modules.auth.models import AccountActivation, LoginAttempt, User
from app.modules.auth.service import aware, digest, now_utc, password_hasher

ORIGIN = {"Origin": "http://127.0.0.1:5173"}
USERS = "/api/v1/admin/users"
ACTIVATE = "/api/v1/auth/activation/confirm"
PASSWORD = "synthetic-test-password"
NEW_PASSWORD = "synthetic-new-account-password"
NEW_USER = {
    "first_name": "Anna",
    "last_name": "Próba",
    "username": "NOWA",
    "email": "new-account@example.com",
    "role": "viewer",
}


def login(client, username, password=PASSWORD):
    return client.post(
        "/api/v1/auth/login", headers=ORIGIN, json={"username": username, "password": password}
    )


def create_account(client, **changes):
    response = client.post(USERS, headers=ORIGIN, json={**NEW_USER, **changes})
    assert response.status_code == 201, response.json()
    return response.json()


def edit_account(client, account, **changes):
    return client.patch(
        f"{USERS}/{account['id']}", headers=ORIGIN, json={"version": account["version"], **changes}
    )


def invite(client, account):
    return client.post(
        f"{USERS}/{account['id']}/activation", headers=ORIGIN, json={"version": account["version"]}
    )


def activate(client, token, headers=ORIGIN):
    return client.post(ACTIVATE, headers=headers, json={"token": token, "password": NEW_PASSWORD})


def token_from(mail):
    fragment = urlsplit(mail[1]).fragment
    return parse_qs(fragment.partition("?")[2])["token"][0]


def add_user(app, username, role, **fields):
    with app.state.sessions() as session:
        user = User(
            username=username,
            display_name=username,
            role=role,
            password_hash=password_hasher.hash(PASSWORD),
            **fields,
        )
        session.add(user)
        session.commit()
        return {"id": str(user.id), "version": user.version}


@pytest.fixture
def messages(monkeypatch):
    sent = []
    monkeypatch.setattr(
        accounts.SmtpSettings,
        "from_environment",
        lambda _: SmtpSettings("sender@example.com", "synthetic"),
    )
    monkeypatch.setattr(
        accounts, "send_account_activation", lambda _, to, url: sent.append((to, url))
    )
    return sent


@pytest.mark.parametrize("role", ["viewer", "editor"])
def test_admin_authorization_applies_to_every_account_operation(application, role):
    app, client = application
    target = add_user(app, "target", "viewer")
    assert client.get(USERS).status_code == 401
    add_user(app, "non-admin", role)
    assert login(client, "non-admin").status_code == 200
    assert client.get(USERS).status_code == 403
    assert client.post(USERS, headers=ORIGIN, json=NEW_USER).status_code == 403
    assert edit_account(client, target, status="blocked").status_code == 403
    assert invite(client, target).status_code == 403


def test_admin_validates_origin_identifiers_and_versions_without_returning_credentials(logged_in):
    _, client = logged_in
    assert client.post(USERS, json=NEW_USER).status_code == 403
    invalid = client.post(USERS, headers=ORIGIN, json={**NEW_USER, "password": PASSWORD})
    assert invalid.status_code == 422 and PASSWORD not in invalid.text
    account = create_account(client)
    assert account["username"] == "nowa"
    assert account["status"] == "pending" and account["needs_activation"]
    assert not {"password", "password_hash", "token", "token_hash"} & account.keys()
    duplicates = (
        {"username": " nowa ", "email": "another@example.com"},
        {"username": "druga", "email": "NEW-ACCOUNT@example.com"},
        {"username": "new-account@example.com", "email": "other@example.com"},
    )
    for fields in duplicates:
        collision = client.post(USERS, headers=ORIGIN, json={**NEW_USER, **fields})
        assert collision.status_code == 409
        assert collision.json()["error"]["code"] == "ACCOUNT_IDENTIFIER_TAKEN"
    updated = edit_account(client, account, first_name="Alicja", role="editor")
    assert updated.status_code == 200
    assert updated.json()["display_name"] == "Alicja Próba"
    assert edit_account(client, account, last_name="Nieaktualne").status_code == 409
    assert edit_account(client, updated.json(), status=None).status_code == 422
    page = client.get(USERS, params={"page": 1, "page_size": 1}).json()
    assert page["total"] == 2 and len(page["items"]) == 1


def test_activation_uses_own_one_time_link_and_allows_login_by_email(logged_in, messages):
    app, admin = logged_in
    user = TestClient(app)
    account = create_account(admin)
    assert messages == []
    for identity in ("nowa", NEW_USER["email"]):
        assert login(user, identity).status_code == 401
    assert edit_account(admin, account, status="active").status_code == 409

    response = invite(admin, account)
    assert response.json() == {"ok": True}
    assert messages[0][0] == NEW_USER["email"]
    assert messages[0][1].startswith("http://127.0.0.1:5173/#activate-account?token=")
    token = token_from(messages[0])
    with app.state.sessions() as session:
        stored = session.get(AccountActivation, digest(token))
        assert stored is not None
        assert timedelta(hours=23) < aware(stored.expires_at) - now_utc() <= timedelta(hours=24)
    assert activate(user, token, {}).status_code == 403
    assert (
        user.post(
            "/api/v1/auth/password/confirm",
            headers=ORIGIN,
            json={"token": token, "password": NEW_PASSWORD},
        ).status_code
        == 400
    )
    assert activate(user, token).status_code == 200
    assert activate(user, token).status_code == 400
    assert login(user, " NEW-ACCOUNT@EXAMPLE.COM ", NEW_PASSWORD).status_code == 200
    assert user.get("/api/v1/auth/me").json()["user"]["username"] == "nowa"


def test_failed_resend_preserves_existing_invitation_and_email_change_invalidates_it(
    logged_in, messages, monkeypatch
):
    app, admin = logged_in
    user = TestClient(app)
    account = create_account(admin)
    assert invite(admin, account).status_code == 200
    first = token_from(messages[-1])

    def fail(*_):
        raise SmtpError("synthetic credential or address")

    monkeypatch.setattr(accounts, "send_account_activation", fail)
    failed = invite(admin, account)
    assert failed.status_code == 503
    assert failed.json()["error"]["code"] == "ACTIVATION_MAIL_FAILED"
    assert "synthetic" not in failed.text
    with app.state.sessions() as session:
        assert session.scalars(select(AccountActivation.token_hash)).all() == [digest(first)]
    updated = edit_account(admin, account, email="changed-address@example.com")
    assert updated.status_code == 200
    assert activate(user, first).status_code == 400


def test_invitation_without_smtp_configuration_leaves_account_available_for_retry(
    logged_in, monkeypatch
):
    app, admin = logged_in
    monkeypatch.setattr(accounts, "load_environment", dict)

    def unexpected_send(*_):
        pytest.fail("Incomplete configuration must stop delivery")

    monkeypatch.setattr(accounts, "send_account_activation", unexpected_send)
    account = create_account(admin)
    response = invite(admin, account)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ACTIVATION_MAIL_UNAVAILABLE"
    with app.state.sessions() as session:
        assert session.scalars(select(AccountActivation)).all() == []
        assert session.get(User, UUID(account["id"])).status == "pending"


def test_successful_resend_replaces_previous_unused_invitation(logged_in, messages):
    app, admin = logged_in
    user = TestClient(app)
    account = create_account(admin)
    assert invite(admin, account).status_code == 200
    assert invite(admin, account).status_code == 200
    assert activate(user, token_from(messages[0])).status_code == 400
    assert activate(user, token_from(messages[1])).status_code == 200


def test_expiry_and_blocked_pending_accounts_require_a_fresh_link(logged_in, messages):
    app, admin = logged_in
    user = TestClient(app)
    account = create_account(admin)
    assert invite(admin, account).status_code == 200
    expired = token_from(messages[-1])
    with app.state.sessions() as session:
        session.get(AccountActivation, digest(expired)).expires_at = now_utc() - timedelta(
            seconds=1
        )
        session.commit()
    assert activate(user, expired).status_code == 400
    assert invite(admin, account).status_code == 200
    replacement = token_from(messages[-1])
    blocked = edit_account(admin, account, status="blocked").json()
    assert blocked["status"] == "blocked"
    assert invite(admin, blocked).status_code == 409
    assert activate(user, replacement).status_code == 400
    assert edit_account(admin, blocked, status="active").status_code == 409


def test_role_and_blocking_revoke_existing_sessions_and_preserve_last_admin(logged_in):
    app, admin = logged_in
    operator = add_user(app, "operator", "editor")
    user = TestClient(app)
    assert login(user, "operator").status_code == 200
    changed = edit_account(admin, operator, role="viewer").json()
    assert user.get("/api/v1/auth/me").status_code == 401
    assert login(user, "operator").json()["user"]["role"] == "viewer"
    assert user.get(USERS).status_code == 403
    assert edit_account(admin, changed, status="blocked").status_code == 200
    assert user.get("/api/v1/auth/me").status_code == 401
    assert login(user, "operator").json() == login(user, "unknown-user").json()
    me = admin.get("/api/v1/auth/me").json()["user"]
    target = {"id": me["id"], "version": 1}
    for change in ({"status": "inactive"}, {"status": "blocked"}, {"role": "editor"}):
        response = edit_account(admin, target, **change)
        assert response.status_code == 409 and response.json()["error"]["code"] == "LAST_ADMIN"
    assert admin.get("/api/v1/auth/me").status_code == 200


def test_email_alias_shares_rate_bucket_and_ambiguous_legacy_email_is_neutral(application):
    app, client = application
    add_user(app, "legacy", "viewer", email="Alias@example.com")
    assert login(client, "alias@example.com", "wrong").status_code == 401
    assert login(client, "legacy", "wrong").status_code == 401
    with app.state.sessions() as session:
        assert session.get(LoginAttempt, digest("account:legacy")).attempts == 2
    add_user(app, "second-legacy", "viewer", email="ALIAS@example.com")
    assert login(client, "alias@example.com").status_code == 401
    assert login(client, "legacy").status_code == 200


def test_admin_email_edit_invalidates_a_pending_self_service_link(logged_in, messages, monkeypatch):
    app, admin = logged_in
    account = add_user(app, "operator", "viewer", email="original@example.com")
    monkeypatch.setattr(
        profile, "send_email_confirmation", lambda _, to, url: messages.append((to, url))
    )
    with TestClient(app) as owner:
        assert login(owner, "operator").status_code == 200
        response = owner.post(
            "/api/v1/auth/email/change/request",
            headers=ORIGIN,
            json={"current_password": PASSWORD, "new_email": "pending@example.com"},
        )
        assert response.status_code == 200
        assert edit_account(admin, account, email="assigned@example.com").status_code == 200
        assert owner.get("/api/v1/auth/me").status_code == 401
        assert login(owner, "operator").status_code == 200
        response = owner.post(
            "/api/v1/auth/email/change/confirm",
            headers=ORIGIN,
            json={"token": token_from(messages[0])},
        )
        assert response.status_code == 400
        assert owner.get("/api/v1/auth/profile").json()["email"] == "assigned@example.com"


@pytest.fixture
def isolated_accounts_app():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires an isolated PostgreSQL database")
    parsed = make_url(url)
    assert parsed.host in ("127.0.0.1", "localhost")
    assert parsed.database.startswith("fleet_flow_test")
    schema = "accounts_" + uuid4().hex
    engine = create_engine(url, execution_options={"schema_translate_map": {None: schema}})
    with engine.begin() as connection:
        connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
    try:
        Base.metadata.create_all(engine)
        yield create_app(Settings(url), engine=engine)
    finally:
        with engine.begin() as connection:
            connection.exec_driver_sql(f'DROP SCHEMA "{schema}" CASCADE')
        engine.dispose()


def test_postgres_unicode_email_uses_the_same_identifier_for_login_and_conflicts(
    isolated_accounts_app,
):
    app = isolated_accounts_app
    add_user(app, "first-admin", "admin")
    email = "İstanbul@example.com"
    owner = add_user(app, "unicode-account", "viewer", email=email)
    with TestClient(app) as admin, TestClient(app) as user:
        assert login(admin, "first-admin").status_code == 200
        assert login(user, email).status_code == 200
        assert login(user, email.lower()).status_code == 200
        for fields in ({"email": email}, {"email": email.lower()}, {"username": email}):
            duplicate = admin.post(USERS, headers=ORIGIN, json={**NEW_USER, **fields})
            assert duplicate.status_code == 409
            assert duplicate.json()["error"]["code"] == "ACCOUNT_IDENTIFIER_TAKEN"

        replacement = "żółć@example.com"
        assert edit_account(admin, owner, email=replacement).status_code == 200
        assert login(user, email).status_code == 401
        assert login(user, replacement.upper()).status_code == 200


def test_postgres_concurrent_admin_changes_cannot_remove_both_admins(isolated_accounts_app):
    app = isolated_accounts_app
    first = add_user(app, "first-admin", "admin")
    second = add_user(app, "second-admin", "admin")
    with TestClient(app) as client:
        other = TestClient(app)
        assert login(client, "first-admin").status_code == 200
        assert login(other, "second-admin").status_code == 200
        with ThreadPoolExecutor(max_workers=2) as workers:
            a = workers.submit(edit_account, client, second, status="blocked")
            b = workers.submit(edit_account, other, first, role="viewer")
            passed, denied = sorted((a.result().status_code, b.result().status_code))
            assert passed == 200 and denied in (401, 403)
        with app.state.sessions() as session:
            assert (
                session.scalar(
                    select(func.count()).select_from(User).where(User.active, User.role == "admin")
                )
                == 1
            )


def test_postgres_concurrent_activation_uses_link_exactly_once(isolated_accounts_app, messages):
    app = isolated_accounts_app
    add_user(app, "first-admin", "admin")
    with TestClient(app) as admin:
        assert login(admin, "first-admin").status_code == 200
        account = create_account(admin)
        assert invite(admin, account).status_code == 200
        token = token_from(messages[-1])
        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(lambda _: activate(TestClient(app), token), range(2)))
        assert sorted(result.status_code for result in results) == [200, 400]
        with app.state.sessions() as session:
            user = session.get(User, UUID(account["id"]))
            assert user.active and not user.needs_activation
            assert session.scalars(select(AccountActivation)).all() == []


@pytest.mark.parametrize("same_account", [True, False], ids=["same-link", "same-address"])
def test_postgres_concurrent_email_confirmation(
    isolated_accounts_app, messages, monkeypatch, same_account
):
    app = isolated_accounts_app
    add_user(app, "first-viewer", "viewer")
    if not same_account:
        add_user(app, "second-viewer", "viewer")
    monkeypatch.setattr(
        profile, "send_email_confirmation", lambda _, to, url: messages.append((to, url))
    )
    email = "verified-address@example.com"

    with TestClient(app) as first, TestClient(app) as second:
        assert login(first, "first-viewer").status_code == 200
        assert login(second, "first-viewer" if same_account else "second-viewer").status_code == 200
        for owner in (first,) if same_account else (first, second):
            response = owner.post(
                "/api/v1/auth/email/change/request",
                headers=ORIGIN,
                json={"current_password": PASSWORD, "new_email": email},
            )
            assert response.status_code == 200
        with ThreadPoolExecutor(max_workers=2) as workers:
            results = [
                workers.submit(
                    owner.post,
                    "/api/v1/auth/email/change/confirm",
                    headers=ORIGIN,
                    json={"token": token_from(message)},
                )
                for owner, message in zip((first, second), (messages[0], messages[-1]), strict=True)
            ]
            assert sorted(result.result().status_code for result in results) == [
                200,
                401 if same_account else 409,
            ]
    with app.state.sessions() as session:
        matches = session.scalars(select(User).where(User.email == email)).all()
        assert len(matches) == 1 and matches[0].version == 2
