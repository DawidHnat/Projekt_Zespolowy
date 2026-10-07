from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.modules.fleet.service import get_vehicle
from app.modules.trips.models import TripRecord
from app.modules.trips.schemas import Trip, TripList, TripUpdate

router = APIRouter(tags=["trips"])


@router.get("/vehicles/{vehicle_id}/trips", response_model=TripList)
def list_trips(
    vehicle_id: str,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TripList:
    source = request.app.state.settings.data_source
    if get_vehicle(session, source, vehicle_id) is None:
        raise HTTPException(status_code=404, detail="Vehicle not found.")
    filters = [TripRecord.vehicle_id == vehicle_id, TripRecord.source == source]
    total = session.scalar(select(func.count()).select_from(TripRecord).where(*filters)) or 0
    trips = session.scalars(
        select(TripRecord)
        .where(*filters)
        .order_by(TripRecord.started_at.desc(), TripRecord.id)
        .offset(offset)
        .limit(limit)
    ).all()
    return TripList(items=[Trip.model_validate(trip) for trip in trips], total=total, source=source)


@router.patch("/trips/{trip_id}", response_model=Trip)
def update_trip(
    trip_id: str,
    changes: TripUpdate,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> Trip:
    trip = session.scalar(
        select(TripRecord).where(
            TripRecord.id == trip_id, TripRecord.source == request.app.state.settings.data_source
        )
    )
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found.")
    for field, value in changes.model_dump(exclude_unset=True).items():
        setattr(trip, field, value)
    session.commit()
    session.refresh(trip)
    return Trip.model_validate(trip)
