from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import MetaData, Table, delete, inspect, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.errors import ApiError
from app.core.models import Driver, Measurement, SyncState, Vehicle
from app.modules.analytics.models import Alert, AlertReceipt, DailyDistance, Rule
from app.modules.auth.models import User
from app.modules.auth.service import aware, check_origin, current_user, editor
from app.modules.drivers.models import DriverAssignment
from app.modules.drivers.service import project_vehicle_drivers
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
    _: Annotated[User, Depends(editor)],
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
        locally_edited=True,
        manual_name=True,
        manual_license_plate=True,
        manual_vehicle_type=bool(payload.vehicle_type),
        active=True,
    )
    session.add(vehicle)
    try:
        session.flush()
        if assigned_driver is not None:
            session.add(
                DriverAssignment(
                    driver_id=assigned_driver.id,
                    vehicle_id=vehicle.id,
                    active=True,
                    started_at=now,
                    recorded_at=now,
                )
            )
            assigned_driver.version += 1
            vehicle.driver_id = assigned_driver.id
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
    _: Annotated[User, Depends(editor)],
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

    for field, value in changes.items():
        setattr(vehicle, field, value)
    for field in changes.keys() & {"name", "license_plate", "vehicle_type"}:
        setattr(vehicle, f"manual_{field}", True)
    vehicle.locally_edited = True
    vehicle.card_version += 1
    try:
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


def _relink_trip_history_tables(
    session: Session,
    source_vehicle_id: UUID,
    target_vehicle_id: UUID,
) -> None:
    """Migrate SCRUM-24 trip_stops and trip_history_days rows when present in schema."""
    conn = session.connection()
    inspector = inspect(conn)
    table_names = set(inspector.get_table_names())
    metadata = MetaData()

    if "trip_stops" in table_names:
        trip_stops = Table("trip_stops", metadata, autoload_with=conn)
        target_stops = {
            aware(row["start_at"]): dict(row)
            for row in session.execute(
                select(trip_stops).where(trip_stops.c.vehicle_id == target_vehicle_id)
            ).mappings()
        }
        src_stops = list(
            session.execute(
                select(trip_stops).where(trip_stops.c.vehicle_id == source_vehicle_id)
            ).mappings()
        )
        for src in src_stops:
            key = aware(src["start_at"])
            existing = target_stops.get(key)
            if existing is None:
                continue
            existing_end = aware(existing["end_at"])
            src_end = aware(src["end_at"])
            merged_end = existing["end_at"] if existing_end >= src_end else src["end_at"]
            merged_duration = max(existing["duration_seconds"], src["duration_seconds"])
            merged_lat = (
                existing["latitude"] if existing["latitude"] is not None else src["latitude"]
            )
            merged_lon = (
                existing["longitude"] if existing["longitude"] is not None else src["longitude"]
            )
            merged_addr = existing["address"] or src["address"]
            session.execute(
                update(trip_stops)
                .where(
                    trip_stops.c.vehicle_id == target_vehicle_id,
                    trip_stops.c.start_at == existing["start_at"],
                )
                .values(
                    end_at=merged_end,
                    duration_seconds=merged_duration,
                    latitude=merged_lat,
                    longitude=merged_lon,
                    address=merged_addr,
                )
            )
            session.execute(
                delete(trip_stops).where(
                    trip_stops.c.vehicle_id == source_vehicle_id,
                    trip_stops.c.start_at == src["start_at"],
                )
            )
        session.execute(
            update(trip_stops)
            .where(trip_stops.c.vehicle_id == source_vehicle_id)
            .values(vehicle_id=target_vehicle_id)
        )

    if "trip_history_days" in table_names:
        trip_days = Table("trip_history_days", metadata, autoload_with=conn)
        target_days = {
            row["report_day"]: dict(row)
            for row in session.execute(
                select(trip_days).where(trip_days.c.vehicle_id == target_vehicle_id)
            ).mappings()
        }
        src_days = list(
            session.execute(
                select(trip_days).where(trip_days.c.vehicle_id == source_vehicle_id)
            ).mappings()
        )
        for src in src_days:
            existing = target_days.get(src["report_day"])
            if existing is None:
                continue
            t_imp = aware(existing["imported_at"]) if existing["imported_at"] else None
            s_imp = aware(src["imported_at"]) if src["imported_at"] else None
            if t_imp and s_imp:
                merged_imp = existing["imported_at"] if t_imp >= s_imp else src["imported_at"]
            else:
                merged_imp = existing["imported_at"] or src["imported_at"]
            if (t_imp is not None and existing["error_code"] is None) or (
                s_imp is not None and src["error_code"] is None
            ):
                merged_err = None
            else:
                merged_err = existing["error_code"] or src["error_code"]
            session.execute(
                update(trip_days)
                .where(
                    trip_days.c.vehicle_id == target_vehicle_id,
                    trip_days.c.report_day == existing["report_day"],
                )
                .values(imported_at=merged_imp, error_code=merged_err)
            )
            session.execute(
                delete(trip_days).where(
                    trip_days.c.vehicle_id == source_vehicle_id,
                    trip_days.c.report_day == src["report_day"],
                )
            )
        session.execute(
            update(trip_days)
            .where(trip_days.c.vehicle_id == source_vehicle_id)
            .values(vehicle_id=target_vehicle_id)
        )


def _merge_extended_trip_columns_if_present(
    session: Session,
    source_trip_id: UUID,
    target_trip_id: UUID,
) -> None:
    conn = session.connection()
    trip_cols = {col["name"] for col in inspect(conn).get_columns("trips")}
    optional_cols = [c for c in ("start_address", "end_address", "driver_id") if c in trip_cols]
    if not optional_cols and "withdrawn_at" not in trip_cols:
        return
    trips_table = Table("trips", MetaData(), autoload_with=conn)
    src_row = (
        session.execute(select(trips_table).where(trips_table.c.id == source_trip_id))
        .mappings()
        .first()
    )
    dst_row = (
        session.execute(select(trips_table).where(trips_table.c.id == target_trip_id))
        .mappings()
        .first()
    )
    if not src_row or not dst_row:
        return
    updates = {}
    for col in optional_cols:
        if dst_row[col] is None and src_row[col] is not None:
            updates[col] = src_row[col]
    if (
        "withdrawn_at" in trip_cols
        and dst_row["withdrawn_at"] is not None
        and src_row["withdrawn_at"] is None
    ):
        updates["withdrawn_at"] = None
    if updates:
        session.execute(
            update(trips_table).where(trips_table.c.id == target_trip_id).values(**updates)
        )


@router.put("/vehicles/{vehicle_id}/odometer", dependencies=[Depends(check_origin)])
def update_manual_odometer(
    vehicle_id: UUID,
    payload: VehicleOdometerBody,
    request: Request,
    session: SessionDep,
    _: Annotated[User, Depends(editor)],
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
    vehicle.manual_odometer_km = payload.odometer_km
    vehicle.manual_odometer_date = payload.recorded_on
    vehicle.locally_edited = True
    vehicle.card_version += 1
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
    _: Annotated[User, Depends(editor)],
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
        for optional_field in ("vehicle_type", "make", "model", "year", "vin"):
            if getattr(vehicle, optional_field) is None:
                setattr(vehicle, optional_field, getattr(source_vehicle, optional_field))

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

        existing_trips = {
            t.external_uid: t
            for t in session.scalars(select(Trip).where(Trip.vehicle_id == vehicle.id)).all()
        }
        for trip in session.scalars(select(Trip).where(Trip.vehicle_id == source_vehicle.id)).all():
            target_trip = existing_trips.get(trip.external_uid)
            if target_trip is None:
                trip.vehicle_id = vehicle.id
                existing_trips[trip.external_uid] = trip
            elif session.get(TripAnnotation, trip.id) is not None:
                session.rollback()
                raise ApiError(
                    409,
                    "LINK_CONFLICT",
                    "Wykryto konflikt adnotacji przejazdu podczas łączenia pojazdów",
                )
            else:
                _merge_extended_trip_columns_if_present(session, trip.id, target_trip.id)
                session.delete(trip)

        _relink_trip_history_tables(session, source_vehicle.id, vehicle.id)

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
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ApiError(
            409,
            "LINK_CONFLICT",
            "Nie udało się bezpiecznie połączyć historii wskazanego pojazdu",
        ) from None

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
    vehicle.driver_id = None
    vehicle.archived = True
    vehicle.archived_at = now
    vehicle.archived_by = user.id
    vehicle.archived_reason = payload.reason
    vehicle.card_version += 1
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
    _: Annotated[User, Depends(editor)],
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
    vehicle.archived = False
    vehicle.archived_at = None
    vehicle.archived_by = None
    vehicle.archived_reason = None
    vehicle.card_version += 1
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
