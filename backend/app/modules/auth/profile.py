from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import SmtpSettings, load_environment
from app.core.database import get_session
from app.core.errors import ApiError
from app.integrations.mail.client import send_password_changed
from app.modules.auth.models import LoginSession, PasswordReset, User
from app.modules.auth.router import count_attempt
from app.modules.auth.service import (
    COOKIE_NAME,
    aware,
    check_origin,
    current_user,
    digest,
    issue_session,
    now_utc,
    password_hasher,
    revoke_sessions,
)

router = APIRouter(prefix="/api/v1/auth", tags=["profile"])
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[User, Depends(current_user)]


class ChangePassword(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: SecretStr = Field(min_length=1, max_length=1024)
    new_password: SecretStr = Field(min_length=12, max_length=1024)


def locked_current_user(session, request, user):
    # Same lock order as password reset: user, then session/token. Login also locks User.
    locked = session.scalar(
        select(User)
        .where(User.id == user.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    token = request.cookies.get(COOKIE_NAME, "")
    login = session.scalar(
        select(LoginSession)
        .where(
            LoginSession.token_hash == digest(token),
            LoginSession.user_id == user.id,
        )
        .execution_options(populate_existing=True)
    )
    if (
        not locked
        or not locked.active
        or locked.role not in ("admin", "editor", "viewer")
        or not login
        or aware(login.expires_at) <= now_utc()
    ):
        raise ApiError(401, "UNAUTHENTICATED", "Zaloguj się ponownie")
    return locked


def notify_password_changed(recipient):
    if not recipient:
        return
    try:
        settings = SmtpSettings.from_environment(load_environment())
        send_password_changed(settings, recipient)
    except Exception:
        # Notification failure must not undo a successful password change or expose SMTP data.
        return


@router.get("/profile")
def profile(user: UserDep):
    return {
        "username": user.username,
        "display_name": user.display_name,
        "email": user.email,
        "role": user.role,
    }


@router.post("/password/change", dependencies=[Depends(check_origin)])
def change_password(
    body: ChangePassword,
    request: Request,
    response: Response,
    background: BackgroundTasks,
    session: SessionDep,
    user: UserDep,
):
    # Counters commit before locking the user; rate limits must not release a held User lock.
    count_attempt(
        session, digest("password-change-user:" + str(user.id)), limit=5, window_seconds=900
    )
    count_attempt(
        session,
        digest("password-change-ip:" + (request.client.host if request.client else "unknown")),
        limit=10,
        window_seconds=900,
    )
    locked = locked_current_user(session, request, user)
    current = body.current_password.get_secret_value()
    new = body.new_password.get_secret_value()
    if not password_hasher.verify(current, locked.password_hash):
        raise ApiError(400, "INVALID_CURRENT_PASSWORD", "Niepoprawne aktualne hasło")
    if new == current:
        raise ApiError(422, "PASSWORD_UNCHANGED", "Wybierz inne nowe hasło")
    locked.password_hash = password_hasher.hash(new)
    revoke_sessions(session, locked)
    session.execute(delete(PasswordReset).where(PasswordReset.user_id == locked.id))
    issue_session(request, response, session, locked)
    recipient = locked.email
    session.commit()
    background.add_task(notify_password_changed, recipient)
    return {"ok": True}


@router.post("/sessions/logout-all", dependencies=[Depends(check_origin)])
def logout_all(request: Request, response: Response, session: SessionDep, user: UserDep):
    locked = locked_current_user(session, request, user)
    revoke_sessions(session, locked)
    session.commit()
    response.delete_cookie(
        COOKIE_NAME,
        path="/",
        httponly=True,
        secure=request.app.state.settings.cookie_secure,
        samesite="strict",
    )
    return {"ok": True}
