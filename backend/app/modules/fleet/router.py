from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import func, or_, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.errors import ApiError
from app.core.models import Driver, Measurement, SyncState, Vehicle
from app.modules.analytics.models import Alert, AlertReceipt, DailyDistance, Rule
from app.modules.audit.service import build_diff, record_audit_event, vehicle_card_snapshot
from app.modules.auth.models import User
from app.modules.auth.service import check_origin, current_user, editor
from app.modules.drivers.compatibility import evaluate_driver_vehicle
from app.modules.drivers.models import DriverAssignment, DriverCategory
from app.modules.drivers.schemas import CATEGORIES
from app.modules.drivers.service import project_vehicle_drivers
from app.modules.fleet.documents import (
    DOCUMENT_KINDS,
    VehicleAttachment,
    read_bounded_upload,
    serialize_document_item,
    serialize_photo_state,
    validate_and_prepare_upload,
)
from app.modules.fleet.refresh import refresh_state, request_refresh
from app.modules.fleet.service import (
    find_identity_conflicts,
    fleet_driver_summaries,
    fleet_markers,
    fleet_page,
    fleet_summary,
    normalize_identity_token,
    serialize_vehicle,
    source_link_candidates,
    source_payload,
    timestamp,
    with_driver_summary,
)
from app.modules.fleet.sync import account_key, source_lock_id
from app.modules.trips.models import Trip, TripAnnotation

router = APIRouter(prefix="/api/v1/fleet", tags=["fleet"], dependencies=[Depends(current_user)])
SessionDep = Annotated[Session, Depends(get_session)]
Search = Annotated[str, Query(max_length=100)]
Status = Literal["moving", "stopped", "offline", "unknown"] | None
ArchiveFilter = Literal["active", "archived", "all"]
VehicleSort = Literal["name-asc", "name-desc", "status", "odometer-asc", "odometer-desc"]


def _clean_plain_str(value: str | None) -> str | None:
    if value is None:
        return None
    if any(ord(ch) < 32 or 0xD800 <= ord(ch) <= 0xDFFF for ch in value):
        raise ValueError("Pole zawiera niedozwolone znaki sterujące")
    cleaned = value.strip()
    return cleaned or None


def _validate_odometer_value(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    if not value.is_finite() or value < 0 or value > Decimal("9999999.9"):
        raise ValueError("Przebieg musi mieścić się w zakresie 0–9 999 999,9 km")
    quantized = value.quantize(Decimal("0.1"))
    if quantized != value:
        raise ValueError("Przebieg dopuszcza maksymalnie jedno miejsce po przecinku")
    return quantized


def field_error_response(status: int, code: str, message: str, fields: dict[str, str]):
    return JSONResponse(
        {"error": {"code": code, "message": message, "fields": fields}},
        status_code=status,
    )


class VehicleCardFieldsMixin(BaseModel):
    make: Annotated[str | None, Field(default=None, max_length=100)] = None
    model: Annotated[str | None, Field(default=None, max_length=100)] = None
    year: Annotated[int | None, Field(default=None, strict=True, ge=1900, le=2100)] = None
    vin: Annotated[str | None, Field(default=None, max_length=100)] = None
    vehicle_type: Annotated[str | None, Field(default=None, max_length=100)] = None
    fuel_type: Annotated[str | None, Field(default=None, max_length=50)] = None
    leasing_company: Annotated[str | None, Field(default=None, max_length=200)] = None
    leasing_contract_no: Annotated[str | None, Field(default=None, max_length=100)] = None
    leasing_end_on: date | None = None
    inspection_due_on: date | None = None
    insurance_due_on: date | None = None
    manual_odometer_km: Decimal | None = None
    manual_odometer_date: date | None = None
    gross_weight_kg: Annotated[int | None, Field(default=None, strict=True, ge=1, le=120000)] = None
    passenger_seats: Annotated[int | None, Field(default=None, strict=True, ge=0, le=120)] = None
    tows_heavy_trailer: bool | None = Field(default=None, strict=True)
    required_category_override: Annotated[str | None, Field(default=None, max_length=10)] = None

    @field_validator(
        "make",
        "model",
        "vin",
        "vehicle_type",
        "fuel_type",
        "leasing_company",
        "leasing_contract_no",
    )
    @classmethod
    def clean_optional_strings(cls, value: str | None) -> str | None:
        return _clean_plain_str(value)

    @field_validator("required_category_override")
    @classmethod
    def check_category_override(cls, value: str | None) -> str | None:
        cleaned = _clean_plain_str(value)
        if cleaned is None:
            return None
        if cleaned not in CATEGORIES:
            raise ValueError("Nieznana kategoria prawa jazdy")
        return cleaned

    @field_validator("manual_odometer_km")
    @classmethod
    def check_manual_odometer(cls, value: Decimal | None) -> Decimal | None:
        return _validate_odometer_value(value)


class VehicleManualCreate(VehicleCardFieldsMixin):
    model_config = ConfigDict(extra="forbid")
    name: Annotated[str, Field(default="", max_length=200)] = ""
    license_plate: Annotated[str, Field(default="", max_length=100)] = ""
    driver_id: UUID | None = None
    allow_source_duplicate: bool = Field(default=False, strict=True)


class VehicleCardUpdate(VehicleCardFieldsMixin):
    model_config = ConfigDict(extra="forbid")
    card_version: int = Field(strict=True, ge=1, le=2147483646)
    name: Annotated[str | None, Field(default=None, max_length=200)] = None
    license_plate: Annotated[str | None, Field(default=None, max_length=100)] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        cleaned = _clean_plain_str(value)
        if cleaned is None:
            raise ValueError("Nazwa pojazdu nie może być pusta")
        return cleaned

    @field_validator("license_plate")
    @classmethod
    def clean_plate(cls, value: str | None) -> str | None:
        return _clean_plain_str(value)

    @model_validator(mode="after")
    def require_update(self):
        if not self.model_fields_set - {"card_version"}:
            raise ValueError("Podaj co najmniej jedno pole kartoteki")
        return self


class VehicleOdometerBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    card_version: int = Field(strict=True, ge=1, le=2147483646)
    odometer_km: Decimal | None = None
    recorded_on: date | None = None

    @field_validator("odometer_km")
    @classmethod
    def check_odometer(cls, value: Decimal | None) -> Decimal | None:
        return _validate_odometer_value(value)

    @model_validator(mode="after")
    def check_pair(self):
        if (self.odometer_km is None) != (self.recorded_on is None):
            raise ValueError("Podaj przebieg razem z datą odczytu albo wyczyść oba pola")
        return self


class VehicleLinkSourceBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    card_version: int = Field(strict=True, ge=1, le=2147483646)
    source_vehicle_id: UUID


class VehicleArchiveBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    card_version: int = Field(strict=True, ge=1, le=2147483646)
    reason: Annotated[str | None, Field(default=None, max_length=500)] = None

    @field_validator("reason")
    @classmethod
    def clean_reason(cls, value: str | None) -> str | None:
        return _clean_plain_str(value)


class VehicleRestoreBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    card_version: int = Field(strict=True, ge=1, le=2147483646)


class VehicleDocumentDatesBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    card_version: int = Field(strict=True, ge=1, le=2147483646)
    inspection_due_on: date | None = None
    insurance_due_on: date | None = None

    @model_validator(mode="after")
    def require_date_field(self):
        if not self.model_fields_set - {"card_version"}:
            raise ValueError("Podaj co najmniej jeden termin dokumentu")
        return self


def context(request, session):
    settings = request.app.state.settings
    source = account_key(settings.webfleet_account)
    return settings, source, source_payload(session, source)


def write_metadata(session, source):
    state = session.get(SyncState, source)
    if state and state.last_success_at:
        return {
            "status": "degraded" if state.error_code else "ok",
            "last_success_at": timestamp(state.last_success_at),
            "error_code": state.error_code,
        }
    return {
        "status": "degraded",
        "last_success_at": None,
        "error_code": "MANUAL_ONLY",
    }


def _lock_identity_namespace(session: Session, source: str) -> None:
    bind = session.get_bind()
    if bind is not None and bind.dialect.name == "postgresql":
        session.execute(
            text("SELECT pg_advisory_xact_lock(:key)"),
            {"key": source_lock_id(source) ^ 0x4D414E55},
        )


def _check_identity_conflicts_or_error(
    session,
    source: str,
    *,
    license_plate: str | None,
    vin: str | None,
    exclude_id=None,
    allow_source_duplicate: bool = False,
):
    conflicts = find_identity_conflicts(
        session,
        source,
        license_plate=license_plate,
        vin=vin,
        exclude_id=exclude_id,
    )
    if not conflicts:
        return None
    fields: dict[str, str] = {}
    has_manual_conflict = False
    for candidate, same_plate, same_vin in conflicts:
        if candidate.is_manual:
            has_manual_conflict = True
            if same_plate:
                fields["license_plate"] = (
                    f"Numer rejestracyjny jest już przypisany do pojazdu „{candidate.name}”."
                )
            if same_vin:
                fields["vin"] = f"Numer VIN jest już przypisany do pojazdu „{candidate.name}”."
        elif not allow_source_duplicate:
            if same_plate and "license_plate" not in fields:
                fields["license_plate"] = (
                    f"Wykryto pojazd WEBFLEET „{candidate.name}” o tej samej rejestracji."
                )
            if same_vin and "vin" not in fields:
                fields["vin"] = f"Wykryto pojazd WEBFLEET „{candidate.name}” o tym samym VIN."
    if not fields:
        return None
    code = "DUPLICATE_VEHICLE_IDENTITY" if has_manual_conflict else "SOURCE_VEHICLE_EXISTS"
    msg = (
        "Powtórzony numer rejestracyjny lub VIN wymaga rozstrzygnięcia"
        if has_manual_conflict
        else "Wykryto istniejący pojazd źródłowy WEBFLEET o tej samej rejestracji lub VIN"
    )
    return field_error_response(409, code, msg, fields)


@router.get("/refresh")
def refresh_status(request: Request, session: SessionDep):
    return refresh_state(request, session)


@router.post("/refresh", dependencies=[Depends(check_origin)])
def refresh_source(request: Request, session: SessionDep):
    return request_refresh(request, session)


@router.get("/vehicles")
def vehicles(
    request: Request,
    session: SessionDep,
    q: Search = "",
    status: Status = None,
    archive: ArchiveFilter = "active",
    sort: VehicleSort = "name-asc",
    page: Annotated[int, Query(ge=1, le=100_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
):
    settings, source, metadata = context(request, session)
    items, total = fleet_page(
        session,
        source,
        settings.stale_seconds,
        q,
        status,
        page,
        page_size,
        sort,
        archive=archive,
        source_degraded=metadata["status"] == "degraded",
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "source": metadata,
    }


@router.post("/vehicles", status_code=201, dependencies=[Depends(check_origin)])
def create_manual_vehicle(
    payload: VehicleManualCreate,
    request: Request,
    session: SessionDep,
    user: Annotated[User, Depends(editor)],
):
    settings = request.app.state.settings
    source = account_key(settings.webfleet_account)
    field_errors: dict[str, str] = {}
    try:
        cleaned_name = _clean_plain_str(payload.name)
    except ValueError as err:
        cleaned_name = None
        field_errors["name"] = str(err)
    if not cleaned_name and "name" not in field_errors:
        field_errors["name"] = "Podaj nazwę pojazdu."
    try:
        cleaned_plate = _clean_plain_str(payload.license_plate)
    except ValueError as err:
        cleaned_plate = None
        field_errors["license_plate"] = str(err)
    if not cleaned_plate and "license_plate" not in field_errors:
        field_errors["license_plate"] = "Podaj numer rejestracyjny pojazdu."
    if (payload.manual_odometer_km is None) != (payload.manual_odometer_date is None):
        if payload.manual_odometer_km is None:
            field_errors["manual_odometer_km"] = "Podaj przebieg dla wybranej daty odczytu."
        else:
            field_errors["manual_odometer_date"] = "Wybierz datę ręcznego odczytu przebiegu."

    if field_errors:
        return field_error_response(
            422, "VALIDATION_ERROR", "Popraw zaznaczone pola formularza", field_errors
        )

    _lock_identity_namespace(session, source)

    assigned_driver = None
    if payload.driver_id is not None:
        assigned_driver = session.scalar(
            select(Driver)
            .where(
                Driver.id == payload.driver_id,
                Driver.source_account == source,
                Driver.active.is_(True),
            )
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if not assigned_driver:
            return field_error_response(
                422,
                "VALIDATION_ERROR",
                "Popraw zaznaczone pola formularza",
                {"driver_id": "Wybrany kierowca jest niedostępny."},
            )

    conflict_resp = _check_identity_conflicts_or_error(
        session,
        source,
        license_plate=cleaned_plate,
        vin=payload.vin,
        allow_source_duplicate=payload.allow_source_duplicate,
    )
    if conflict_resp is not None:
        return conflict_resp

    now = datetime.now(UTC)
    vehicle = Vehicle(
        source_account=source,
        external_uid=None,
        is_manual=True,
        name=cleaned_name,
        number=None,
        license_plate=cleaned_plate,
        vehicle_type=payload.vehicle_type,
        make=payload.make,
        model=payload.model,
        year=payload.year,
        vin=payload.vin,
        fuel_type=payload.fuel_type,
        leasing_company=payload.leasing_company,
        leasing_contract_no=payload.leasing_contract_no,
        leasing_end_on=payload.leasing_end_on,
        inspection_due_on=payload.inspection_due_on,
        insurance_due_on=payload.insurance_due_on,
        manual_odometer_km=payload.manual_odometer_km,
        manual_odometer_date=payload.manual_odometer_date,
        gross_weight_kg=payload.gross_weight_kg,
        passenger_seats=payload.passenger_seats,
        tows_heavy_trailer=bool(payload.tows_heavy_trailer),
        required_category_override=payload.required_category_override,
        locally_edited=True,
        manual_name=True,
        manual_license_plate=True,
        manual_vehicle_type=bool(payload.vehicle_type),
        active=True,
    )
    if assigned_driver is not None:
        driver_cats = list(
            session.scalars(
                select(DriverCategory.category).where(
                    DriverCategory.driver_id == assigned_driver.id
                )
            ).all()
        )
        comp = evaluate_driver_vehicle(driver_cats, vehicle)
        if comp["status"] == "incompatible":
            session.rollback()
            raise ApiError(409, "LICENSE_INCOMPATIBLE", comp["message"])
    session.add(vehicle)
    try:
        session.flush()
        if assigned_driver is not None:
            new_assign = DriverAssignment(
                driver_id=assigned_driver.id,
                vehicle_id=vehicle.id,
                active=True,
                started_at=now,
                recorded_at=now,
            )
            session.add(new_assign)
            session.flush()
            assigned_driver.version += 1
            vehicle.driver_id = assigned_driver.id
            record_audit_event(
                session,
                entity_type="driver_assignment",
                entity_id=new_assign.id,
                vehicle_id=vehicle.id,
                operation="driver_assignment.created",
                actor_id=user.id,
                source_account=source,
                changes={
                    "driver_id": {"before": None, "after": assigned_driver.id},
                    "vehicle_id": {"before": None, "after": vehicle.id},
                    "active": {"before": None, "after": True},
                    "started_at": {"before": None, "after": now},
                },
                request=request,
                occurred_at=now,
            )
        record_audit_event(
            session,
            entity_type="vehicle",
            entity_id=vehicle.id,
            vehicle_id=vehicle.id,
            operation="vehicle.created",
            actor_id=user.id,
            source_account=source,
            changes=build_diff("vehicle", {}, vehicle_card_snapshot(vehicle)),
            request=request,
            occurred_at=now,
        )
        session.commit()
    except IntegrityError:
        session.rollback()
        return field_error_response(
            409,
            "DUPLICATE_VEHICLE_IDENTITY",
            "Powtórzony numer rejestracyjny lub VIN wymaga rozstrzygnięcia",
            {
                "license_plate": (
                    "Numer rejestracyjny lub VIN jest już przypisany do innego pojazdu ręcznego."
                )
            },
        )
    metadata = write_metadata(session, source)
    drivers = fleet_driver_summaries(session, [vehicle.id], source)
    return with_driver_summary(
        serialize_vehicle(
            vehicle,
            None,
            assigned_driver,
            now,
            settings.stale_seconds,
            metadata["status"] == "degraded",
            link_candidates=source_link_candidates(session, vehicle),
        ),
        drivers.get(vehicle.id),
    )


@router.get("/map")
def fleet_map(
    request: Request,
    session: SessionDep,
    q: Search = "",
    status: Status = None,
    archive: ArchiveFilter = "active",
):
    settings, source, metadata = context(request, session)
    features, total = fleet_markers(
        session,
        source,
        settings.stale_seconds,
        q,
        status,
        archive=archive,
        source_degraded=metadata["status"] == "degraded",
    )
    return {
        "type": "FeatureCollection",
        "features": features,
        "source": metadata,
        "located": len(features),
        "total": total,
    }


@router.get("/summary")
def summary(request: Request, session: SessionDep):
    settings, source, metadata = context(request, session)
    return {
        **fleet_summary(
            session,
            source,
            settings.stale_seconds,
            source_degraded=metadata["status"] == "degraded",
        ),
        "source": metadata,
    }


@router.get("/vehicles/{vehicle_id}")
def vehicle_detail(vehicle_id: UUID, request: Request, session: SessionDep):
    settings, source, metadata = context(request, session)
    row = session.execute(
        select(Vehicle, Measurement, Driver)
        .outerjoin(Measurement, Measurement.vehicle_id == Vehicle.id)
        .outerjoin(Driver, Driver.id == Vehicle.driver_id)
        .where(
            Vehicle.id == vehicle_id,
            Vehicle.source_account == source,
            or_(Vehicle.active.is_(True), Vehicle.archived.is_(True)),
        )
    ).first()
    if not row:
        raise ApiError(404, "NOT_FOUND", "Pojazd nie istnieje")
    vehicle = row[0]
    author = session.get(User, vehicle.archived_by) if vehicle.archived_by else None
    drivers = fleet_driver_summaries(session, [vehicle_id], source)
    return with_driver_summary(
        serialize_vehicle(
            *row,
            datetime.now(UTC),
            settings.stale_seconds,
            metadata["status"] == "degraded",
            archive_author=author,
            link_candidates=source_link_candidates(session, vehicle),
        ),
        drivers.get(vehicle_id),
    )


@router.patch("/vehicles/{vehicle_id}", dependencies=[Depends(check_origin)])
def update_vehicle_card(
    vehicle_id: UUID,
    payload: VehicleCardUpdate,
    request: Request,
    session: SessionDep,
    user: Annotated[User, Depends(editor)],
):
    settings = request.app.state.settings
    source = account_key(settings.webfleet_account)
    if "license_plate" in payload.model_fields_set or "vin" in payload.model_fields_set:
        _lock_identity_namespace(session, source)
    row = session.execute(
        select(Vehicle, Measurement, Driver)
        .outerjoin(Measurement, Measurement.vehicle_id == Vehicle.id)
        .outerjoin(Driver, Driver.id == Vehicle.driver_id)
        .where(
            Vehicle.id == vehicle_id,
            Vehicle.source_account == source,
            or_(Vehicle.active.is_(True), Vehicle.archived.is_(True)),
        )
        .with_for_update(of=Vehicle)
        .execution_options(populate_existing=True)
    ).first()
    if not row:
        raise ApiError(404, "NOT_FOUND", "Pojazd nie istnieje")
    vehicle, measurement, driver = row
    if vehicle.archived:
        raise ApiError(409, "VEHICLE_ARCHIVED", "Przywróć pojazd przed edycją kartoteki")
    if vehicle.card_version != payload.card_version:
        raise ApiError(409, "VERSION_CONFLICT", "Kartoteka pojazdu zmieniła się podczas edycji")

    changes = payload.model_dump(exclude_unset=True, exclude={"card_version"})
    if vehicle.is_manual and "license_plate" in changes and not changes["license_plate"]:
        return field_error_response(
            422,
            "VALIDATION_ERROR",
            "Numer rejestracyjny pojazdu ręcznego jest wymagany",
            {"license_plate": "Podaj numer rejestracyjny pojazdu."},
        )

    next_odo_km = changes.get("manual_odometer_km", vehicle.manual_odometer_km)
    next_odo_date = changes.get("manual_odometer_date", vehicle.manual_odometer_date)
    if (next_odo_km is None) != (next_odo_date is None):
        field = "manual_odometer_km" if next_odo_km is None else "manual_odometer_date"
        return field_error_response(
            422,
            "VALIDATION_ERROR",
            "Podaj przebieg razem z datą odczytu albo wyczyść oba pola",
            {field: "Przebieg ręczny wymaga podania zarówno wartości, jak i daty."},
        )

    next_plate = changes.get("license_plate", vehicle.license_plate)
    next_vin = changes.get("vin", vehicle.vin)
    if "license_plate" in changes or "vin" in changes:
        conflict_resp = _check_identity_conflicts_or_error(
            session,
            source,
            license_plate=next_plate if "license_plate" in changes else None,
            vin=next_vin if "vin" in changes else None,
            exclude_id=vehicle.id,
            allow_source_duplicate=True,
        )
        if conflict_resp is not None:
            return conflict_resp

    before_card = vehicle_card_snapshot(vehicle)
    if "tows_heavy_trailer" in changes:
        changes["tows_heavy_trailer"] = bool(changes["tows_heavy_trailer"])
    for field, value in changes.items():
        setattr(vehicle, field, value)
    for field in changes.keys() & {"name", "license_plate", "vehicle_type"}:
        setattr(vehicle, f"manual_{field}", True)
    vehicle.locally_edited = True
    vehicle.card_version += 1
    try:
        record_audit_event(
            session,
            entity_type="vehicle",
            entity_id=vehicle.id,
            vehicle_id=vehicle.id,
            operation="vehicle.updated",
            actor_id=user.id,
            source_account=source,
            changes=build_diff("vehicle", before_card, vehicle_card_snapshot(vehicle)),
            request=request,
        )
        session.commit()
    except IntegrityError:
        session.rollback()
        return field_error_response(
            409,
            "DUPLICATE_VEHICLE_IDENTITY",
            "Powtórzony numer rejestracyjny lub VIN wymaga rozstrzygnięcia",
            {
                "license_plate": (
                    "Numer rejestracyjny lub VIN jest już przypisany do innego pojazdu ręcznego."
                )
            },
        )
    metadata = write_metadata(session, source)
    drivers = fleet_driver_summaries(session, [vehicle_id], source)
    return with_driver_summary(
        serialize_vehicle(
            vehicle,
            measurement,
            driver,
            datetime.now(UTC),
            settings.stale_seconds,
            metadata["status"] == "degraded",
            link_candidates=source_link_candidates(session, vehicle),
        ),
        drivers.get(vehicle_id),
    )


@router.put("/vehicles/{vehicle_id}/odometer", dependencies=[Depends(check_origin)])
def update_manual_odometer(
    vehicle_id: UUID,
    payload: VehicleOdometerBody,
    request: Request,
    session: SessionDep,
    user: Annotated[User, Depends(editor)],
):
    settings = request.app.state.settings
    source = account_key(settings.webfleet_account)
    if "license_plate" in payload.model_fields_set or "vin" in payload.model_fields_set:
        _lock_identity_namespace(session, source)
    row = session.execute(
        select(Vehicle, Measurement, Driver)
        .outerjoin(Measurement, Measurement.vehicle_id == Vehicle.id)
        .outerjoin(Driver, Driver.id == Vehicle.driver_id)
        .where(
            Vehicle.id == vehicle_id,
            Vehicle.source_account == source,
            or_(Vehicle.active.is_(True), Vehicle.archived.is_(True)),
        )
        .with_for_update(of=Vehicle)
        .execution_options(populate_existing=True)
    ).first()
    if not row:
        raise ApiError(404, "NOT_FOUND", "Pojazd nie istnieje")
    vehicle, measurement, driver = row
    if vehicle.archived:
        raise ApiError(409, "VEHICLE_ARCHIVED", "Przywróć pojazd przed zapisem przebiegu")
    if vehicle.card_version != payload.card_version:
        raise ApiError(409, "VERSION_CONFLICT", "Kartoteka pojazdu zmieniła się podczas edycji")
    before_odo = {
        "manual_odometer_km": vehicle.manual_odometer_km,
        "manual_odometer_date": vehicle.manual_odometer_date,
    }
    vehicle.manual_odometer_km = payload.odometer_km
    vehicle.manual_odometer_date = payload.recorded_on
    vehicle.locally_edited = True
    vehicle.card_version += 1
    record_audit_event(
        session,
        entity_type="vehicle_odometer",
        entity_id=vehicle.id,
        vehicle_id=vehicle.id,
        operation="vehicle.odometer_updated",
        actor_id=user.id,
        source_account=source,
        changes=build_diff(
            "vehicle_odometer",
            before_odo,
            {
                "manual_odometer_km": vehicle.manual_odometer_km,
                "manual_odometer_date": vehicle.manual_odometer_date,
            },
        ),
        request=request,
    )
    session.commit()
    metadata = write_metadata(session, source)
    drivers = fleet_driver_summaries(session, [vehicle_id], source)
    return with_driver_summary(
        serialize_vehicle(
            vehicle,
            measurement,
            driver,
            datetime.now(UTC),
            settings.stale_seconds,
            metadata["status"] == "degraded",
            link_candidates=source_link_candidates(session, vehicle),
        ),
        drivers.get(vehicle_id),
    )


@router.post("/vehicles/{vehicle_id}/link-source", dependencies=[Depends(check_origin)])
def link_manual_vehicle_to_source(
    vehicle_id: UUID,
    payload: VehicleLinkSourceBody,
    request: Request,
    session: SessionDep,
    user: Annotated[User, Depends(editor)],
):
    if vehicle_id == payload.source_vehicle_id:
        raise ApiError(422, "VALIDATION_ERROR", "Wskaż odrębny pojazd źródłowy WEBFLEET")
    settings = request.app.state.settings
    source = account_key(settings.webfleet_account)
    locked = {
        v.id: v
        for v in session.scalars(
            select(Vehicle)
            .where(
                Vehicle.id.in_([vehicle_id, payload.source_vehicle_id]),
                Vehicle.source_account == source,
            )
            .order_by(Vehicle.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        ).all()
    }
    vehicle = locked.get(vehicle_id)
    source_vehicle = locked.get(payload.source_vehicle_id)
    if not vehicle or not source_vehicle or not vehicle.active or not source_vehicle.active:
        raise ApiError(404, "NOT_FOUND", "Pojazd ręczny lub źródłowy nie istnieje")
    if vehicle.archived or source_vehicle.archived:
        raise ApiError(409, "VEHICLE_ARCHIVED", "Nie można łączyć zarchiwizowanych pojazdów")
    if not vehicle.is_manual:
        raise ApiError(409, "ALREADY_LINKED", "Pojazd jest już powiązany ze źródłem WEBFLEET")
    if source_vehicle.is_manual or not source_vehicle.external_uid:
        raise ApiError(409, "NOT_SOURCE_VEHICLE", "Wskazany rekord nie jest pojazdem WEBFLEET")
    if vehicle.card_version != payload.card_version:
        raise ApiError(409, "VERSION_CONFLICT", "Kartoteka pojazdu zmieniła się podczas edycji")

    manual_plate = normalize_identity_token(vehicle.license_plate)
    source_plate = normalize_identity_token(source_vehicle.license_plate)
    manual_vin = normalize_identity_token(vehicle.vin)
    source_vin = normalize_identity_token(source_vehicle.vin)
    if manual_vin and source_vin and manual_vin != source_vin:
        raise ApiError(
            409,
            "IDENTITY_MISMATCH",
            "Pojazd źródłowy ma sprzeczny numer VIN względem kartoteki ręcznej",
        )
    same_plate = bool(manual_plate and source_plate and manual_plate == source_plate)
    same_vin = bool(manual_vin and source_vin and manual_vin == source_vin)
    if (manual_plate and source_plate and not same_plate and not same_vin) or not (
        same_plate or same_vin
    ):
        raise ApiError(
            409,
            "IDENTITY_MISMATCH",
            "Pojazd źródłowy nie pasuje znormalizowaną rejestracją ani numerem VIN",
        )

    before_link = vehicle_card_snapshot(vehicle)

    # Canonical lock order: Vehicle (already locked) -> Driver -> DriverAssignment.
    candidate_driver_ids = sorted(
        set(
            session.scalars(
                select(DriverAssignment.driver_id).where(
                    DriverAssignment.vehicle_id == source_vehicle.id,
                    DriverAssignment.active.is_(True),
                )
            ).all()
        )
    )
    locked_drivers = (
        {
            drv.id: drv
            for drv in session.scalars(
                select(Driver)
                .where(Driver.id.in_(candidate_driver_ids))
                .order_by(Driver.id)
                .with_for_update()
                .execution_options(populate_existing=True)
            ).all()
        }
        if candidate_driver_ids
        else {}
    )

    try:
        saved_uid = source_vehicle.external_uid
        saved_number = source_vehicle.number
        for optional_field in (
            "vehicle_type",
            "make",
            "model",
            "year",
            "vin",
            "gross_weight_kg",
            "passenger_seats",
            "required_category_override",
        ):
            if getattr(vehicle, optional_field) is None:
                setattr(vehicle, optional_field, getattr(source_vehicle, optional_field))
        if not vehicle.tows_heavy_trailer and source_vehicle.tows_heavy_trailer:
            vehicle.tows_heavy_trailer = True

        source_measurement = session.get(Measurement, source_vehicle.id)
        existing_measurement = session.get(Measurement, vehicle.id)
        if source_measurement is not None and existing_measurement is None:
            session.add(
                Measurement(
                    vehicle_id=vehicle.id,
                    latitude=source_measurement.latitude,
                    longitude=source_measurement.longitude,
                    odometer_km=source_measurement.odometer_km,
                    ignition_on=source_measurement.ignition_on,
                    standing_still=source_measurement.standing_still,
                    gps_quality=source_measurement.gps_quality,
                    position_at=source_measurement.position_at,
                    received_at=source_measurement.received_at,
                    speed_kmh=source_measurement.speed_kmh,
                    position_address=source_measurement.position_address,
                )
            )
        if source_measurement is not None:
            session.delete(source_measurement)

        existing_trip_uids = set(
            session.scalars(select(Trip.external_uid).where(Trip.vehicle_id == vehicle.id)).all()
        )
        for trip in session.scalars(select(Trip).where(Trip.vehicle_id == source_vehicle.id)).all():
            if trip.external_uid not in existing_trip_uids:
                trip.vehicle_id = vehicle.id
                existing_trip_uids.add(trip.external_uid)
            elif session.get(TripAnnotation, trip.id) is not None:
                session.rollback()
                raise ApiError(
                    409,
                    "LINK_CONFLICT",
                    "Wykryto konflikt adnotacji przejazdu podczas łączenia pojazdów",
                )
            else:
                session.delete(trip)

        manual_distances = {
            row.event_day: row
            for row in session.scalars(
                select(DailyDistance).where(DailyDistance.vehicle_id == vehicle.id)
            ).all()
        }
        for src_dist in session.scalars(
            select(DailyDistance).where(DailyDistance.vehicle_id == source_vehicle.id)
        ).all():
            target_dist = manual_distances.get(src_dist.event_day)
            if target_dist is None:
                src_dist.vehicle_id = vehicle.id
                manual_distances[src_dist.event_day] = src_dist
            else:
                if src_dist.distance_km > target_dist.distance_km:
                    target_dist.distance_km = src_dist.distance_km
                if src_dist.first_observed_at < target_dist.first_observed_at:
                    target_dist.first_observed_at = src_dist.first_observed_at
                if src_dist.last_observed_at > target_dist.last_observed_at:
                    target_dist.last_observed_at = src_dist.last_observed_at
                session.delete(src_dist)

        session.execute(
            update(Rule).where(Rule.vehicle_id == source_vehicle.id).values(vehicle_id=vehicle.id)
        )
        # Alerts have UniqueConstraint(rule_id, vehicle_id, event_day) and AlertReceipt FK.
        manual_alerts = {
            (alert.rule_id, alert.event_day): alert
            for alert in session.scalars(select(Alert).where(Alert.vehicle_id == vehicle.id)).all()
        }
        for src_alert in session.scalars(
            select(Alert).where(Alert.vehicle_id == source_vehicle.id)
        ).all():
            target_alert = manual_alerts.get((src_alert.rule_id, src_alert.event_day))
            if target_alert is None:
                src_alert.vehicle_id = vehicle.id
                manual_alerts[(src_alert.rule_id, src_alert.event_day)] = src_alert
            else:
                if src_alert.distance_km > target_alert.distance_km:
                    target_alert.distance_km = src_alert.distance_km
                existing_receipts = {
                    rec.user_id: rec
                    for rec in session.scalars(
                        select(AlertReceipt).where(AlertReceipt.alert_id == target_alert.id)
                    ).all()
                }
                for src_rec in session.scalars(
                    select(AlertReceipt).where(AlertReceipt.alert_id == src_alert.id)
                ).all():
                    existing_rec = existing_receipts.get(src_rec.user_id)
                    if existing_rec is None:
                        new_rec = AlertReceipt(
                            alert_id=target_alert.id,
                            user_id=src_rec.user_id,
                            read_at=src_rec.read_at,
                        )
                        session.add(new_rec)
                        existing_receipts[src_rec.user_id] = new_rec
                    elif src_rec.read_at < existing_rec.read_at:
                        existing_rec.read_at = src_rec.read_at
                    session.delete(src_rec)
                session.flush()
                session.delete(src_alert)

        orphan_photo_keys: list[str] = []
        has_manual_photo = session.scalar(
            select(VehicleAttachment.id).where(
                VehicleAttachment.vehicle_id == vehicle.id,
                VehicleAttachment.kind == "vehicle_photo",
            )
        )
        if has_manual_photo is not None:
            for extra_photo in session.scalars(
                select(VehicleAttachment).where(
                    VehicleAttachment.vehicle_id == source_vehicle.id,
                    VehicleAttachment.kind == "vehicle_photo",
                )
            ).all():
                orphan_photo_keys.append(extra_photo.storage_key)
                session.delete(extra_photo)
        session.execute(
            update(VehicleAttachment)
            .where(VehicleAttachment.vehicle_id == source_vehicle.id)
            .values(vehicle_id=vehicle.id)
        )

        now_link = datetime.now(UTC)
        for assignment in session.scalars(
            select(DriverAssignment)
            .where(DriverAssignment.vehicle_id == source_vehicle.id)
            .order_by(DriverAssignment.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        ).all():
            duplicate_open = assignment.active and session.scalar(
                select(DriverAssignment.id).where(
                    DriverAssignment.driver_id == assignment.driver_id,
                    DriverAssignment.vehicle_id == vehicle.id,
                    DriverAssignment.active.is_(True),
                )
            )
            if duplicate_open:
                assignment.active = False
                assignment.ended_at = now_link
                if assignment.driver_id in locked_drivers:
                    locked_drivers[assignment.driver_id].version += 1
            assignment.vehicle_id = vehicle.id

        session.flush()
        session.delete(source_vehicle)
        session.flush()

        vehicle.external_uid = saved_uid
        vehicle.is_manual = False
        vehicle.number = saved_number
        vehicle.locally_edited = True
        vehicle.manual_name = True
        vehicle.manual_license_plate = True
        vehicle.manual_vehicle_type = bool(vehicle.vehicle_type)
        vehicle.card_version += 1
        project_vehicle_drivers(session, [vehicle.id], source)
        record_audit_event(
            session,
            entity_type="vehicle",
            entity_id=vehicle.id,
            vehicle_id=vehicle.id,
            operation="vehicle.source_linked",
            actor_id=user.id,
            source_account=source,
            changes=build_diff("vehicle", before_link, vehicle_card_snapshot(vehicle)),
            request=request,
        )
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ApiError(
            409,
            "LINK_CONFLICT",
            "Nie udało się bezpiecznie połączyć historii wskazanego pojazdu",
        ) from None
    for storage_key in orphan_photo_keys:
        request.app.state.attachment_store.remove(storage_key)

    now = datetime.now(UTC)
    metadata = write_metadata(session, source)
    measurement = session.get(Measurement, vehicle.id)
    driver = session.get(Driver, vehicle.driver_id) if vehicle.driver_id else None
    drivers = fleet_driver_summaries(session, [vehicle.id], source)
    return with_driver_summary(
        serialize_vehicle(
            vehicle,
            measurement,
            driver,
            now,
            settings.stale_seconds,
            metadata["status"] == "degraded",
            link_candidates=[],
        ),
        drivers.get(vehicle.id),
    )


@router.post("/vehicles/{vehicle_id}/archive", dependencies=[Depends(check_origin)])
def archive_vehicle(
    vehicle_id: UUID,
    payload: VehicleArchiveBody,
    request: Request,
    session: SessionDep,
    user: Annotated[User, Depends(editor)],
):
    settings = request.app.state.settings
    source = account_key(settings.webfleet_account)
    row = session.execute(
        select(Vehicle, Measurement, Driver)
        .outerjoin(Measurement, Measurement.vehicle_id == Vehicle.id)
        .outerjoin(Driver, Driver.id == Vehicle.driver_id)
        .where(
            Vehicle.id == vehicle_id,
            Vehicle.source_account == source,
            or_(Vehicle.active.is_(True), Vehicle.archived.is_(True)),
        )
        .with_for_update(of=Vehicle)
        .execution_options(populate_existing=True)
    ).first()
    if not row:
        raise ApiError(404, "NOT_FOUND", "Pojazd nie istnieje")
    vehicle, measurement, _ = row
    if vehicle.card_version != payload.card_version:
        raise ApiError(409, "VERSION_CONFLICT", "Kartoteka pojazdu zmieniła się podczas edycji")
    if vehicle.archived:
        raise ApiError(409, "ALREADY_ARCHIVED", "Pojazd znajduje się już w archiwum")
    now = datetime.now(UTC)
    # Canonical lock order shared with driver endpoints: Vehicle -> Driver -> DriverAssignment.
    candidate_driver_ids = sorted(
        set(
            session.scalars(
                select(DriverAssignment.driver_id).where(
                    DriverAssignment.vehicle_id == vehicle.id,
                    DriverAssignment.active.is_(True),
                )
            ).all()
        )
    )
    locked_drivers = (
        {
            assigned_driver.id: assigned_driver
            for assigned_driver in session.scalars(
                select(Driver)
                .where(Driver.id.in_(candidate_driver_ids))
                .order_by(Driver.id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        }
        if candidate_driver_ids
        else {}
    )
    active_assignments = [
        item
        for item in session.scalars(
            select(DriverAssignment)
            .where(DriverAssignment.vehicle_id == vehicle.id, DriverAssignment.active.is_(True))
            .order_by(DriverAssignment.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        ).all()
        if item.active
    ]
    for driver_id in sorted({item.driver_id for item in active_assignments}):
        if driver_id in locked_drivers:
            locked_drivers[driver_id].version += 1
    for item in active_assignments:
        item.active = False
        item.ended_at = now
        record_audit_event(
            session,
            entity_type="driver_assignment",
            entity_id=item.id,
            vehicle_id=vehicle.id,
            operation="driver_assignment.closed",
            actor_id=user.id,
            source_account=source,
            changes={
                "active": {"before": True, "after": False},
                "ended_at": {"before": None, "after": now},
            },
            request=request,
            occurred_at=now,
        )
    vehicle.driver_id = None
    vehicle.archived = True
    vehicle.archived_at = now
    vehicle.archived_by = user.id
    vehicle.archived_reason = payload.reason
    vehicle.card_version += 1
    record_audit_event(
        session,
        entity_type="vehicle",
        entity_id=vehicle.id,
        vehicle_id=vehicle.id,
        operation="vehicle.archived",
        actor_id=user.id,
        source_account=source,
        changes={
            "archived": {"before": False, "after": True},
            "archived_reason": {"before": None, "after": payload.reason},
        },
        request=request,
        occurred_at=now,
    )
    session.commit()
    metadata = write_metadata(session, source)
    drivers = fleet_driver_summaries(session, [vehicle_id], source)
    return with_driver_summary(
        serialize_vehicle(
            vehicle,
            measurement,
            None,
            now,
            settings.stale_seconds,
            metadata["status"] == "degraded",
            archive_author=user,
        ),
        drivers.get(vehicle_id),
    )


@router.post("/vehicles/{vehicle_id}/restore", dependencies=[Depends(check_origin)])
def restore_vehicle(
    vehicle_id: UUID,
    payload: VehicleRestoreBody,
    request: Request,
    session: SessionDep,
    user: Annotated[User, Depends(editor)],
):
    settings = request.app.state.settings
    source = account_key(settings.webfleet_account)
    if "license_plate" in payload.model_fields_set or "vin" in payload.model_fields_set:
        _lock_identity_namespace(session, source)
    row = session.execute(
        select(Vehicle, Measurement, Driver)
        .outerjoin(Measurement, Measurement.vehicle_id == Vehicle.id)
        .outerjoin(Driver, Driver.id == Vehicle.driver_id)
        .where(
            Vehicle.id == vehicle_id,
            Vehicle.source_account == source,
            or_(Vehicle.active.is_(True), Vehicle.archived.is_(True)),
        )
        .with_for_update(of=Vehicle)
        .execution_options(populate_existing=True)
    ).first()
    if not row:
        raise ApiError(404, "NOT_FOUND", "Pojazd nie istnieje")
    vehicle, measurement, driver = row
    if vehicle.card_version != payload.card_version:
        raise ApiError(409, "VERSION_CONFLICT", "Kartoteka pojazdu zmieniła się podczas edycji")
    if not vehicle.archived:
        raise ApiError(409, "NOT_ARCHIVED", "Pojazd nie znajduje się w archiwum")
    prev_reason = vehicle.archived_reason
    vehicle.archived = False
    vehicle.archived_at = None
    vehicle.archived_by = None
    vehicle.archived_reason = None
    vehicle.card_version += 1
    record_audit_event(
        session,
        entity_type="vehicle",
        entity_id=vehicle.id,
        vehicle_id=vehicle.id,
        operation="vehicle.restored",
        actor_id=user.id,
        source_account=source,
        changes={
            "archived": {"before": True, "after": False},
            "archived_reason": {"before": prev_reason, "after": None},
        },
        request=request,
    )
    session.commit()
    metadata = write_metadata(session, source)
    drivers = fleet_driver_summaries(session, [vehicle_id], source)
    return with_driver_summary(
        serialize_vehicle(
            vehicle,
            measurement,
            driver,
            datetime.now(UTC),
            settings.stale_seconds,
            metadata["status"] == "degraded",
            link_candidates=source_link_candidates(session, vehicle),
        ),
        drivers.get(vehicle_id),
    )


def _find_vehicle_for_documents(session: Session, source: str, vehicle_id: UUID, *, lock: bool):
    stmt = select(Vehicle).where(
        Vehicle.id == vehicle_id,
        Vehicle.source_account == source,
        or_(Vehicle.active.is_(True), Vehicle.archived.is_(True)),
    )
    if lock:
        stmt = stmt.with_for_update()
    vehicle = session.scalar(stmt)
    if not vehicle:
        raise ApiError(404, "NOT_FOUND", "Pojazd nie istnieje")
    return vehicle


def _documents_state_payload(session: Session, settings, vehicle: Vehicle) -> dict:
    attachments = session.scalars(
        select(VehicleAttachment)
        .where(VehicleAttachment.vehicle_id == vehicle.id)
        .order_by(VehicleAttachment.created_at, VehicleAttachment.id)
    ).all()
    photo = next((item for item in attachments if item.kind == "vehicle_photo"), None)
    docs = [serialize_document_item(item) for item in attachments if item.kind in DOCUMENT_KINDS]
    return {
        "vehicle_id": str(vehicle.id),
        "card_version": vehicle.card_version,
        "inspection_due_on": (
            vehicle.inspection_due_on.isoformat() if vehicle.inspection_due_on else None
        ),
        "insurance_due_on": (
            vehicle.insurance_due_on.isoformat() if vehicle.insurance_due_on else None
        ),
        "limits": {
            "max_file_bytes": settings.upload_max_file_bytes,
            "max_files_per_kind": settings.upload_max_files_per_kind,
            "photo_max_edge_px": settings.upload_photo_max_edge_px,
        },
        "photo": serialize_photo_state(vehicle.photo_version, photo),
        "items": docs,
    }


def _scan_quarantined_file(request: Request, storage_key: str, quarantine_path, mime_type: str):
    store = request.app.state.attachment_store
    scanner = request.app.state.malware_scanner
    try:
        verdict = scanner.scan(quarantine_path, mime_type=mime_type)
    except Exception:
        return "scanner_unavailable", "SCANNER_ERROR", storage_key
    if verdict.status == "clean":
        store.promote_to_clean(storage_key)
        return "clean", None, storage_key
    if verdict.status == "rejected":
        store.remove(storage_key)
        return "rejected", verdict.code or "MALWARE_DETECTED", None
    if verdict.status == "quarantined":
        return "quarantined", verdict.code or "SCAN_PENDING", storage_key
    return "scanner_unavailable", verdict.code or "SCANNER_UNAVAILABLE", storage_key


def _binary_attachment_headers(filename: str, *, inline: bool = False, etag: str | None = None):
    ascii_fallback = "".join(
        ch if 32 <= ord(ch) < 127 and ch not in ('"', "\\") else "_" for ch in filename
    )
    disposition_kind = "inline" if inline else "attachment"
    disposition = (
        f"{disposition_kind}; filename=\"{ascii_fallback}\"; filename*=UTF-8''{quote(filename)}"
    )
    headers = {
        "Content-Disposition": disposition,
        "Content-Security-Policy": "default-src 'none'; sandbox",
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "private, no-store",
    }
    if etag:
        headers["ETag"] = etag
    return headers


@router.get("/vehicles/{vehicle_id}/documents")
def list_vehicle_documents(vehicle_id: UUID, request: Request, session: SessionDep):
    settings = request.app.state.settings
    source = account_key(settings.webfleet_account)
    vehicle = _find_vehicle_for_documents(session, source, vehicle_id, lock=False)
    return _documents_state_payload(session, settings, vehicle)


@router.patch("/vehicles/{vehicle_id}/documents/dates", dependencies=[Depends(check_origin)])
def update_vehicle_document_dates(
    vehicle_id: UUID,
    payload: VehicleDocumentDatesBody,
    request: Request,
    session: SessionDep,
    user: Annotated[User, Depends(editor)],
):
    settings = request.app.state.settings
    source = account_key(settings.webfleet_account)
    vehicle = _find_vehicle_for_documents(session, source, vehicle_id, lock=True)
    if vehicle.archived:
        raise ApiError(409, "VEHICLE_ARCHIVED", "Przywróć pojazd przed edycją terminów")
    if vehicle.card_version != payload.card_version:
        raise ApiError(409, "VERSION_CONFLICT", "Kartoteka pojazdu zmieniła się podczas edycji")
    before_dates = {
        "inspection_due_on": vehicle.inspection_due_on,
        "insurance_due_on": vehicle.insurance_due_on,
    }
    if "inspection_due_on" in payload.model_fields_set:
        vehicle.inspection_due_on = payload.inspection_due_on
    if "insurance_due_on" in payload.model_fields_set:
        vehicle.insurance_due_on = payload.insurance_due_on
    vehicle.locally_edited = True
    vehicle.card_version += 1
    record_audit_event(
        session,
        entity_type="vehicle_document",
        entity_id=vehicle.id,
        vehicle_id=vehicle.id,
        operation="vehicle.document_dates_updated",
        actor_id=user.id,
        source_account=source,
        changes=build_diff(
            "vehicle_document",
            before_dates,
            {
                "inspection_due_on": vehicle.inspection_due_on,
                "insurance_due_on": vehicle.insurance_due_on,
            },
        ),
        request=request,
    )
    session.commit()
    return _documents_state_payload(session, settings, vehicle)


@router.post(
    "/vehicles/{vehicle_id}/documents", status_code=201, dependencies=[Depends(check_origin)]
)
async def upload_vehicle_document(
    vehicle_id: UUID,
    request: Request,
    session: SessionDep,
    user: Annotated[User, Depends(editor)],
    kind: Annotated[Literal["inspection", "insurance"] | None, Query()] = None,
):
    settings = request.app.state.settings
    source = account_key(settings.webfleet_account)
    raw_name, declared_mime, raw_bytes, form_fields = await read_bounded_upload(
        request, max_bytes=settings.upload_max_file_bytes
    )
    resolved_kind = kind or form_fields.get("kind")
    if resolved_kind not in DOCUMENT_KINDS:
        raise ApiError(422, "VALIDATION_ERROR", "Wskaż rodzaj dokumentu (inspection lub insurance)")

    vehicle = _find_vehicle_for_documents(session, source, vehicle_id, lock=True)
    if vehicle.archived:
        raise ApiError(409, "VEHICLE_ARCHIVED", "Przywróć pojazd przed dodaniem dokumentu")

    existing_count = session.scalar(
        select(func.count())
        .select_from(VehicleAttachment)
        .where(VehicleAttachment.vehicle_id == vehicle.id, VehicleAttachment.kind == resolved_kind)
    )
    if (existing_count or 0) >= settings.upload_max_files_per_kind:
        limit = settings.upload_max_files_per_kind
        raise ApiError(
            409,
            "DOCUMENT_LIMIT_REACHED",
            f"Osiągnięto limit {limit} plików dla tego rodzaju dokumentu",
        )

    validated = validate_and_prepare_upload(
        kind=resolved_kind,
        raw_filename=raw_name,
        declared_mime=declared_mime,
        raw_bytes=raw_bytes,
        max_bytes=settings.upload_max_file_bytes,
        max_pixels=settings.upload_max_image_pixels,
        photo_max_edge_px=settings.upload_photo_max_edge_px,
    )
    store = request.app.state.attachment_store
    candidate_key, qpath = store.write_quarantine(validated.payload)
    try:
        scan_status, scan_code, stored_key = _scan_quarantined_file(
            request, candidate_key, qpath, validated.mime_type
        )
        if scan_status == "rejected":
            raise ApiError(
                422, "MALWARE_REJECTED", "Plik został odrzucony przez kontrolę bezpieczeństwa"
            )
        now = datetime.now(UTC)
        record = VehicleAttachment(
            vehicle_id=vehicle.id,
            kind=resolved_kind,
            original_name=validated.safe_name,
            mime_type=validated.mime_type,
            size_bytes=len(validated.payload),
            sha256=validated.sha256,
            storage_key=stored_key,
            scan_status=scan_status,
            scan_code=scan_code,
            width_px=validated.width_px,
            height_px=validated.height_px,
            version=1,
            uploaded_by=user.id,
            created_at=now,
            updated_at=now,
        )
        session.add(record)
        session.flush()
        record_audit_event(
            session,
            entity_type="vehicle_document",
            entity_id=record.id,
            vehicle_id=vehicle.id,
            operation="vehicle.document_uploaded",
            actor_id=user.id,
            source_account=source,
            changes={
                "kind": {"before": None, "after": resolved_kind},
                "name": {"before": None, "after": record.original_name},
                "mime_type": {"before": None, "after": record.mime_type},
                "size_bytes": {"before": None, "after": record.size_bytes},
                "scan_status": {"before": None, "after": record.scan_status},
                "version": {"before": None, "after": 1},
            },
            request=request,
            occurred_at=now,
        )
        session.commit()
        return serialize_document_item(record)
    except Exception:
        session.rollback()
        store.remove(candidate_key)
        raise


@router.get("/vehicles/{vehicle_id}/documents/{document_id}/content")
def download_vehicle_document(
    vehicle_id: UUID, document_id: UUID, request: Request, session: SessionDep
):
    settings = request.app.state.settings
    source = account_key(settings.webfleet_account)
    vehicle = _find_vehicle_for_documents(session, source, vehicle_id, lock=False)
    record = session.scalar(
        select(VehicleAttachment).where(
            VehicleAttachment.id == document_id,
            VehicleAttachment.vehicle_id == vehicle.id,
            VehicleAttachment.kind.in_(DOCUMENT_KINDS),
        )
    )
    if not record:
        raise ApiError(404, "NOT_FOUND", "Dokument nie istnieje")
    if record.scan_status != "clean" or not record.storage_key:
        raise ApiError(
            409, "FILE_NOT_AVAILABLE", "Plik nie przeszedł jeszcze pozytywnej weryfikacji skanera"
        )
    try:
        content = request.app.state.attachment_store.read_clean(record.storage_key)
    except FileNotFoundError:
        raise ApiError(404, "NOT_FOUND", "Plik dokumentu jest niedostępny") from None
    return Response(
        content=content,
        media_type=record.mime_type,
        headers=_binary_attachment_headers(
            record.original_name, inline=False, etag=f'"doc-v{record.version}"'
        ),
    )


@router.put("/vehicles/{vehicle_id}/documents/{document_id}", dependencies=[Depends(check_origin)])
async def replace_vehicle_document(
    vehicle_id: UUID,
    document_id: UUID,
    request: Request,
    session: SessionDep,
    user: Annotated[User, Depends(editor)],
):
    settings = request.app.state.settings
    source = account_key(settings.webfleet_account)
    raw_name, declared_mime, raw_bytes, _ = await read_bounded_upload(
        request, max_bytes=settings.upload_max_file_bytes
    )
    vehicle = _find_vehicle_for_documents(session, source, vehicle_id, lock=True)
    if vehicle.archived:
        raise ApiError(409, "VEHICLE_ARCHIVED", "Przywróć pojazd przed podmianą dokumentu")
    record = session.scalar(
        select(VehicleAttachment)
        .where(
            VehicleAttachment.id == document_id,
            VehicleAttachment.vehicle_id == vehicle.id,
            VehicleAttachment.kind.in_(DOCUMENT_KINDS),
        )
        .with_for_update()
    )
    if not record:
        raise ApiError(404, "NOT_FOUND", "Dokument nie istnieje")

    validated = validate_and_prepare_upload(
        kind=record.kind,
        raw_filename=raw_name,
        declared_mime=declared_mime,
        raw_bytes=raw_bytes,
        max_bytes=settings.upload_max_file_bytes,
        max_pixels=settings.upload_max_image_pixels,
        photo_max_edge_px=settings.upload_photo_max_edge_px,
    )
    store = request.app.state.attachment_store
    candidate_key, qpath = store.write_quarantine(validated.payload)
    try:
        scan_status, _, stored_key = _scan_quarantined_file(
            request, candidate_key, qpath, validated.mime_type
        )
        if scan_status == "rejected":
            raise ApiError(
                422, "MALWARE_REJECTED", "Nowy plik został odrzucony — zachowano poprzedni dokument"
            )
        if scan_status == "scanner_unavailable":
            store.remove(candidate_key)
            raise ApiError(
                503,
                "SCANNER_UNAVAILABLE",
                "Skaner bezpieczeństwa jest niedostępny — zachowano poprzedni dokument",
            )
        if scan_status != "clean" or not stored_key:
            store.remove(candidate_key)
            raise ApiError(
                409,
                "FILE_QUARANTINED",
                "Nowy plik oczekuje w kwarantannie — zachowano poprzedni dokument",
            )
        previous_key = record.storage_key
        prev_name = record.original_name
        prev_ver = record.version
        record.original_name = validated.safe_name
        record.mime_type = validated.mime_type
        record.size_bytes = len(validated.payload)
        record.sha256 = validated.sha256
        record.storage_key = stored_key
        record.scan_status = "clean"
        record.scan_code = None
        record.width_px = validated.width_px
        record.height_px = validated.height_px
        record.version += 1
        record.uploaded_by = user.id
        record.updated_at = datetime.now(UTC)
        record_audit_event(
            session,
            entity_type="vehicle_document",
            entity_id=record.id,
            vehicle_id=vehicle.id,
            operation="vehicle.document_replaced",
            actor_id=user.id,
            source_account=source,
            changes={
                "name": {"before": prev_name, "after": record.original_name},
                "version": {"before": prev_ver, "after": record.version},
            },
            request=request,
            occurred_at=record.updated_at,
        )
        session.commit()
    except Exception:
        session.rollback()
        store.remove(candidate_key)
        raise

    if previous_key and previous_key != stored_key:
        store.remove(previous_key)
    return serialize_document_item(record)


@router.delete(
    "/vehicles/{vehicle_id}/documents/{document_id}", dependencies=[Depends(check_origin)]
)
def delete_vehicle_document(
    vehicle_id: UUID,
    document_id: UUID,
    request: Request,
    session: SessionDep,
    user: Annotated[User, Depends(editor)],
):
    settings = request.app.state.settings
    source = account_key(settings.webfleet_account)
    vehicle = _find_vehicle_for_documents(session, source, vehicle_id, lock=True)
    if vehicle.archived:
        raise ApiError(409, "VEHICLE_ARCHIVED", "Przywróć pojazd przed usunięciem dokumentu")
    record = session.scalar(
        select(VehicleAttachment)
        .where(
            VehicleAttachment.id == document_id,
            VehicleAttachment.vehicle_id == vehicle.id,
            VehicleAttachment.kind.in_(DOCUMENT_KINDS),
        )
        .with_for_update()
    )
    if not record:
        raise ApiError(404, "NOT_FOUND", "Dokument nie istnieje")
    old_key = record.storage_key
    doc_id = record.id
    doc_kind = record.kind
    doc_name = record.original_name
    session.delete(record)
    record_audit_event(
        session,
        entity_type="vehicle_document",
        entity_id=doc_id,
        vehicle_id=vehicle.id,
        operation="vehicle.document_deleted",
        actor_id=user.id,
        source_account=source,
        changes={
            "kind": {"before": doc_kind, "after": None},
            "name": {"before": doc_name, "after": None},
            "deleted": {"before": False, "after": True},
        },
        request=request,
    )
    session.commit()
    request.app.state.attachment_store.remove(old_key)
    return {"ok": True}


@router.put("/vehicles/{vehicle_id}/photo", dependencies=[Depends(check_origin)])
async def put_vehicle_photo(
    vehicle_id: UUID,
    request: Request,
    session: SessionDep,
    user: Annotated[User, Depends(editor)],
):
    settings = request.app.state.settings
    source = account_key(settings.webfleet_account)
    raw_name, declared_mime, raw_bytes, _ = await read_bounded_upload(
        request, max_bytes=settings.upload_max_file_bytes
    )
    vehicle = _find_vehicle_for_documents(session, source, vehicle_id, lock=True)
    if vehicle.archived:
        raise ApiError(409, "VEHICLE_ARCHIVED", "Przywróć pojazd przed zmianą zdjęcia")

    validated = validate_and_prepare_upload(
        kind="vehicle_photo",
        raw_filename=raw_name,
        declared_mime=declared_mime,
        raw_bytes=raw_bytes,
        max_bytes=settings.upload_max_file_bytes,
        max_pixels=settings.upload_max_image_pixels,
        photo_max_edge_px=settings.upload_photo_max_edge_px,
    )
    existing = session.scalar(
        select(VehicleAttachment)
        .where(
            VehicleAttachment.vehicle_id == vehicle.id,
            VehicleAttachment.kind == "vehicle_photo",
        )
        .with_for_update()
    )
    store = request.app.state.attachment_store
    candidate_key, qpath = store.write_quarantine(validated.payload)
    previous_key: str | None = None
    try:
        scan_status, scan_code, stored_key = _scan_quarantined_file(
            request, candidate_key, qpath, validated.mime_type
        )
        if scan_status == "rejected":
            raise ApiError(
                422, "MALWARE_REJECTED", "Zdjęcie zostało odrzucone przez kontrolę bezpieczeństwa"
            )
        if existing is not None and existing.scan_status == "clean" and scan_status != "clean":
            store.remove(candidate_key)
            if scan_status == "scanner_unavailable":
                raise ApiError(
                    503,
                    "SCANNER_UNAVAILABLE",
                    "Skaner bezpieczeństwa jest niedostępny — zachowano poprzednie zdjęcie",
                )
            raise ApiError(
                409,
                "FILE_QUARANTINED",
                "Nowe zdjęcie oczekuje w kwarantannie — zachowano poprzednie zdjęcie",
            )

        now = datetime.now(UTC)
        if existing is None:
            record = VehicleAttachment(
                vehicle_id=vehicle.id,
                kind="vehicle_photo",
                original_name=validated.safe_name,
                mime_type=validated.mime_type,
                size_bytes=len(validated.payload),
                sha256=validated.sha256,
                storage_key=stored_key,
                scan_status=scan_status,
                scan_code=scan_code,
                width_px=validated.width_px,
                height_px=validated.height_px,
                version=1,
                uploaded_by=user.id,
                created_at=now,
                updated_at=now,
            )
            session.add(record)
        else:
            previous_key = existing.storage_key
            existing.original_name = validated.safe_name
            existing.mime_type = validated.mime_type
            existing.size_bytes = len(validated.payload)
            existing.sha256 = validated.sha256
            existing.storage_key = stored_key
            existing.scan_status = scan_status
            existing.scan_code = scan_code
            existing.width_px = validated.width_px
            existing.height_px = validated.height_px
            existing.version += 1
            existing.uploaded_by = user.id
            existing.updated_at = now
            record = existing

        if scan_status == "clean":
            vehicle.photo_version += 1
        session.flush()
        record_audit_event(
            session,
            entity_type="vehicle_document",
            entity_id=record.id,
            vehicle_id=vehicle.id,
            operation="vehicle.photo_updated",
            actor_id=user.id,
            source_account=source,
            changes={
                "kind": {"before": None, "after": "vehicle_photo"},
                "mime_type": {"before": None, "after": record.mime_type},
                "scan_status": {"before": None, "after": record.scan_status},
                "version": {"before": None, "after": record.version},
            },
            request=request,
            occurred_at=now,
        )
        session.commit()
    except Exception:
        session.rollback()
        store.remove(candidate_key)
        raise

    if previous_key and previous_key != stored_key:
        store.remove(previous_key)
    return serialize_photo_state(vehicle.photo_version, record)


@router.get("/vehicles/{vehicle_id}/photo/content")
def get_vehicle_photo_content(vehicle_id: UUID, request: Request, session: SessionDep):
    settings = request.app.state.settings
    source = account_key(settings.webfleet_account)
    vehicle = _find_vehicle_for_documents(session, source, vehicle_id, lock=False)
    record = session.scalar(
        select(VehicleAttachment).where(
            VehicleAttachment.vehicle_id == vehicle.id,
            VehicleAttachment.kind == "vehicle_photo",
        )
    )
    if not record:
        raise ApiError(404, "NOT_FOUND", "Pojazd nie posiada zapisanego zdjęcia")
    if record.scan_status != "clean" or not record.storage_key:
        raise ApiError(
            409, "FILE_NOT_AVAILABLE", "Zdjęcie nie przeszło jeszcze pozytywnej weryfikacji skanera"
        )
    try:
        content = request.app.state.attachment_store.read_clean(record.storage_key)
    except FileNotFoundError:
        raise ApiError(404, "NOT_FOUND", "Plik zdjęcia jest niedostępny") from None
    return Response(
        content=content,
        media_type=record.mime_type,
        headers=_binary_attachment_headers(
            record.original_name, inline=True, etag=f'"photo-v{vehicle.photo_version}"'
        ),
    )


@router.delete("/vehicles/{vehicle_id}/photo", dependencies=[Depends(check_origin)])
def delete_vehicle_photo(
    vehicle_id: UUID,
    request: Request,
    session: SessionDep,
    user: Annotated[User, Depends(editor)],
):
    settings = request.app.state.settings
    source = account_key(settings.webfleet_account)
    vehicle = _find_vehicle_for_documents(session, source, vehicle_id, lock=True)
    if vehicle.archived:
        raise ApiError(409, "VEHICLE_ARCHIVED", "Przywróć pojazd przed usunięciem zdjęcia")
    record = session.scalar(
        select(VehicleAttachment)
        .where(
            VehicleAttachment.vehicle_id == vehicle.id,
            VehicleAttachment.kind == "vehicle_photo",
        )
        .with_for_update()
    )
    if not record:
        raise ApiError(404, "NOT_FOUND", "Pojazd nie posiada zapisanego zdjęcia")
    old_key = record.storage_key
    photo_id = record.id
    was_clean = record.scan_status == "clean"
    session.delete(record)
    if was_clean:
        vehicle.photo_version += 1
    record_audit_event(
        session,
        entity_type="vehicle_document",
        entity_id=photo_id,
        vehicle_id=vehicle.id,
        operation="vehicle.photo_deleted",
        actor_id=user.id,
        source_account=source,
        changes={"deleted": {"before": False, "after": True}},
        request=request,
    )
    session.commit()
    request.app.state.attachment_store.remove(old_key)
    return {"ok": True, "photo_version": vehicle.photo_version}
