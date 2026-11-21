"""Shared issuance and delivery handling for one-use password links."""

import secrets
from datetime import datetime, timedelta
from uuid import UUID

from pydantic import BaseModel, Field, SecretStr, field_validator
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.modules.auth.models import AccountActivation, PasswordReset
from app.modules.auth.service import aware, digest, lock_user, now_utc

type LinkModel = type[AccountActivation] | type[PasswordReset]


class PasswordLinkBody(BaseModel):
    token: str = Field(min_length=20, max_length=100)
    password: SecretStr = Field(min_length=12, max_length=1024)

    @field_validator("token")
    @classmethod
    def valid_token_text(cls, value: str) -> str:
        if not value.isascii():
            raise ValueError("Invalid token text")
        return value

    @field_validator("password")
    @classmethod
    def valid_password_text(cls, value: SecretStr) -> SecretStr:
        try:
            value.get_secret_value().encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ValueError("Invalid password text") from exc
        return value


def stage_link(
    session: Session, model: LinkModel, user_id: UUID, lifetime: timedelta
) -> tuple[str, datetime]:
    # The caller holds the User lock. Monotonic expiry distinguishes concurrent deliveries.
    token = secrets.token_urlsafe(32)
    now = now_utc()
    expires_at = now + lifetime
    latest_expiry = session.scalar(
        select(func.max(model.expires_at)).where(model.user_id == user_id)
    )
    if latest_expiry is not None and aware(latest_expiry) >= expires_at:
        expires_at = aware(latest_expiry) + timedelta(microseconds=1)
    session.execute(delete(model).where(model.user_id == user_id, model.expires_at <= now))
    session.add(model(token_hash=digest(token), user_id=user_id, expires_at=expires_at))
    return token, expires_at


def settle_delivery(
    session: Session,
    model: LinkModel,
    user_id: UUID,
    token: str,
    expires_at: datetime,
    delivered: bool,
) -> None:
    lock_user(session, user_id)
    token_hash = digest(token)
    criteria = (
        (model.token_hash != token_hash, model.expires_at <= expires_at)
        if delivered
        else (model.token_hash == token_hash,)
    )
    session.execute(delete(model).where(model.user_id == user_id, *criteria))
