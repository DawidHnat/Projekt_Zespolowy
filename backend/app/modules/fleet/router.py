from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.errors import ApiError
from app.core.models import Driver, Measurement, Vehicle
from app.modules.auth.models import User
from app.modules.auth.service import check_origin, current_user, editor
from app.modules.fleet.refresh import refresh_state, request_refresh
from app.modules.fleet.service import (
    fleet_driver_summaries,
    fleet_markers,
    fleet_page,
    fleet_summary,
    serialize_vehicle,
    source_payload,
    with_driver_summary,
)
from app.modules.fleet.sync import account_key

router = APIRouter(prefix="/api/v1/fleet", tags=["fleet"], dependencies=[Depends(current_user)])
SessionDep = Annotated[Session, Depends(get_session)]
Search = Annotated[str, Query(max_length=100)]
Status = Literal["moving", "stopped", "offline", "unknown"] | None
VehicleSort = Literal["name-asc", "name-desc", "status", "odometer-asc", "odometer-desc"]


class VehicleCardUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    card_version: int = Field(strict=True, ge=1, le=2147483646)
    name: Annotated[str | None, Field(default=None, max_length=200)] = None
    make: Annotated[str | None, Field(default=None, max_length=100)] = None
    model: Annotated[str | None, Field(default=None, max_length=100)] = None
    year: Annotated[int | None, Field(default=None, ge=1900, le=2100)] = None
    vin: Annotated[str | None, Field(default=None, max_length=100)] = None
    license_plate: Annotated[str | None, Field(default=None, max_length=100)] = None
    vehicle_type: Annotated[str | None, Field(default=None, max_length=100)] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            raise ValueError("Nazwa pojazdu nie może być pusta")
        return value.strip()

    @field_validator("make", "model", "vin", "license_plate", "vehicle_type")
    @classmethod
    def clean_optional_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @model_validator(mode="after")
    def require_update(self):
        if not self.model_fields_set - {"card_version"}:
            raise ValueError("Podaj co najmniej jedno pole kartoteki")
        return self


def context(request, session):
    settings = request.app.state.settings
    source = account_key(settings.webfleet_account)
    return settings, source, source_payload(session, source)


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
        source_degraded=metadata["status"] == "degraded",
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "source": metadata,
    }


@router.get("/map")
def fleet_map(request: Request, session: SessionDep, q: Search = "", status: Status = None):
    settings, source, metadata = context(request, session)
    features, total = fleet_markers(
        session,
        source,
        settings.stale_seconds,
        q,
        status,
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
    from datetime import UTC, datetime

    settings, source, metadata = context(request, session)
    row = session.execute(
        select(Vehicle, Measurement, Driver)
        .outerjoin(Measurement, Measurement.vehicle_id == Vehicle.id)
        .outerjoin(Driver, Driver.id == Vehicle.driver_id)
        .where(Vehicle.id == vehicle_id, Vehicle.source_account == source, Vehicle.active.is_(True))
    ).first()
    if not row:
        raise ApiError(404, "NOT_FOUND", "Pojazd nie istnieje")
    drivers = fleet_driver_summaries(session, [vehicle_id], source)
    return with_driver_summary(
        serialize_vehicle(
            *row,
            datetime.now(UTC),
            settings.stale_seconds,
            metadata["status"] == "degraded",
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
    from datetime import UTC, datetime

    settings, source, metadata = context(request, session)
    row = session.execute(
        select(Vehicle, Measurement, Driver)
        .outerjoin(Measurement, Measurement.vehicle_id == Vehicle.id)
        .outerjoin(Driver, Driver.id == Vehicle.driver_id)
        .where(Vehicle.id == vehicle_id, Vehicle.source_account == source, Vehicle.active.is_(True))
        .with_for_update(of=Vehicle)
    ).first()
    if not row:
        raise ApiError(404, "NOT_FOUND", "Pojazd nie istnieje")
    vehicle, measurement, driver = row
    if vehicle.card_version != payload.card_version:
        raise ApiError(409, "VERSION_CONFLICT", "Kartoteka pojazdu zmieniła się podczas edycji")
    changes = payload.model_dump(exclude_unset=True, exclude={"card_version"})
    for field, value in changes.items():
        setattr(vehicle, field, value)
    for field in changes.keys() & {"name", "license_plate", "vehicle_type"}:
        setattr(vehicle, f"manual_{field}", True)
    vehicle.locally_edited = True
    vehicle.card_version += 1
    session.commit()
    drivers = fleet_driver_summaries(session, [vehicle_id], source)
    return with_driver_summary(
        serialize_vehicle(
            vehicle,
            measurement,
            driver,
            datetime.now(UTC),
            settings.stale_seconds,
            metadata["status"] == "degraded",
        ),
        drivers.get(vehicle_id),
    )
