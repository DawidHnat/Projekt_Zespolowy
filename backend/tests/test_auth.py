from datetime import timedelta

from sqlalchemy import select

from app.modules.auth.models import LoginSession, User
from app.modules.auth.service import COOKIE_NAME, digest, now_utc

ORIGIN = {"Origin": "http://127.0.0.1:5173"}


def test_login_opaque_session_and_logout(logged_in):
    app, client = logged_in
    token = client.cookies.get(COOKIE_NAME)
    with app.state.sessions() as session:
        row = session.scalar(select(LoginSession))
        assert row.token_hash == digest(token)
        assert row.token_hash != token
        user = session.scalar(select(User))
        assert user.password_hash.startswith("$argon2id$")
    assert client.get("/api/v1/auth/me").json()["user"]["username"] == "test-user"
    assert client.post("/api/v1/auth/logout", headers=ORIGIN).status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401
    client.cookies.set(COOKIE_NAME, token)
    assert client.get("/api/v1/auth/me").status_code == 401


def test_expired_and_disabled_accounts(logged_in):
    app, client = logged_in
    with app.state.sessions() as session:
        row = session.scalar(select(LoginSession))
        row.expires_at = now_utc() - timedelta(seconds=1)
        session.commit()
    assert client.get("/api/v1/auth/me").status_code == 401
    with app.state.sessions() as session:
        user = session.scalar(select(User))
        user.active = False
        session.commit()
    response = client.post(
        "/api/v1/auth/login",
        headers=ORIGIN,
        json={"username": "test-user", "password": "synthetic-test-password"},
    )
    assert response.status_code == 401


def test_origin_and_cookie_flags(application):
    _, client = application
    body = {"username": "test-user", "password": "synthetic-test-password"}
    assert client.post("/api/v1/auth/login", json=body).status_code == 403
    assert (
        client.post(
            "/api/v1/auth/login", headers={"Origin": "https://other.example"}, json=body
        ).status_code
        == 403
    )
    response = client.post("/api/v1/auth/login", headers=ORIGIN, json=body)
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie
    assert (
        client.post("/api/v1/auth/logout", headers={"Origin": "https://other.example"}).status_code
        == 403
    )
    assert client.get("/api/v1/auth/me").status_code == 200


def test_unknown_user_bad_password_and_rate_limit(application):
    _, client = application
    one = client.post(
        "/api/v1/auth/login",
        headers=ORIGIN,
        json={"username": "unknown", "password": "synthetic-secret"},
    )
    two = client.post(
        "/api/v1/auth/login",
        headers=ORIGIN,
        json={"username": "test-user", "password": "synthetic-secret"},
    )
    assert one.status_code == two.status_code == 401
    assert one.json() == two.json()
    for _ in range(8):
        assert (
            client.post(
                "/api/v1/auth/login",
                headers=ORIGIN,
                json={"username": "unknown", "password": "wrong"},
            ).status_code
            == 401
        )
    assert (
        client.post(
            "/api/v1/auth/login", headers=ORIGIN, json={"username": "other", "password": "wrong"}
        ).status_code
        == 429
    )


def test_validation_does_not_reflect_password(application):
    _, client = application
    result = client.post(
        "/api/v1/auth/login", headers=ORIGIN, json={"username": "", "password": "do-not-reflect-me"}
    )
    assert result.status_code == 422
    assert "do-not-reflect-me" not in result.text
