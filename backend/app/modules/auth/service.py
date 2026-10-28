import hashlib
import secrets
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Request
from pwdlib import PasswordHash
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.errors import ApiError
from app.modules.auth.models import LoginSession, User
from app.modules.auth.policies import can_authenticate, can_edit

COOKIE_NAME = "fleet_flow_session"
password_hasher = PasswordHash.recommended()
dummy_hash = password_hasher.hash(secrets.token_urlsafe(32))


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def now_utc() -> datetime:
    return datetime.now(UTC)


def aware(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def check_origin(request: Request):
    if request.headers.get("origin") not in request.app.state.settings.origins:
        raise ApiError(403, "FORBIDDEN", "Niedozwolone źródło żądania")


def current_user(request: Request, session: Annotated[Session, Depends(get_session)]) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token or len(token) > 100:
        raise ApiError(401, "UNAUTHENTICATED", "Zaloguj się do Fleet-Flow")
    login = session.get(LoginSession, digest(token))
    if not login or aware(login.expires_at) <= now_utc():
        raise ApiError(401, "UNAUTHENTICATED", "Sesja wygasła — zaloguj się ponownie")
    user = session.get(User, login.user_id)
    if not user or not user.active or not can_authenticate(user.role):
        raise ApiError(401, "UNAUTHENTICATED", "Konto jest niedostępne")
    return user


def editor(
    user: Annotated[User, Depends(current_user)], _: Annotated[None, Depends(check_origin)]
) -> User:
    if not can_edit(user.role):
        raise ApiError(403, "FORBIDDEN", "Ta operacja wymaga uprawnień do edycji")
    return user


def user_payload(user: User):
    return {
        "user": {
            "id": str(user.id),
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role,
        }
    }


def revoke_sessions(session: Session, user: User):
    session.execute(delete(LoginSession).where(LoginSession.user_id == user.id))


def find_user(session: Session, username: str):
    return session.scalar(select(User).where(User.username == username.strip().lower()))
