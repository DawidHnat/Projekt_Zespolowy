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
from sqlalchemy import create_engine, delete, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.models import Measurement, SyncState, Vehicle
from app.core.settings import Settings
from app.main import create_app
from app.modules.auth.models import LoginAttempt, LoginSession, User
from app.modules.auth.service import password_hasher
from app.modules.fleet.sync import account_key
from app.modules.trips.models import Trip

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
        known = {"e2e-editor", "e2e-viewer"}
        if any(username not in known for username in session.scalars(select(User.username))):
            raise RuntimeError("E2E database contains non-fixture users")
        for role in ("editor", "viewer"):
            username = f"e2e-{role}"
            user = session.scalar(select(User).where(User.username == username))
            if not user:
                session.add(
                    User(
                        username=username,
                        display_name=f"Test {role}",
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


def main():
    database_url = test_database_url()
    engine = create_engine(database_url)
    if sys.argv[1:] == ["reset-case"]:
        with Session(engine) as session:
            session.execute(delete(LoginAttempt))
            session.execute(delete(LoginSession))
            measurement = session.get(Measurement, VEHICLE)
            measurement.position_at = measurement.received_at = datetime.now(UTC)
            measurement.standing_still = True
            session.commit()
        source_state(engine, "ok")
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
