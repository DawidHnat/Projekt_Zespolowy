"""Import one read-only vehicle snapshot, without replacing local trip annotations."""

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import make_engine
from app.integrations.webfleet.client import WebfleetClient, WebfleetError
from app.integrations.webfleet.mapper import map_vehicles
from app.modules.fleet.models import VehicleRecord
from app.modules.fleet.schemas import Vehicle


def store_snapshot(session: Session, vehicles: list[Vehicle]) -> int:
    """Upsert provider snapshots atomically. Omitted vehicles retain data, marked offline."""
    existing = {
        vehicle.id: vehicle
        for vehicle in session.scalars(
            select(VehicleRecord).where(VehicleRecord.source == "webfleet")
        )
    }
    incoming_ids = {vehicle.id for vehicle in vehicles}
    for snapshot in vehicles:
        fields = snapshot.model_dump()
        record = existing.get(snapshot.id)
        if record is None:
            session.add(VehicleRecord(source="webfleet", **fields))
        else:
            for field, value in fields.items():
                setattr(record, field, value)
    for vehicle_id in existing.keys() - incoming_ids:
        existing[vehicle_id].status = "offline"
    session.commit()
    return len(vehicles)


def main() -> None:
    settings = get_settings()
    if settings.data_source != "webfleet":
        raise SystemExit("Webfleet sync requires DATA_SOURCE=webfleet. No data changed.")
    try:
        with WebfleetClient(settings) as client:
            vehicles = map_vehicles(client.vehicles(), client.objects())
        engine = make_engine(settings.database_url)
        try:
            with Session(engine) as session:
                count = store_snapshot(session, vehicles)
        finally:
            engine.dispose()
    except WebfleetError as error:
        raise SystemExit(str(error)) from None
    except SQLAlchemyError:
        raise SystemExit(
            "Snapshot could not be saved. Check your database; no partial import committed."
        ) from None
    print(f"Imported {count} Webfleet vehicle snapshots. Trips import is not implemented yet.")


if __name__ == "__main__":
    main()
