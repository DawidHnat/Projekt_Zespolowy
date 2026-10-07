"""Explicit demonstration data. Run after migrations; never called by API startup."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import make_engine
from app.modules.fleet.models import VehicleRecord
from app.modules.trips.models import TripRecord


def seed_demo(session: Session, now: datetime | None = None) -> int:
    if session.scalar(select(VehicleRecord.id).where(VehicleRecord.source == "demo").limit(1)):
        return 0
    now = (now or datetime.now(UTC)).replace(microsecond=0)
    vehicles = [
        ("demo-1", "GD 1234A", "Dostawczy Gdańsk", "driving", 48, 74210, 54.3520, 18.6466),
        ("demo-2", "GWE 8421", "Serwis Gdynia", "parked", 0, 48120, 54.5189, 18.5305),
        ("demo-3", "GA 9082C", "Transport regionalny", "driving", 96, 132850, 54.2537, 18.6276),
        ("demo-4", "GSP 3178", "Auto rezerwowe", "offline", 0, 21940, None, None),
    ]
    for vehicle_id, registration, name, status, speed, odometer, latitude, longitude in vehicles:
        session.add(
            VehicleRecord(
                id=vehicle_id,
                source="demo",
                registration=registration,
                name=name,
                status=status,
                speed_kmh=speed,
                odometer_km=odometer,
                latitude=latitude,
                longitude=longitude,
                updated_at=now
                - (timedelta(days=2) if status == "offline" else timedelta(minutes=3)),
            )
        )
    session.flush()
    for index, vehicle_id, distance, origin, destination in [
        (1, "demo-1", 22.4, "Gdańsk, Magazynowa 12", "Sopot, Niepodległości 15"),
        (2, "demo-1", 19.6, "Sopot, Niepodległości 15", "Gdańsk, Magazynowa 12"),
        (3, "demo-2", 31.8, "Gdynia, Hutnicza 8", "Rumia, Dąbrowskiego 6"),
        (4, "demo-3", 87.2, "Gdańsk, Magazynowa 12", "Tczew, Gdańska 23"),
    ]:
        started = now - timedelta(days=1, hours=index)
        session.add(
            TripRecord(
                id=f"demo-trip-{index}",
                vehicle_id=vehicle_id,
                source="demo",
                started_at=started,
                ended_at=started + timedelta(minutes=40),
                distance_km=distance,
                start_address=origin,
                end_address=destination,
                purpose="Dostawa do klienta" if index == 1 else "",
                notes="Przykładowy przejazd — dane demonstracyjne." if index == 1 else "",
            )
        )
    session.commit()
    return len(vehicles)


def main() -> None:
    settings = get_settings()
    if settings.data_source != "demo":
        raise SystemExit("Demo seeding requires DATA_SOURCE=demo. No data changed.")
    engine = make_engine(settings.database_url)
    with Session(engine) as session:
        count = seed_demo(session)
    engine.dispose()
    print(f"Added {count} demo vehicles. Existing demonstration data is preserved.")


if __name__ == "__main__":
    main()
