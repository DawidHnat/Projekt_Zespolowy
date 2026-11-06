from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID

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
from app.modules.trips.models import Trip, TripAnnotation
from app.modules.trips.service import annotation_payload, trip_payload

router = APIRouter(prefix="/api/v1/trips", tags=["trips"])
SessionDep = Annotated[Session, Depends(get_session)]


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


@router.get("", dependencies=[Depends(current_user)])
def trips(
    request: Request,
    session: SessionDep,
    vehicle_id: UUID,
    from_time: Annotated[datetime, Query(alias="from")],
    to_time: Annotated[datetime, Query(alias="to")],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
):
    if (
        from_time.tzinfo is None
        or to_time.tzinfo is None
        or not timedelta(0) < to_time - from_time <= timedelta(days=93)
    ):
        raise ApiError(422, "VALIDATION_ERROR", "Podaj poprawny zakres ze strefą czasu (do 93 dni)")
    vehicle = session.get(Vehicle, vehicle_id)
    source = account_key(request.app.state.settings.webfleet_account)
    if vehicle is None or vehicle.source_account != source:
        raise ApiError(404, "NOT_FOUND", "Pojazd nie istnieje")
    # Full known trips overlapping [from, to); an unknown end is treated as a point at start.
    filters = (
        Trip.vehicle_id == vehicle_id,
        Trip.start_at < aware(to_time),
        or_(
            Trip.end_at > aware(from_time),
            and_(
                or_(Trip.end_at.is_(None), Trip.end_at == Trip.start_at),
                Trip.start_at >= aware(from_time),
            ),
        ),
    )
    total = session.scalar(select(func.count()).select_from(Trip).where(*filters))
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
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{trip_id}", dependencies=[Depends(current_user)])
def trip_detail(trip_id: UUID, request: Request, session: SessionDep):
    trip = scoped_trip(session, request, trip_id)
    annotation = session.get(TripAnnotation, trip.id)
    author = session.get(User, annotation.updated_by) if annotation else None
    return trip_payload(trip, annotation, author)


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
