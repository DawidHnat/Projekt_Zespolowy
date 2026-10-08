import secrets
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from pydantic import BaseModel, Field, SecretStr
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import SmtpSettings, load_environment
from app.core.database import get_session
from app.core.errors import ApiError
from app.integrations.mail.client import send_password_reset
from app.modules.auth.models import PasswordReset, User
from app.modules.auth.router import count_attempt
from app.modules.auth.service import (
    aware,
    check_origin,
    digest,
    now_utc,
    password_hasher,
    revoke_sessions,
)

router = APIRouter(
    prefix="/api/v1/auth/password", tags=["auth"], dependencies=[Depends(check_origin)]
)
SessionDep = Annotated[Session, Depends(get_session)]


class RequestReset(BaseModel):
    username: str = Field(min_length=1, max_length=100)


class ConfirmReset(BaseModel):
    token: str = Field(min_length=20, max_length=100)
    password: SecretStr = Field(min_length=12, max_length=1024)


def deliver_reset(app, username, origin):
    try:
        with app.state.sessions() as session:
            user = session.scalar(select(User).where(User.username == username).with_for_update())
            if not user or not user.active or not user.email:
                return
            settings = SmtpSettings.from_environment(load_environment())
            token = secrets.token_urlsafe(32)
            session.execute(delete(PasswordReset).where(PasswordReset.user_id == user.id))
            session.add(
                PasswordReset(
                    token_hash=digest(token),
                    user_id=user.id,
                    expires_at=now_utc() + timedelta(minutes=20),
                )
            )
            recipient = user.email
            session.commit()
        send_password_reset(settings, recipient, origin + "/#reset-password?token=" + token)
    except Exception:
        # Never reveal whether an account exists or log a token/SMTP exception.
        # Users can request another link or ask the local administrator.
        return


@router.post("/request")
def request_reset(
    body: RequestReset, request: Request, background: BackgroundTasks, session: SessionDep
):
    username = body.username.strip().lower()
    try:
        count_attempt(
            session,
            digest("reset-ip:" + (request.client.host if request.client else "unknown")),
            limit=10,
            window_seconds=3600,
        )
        count_attempt(session, digest("reset-account:" + username), limit=3, window_seconds=3600)
    except ApiError:
        return {"ok": True}
    background.add_task(deliver_reset, request.app, username, request.headers["origin"])
    return {"ok": True}


@router.post("/confirm")
def confirm_reset(body: ConfirmReset, request: Request, session: SessionDep):
    count_attempt(
        session, digest("reset-confirm:" + (request.client.host if request.client else "unknown"))
    )
    row = session.scalar(
        select(PasswordReset).where(PasswordReset.token_hash == digest(body.token))
    )
    if not row or aware(row.expires_at) <= now_utc():
        raise ApiError(400, "INVALID_RESET", "Link jest niepoprawny lub wygasł")
    # Consistent lock order with request/delivery: User, then reset token.
    user = session.scalar(select(User).where(User.id == row.user_id).with_for_update())
    row = session.scalar(
        select(PasswordReset)
        .where(PasswordReset.token_hash == digest(body.token))
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if not row or aware(row.expires_at) <= now_utc():
        raise ApiError(400, "INVALID_RESET", "Link jest niepoprawny lub wygasł")
    if not user or not user.active:
        raise ApiError(400, "INVALID_RESET", "Link jest niepoprawny lub wygasł")
    user.password_hash = password_hasher.hash(body.password.get_secret_value())
    revoke_sessions(session, user)
    session.execute(delete(PasswordReset).where(PasswordReset.user_id == user.id))
    session.commit()
    return {"ok": True}
