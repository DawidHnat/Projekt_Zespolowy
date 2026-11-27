from datetime import date, datetime, timedelta
from typing import Annotated
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.errors import ApiError
from app.core.models import Vehicle
from app.modules.auth.models import User
from app.modules.auth.service import aware, current_user, editor, now_utc
from app.modules.fleet.sync import account_key
from app.modules.trips.models import Trip, TripAnnotation, TripStop
from app.modules.trips.service import WARSAW, annotation_payload, report_coverage, trip_payload

router = APIRouter(prefix="/api/v1/trips", tags=["trips"])
SessionDep = Annotated[Session, Depends(get_session)]


def mileage_window(from_day: date, through: date):
    zone = ZoneInfo("Europe/Warsaw")
    try:
        if not 0 <= (through - from_day).days < 93:
            raise ValueError
        lower = datetime.combine(from_day, datetime.min.time(), zone)
        upper = datetime.combine(through + timedelta(days=1), datetime.min.time(), zone)
        return lower.astimezone(ZoneInfo("UTC")), upper.astimezone(ZoneInfo("UTC"))
    except (OverflowError, ValueError):
        raise ApiError(
            422,
            "VALIDATION_ERROR",
            "Wybierz prawidłowy okres do 93 dni",
        ) from None


class AnnotationPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    purpose: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    version: int = Field(strict=True, ge=1, le=2147483646)

    @field_validator("purpose", "description")
    @classmethod
    def clean_text(cls, value, info):
        if value is None:
            return None
        for char in value:
            if (ord(char) < 32 and char not in "\n\r\t") or 0xD800 <= ord(char) <= 0xDFFF:
                raise ValueError("Invalid text")
        if info.field_name == "purpose" and ("\n" in value or "\r" in value):
            raise ValueError("Purpose must be a single line")
        return value.strip() or None

    @model_validator(mode="after")
    def has_changes(self):
        if not {"purpose", "description"} & self.model_fields_set:
            raise ValueError("At least one annotation field is required")
        return self


def scoped_trip(session, request, trip_id, *, lock=False):
    statement = (
        select(Trip)
        .join(Vehicle, Vehicle.id == Trip.vehicle_id)
        .where(
            Trip.id == trip_id,
            Vehicle.source_account == account_key(request.app.state.settings.webfleet_account),
        )
    )
    if lock:
        # Serializes both first writes and later edits, including the absent annotation case.
        statement = statement.with_for_update(of=Trip)
    trip = session.scalar(statement)
    if trip is None:
        raise ApiError(404, "NOT_FOUND", "Przejazd nie istnieje")
    return trip


def utc_window(from_time: datetime, to_time: datetime):
    try:
        if from_time.tzinfo is None or to_time.tzinfo is None:
            raise ValueError
        lower, upper = aware(from_time), aware(to_time)
        if not timedelta(0) < upper - lower <= timedelta(days=93):
            raise ValueError
        # Also validate conversion used by the Polish report coverage.
        lower.astimezone(WARSAW)
        upper.astimezone(WARSAW)
        return lower, upper
    except (OverflowError, ValueError):
        raise ApiError(
            422, "VALIDATION_ERROR", "Podaj poprawny zakres ze strefą czasu (do 93 dni)"
        ) from None


def vehicle_in_source(session, vehicle_id, source):
    vehicle = session.get(Vehicle, vehicle_id)
    if vehicle is None or vehicle.source_account != source:
        raise ApiError(404, "NOT_FOUND", "Pojazd nie istnieje")
    return vehicle


@router.get("", dependencies=[Depends(current_user)])
def trips(
    request: Request,
    session: SessionDep,
    from_time: Annotated[datetime, Query(alias="from")],
    to_time: Annotated[datetime, Query(alias="to")],
    vehicle_id: UUID | None = None,
    page: Annotated[int, Query(ge=1, le=100_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
):
    lower, upper = utc_window(from_time, to_time)
    source = account_key(request.app.state.settings.webfleet_account)
    filters = [
        Vehicle.source_account == source,
        Trip.start_at < upper,
        or_(
            Trip.end_at > lower,
            and_(
                or_(Trip.end_at.is_(None), Trip.end_at == Trip.start_at),
                Trip.start_at >= lower,
            ),
        ),
    ]
    if vehicle_id is not None:
        vehicle_in_source(session, vehicle_id, source)
        filters.append(Trip.vehicle_id == vehicle_id)
    total = session.scalar(select(func.count()).select_from(Trip).join(Vehicle).where(*filters))
    rows = session.execute(
        select(Trip, TripAnnotation, User, Vehicle.name)
        .join(Vehicle)
        .outerjoin(TripAnnotation, TripAnnotation.trip_id == Trip.id)
        .outerjoin(User, User.id == TripAnnotation.updated_by)
        .where(*filters)
        .order_by(Trip.start_at.desc(), Trip.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return {
        "items": [trip_payload(*row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "coverage": report_coverage(session, vehicle_id, lower, upper) if vehicle_id else None,
    }


@router.get("/stops", dependencies=[Depends(current_user)])
def stops(
    request: Request,
    session: SessionDep,
    vehicle_id: UUID,
    from_time: Annotated[datetime, Query(alias="from")],
    to_time: Annotated[datetime, Query(alias="to")],
    min_duration_seconds: Annotated[int, Query(ge=0, le=86400)] = 300,
    page: Annotated[int, Query(ge=1, le=100_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
):
    lower, upper = utc_window(from_time, to_time)
    vehicle_in_source(session, vehicle_id, account_key(request.app.state.settings.webfleet_account))
    filters = (
        TripStop.vehicle_id == vehicle_id,
        TripStop.start_at < upper,
        TripStop.end_at > lower,
        TripStop.duration_seconds >= min_duration_seconds,
    )
    total = session.scalar(select(func.count()).select_from(TripStop).where(*filters))
    rows = session.scalars(
        select(TripStop)
        .where(*filters)
        .order_by(TripStop.start_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return {
        "items": [
            {
                "start_at": aware(stop.start_at).isoformat(),
                "end_at": aware(stop.end_at).isoformat(),
                "duration_seconds": stop.duration_seconds,
                "address": stop.address,
                "latitude": stop.latitude,
                "longitude": stop.longitude,
            }
            for stop in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "coverage": report_coverage(session, vehicle_id, lower, upper),
    }


@router.get("/mileage", dependencies=[Depends(current_user)])
def mileage(
    request: Request,
    session: SessionDep,
    vehicle_id: UUID,
    from_day: date,
    through: date,
    page: Annotated[int, Query(ge=1, le=100_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
):
    lower, upper = mileage_window(from_day, through)
    vehicle = session.get(Vehicle, vehicle_id)
    source = account_key(request.app.state.settings.webfleet_account)
    if vehicle is None or vehicle.source_account != source:
        raise ApiError(404, "NOT_FOUND", "Pojazd nie istnieje")

    # PO decision 27.11 (SCRUM-62): sum of known distances and trips without a purpose
    # over the whole range; trips withdrawn by the source report are not current data.
    filters = (
        Trip.vehicle_id == vehicle_id,
        Trip.start_at >= lower,
        Trip.start_at < upper,
        Trip.withdrawn_at.is_(None),
    )
    missing_purpose = or_(
        TripAnnotation.purpose.is_(None),
        func.trim(TripAnnotation.purpose) == "",
    )
    known_distance = and_(Trip.distance_km.is_not(None), Trip.distance_km >= 0)
    result = session.execute(
        select(
            func.count(Trip.id).label("total"),
            func.sum(Trip.distance_km).filter(known_distance).label("known"),
            func.count(Trip.id).filter(missing_purpose).label("missing_purpose"),
            func.count(Trip.id).filter(~known_distance).label("missing_distance"),
        )
        .outerjoin(TripAnnotation, TripAnnotation.trip_id == Trip.id)
        .where(*filters)
    ).one()

    rows = session.execute(
        select(Trip, TripAnnotation, User)
        .outerjoin(TripAnnotation, TripAnnotation.trip_id == Trip.id)
        .outerjoin(User, User.id == TripAnnotation.updated_by)
        .where(*filters)
        .order_by(Trip.start_at.desc(), Trip.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return {
        "items": [trip_payload(*row) for row in rows],
        "total": result.total,
        "page": page,
        "page_size": page_size,
        "summary": {
            "known_km": float(result.known) if result.known is not None else None,
            "missing_purpose": result.missing_purpose,
            "missing_distance": result.missing_distance,
        },
        "coverage": report_coverage(session, vehicle_id, lower, upper),
    }


@router.get("/{trip_id}", dependencies=[Depends(current_user)])
def trip_detail(trip_id: UUID, request: Request, session: SessionDep):
    trip = scoped_trip(session, request, trip_id)
    annotation = session.get(TripAnnotation, trip.id)
    author = session.get(User, annotation.updated_by) if annotation else None
    return trip_payload(trip, annotation, author, session.get(Vehicle, trip.vehicle_id).name)


@router.patch("/{trip_id}/annotation")
def patch_annotation(
    trip_id: UUID,
    body: AnnotationPatch,
    request: Request,
    session: SessionDep,
    user: Annotated[User, Depends(editor)],
):
    trip = scoped_trip(session, request, trip_id, lock=True)
    annotation = session.get(TripAnnotation, trip.id)
    version = annotation.version if annotation else 1
    if body.version != version:
        raise ApiError(
            409, "VERSION_CONFLICT", "Notatka została zmieniona. Odczytaj bieżącą wersję"
        )
    if annotation is None:
        annotation = TripAnnotation(trip_id=trip.id)
        session.add(annotation)
    for field in ("purpose", "description"):
        if field in body.model_fields_set:
            setattr(annotation, field, getattr(body, field))
    annotation.version = version + 1
    annotation.updated_by = user.id
    annotation.updated_at = now_utc()
    session.commit()
    return annotation_payload(annotation, user)
