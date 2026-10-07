from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.modules.fleet import service
from app.modules.fleet.schemas import Vehicle, VehicleList, VehicleStatus

router = APIRouter(prefix="/vehicles", tags=["fleet"])


@router.get("", response_model=VehicleList)
def list_vehicles(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    query: Annotated[str, Query(max_length=100)] = "",
    status: VehicleStatus | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> VehicleList:
    source = request.app.state.settings.data_source
    items, total = service.list_vehicles(session, source, query, status, limit, offset)
    return VehicleList(
        items=[Vehicle.model_validate(item) for item in items], total=total, source=source
    )


@router.get("/{vehicle_id}", response_model=Vehicle)
def get_vehicle(
    vehicle_id: str, request: Request, session: Annotated[Session, Depends(get_session)]
) -> Vehicle:
    vehicle = service.get_vehicle(session, request.app.state.settings.data_source, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found.")
    return Vehicle.model_validate(vehicle)
