import json
import math
import re
from datetime import UTC, datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.errors import ApiError
from app.modules.auth.models import User
from app.modules.auth.service import check_origin, current_user
from app.modules.preferences.image import reencode_background
from app.modules.preferences.models import AccountBackgroundImage, AccountPreference

router = APIRouter(prefix="/api/v1/preferences", tags=["preferences"])
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[User, Depends(current_user)]
MODULES = ("dashboard", "vehicles")
WIDGETS = {"metrics", "map", "activity", "vehicles", "utilization", "trips"}
PROFILES = {"desktop", "compact"}
VEHICLE_ID = re.compile(r"^[a-f\d]{8}-(?:[a-f\d]{4}-){3}[a-f\d]{12}$", re.I)
CARD_SORTS = {"name-asc", "name-desc", "status", "odometer-asc", "odometer-desc"}
VEHICLE_STATUSES = {"moving", "stopped", "offline", "unknown"}
MAX_VALUE_BYTES = 128 * 1024
MAX_BACKGROUND_BYTES = 8 * 1024 * 1024
MAP_WIDGETS = {"map", "vehicles"}
THEMES = {"light", "dark", "system"}
MATERIALS = {"solid", "glass"}
BACKGROUND_PRESETS = {"city", "mountains", "lagoon", "aurora"}


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
    required = {"visibleWidgets", "layouts"}
    appearance = {"theme", "accent", "material", "background"}
    if not required.issubset(value) or set(value) - required - appearance:
        raise ValueError("Invalid dashboard preference fields")
    if set(value) & appearance and not appearance.issubset(value):
        raise ValueError("Incomplete dashboard appearance preferences")
    visible = value["visibleWidgets"]
    if (
        not isinstance(visible, list)
        or len(visible) > len(WIDGETS)
        or len(set(visible)) != len(visible)
        or any(widget not in WIDGETS for widget in visible)
    ):
        raise ValueError("Invalid visible widget list")
    layouts = _object(value["layouts"], "layouts")
    if "dashboard" not in layouts or set(layouts) - {"dashboard", "map"}:
        raise ValueError("Invalid dashboard layouts")
    for section_name, section_value in layouts.items():
        section = _object(section_value, f"{section_name} layout")
        if set(section) != PROFILES:
            raise ValueError(f"Invalid {section_name} profiles")
        expected_widgets = WIDGETS if section_name == "dashboard" else MAP_WIDGETS
        for profile, entries in section.items():
            if not isinstance(entries, list) or len(entries) != len(expected_widgets):
                raise ValueError(f"Invalid {profile} layout")
            seen: set[str] = set()
            for entry in entries:
                item = _object(entry, "layout item")
                widget = item.get("i")
                if widget not in expected_widgets or widget in seen:
                    raise ValueError("Invalid or duplicate widget ID")
                seen.add(widget)
                columns = 12 if profile == "desktop" else 1
                for key, lower, upper in (
                    ("x", 0, columns),
                    ("y", 0, 200),
                    ("w", 1, columns),
                    ("h", 1, 24),
                ):
                    if not _bounded_number(item.get(key), lower, upper):
                        raise ValueError("Invalid widget dimensions")
                if item["x"] + item["w"] > columns:
                    raise ValueError("Widget exceeds its layout width")
            if seen != expected_widgets:
                raise ValueError(f"Incomplete {section_name} layout")

    if appearance.issubset(value):
        if value["theme"] not in THEMES:
            raise ValueError("Invalid dashboard theme")
        if not isinstance(value["accent"], str) or not re.fullmatch(
            r"#[a-fA-F0-9]{6}", value["accent"]
        ):
            raise ValueError("Invalid dashboard accent")
        if value["material"] not in MATERIALS:
            raise ValueError("Invalid dashboard material")
        background = _object(value["background"], "background")
        if set(background) != {"kind", "preset", "veil", "blur", "customId"}:
            raise ValueError("Invalid background fields")
        if background["kind"] not in {"default", "preset", "custom"}:
            raise ValueError("Invalid background kind")
        if background["preset"] not in BACKGROUND_PRESETS:
            raise ValueError("Invalid background preset")
        if not _bounded_number(background["veil"], 0, 70) or not _bounded_number(
            background["blur"], 0, 16
        ):
            raise ValueError("Invalid background adjustments")
        custom_id = background["customId"]
        if custom_id is not None:
            try:
                UUID(custom_id)
            except (TypeError, ValueError) as error:
                raise ValueError("Invalid background image ID") from error


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
    if set(filters) != {"q", "status"}:
        raise ValueError("Invalid vehicle filters")
    if not isinstance(filters["q"], str) or len(filters["q"]) > 100:
        raise ValueError("Invalid vehicle search")
    if filters["status"] not in VEHICLE_STATUSES | {""}:
        raise ValueError("Invalid vehicle status")
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


@router.put("/background/{image_id}")
async def write_background_image(
    image_id: UUID,
    request: Request,
    session: SessionDep,
    user: UserDep,
    _: Annotated[None, Depends(check_origin)],
):
    if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "image/webp":
        raise ApiError(415, "UNSUPPORTED_MEDIA_TYPE", "Tło musi być zapisane jako WebP")
    length = request.headers.get("content-length")
    if length is not None:
        try:
            declared_size = int(length)
        except ValueError as error:
            raise ApiError(400, "INVALID_CONTENT_LENGTH", "Niepoprawny rozmiar pliku") from error
        if declared_size < 0:
            raise ApiError(400, "INVALID_CONTENT_LENGTH", "Niepoprawny rozmiar pliku")
        if declared_size > MAX_BACKGROUND_BYTES:
            raise ApiError(413, "PAYLOAD_TOO_LARGE", "Plik tła przekracza limit 8 MB")
    chunks = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > MAX_BACKGROUND_BYTES:
            raise ApiError(413, "PAYLOAD_TOO_LARGE", "Plik tła przekracza limit 8 MB")
        chunks.append(chunk)
    image = reencode_background(b"".join(chunks))

    locked_user = session.scalar(select(User).where(User.id == user.id).with_for_update())
    if locked_user is None:
        raise ApiError(401, "UNAUTHENTICATED", "Konto jest niedostępne")
    collision = session.scalar(
        select(AccountBackgroundImage).where(
            AccountBackgroundImage.image_id == image_id,
            AccountBackgroundImage.user_id != user.id,
        )
    )
    if collision:
        raise ApiError(409, "IMAGE_ID_CONFLICT", "Identyfikator obrazu jest już używany")
    record = session.get(AccountBackgroundImage, user.id)
    if record is None:
        record = AccountBackgroundImage(
            user_id=user.id,
            image_id=image_id,
            image=image,
            updated_at=datetime.now(UTC),
        )
        session.add(record)
    else:
        record.image_id = image_id
        record.image = image
        record.updated_at = datetime.now(UTC)
    try:
        session.commit()
    except IntegrityError:
        # Another account claimed the same image_id concurrently (UNIQUE): no partial write.
        session.rollback()
        raise ApiError(409, "IMAGE_ID_CONFLICT", "Identyfikator obrazu jest już używany") from None
    return {"id": str(image_id)}


@router.get("/background/{image_id}")
def read_background_image(
    image_id: UUID,
    session: SessionDep,
    user: UserDep,
):
    record = session.get(AccountBackgroundImage, user.id)
    if record is None or record.image_id != image_id:
        raise ApiError(404, "IMAGE_NOT_FOUND", "Nie znaleziono zapisanego tła")
    return Response(content=record.image, media_type="image/webp")


@router.delete("/background/{image_id}", status_code=204)
def delete_background_image(
    image_id: UUID,
    session: SessionDep,
    user: UserDep,
    _: Annotated[None, Depends(check_origin)],
):
    # Same serialization as writes; delete only this account's current image_id, so a
    # concurrently replaced background is never removed by a stale request.
    locked_user = session.scalar(select(User).where(User.id == user.id).with_for_update())
    if locked_user is None:
        raise ApiError(401, "UNAUTHENTICATED", "Konto jest niedostępne")
    removed = session.execute(
        delete(AccountBackgroundImage).where(
            AccountBackgroundImage.user_id == user.id,
            AccountBackgroundImage.image_id == image_id,
        )
    ).rowcount
    if not removed:
        session.rollback()
        raise ApiError(404, "IMAGE_NOT_FOUND", "Nie znaleziono zapisanego tła")
    session.commit()
    return Response(status_code=204)
