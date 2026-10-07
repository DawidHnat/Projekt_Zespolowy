from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import DataSource
from app.modules.fleet.models import VehicleRecord
from app.modules.fleet.schemas import VehicleStatus


def list_vehicles(
    session: Session,
    source: DataSource,
    query: str,
    status: VehicleStatus | None,
    limit: int,
    offset: int,
) -> tuple[list[VehicleRecord], int]:
    filters = [VehicleRecord.source == source]
    if query.strip():
        # contains(autoescape=True) searches literal text, including '%' and '_'.
        needle = query.strip().lower()
        filters.append(
            or_(
                func.lower(VehicleRecord.name).contains(needle, autoescape=True),
                func.lower(VehicleRecord.registration).contains(needle, autoescape=True),
            )
        )
    if status is not None:
        filters.append(VehicleRecord.status == status)
    total = session.scalar(select(func.count()).select_from(VehicleRecord).where(*filters)) or 0
    items = session.scalars(
        select(VehicleRecord)
        .where(*filters)
        .order_by(VehicleRecord.registration, VehicleRecord.id)
        .offset(offset)
        .limit(limit)
    ).all()
    return list(items), total


def get_vehicle(session: Session, source: DataSource, vehicle_id: str) -> VehicleRecord | None:
    return session.scalar(
        select(VehicleRecord).where(VehicleRecord.id == vehicle_id, VehicleRecord.source == source)
    )
