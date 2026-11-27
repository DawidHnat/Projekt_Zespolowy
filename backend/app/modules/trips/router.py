from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.errors import ApiError
from app.core.models import Driver, Vehicle
from app.modules.audit.service import build_diff, record_audit_event
from app.modules.auth.models import User
from app.modules.auth.service import aware, current_user, editor, now_utc
from app.modules.drivers.compatibility import evaluate_driver_vehicle
from app.modules.drivers.models import DriverCategory
from app.modules.fleet.sync import account_key
from app.modules.trips.models import Trip, TripAnnotation
from app.modules.trips.service import annotation_payload, trip_payload

router = APIRouter(prefix="/api/v1/trips", tags=["trips"])
SessionDep = Annotated[Session, Depends(get_session)]


class AnnotationPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    purpose: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    driver_id: UUID | None = None
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
        if not {"purpose", "description", "driver_id"} & self.model_fields_set:
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


@router.get("", dependencies=[Depends(current_user)])
def trips(
    request: Request,
    session: SessionDep,
    vehicle_id: UUID,
    from_time: Annotated[datetime, Query(alias="from")],
    to_time: Annotated[datetime, Query(alias="to")],
    page: Annotated[int, Query(ge=1, le=100_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
):
    try:
        if from_time.tzinfo is None or to_time.tzinfo is None:
            raise ApiError(
                422, "VALIDATION_ERROR", "Podaj poprawny zakres ze strefą czasu (do 93 dni)"
            )
        from_utc = aware(from_time)
        to_utc = aware(to_time)
        diff = to_utc - from_utc
        if not timedelta(0) < diff <= timedelta(days=93):
            raise ApiError(
                422, "VALIDATION_ERROR", "Podaj poprawny zakres ze strefą czasu (do 93 dni)"
            )
    except (OverflowError, ValueError) as exc:
        raise ApiError(
            422, "VALIDATION_ERROR", "Podaj poprawny zakres ze strefą czasu (do 93 dni)"
        ) from exc
    vehicle = session.get(Vehicle, vehicle_id)
    source = account_key(request.app.state.settings.webfleet_account)
    if vehicle is None or vehicle.source_account != source:
        raise ApiError(404, "NOT_FOUND", "Pojazd nie istnieje")
    # Full known trips overlapping [from, to); an unknown end is treated as a point at start.
    filters = (
        Trip.vehicle_id == vehicle_id,
        Trip.start_at < to_utc,
        or_(
            Trip.end_at > from_utc,
            and_(
                or_(Trip.end_at.is_(None), Trip.end_at == Trip.start_at),
                Trip.start_at >= from_utc,
            ),
        ),
    )
    total = session.scalar(select(func.count()).select_from(Trip).where(*filters))
    rows = session.execute(
        select(Trip, TripAnnotation, User, Driver)
        .outerjoin(TripAnnotation, TripAnnotation.trip_id == Trip.id)
        .outerjoin(User, User.id == TripAnnotation.updated_by)
        .outerjoin(Driver, Driver.id == TripAnnotation.driver_id)
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
    }


@router.get("/{trip_id}", dependencies=[Depends(current_user)])
def trip_detail(trip_id: UUID, request: Request, session: SessionDep):
    trip = scoped_trip(session, request, trip_id)
    annotation = session.get(TripAnnotation, trip.id)
    author = session.get(User, annotation.updated_by) if annotation else None
    trip_driver = (
        session.get(Driver, annotation.driver_id) if annotation and annotation.driver_id else None
    )
    return trip_payload(trip, annotation, author, trip_driver)


@router.patch("/{trip_id}/annotation")
def patch_annotation(
    trip_id: UUID,
    body: AnnotationPatch,
    request: Request,
    session: SessionDep,
    user: Annotated[User, Depends(editor)],
):
    trip = scoped_trip(session, request, trip_id, lock=True)
    source = account_key(request.app.state.settings.webfleet_account)
    annotation = session.get(TripAnnotation, trip.id)
    version = annotation.version if annotation else 1
    if body.version != version:
        raise ApiError(
            409, "VERSION_CONFLICT", "Notatka została zmieniona. Odczytaj bieżącą wersję"
        )
    selected_driver = None
    if "driver_id" in body.model_fields_set and body.driver_id is not None:
        selected_driver = session.scalar(
            select(Driver).where(
                Driver.id == body.driver_id,
                Driver.source_account == source,
                Driver.active.is_(True),
            )
        )
        if selected_driver is None:
            raise ApiError(404, "NOT_FOUND", "Wybrany kierowca jest niedostępny")
        vehicle = session.get(Vehicle, trip.vehicle_id)
        driver_cats = list(
            session.scalars(
                select(DriverCategory.category).where(
                    DriverCategory.driver_id == selected_driver.id
                )
            ).all()
        )
        comp = evaluate_driver_vehicle(driver_cats, vehicle)
        if comp["status"] == "incompatible":
            raise ApiError(409, "LICENSE_INCOMPATIBLE", comp["message"])
    before_ann = {
        "purpose": annotation.purpose if annotation else None,
        "description": annotation.description if annotation else None,
        "driver_id": annotation.driver_id if annotation else None,
        "version": version if annotation else None,
    }
    if annotation is None:
        annotation = TripAnnotation(trip_id=trip.id)
        session.add(annotation)
    for field in ("purpose", "description", "driver_id"):
        if field in body.model_fields_set:
            setattr(annotation, field, getattr(body, field))
    annotation.version = version + 1
    annotation.updated_by = user.id
    annotation.updated_at = now_utc()
    after_ann = {
        "purpose": annotation.purpose,
        "description": annotation.description,
        "driver_id": annotation.driver_id,
        "version": annotation.version,
    }
    record_audit_event(
        session,
        entity_type="trip_annotation",
        entity_id=trip.id,
        vehicle_id=trip.vehicle_id,
        operation="trip_annotation.updated",
        actor_id=user.id,
        source_account=source,
        changes=build_diff("trip_annotation", before_ann, after_ann),
        request=request,
        occurred_at=annotation.updated_at,
    )
    session.commit()
    trip_driver = (
        selected_driver
        if "driver_id" in body.model_fields_set
        else (session.get(Driver, annotation.driver_id) if annotation.driver_id else None)
    )
    return annotation_payload(annotation, user, trip_driver)
