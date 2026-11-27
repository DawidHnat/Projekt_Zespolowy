import json
import math
import re
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.errors import ApiError
from app.modules.auth.models import User
from app.modules.auth.service import check_origin, current_user
from app.modules.preferences.models import AccountPreference

router = APIRouter(prefix="/api/v1/preferences", tags=["preferences"])
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[User, Depends(current_user)]
MODULES = ("dashboard", "vehicles")
WIDGETS = {"metrics", "map", "activity", "vehicles", "utilization", "trips"}
PROFILES = {"desktop", "compact"}
VEHICLE_ID = re.compile(r"^[a-f\d]{8}-(?:[a-f\d]{4}-){3}[a-f\d]{12}$", re.I)
CARD_SORTS = {"name-asc", "name-desc", "status", "odometer-asc", "odometer-desc"}
VEHICLE_STATUSES = {"moving", "stopped", "offline", "unknown"}
ARCHIVE_SCOPES = {"active", "archived", "all"}
MAX_VALUE_BYTES = 128 * 1024


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _bounded_number(value: Any, minimum: float, maximum: float) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    if isinstance(value, int):
        return minimum <= value <= maximum
    return math.isfinite(value) and minimum <= value <= maximum


def _validate_dashboard(value: dict[str, Any]) -> None:
    if set(value) != {"visibleWidgets", "layouts"}:
        raise ValueError("Invalid dashboard preference fields")
    visible = value["visibleWidgets"]
    if (
        not isinstance(visible, list)
        or len(visible) > len(WIDGETS)
        or len(set(visible)) != len(visible)
        or any(widget not in WIDGETS for widget in visible)
    ):
        raise ValueError("Invalid visible widget list")
    layouts = _object(value["layouts"], "layouts")
    if set(layouts) != {"dashboard"}:
        raise ValueError("Only dashboard layouts are supported")
    section = _object(layouts["dashboard"], "dashboard layout")
    if set(section) != PROFILES:
        raise ValueError("Invalid dashboard profiles")
    for profile, entries in section.items():
        if not isinstance(entries, list) or len(entries) != len(WIDGETS):
            raise ValueError(f"Invalid {profile} layout")
        seen: set[str] = set()
        for entry in entries:
            item = _object(entry, "layout item")
            widget = item.get("i")
            if widget not in WIDGETS or widget in seen:
                raise ValueError("Invalid or duplicate widget ID")
            seen.add(widget)
            for key, lower, upper in (
                ("x", 0, 12),
                ("y", 0, 200),
                ("w", 1, 12),
                ("h", 1, 24),
            ):
                if not _bounded_number(item.get(key), lower, upper):
                    raise ValueError("Invalid widget dimensions")


def _validate_vehicles(value: dict[str, Any]) -> None:
    if set(value) != {"layout", "sort", "filters", "pageSize"}:
        raise ValueError("Invalid vehicle preference fields")
    if value["sort"] not in CARD_SORTS:
        raise ValueError("Invalid vehicle sort")
    if (
        not isinstance(value["pageSize"], int)
        or isinstance(value["pageSize"], bool)
        or value["pageSize"] not in (10, 25, 50, 100)
    ):
        raise ValueError("Invalid vehicle page size")
    filters = _object(value["filters"], "filters")
    if set(filters) not in ({"q", "status"}, {"q", "status", "archive"}):
        raise ValueError("Invalid vehicle filters")
    if not isinstance(filters["q"], str) or len(filters["q"]) > 100:
        raise ValueError("Invalid vehicle search")
    if filters["status"] not in VEHICLE_STATUSES | {""}:
        raise ValueError("Invalid vehicle status")
    if "archive" in filters and filters["archive"] not in ARCHIVE_SCOPES:
        raise ValueError("Invalid vehicle archive filter")
    layout = _object(value["layout"], "layout")
    if set(layout) != {"version", "defaultSize", "sizes"} or layout["version"] != 2:
        raise ValueError("Invalid vehicle layout")
    for size in (layout["defaultSize"],):
        item = _object(size, "default size")
        if set(item) != {"width", "height"}:
            raise ValueError("Invalid default size")
        if not _bounded_number(item["width"], 280, 720) or not _bounded_number(
            item["height"], 420, 720
        ):
            raise ValueError("Invalid default size")
    sizes = _object(layout["sizes"], "vehicle sizes")
    if len(sizes) > 2000:
        raise ValueError("Too many vehicle sizes")
    for vehicle_id, size in sizes.items():
        item = _object(size, "vehicle size")
        if not VEHICLE_ID.fullmatch(vehicle_id) or set(item) != {"width", "height"}:
            raise ValueError("Invalid vehicle size")
        if not _bounded_number(item["width"], 280, 720) or not _bounded_number(
            item["height"], 420, 720
        ):
            raise ValueError("Invalid vehicle size")


class PreferenceWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int = Field(strict=True, ge=0, le=2_147_483_646)
    value: dict[str, Any]

    @field_validator("value")
    @classmethod
    def bounded_json(cls, value):
        try:
            serialized = json.dumps(value, allow_nan=False, separators=(",", ":"))
        except (TypeError, ValueError) as error:
            raise ValueError("Preference value must be valid JSON") from error
        if len(serialized.encode()) > MAX_VALUE_BYTES:
            raise ValueError("Preference value is too large")
        return value


def preference_payload(module: str, record: AccountPreference | None):
    return {
        "module": module,
        "version": record.version if record else 0,
        "value": record.value if record else None,
        "updated_at": record.updated_at.isoformat() if record else None,
    }


@router.get("/{module}")
def read_preference(module: Literal["dashboard", "vehicles"], session: SessionDep, user: UserDep):
    record = session.get(AccountPreference, (user.id, module))
    return preference_payload(module, record)


@router.put("/{module}")
def write_preference(
    module: Literal["dashboard", "vehicles"],
    body: PreferenceWrite,
    session: SessionDep,
    user: UserDep,
    _: Annotated[None, Depends(check_origin)],
):
    try:
        if module == "dashboard":
            _validate_dashboard(body.value)
        else:
            _validate_vehicles(body.value)
    except (TypeError, ValueError) as error:
        raise ApiError(422, "VALIDATION_ERROR", "Niepoprawne preferencje modułu") from error

    # Locking the account row also serializes first writes, when no preference row exists yet.
    locked_user = session.scalar(select(User).where(User.id == user.id).with_for_update())
    if locked_user is None:
        raise ApiError(401, "UNAUTHENTICATED", "Konto jest niedostępne")
    record = session.get(AccountPreference, (user.id, module))
    current_version = record.version if record else 0
    if body.version != current_version:
        raise ApiError(409, "VERSION_CONFLICT", "Preferencje zmieniły się na innym urządzeniu")
    if current_version >= 2_147_483_646:
        raise ApiError(409, "VERSION_CONFLICT", "Osiągnięto limit wersji preferencji")
    if record is None:
        record = AccountPreference(user_id=user.id, module=module, version=1, value=body.value)
        session.add(record)
    else:
        record.version += 1
        record.value = body.value
    record.updated_at = datetime.now(UTC)
    session.commit()
    return preference_payload(module, record)
