from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, false
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.core.models import Base


def normalize_identifier(value: str) -> str:
    return value.strip().lower()


class AccountStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"


ACCOUNT_STATE_CHECK = (
    "(NOT needs_activation OR NOT active) AND "
    "(disabled_state IS NULL OR "
    "(NOT active AND (disabled_state = 'blocked' OR "
    "(disabled_state = 'pending' AND needs_activation))))"
)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'editor', 'viewer')", name="ck_users_role"),
        CheckConstraint(ACCOUNT_STATE_CHECK, name="ck_users_access_state"),
        CheckConstraint("version >= 1", name="ck_users_version"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    display_name: Mapped[str] = mapped_column(String(120))
    first_name: Mapped[str | None] = mapped_column(String(60))
    last_name: Mapped[str | None] = mapped_column(String(60))
    password_hash: Mapped[str] = mapped_column(String(300))
    role: Mapped[str] = mapped_column(String(20), default="viewer")
    active: Mapped[bool] = mapped_column(default=True)
    disabled_state: Mapped[str | None] = mapped_column(String(10))
    needs_activation: Mapped[bool] = mapped_column(default=False, server_default=false())
    version: Mapped[int] = mapped_column(default=1, server_default="1")
    email: Mapped[str | None] = mapped_column(String(254))
    email_identifier: Mapped[str | None] = mapped_column(String(508), index=True)

    @validates("email")
    def update_email_identifier(self, _: str, email: str | None) -> str | None:
        self.email_identifier = normalize_identifier(email or "") or None
        return email

    @property
    def status(self) -> AccountStatus:
        if self.active:
            return AccountStatus.ACTIVE
        return AccountStatus(self.disabled_state or AccountStatus.INACTIVE)

    @status.setter
    def status(self, value: AccountStatus) -> None:
        self.active = value == AccountStatus.ACTIVE
        self.disabled_state = (
            value if value in (AccountStatus.PENDING, AccountStatus.BLOCKED) else None
        )


class LoginSession(Base):
    __tablename__ = "login_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int]


class PasswordReset(Base):
    __tablename__ = "password_resets"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AccountActivation(Base):
    __tablename__ = "account_activations"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
