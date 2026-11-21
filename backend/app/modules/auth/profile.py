from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import ConfigurationError, SmtpSettings, load_environment
from app.core.database import get_session
from app.core.errors import ApiError
from app.integrations.mail.client import SmtpError, send_email_confirmation, send_password_changed
from app.modules.auth.links import (
    CurrentPassword,
    LinkBody,
    NewPassword,
    settle_delivery,
    stage_link,
)
from app.modules.auth.models import EmailChange, User
from app.modules.auth.router import count_attempt
from app.modules.auth.service import (
    COOKIE_NAME,
    aware,
    check_identifiers,
    check_origin,
    current_user,
    digest,
    issue_session,
    lock_account_changes,
    locked_current_user,
    now_utc,
    password_hasher,
    revoke_recovery_links,
    revoke_sessions,
)

router = APIRouter(prefix="/api/v1/auth", tags=["profile"])
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[User, Depends(current_user)]


class ChangePassword(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: CurrentPassword
    new_password: NewPassword


class RequestEmailChange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: CurrentPassword
    new_email: EmailStr


class ConfirmEmailChange(LinkBody):
    model_config = ConfigDict(extra="forbid")


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
        "first_name": user.first_name,
        "last_name": user.last_name,
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
    revoke_recovery_links(session, locked)
    issue_session(request, response, session, locked)
    recipient = locked.email
    session.commit()
    background.add_task(notify_password_changed, recipient)
    return {"ok": True}


@router.post("/email/change/request", dependencies=[Depends(check_origin)])
def request_email_change(
    body: RequestEmailChange, request: Request, session: SessionDep, user: UserDep
):
    ip = request.client.host if request.client else "unknown"
    count_attempt(session, digest(f"email-change-user:{user.id}"), limit=3)
    count_attempt(session, digest(f"email-change-ip:{ip}"), limit=10)
    locked = locked_current_user(session, request, user)
    if not password_hasher.verify(body.current_password.get_secret_value(), locked.password_hash):
        raise ApiError(400, "INVALID_CURRENT_PASSWORD", "Niepoprawne aktualne hasło")
    recipient = body.new_email
    if recipient.lower() == (locked.email or "").strip().lower():
        raise ApiError(409, "EMAIL_UNCHANGED", "Wpisz inny adres e-mail")
    try:
        settings = SmtpSettings.from_environment(load_environment())
    except ConfigurationError:
        raise ApiError(
            503, "EMAIL_CONFIRMATION_UNAVAILABLE", "Wysyłka linku jest niedostępna"
        ) from None

    user_id = locked.id
    link = EmailChange(user_id=user_id, new_email=recipient, account_version=locked.version)
    token, expires_at = stage_link(session, link, timedelta(minutes=20))
    session.commit()
    url = request.headers["origin"] + "/#confirm-email?token=" + token
    delivered = False
    try:
        send_email_confirmation(settings, recipient, url)
        delivered = True
    except SmtpError:
        raise ApiError(503, "EMAIL_CONFIRMATION_FAILED", "Nie udało się wysłać linku") from None
    finally:
        settle_delivery(session, EmailChange, user_id, token, expires_at, delivered)
        session.commit()
    return {"ok": True}


@router.post("/email/change/confirm", dependencies=[Depends(check_origin)])
def confirm_email_change(
    body: ConfirmEmailChange,
    request: Request,
    response: Response,
    session: SessionDep,
    user: UserDep,
):
    count_attempt(session, digest(f"email-confirm-user:{user.id}"))
    # Share the account-write lock with admin operations and the CLI before locking User.
    lock_account_changes(session)
    locked = locked_current_user(session, request, user)
    link = session.scalar(
        select(EmailChange).where(
            EmailChange.token_hash == digest(body.token), EmailChange.user_id == locked.id
        )
    )
    if not link or aware(link.expires_at) <= now_utc() or link.account_version != locked.version:
        raise ApiError(400, "INVALID_EMAIL_CONFIRMATION", "Link jest niepoprawny lub wygasł")
    check_identifiers(session, link.new_email, except_user=locked.id)
    locked.email = link.new_email
    locked.version += 1
    revoke_sessions(session, locked)
    revoke_recovery_links(session, locked)
    issue_session(request, response, session, locked)
    session.commit()
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
