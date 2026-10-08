from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.errors import ApiError
from app.core.models import Driver, Measurement, Vehicle
from app.modules.auth.service import current_user
from app.modules.fleet.service import fleet_rows, serialize_vehicle, source_payload
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
    items = fleet_rows(session, source, settings.stale_seconds, q, status)
    start = (page - 1) * page_size
    return {
        "items": items[start : start + page_size],
        "total": len(items),
        "page": page,
        "page_size": page_size,
        "source": metadata,
    }


@router.get("/map")
def fleet_map(request: Request, session: SessionDep, q: Search = "", status: Status = None):
    settings, source, metadata = context(request, session)
    items = fleet_rows(session, source, settings.stale_seconds, q, status)
    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [item["longitude"], item["latitude"]]},
            "properties": {
                key: item[key] for key in ("id", "name", "status", "is_stale", "position_at")
            },
        }
        for item in items
        if item["longitude"] is not None and item["latitude"] is not None
    ]
    return {
        "type": "FeatureCollection",
        "features": features,
        "source": metadata,
        "located": len(features),
        "total": len(items),
    }


@router.get("/summary")
def summary(request: Request, session: SessionDep):
    settings, source, metadata = context(request, session)
    items = fleet_rows(session, source, settings.stale_seconds)
    return {
        "total": len(items),
        **{
            key: sum(item["status"] == key for item in items)
            for key in ("moving", "stopped", "offline", "unknown")
        },
        "source": metadata,
    }


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
    return serialize_vehicle(*row, datetime.now(UTC), settings.stale_seconds)
