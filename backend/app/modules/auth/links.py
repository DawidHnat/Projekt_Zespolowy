"""Shared issuance and delivery handling for one-use account links."""

import secrets
from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, Field, SecretStr, field_validator
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.modules.auth.models import AccountActivation, EmailChange, PasswordReset
from app.modules.auth.service import aware, digest, lock_user, now_utc

type AccountLink = AccountActivation | EmailChange | PasswordReset


def valid_password_text(value: SecretStr) -> SecretStr:
    try:
        value.get_secret_value().encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError("Invalid password text") from exc
    return value


type CurrentPassword = Annotated[
    SecretStr, Field(min_length=1, max_length=1024), AfterValidator(valid_password_text)
]
type NewPassword = Annotated[
    SecretStr, Field(min_length=12, max_length=1024), AfterValidator(valid_password_text)
]


class LinkBody(BaseModel):
    token: str = Field(min_length=20, max_length=100)

    @field_validator("token")
    @classmethod
    def valid_token_text(cls, value: str) -> str:
        if not value.isascii():
            raise ValueError("Invalid token text")
        return value


class PasswordLinkBody(LinkBody):
    password: NewPassword


def stage_link(session: Session, link: AccountLink, lifetime: timedelta) -> tuple[str, datetime]:
    # The caller holds the User lock. Monotonic expiry distinguishes concurrent deliveries.
    model, user_id = type(link), link.user_id
    token = secrets.token_urlsafe(32)
    now = now_utc()
    expires_at = now + lifetime
    latest_expiry = session.scalar(
        select(func.max(model.expires_at)).where(model.user_id == user_id)
    )
    if latest_expiry is not None and aware(latest_expiry) >= expires_at:
        expires_at = aware(latest_expiry) + timedelta(microseconds=1)
    session.execute(delete(model).where(model.user_id == user_id, model.expires_at <= now))
    link.token_hash = digest(token)
    link.expires_at = expires_at
    session.add(link)
    return token, expires_at


def settle_delivery(
    session: Session,
    model: type[AccountLink],
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
