import secrets
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field, SecretStr
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.errors import ApiError
from app.modules.auth.models import LoginAttempt, LoginSession, User
from app.modules.auth.service import (
    COOKIE_NAME,
    aware,
    check_origin,
    current_user,
    digest,
    dummy_hash,
    find_user,
    now_utc,
    password_hasher,
    user_payload,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginBody(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: SecretStr = Field(min_length=1, max_length=1024)


def count_attempt(session: Session, key: str):
    now = now_utc()
    # PostgreSQL UPSERT serializes simultaneous attempts for the same bucket.
    if session.bind.dialect.name == "postgresql":
        from sqlalchemy import case
        from sqlalchemy.dialects.postgresql import insert

        statement = insert(LoginAttempt).values(key=key, window_start=now, attempts=1)
        expired = LoginAttempt.window_start <= now - timedelta(minutes=1)
        statement = statement.on_conflict_do_update(
            index_elements=[LoginAttempt.key],
            set_={
                "window_start": case((expired, now), else_=LoginAttempt.window_start),
                "attempts": case((expired, 1), else_=LoginAttempt.attempts + 1),
            },
        ).returning(LoginAttempt.attempts)
        count = session.scalar(statement)
    else:  # Isolated SQLite unit tests, never the deployed application.
        row = session.get(LoginAttempt, key)
        if not row:
            row = LoginAttempt(key=key, window_start=now, attempts=0)
            session.add(row)
        elif aware(row.window_start) <= now - timedelta(minutes=1):
            row.window_start, row.attempts = now, 0
        row.attempts += 1
        count = row.attempts
    session.commit()
    if count > 10:
        raise ApiError(429, "RATE_LIMITED", "Zbyt wiele prób. Spróbuj za minutę")


@router.post("/login", dependencies=[Depends(check_origin)])
def login(
    body: LoginBody,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_session)],
):
    username = body.username.strip().lower()
    count_attempt(session, digest("ip:" + (request.client.host if request.client else "unknown")))
    count_attempt(session, digest("account:" + username))
    user = find_user(session, username)
    valid = password_hasher.verify(
        body.password.get_secret_value(), user.password_hash if user else dummy_hash
    )
    if not valid or not user or not user.active or user.role not in ("admin", "editor", "viewer"):
        raise ApiError(401, "INVALID_CREDENTIALS", "Niepoprawny login lub hasło")
    now = now_utc()
    session.execute(delete(LoginAttempt).where(LoginAttempt.window_start < now - timedelta(days=1)))
    session.execute(delete(LoginSession).where(LoginSession.expires_at <= now))
    previous = request.cookies.get(COOKIE_NAME)
    if previous:
        row = session.get(LoginSession, digest(previous))
        if row:
            session.delete(row)
    token = secrets.token_urlsafe(32)
    seconds = request.app.state.settings.session_hours * 3600
    session.add(
        LoginSession(
            token_hash=digest(token), user_id=user.id, expires_at=now + timedelta(seconds=seconds)
        )
    )
    session.commit()
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=seconds,
        httponly=True,
        secure=request.app.state.settings.cookie_secure,
        samesite="strict",
        path="/",
    )
    return user_payload(user)


@router.get("/me")
def me(user: Annotated[User, Depends(current_user)]):
    return user_payload(user)


@router.post("/logout", dependencies=[Depends(check_origin)])
def logout(request: Request, response: Response, session: Annotated[Session, Depends(get_session)]):
    token = request.cookies.get(COOKIE_NAME)
    if token:
        row = session.get(LoginSession, digest(token))
        if row:
            session.delete(row)
            session.commit()
    response.delete_cookie(
        COOKIE_NAME,
        path="/",
        httponly=True,
        secure=request.app.state.settings.cookie_secure,
        samesite="strict",
    )
    return {"ok": True}
