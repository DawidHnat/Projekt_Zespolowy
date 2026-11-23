from datetime import timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    model_validator,
)
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import ConfigurationError, SmtpSettings, load_environment
from app.core.database import get_session
from app.core.errors import ApiError
from app.integrations.mail.client import SmtpError, send_account_activation
from app.modules.auth.links import PasswordLinkBody, settle_delivery, stage_link
from app.modules.auth.models import AccountActivation, AccountStatus, User, normalize_identifier
from app.modules.auth.policies import Role
from app.modules.auth.router import count_attempt
from app.modules.auth.service import (
    administrator,
    aware,
    check_identifiers,
    check_origin,
    digest,
    dummy_hash,
    lock_account_changes,
    lock_user,
    locked_current_user,
    now_utc,
    password_hasher,
    revoke_recovery_links,
    revoke_sessions,
)

router = APIRouter(prefix="/api/v1", tags=["accounts"])
SessionDep = Annotated[Session, Depends(get_session)]
AdminDep = Annotated[User, Depends(administrator)]
NO_CONTROL_CHARACTERS = r"^[^\x00-\x1f\x7f]+$"


def normalize_username(value: str) -> str:
    normalized = normalize_identifier(value)
    if len(normalized) > 100:
        raise ValueError("Username exceeds the maximum length after normalization")
    return normalized


type Name = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, min_length=1, max_length=60, pattern=NO_CONTROL_CHARACTERS
    ),
]
type Username = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, min_length=1, max_length=100, pattern=NO_CONTROL_CHARACTERS
    ),
    AfterValidator(normalize_username),
]


class CreateAccount(BaseModel):
    model_config = ConfigDict(extra="forbid")
    first_name: Name
    last_name: Name
    username: Username
    email: EmailStr
    role: Role


class AccountVersion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int = Field(ge=1)


class EditAccount(AccountVersion):
    first_name: Name | None = None
    last_name: Name | None = None
    username: Username | None = None
    email: EmailStr | None = None
    role: Role | None = None
    status: AccountStatus | None = None

    @model_validator(mode="after")
    def reject_null_fields(self):
        if any(getattr(self, key) is None for key in self.model_fields_set - {"email"}):
            raise ValueError("Fields other than email cannot be null")
        return self


class ManagedAccount(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    username: str
    first_name: str | None
    last_name: str | None
    display_name: str
    email: str | None
    role: Role
    status: AccountStatus
    needs_activation: bool
    version: int


class AccountsPage(BaseModel):
    items: list[ManagedAccount]
    page: int
    page_size: int
    total: int


def lock_administration(session: Session, request: Request, actor: User) -> None:
    lock_account_changes(session)
    administrator(locked_current_user(session, request, actor))


def get_account_for_update(session: Session, user_id: UUID, version: int) -> User:
    user = lock_user(session, user_id)
    if user is None:
        raise ApiError(404, "ACCOUNT_NOT_FOUND", "Konto nie istnieje")
    if user.version != version:
        raise ApiError(409, "ACCOUNT_VERSION_CONFLICT", "Konto zmieniono. Wczytaj aktualne dane")
    return user


def display_name(first: str | None, last: str | None) -> str:
    value = " ".join(part for part in (first, last) if part)
    if len(value) > 120:
        raise ApiError(422, "VALIDATION_ERROR", "Imię i nazwisko mogą mieć łącznie 120 znaków")
    return value


@router.get("/admin/users", response_model=AccountsPage)
def list_accounts(
    session: SessionDep,
    _: AdminDep,
    page: Annotated[int, Query(ge=1, le=10000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
):
    total = session.scalar(select(func.count()).select_from(User)) or 0
    items = session.scalars(
        select(User).order_by(User.username).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return {"items": items, "page": page, "page_size": page_size, "total": total}


@router.post(
    "/admin/users",
    response_model=ManagedAccount,
    status_code=201,
    dependencies=[Depends(check_origin)],
)
def create_account(body: CreateAccount, request: Request, session: SessionDep, actor: AdminDep):
    lock_administration(session, request, actor)
    check_identifiers(session, body.username, body.email)
    user = User(
        username=body.username,
        email=body.email,
        first_name=body.first_name,
        last_name=body.last_name,
        display_name=display_name(body.first_name, body.last_name),
        role=body.role,
        status=AccountStatus.PENDING,
        needs_activation=True,
        password_hash=dummy_hash,
    )
    session.add(user)
    session.commit()
    return user


@router.patch(
    "/admin/users/{user_id}", response_model=ManagedAccount, dependencies=[Depends(check_origin)]
)
def edit_account(
    user_id: UUID, body: EditAccount, request: Request, session: SessionDep, actor: AdminDep
):
    lock_administration(session, request, actor)
    user = get_account_for_update(session, user_id, body.version)
    changes = body.model_dump(exclude_unset=True, exclude={"version", "status"})
    changes = {key: value for key, value in changes.items() if getattr(user, key) != value}
    status = body.status or user.status
    if user.needs_activation and status == AccountStatus.ACTIVE:
        raise ApiError(409, "ACCOUNT_ACTIVATION_REQUIRED", "Użytkownik musi ustawić pierwsze hasło")
    if not user.needs_activation and status == AccountStatus.PENDING:
        raise ApiError(409, "ACCOUNT_ALREADY_ACTIVATED", "To konto jest już aktywowane")
    if (
        user.active
        and user.role == "admin"
        and (status != AccountStatus.ACTIVE or changes.get("role", user.role) != "admin")
        and not session.scalar(
            select(User.id).where(User.active, User.role == "admin", User.id != user.id).limit(1)
        )
    ):
        raise ApiError(409, "LAST_ADMIN", "Zachowaj co najmniej jednego aktywnego administratora")
    if not changes and status == user.status:
        return user
    check_identifiers(session, changes.get("username"), changes.get("email"), except_user=user.id)
    if status != user.status or changes.keys() & {"username", "email", "role"}:
        revoke_sessions(session, user)
        revoke_recovery_links(session, user)
        session.execute(delete(AccountActivation).where(AccountActivation.user_id == user.id))
    if changes.keys() & {"first_name", "last_name"}:
        user.display_name = display_name(
            changes.get("first_name", user.first_name), changes.get("last_name", user.last_name)
        )
    for field, value in changes.items():
        setattr(user, field, value)
    user.status = status
    user.version += 1
    session.commit()
    return user


@router.post("/admin/users/{user_id}/activation", dependencies=[Depends(check_origin)])
def send_activation(
    user_id: UUID, body: AccountVersion, request: Request, session: SessionDep, actor: AdminDep
):
    # The rate-limit writes commit before the account and User locks are acquired.
    count_attempt(session, digest(f"activation-send-admin:{actor.id}"), limit=10)
    count_attempt(session, digest(f"activation-send-account:{user_id}"), limit=3)
    lock_administration(session, request, actor)
    user = get_account_for_update(session, user_id, body.version)
    if user.status != AccountStatus.PENDING or not user.email:
        raise ApiError(
            409,
            "ACCOUNT_INVITE_UNAVAILABLE",
            "Zaproszenie wymaga oczekującego konta z adresem e-mail",
        )
    try:
        settings = SmtpSettings.from_environment(load_environment())
    except ConfigurationError:
        raise ApiError(
            503, "ACTIVATION_MAIL_UNAVAILABLE", "Skonfiguruj pocztę SMTP i ponów wysyłkę"
        ) from None
    recipient = user.email
    token, expires_at = stage_link(session, AccountActivation(user_id=user_id), timedelta(hours=24))
    session.commit()
    url = request.headers["origin"] + "/#activate-account?token=" + token
    delivered = False
    try:
        send_account_activation(settings, recipient, url)
        delivered = True
    except SmtpError:
        raise ApiError(503, "ACTIVATION_MAIL_FAILED", "Nie udało się wysłać zaproszenia") from None
    finally:
        settle_delivery(session, AccountActivation, user_id, token, expires_at, delivered)
        session.commit()
    return {"ok": True}


@router.post("/auth/activation/confirm", dependencies=[Depends(check_origin)])
def confirm_activation(body: PasswordLinkBody, request: Request, session: SessionDep):
    ip = request.client.host if request.client else "unknown"
    count_attempt(session, digest("activation-confirm:" + ip))
    invalid = ApiError(400, "INVALID_ACTIVATION", "Link aktywacyjny jest niepoprawny lub wygasł")
    token_hash = digest(body.token)
    link = session.get(AccountActivation, token_hash)
    if not link or aware(link.expires_at) <= now_utc():
        raise invalid
    user = lock_user(session, link.user_id)
    link = session.get(AccountActivation, token_hash, populate_existing=True)
    if (
        not user
        or user.status != AccountStatus.PENDING
        or not link
        or aware(link.expires_at) <= now_utc()
    ):
        raise invalid
    user.password_hash = password_hasher.hash(body.password.get_secret_value())
    user.needs_activation = False
    user.status = AccountStatus.ACTIVE
    user.version += 1
    session.execute(delete(AccountActivation).where(AccountActivation.user_id == user.id))
    session.commit()
    return {"ok": True}
