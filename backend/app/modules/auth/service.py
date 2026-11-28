import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, Request, Response
from pwdlib import PasswordHash
from pwdlib.exceptions import HashVerificationError, UnknownHashError
from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.errors import ApiError
from app.modules.auth.models import (
    EmailChange,
    LoginSession,
    PasswordReset,
    User,
    normalize_identifier,
)
from app.modules.auth.policies import can_authenticate, can_edit, can_manage_accounts

COOKIE_NAME = "fleet_flow_session"
password_hasher = PasswordHash.recommended()
dummy_hash = password_hasher.hash(secrets.token_urlsafe(32))


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        return password_hasher.verify(password, encoded_hash)
    except (HashVerificationError, UnknownHashError):
        return False


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


def administrator(user: Annotated[User, Depends(current_user)]) -> User:
    if not can_manage_accounts(user.role):
        raise ApiError(403, "FORBIDDEN", "Ta operacja wymaga roli administratora")
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


def revoke_recovery_links(session: Session, user: User) -> None:
    session.execute(delete(PasswordReset).where(PasswordReset.user_id == user.id))
    session.execute(delete(EmailChange).where(EmailChange.user_id == user.id))


def find_user(session: Session, username: str, *, lock=False):
    statement = select(User).where(User.username == normalize_identifier(username))
    if lock:
        statement = statement.with_for_update().execution_options(populate_existing=True)
    return session.scalar(statement)


def find_login_user(session: Session, identifier: str) -> User | None:
    # Keep existing usernames usable even when legacy email data is ambiguous.
    username_matches = User.username == identifier
    matches = session.scalars(
        select(User)
        .where(or_(username_matches, User.email_identifier == identifier))
        .order_by(username_matches.desc())
        .limit(2)
    ).all()
    if matches and (len(matches) == 1 or matches[0].username == identifier):
        return matches[0]
    return None


def lock_user(session: Session, user_id):
    return session.scalar(
        select(User)
        .where(User.id == user_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


def locked_current_user(session: Session, request: Request, user: User) -> User:
    # Authentication, password operations and administration lock the user first.
    locked = lock_user(session, user.id)
    login = session.scalar(
        select(LoginSession)
        .where(
            LoginSession.token_hash == digest(request.cookies.get(COOKIE_NAME, "")),
            LoginSession.user_id == user.id,
        )
        .execution_options(populate_existing=True)
    )
    if (
        not locked
        or not locked.active
        or not can_authenticate(locked.role)
        or not login
        or aware(login.expires_at) <= now_utc()
    ):
        raise ApiError(401, "UNAUTHENTICATED", "Zaloguj się ponownie")
    return locked


def lock_account_changes(session: Session) -> None:
    # Serialize account management across workers, including the CLI, before User locks.
    if session.get_bind().dialect.name == "postgresql":
        session.execute(select(func.pg_advisory_xact_lock(0x464C454554555352)))


def check_identifiers(session: Session, *changed: str | None, except_user=None) -> None:
    identifiers = {normalize_identifier(value) for value in changed if value}
    if not identifiers:
        return
    duplicate = select(User.id).where(
        or_(User.username.in_(identifiers), User.email_identifier.in_(identifiers))
    )
    if except_user is not None:
        duplicate = duplicate.where(User.id != except_user)
    if session.scalar(duplicate.limit(1)) is not None:
        raise ApiError(409, "ACCOUNT_IDENTIFIER_TAKEN", "Login lub adres e-mail jest już używany")


def issue_session(request: Request, response: Response, session: Session, user: User):
    token = secrets.token_urlsafe(32)
    seconds = request.app.state.settings.session_hours * 3600
    session.add(
        LoginSession(
            token_hash=digest(token),
            user_id=user.id,
            expires_at=now_utc() + timedelta(seconds=seconds),
        )
    )
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=seconds,
        httponly=True,
        secure=request.app.state.settings.cookie_secure,
        samesite="strict",
        path="/",
    )
