from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.modules.analytics.schemas import Alert, AlertList, Summary
from app.modules.fleet.models import VehicleRecord
from app.modules.trips.models import TripRecord

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=Summary)
def summary(request: Request, session: Annotated[Session, Depends(get_session)]) -> Summary:
    source = request.app.state.settings.data_source
    total_vehicles = (
        session.scalar(
            select(func.count()).select_from(VehicleRecord).where(VehicleRecord.source == source)
        )
        or 0
    )
    driving_vehicles = (
        session.scalar(
            select(func.count())
            .select_from(VehicleRecord)
            .where(VehicleRecord.source == source, VehicleRecord.status == "driving")
        )
        or 0
    )
    trips_count, distance = session.execute(
        select(func.count(), func.coalesce(func.sum(TripRecord.distance_km), 0))
        .select_from(TripRecord)
        .where(TripRecord.source == source)
    ).one()
    return Summary(
        total_vehicles=total_vehicles,
        driving_vehicles=driving_vehicles,
        distance_km=round(float(distance), 2),
        trips_count=trips_count,
        source=source,
    )


@router.get("/alerts", response_model=AlertList)
def alerts(request: Request, session: Annotated[Session, Depends(get_session)]) -> AlertList:
    source = request.app.state.settings.data_source
    vehicles = session.scalars(
        select(VehicleRecord)
        .where(
            VehicleRecord.source == source,
            or_(VehicleRecord.status == "offline", VehicleRecord.speed_kmh > 90),
        )
        .order_by(VehicleRecord.registration, VehicleRecord.id)
    ).all()
    items = []
    for vehicle in vehicles:
        if vehicle.status == "offline":
            items.append(
                Alert(
                    id=f"offline:{vehicle.id}",
                    vehicle_id=vehicle.id,
                    severity="info",
                    title="Brak aktualnej pozycji",
                    description=f"{vehicle.registration}: sprawdź czas ostatniej aktualizacji.",
                )
            )
        elif vehicle.speed_kmh is not None and vehicle.speed_kmh > 90:
            items.append(
                Alert(
                    id=f"speed:{vehicle.id}",
                    vehicle_id=vehicle.id,
                    severity="warning",
                    title="Prędkość powyżej progu demonstracyjnego",
                    description=f"{vehicle.registration}: {vehicle.speed_kmh:g} km/h (próg 90).",
                )
            )
    return AlertList(items=items, total=len(items), source=source)
