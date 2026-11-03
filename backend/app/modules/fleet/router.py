from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.errors import ApiError
from app.core.models import Driver, Measurement, Vehicle
from app.modules.auth.service import current_user
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


def context(request, session):
    settings = request.app.state.settings
    source = account_key(settings.webfleet_account)
    return settings, source, source_payload(session, source)


@router.get("/vehicles")
def vehicles(
    request: Request,
    session: SessionDep,
    q: Search = "",
    status: Status = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
):
    settings, source, metadata = context(request, session)
    items, total = fleet_page(session, source, settings.stale_seconds, q, status, page, page_size)
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
    features, total = fleet_markers(session, source, settings.stale_seconds, q, status)
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
    return {**fleet_summary(session, source, settings.stale_seconds), "source": metadata}


@router.get("/vehicles/{vehicle_id}")
def vehicle_detail(vehicle_id: UUID, request: Request, session: SessionDep):
    from datetime import UTC, datetime

    settings, source, _ = context(request, session)
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
        serialize_vehicle(*row, datetime.now(UTC), settings.stale_seconds), drivers.get(vehicle_id)
    )
