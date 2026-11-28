"""Opt-in disposable PostgreSQL fixture. Never used by the product entry point."""

import os
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID
from zoneinfo import ZoneInfo

import uvicorn
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, delete, select, update
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import WebfleetSettings
from app.core.models import Driver, Measurement, SyncState, Vehicle
from app.core.settings import Settings
from app.main import create_app
from app.modules.analytics.models import Alert, AlertReceipt, DailyDistance, Rule
from app.modules.auth.models import LoginAttempt, LoginSession, User
from app.modules.auth.service import password_hasher
from app.modules.drivers.models import DriverAssignment, DriverCategory
from app.modules.fleet.sync import account_key
from app.modules.preferences.models import AccountPreference
from app.modules.trips.importer import import_one_day
from app.modules.trips.models import (
    Trip,
    TripAnnotation,
    TripHistoryDay,
    TripHistorySource,
    TripStop,
)
from app.modules.trips.service import WARSAW, polish_day

ACCOUNT = "synthetic-e2e-source"
VEHICLE = UUID("11111111-1111-4111-8111-111111111111")
TRIP = UUID("22222222-2222-4222-8222-222222222222")


def test_database_url():
    if os.environ.get("FLEET_FLOW_E2E") != "true":
        raise RuntimeError("E2E fixture requires explicit opt-in")
    value = os.environ.get("E2E_DATABASE_URL", "")
    url = make_url(value)
    if (
        url.drivername != "postgresql+psycopg"
        or url.database != "fleet_flow_test_e2e"
        or url.host not in ("127.0.0.1", "localhost")
    ):
        raise RuntimeError("E2E fixture requires the dedicated local fleet_flow_test_e2e database")
    return value


def source_state(engine, mode):
    with Session(engine) as session:
        state = session.get(SyncState, account_key(ACCOUNT))
        state.last_success_at = None if mode == "unavailable" else datetime.now(UTC)
        state.error_code = "TIMEOUT" if mode == "degraded" else None
        session.commit()


def seed(engine):
    now = datetime.now(UTC)
    trip_start = now.astimezone(ZoneInfo("Europe/Warsaw")).replace(
        hour=10, minute=0, second=0, microsecond=0
    )
    with Session(engine) as session:
        known = {"e2e-admin", "e2e-editor", "e2e-viewer", "e2e-editor-two"}
        if any(username not in known for username in session.scalars(select(User.username))):
            raise RuntimeError("E2E database contains non-fixture users")
        fixtures = (
            ("e2e-admin", "Test admin", "admin"),
            ("e2e-editor", "Test editor", "editor"),
            ("e2e-viewer", "Test viewer", "viewer"),
            ("e2e-editor-two", "Test editor two", "editor"),
        )
        for username, display_name, role in fixtures:
            user = session.scalar(select(User).where(User.username == username))
            if not user:
                session.add(
                    User(
                        username=username,
                        display_name=display_name,
                        role=role,
                        password_hash=password_hasher.hash("synthetic-e2e-password"),
                    )
                )
        source = account_key(ACCOUNT)
        if not session.get(SyncState, source):
            session.add(SyncState(source_account=source, last_success_at=now))
        if not session.get(Vehicle, VEHICLE):
            session.add(
                Vehicle(
                    id=VEHICLE,
                    source_account=source,
                    external_uid="e2e-only",
                    name="Pojazd E2E",
                    license_plate="TEST E2E",
                )
            )
            session.flush()
            session.add(
                Measurement(
                    vehicle_id=VEHICLE,
                    latitude=0,
                    longitude=0,
                    gps_quality="A",
                    standing_still=True,
                    position_at=now,
                    received_at=now,
                    odometer_km=Decimal("1234.5"),
                )
            )
        existing_trip = session.get(Trip, TRIP)
        if existing_trip:
            existing_trip.start_at = trip_start
            existing_trip.end_at = trip_start + timedelta(minutes=10)
        else:
            session.add(
                Trip(
                    id=TRIP,
                    vehicle_id=VEHICLE,
                    external_uid="e2e-trip",
                    start_at=trip_start,
                    end_at=trip_start + timedelta(minutes=10),
                    distance_km=Decimal("12.5"),
                )
            )
        session.commit()
    source_state(engine, "ok")


def imported_history_case(engine, *, clear=False):
    source = account_key(ACCOUNT)
    if clear:
        with Session(engine) as session:
            imported = select(Trip.id).where(
                Trip.vehicle_id == VEHICLE, Trip.external_uid == "500001"
            )
            session.execute(delete(TripAnnotation).where(TripAnnotation.trip_id.in_(imported)))
            session.execute(
                delete(Trip).where(Trip.vehicle_id == VEHICLE, Trip.external_uid == "500001")
            )
            session.execute(delete(TripStop).where(TripStop.vehicle_id == VEHICLE))
            session.execute(delete(TripHistoryDay).where(TripHistoryDay.vehicle_id == VEHICLE))
            session.execute(
                delete(TripHistorySource).where(TripHistorySource.source_account == source)
            )
            session.commit()
        return
    now = datetime.now(UTC)
    day = now.astimezone(WARSAW).date() - timedelta(days=1)
    start, _ = polish_day(day)
    with Session(engine) as session:
        limiter = session.get(TripHistorySource, source)
        if limiter is not None:
            now = max(now, limiter.next_attempt_at)

    class FixtureSource:
        def __init__(self, _):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        async def fetch_trip_history(self, uid, lower, upper):
            assert uid == "e2e-only" and (lower, upper) == polish_day(day)
            departure = start + timedelta(hours=8)
            arrival = departure + timedelta(minutes=22)
            trips = [
                {
                    "tripid": "500001",
                    "start_time": departure.isoformat(),
                    "end_time": arrival.isoformat(),
                    "distance": 12345,
                    "start_postext": "Początek E2E",
                    "end_postext": "Koniec E2E",
                }
            ]
            stops = [
                {
                    "start_time": arrival.isoformat(),
                    "end_time": (arrival + timedelta(minutes=8)).isoformat(),
                    "postext": "Postój E2E",
                }
            ]
            return trips, stops

    settings = WebfleetSettings(ACCOUNT, "synthetic", "synthetic", "synthetic")
    result = import_one_day(
        engine,
        settings,
        VEHICLE,
        day,
        day,
        refresh=True,
        client_factory=FixtureSource,
        clock=lambda: now,
    )
    assert result == "imported"


def main():
    database_url = test_database_url()
    engine = create_engine(database_url)
    if sys.argv[1:] in (["import-history-case"], ["clear-history-case"]):
        imported_history_case(engine, clear=sys.argv[1] == "clear-history-case")
        engine.dispose()
        return
    if sys.argv[1:] == ["reset-case"]:
        with Session(engine) as session:
            session.execute(delete(LoginAttempt))
            session.execute(delete(LoginSession))
            session.execute(delete(AccountPreference))
            for user in session.scalars(
                select(User).where(
                    User.username.in_(("e2e-editor", "e2e-viewer", "e2e-editor-two"))
                )
            ):
                user.password_hash = password_hasher.hash("synthetic-e2e-password")
            session.execute(update(Vehicle).values(driver_id=None))
            session.flush()
            for model in (DriverAssignment, DriverCategory, Driver):
                session.execute(delete(model))
            session.execute(delete(Vehicle).where(Vehicle.external_uid.like("e2e-driver-car-%")))
            for model in (AlertReceipt, Alert, Rule, DailyDistance):
                session.execute(delete(model))
            measurement = session.get(Measurement, VEHICLE)
            measurement.position_at = measurement.received_at = datetime.now(UTC)
            measurement.standing_still = True
            session.commit()
        source_state(engine, "ok")
        engine.dispose()
        return
    if sys.argv[1:] == ["drivers-case"]:
        with Session(engine) as session:
            source, now = account_key(ACCOUNT), datetime.now(UTC)
            cars = [session.get(Vehicle, VEHICLE)]
            for index in range(1, 20):
                car = Vehicle(
                    source_account=source,
                    external_uid=f"e2e-driver-car-{index}",
                    name=f"Auto kierowcy {index:02d}",
                    license_plate=f"SYN DIR {index:02d}",
                )
                session.add(car)
                cars.append(car)
            session.flush()
            for index in range(26):
                first = "Anna" if index == 0 else "Bartosz" if index == 1 else "Syntetyczny"
                last = f"Test{index:02d}" if index != 24 else "Ż" * 100
                person = Driver(
                    source_account=source,
                    first_name=first,
                    last_name=last,
                    display_name=f"{first} {last}",
                    identifier=f"SYN-DIR-{index:02d}",
                    phone=f"+48 600 000 {index:03d}",
                    email=f"synthetic-dir-{index:02d}@example.com",
                    active=index != 25,
                )
                session.add(person)
                session.flush()
                if index < 2:
                    session.add(DriverCategory(driver_id=person.id, category="B"))
                    for car in cars if index == 0 else cars[:1]:
                        session.add(
                            DriverAssignment(driver_id=person.id, vehicle_id=car.id, started_at=now)
                        )
            session.commit()
        engine.dispose()
        return
    if sys.argv[1:] == ["multiple-drivers"]:
        with Session(engine) as session:
            for suffix in ("A", "B"):
                person = Driver(
                    source_account=account_key(ACCOUNT),
                    first_name="Kierowca",
                    last_name=f"E2E {suffix}",
                    display_name=f"Kierowca E2E {suffix}",
                    identifier=f"SYN-E2E-{suffix}",
                )
                session.add(person)
                session.flush()
                session.add(
                    DriverAssignment(
                        driver_id=person.id, vehicle_id=VEHICLE, started_at=datetime.now(UTC)
                    )
                )
            session.commit()
        engine.dispose()
        return
    if len(sys.argv) == 3 and sys.argv[1] == "alerts-case":
        if sys.argv[2] not in ("single", "pages"):
            raise RuntimeError("Invalid synthetic alerts case")
        with Session(engine) as session:
            now = datetime.now(UTC)
            day = now.astimezone(ZoneInfo("Europe/Warsaw")).date()
            session.add(
                DailyDistance(
                    vehicle_id=VEHICLE,
                    event_day=day,
                    distance_km=Decimal("125.5"),
                    first_observed_at=now - timedelta(minutes=10),
                    last_observed_at=now,
                )
            )
            for _ in range(1 if sys.argv[2] == "single" else 26):
                rule = Rule(source_account=account_key(ACCOUNT), threshold_km=Decimal("100"))
                session.add(rule)
                session.flush()
                session.add(
                    Alert(
                        rule_id=rule.id,
                        vehicle_id=VEHICLE,
                        event_day=day,
                        occurred_at=now,
                        created_at=now,
                        threshold_km=Decimal("100"),
                        distance_km=Decimal("125.5"),
                    )
                )
            session.commit()
        engine.dispose()
        return
    if len(sys.argv) == 3 and sys.argv[1] == "measurement-state":
        if sys.argv[2] not in ("moving", "stopped", "offline", "unknown"):
            raise RuntimeError("Invalid synthetic measurement state")
        with Session(engine) as session:
            measurement = session.get(Measurement, VEHICLE)
            now = datetime.now(UTC)
            measurement.position_at = now - timedelta(hours=1) if sys.argv[2] == "offline" else now
            measurement.received_at = now
            measurement.standing_still = (
                None if sys.argv[2] == "unknown" else sys.argv[2] != "moving"
            )
            session.commit()
        engine.dispose()
        return
    if len(sys.argv) == 3 and sys.argv[1] == "source-state":
        if sys.argv[2] not in ("ok", "degraded", "unavailable"):
            raise RuntimeError("Invalid test source state")
        source_state(engine, sys.argv[2])
        engine.dispose()
        return
    # Override dotenv values for Alembic. No live WEBFLEET/SMTP worker is started.
    os.environ["DATABASE_URL"] = database_url
    os.environ["CORS_ORIGINS"] = "http://127.0.0.1:54173"
    os.environ["COOKIE_SECURE"] = "false"
    os.environ["SYNC_ENABLED"] = "false"
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    seed(engine)
    settings = Settings(database_url, origins=("http://127.0.0.1:54173",), webfleet_account=ACCOUNT)
    app = create_app(settings, engine=engine)
    uvicorn.run(app, host="127.0.0.1", port=58000, access_log=False)


if __name__ == "__main__":
    main()
