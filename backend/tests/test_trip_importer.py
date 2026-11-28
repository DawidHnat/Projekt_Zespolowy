import os
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import WebfleetSettings
from app.core.models import Driver, Vehicle
from app.core.settings import Settings
from app.integrations.webfleet.client import WebfleetClient
from app.main import create_app
from app.modules.auth.models import LoginSession, User
from app.modules.auth.service import password_hasher
from app.modules.drivers.models import DriverAssignment
from app.modules.fleet.sync import account_key
from app.modules.trips.importer import import_one_day
from app.modules.trips.models import (
    Trip,
    TripAnnotation,
    TripHistoryDay,
    TripHistorySource,
    TripStop,
)
from app.modules.trips.service import polish_day

FIRST = date(2026, 10, 24)
LAST = date(2026, 10, 25)
UID = "synthetic-history-object"
AUTH = {"Origin": "http://127.0.0.1:5173"}


@pytest.mark.parametrize(("day", "hours"), [(date(2026, 3, 29), 23), (LAST, 25)])
def test_report_windows_follow_polish_daylight_saving(day, hours):
    lower, upper = polish_day(day)
    assert upper - lower == timedelta(hours=hours)
    assert lower.tzinfo is UTC and upper.tzinfo is UTC


def test_postgres_import_resumes_and_preserves_trip_identity_and_annotations():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires an isolated PostgreSQL database")
    parsed = make_url(url)
    assert parsed.host in ("127.0.0.1", "localhost")
    assert parsed.database.startswith("fleet_flow_test")
    engine = create_engine(url)
    suffix = uuid4().hex
    account = "history-test-" + suffix
    settings = WebfleetSettings(account, "test", "test", "test")
    source = account_key(account)
    vehicle_id, driver_id, user_id = uuid4(), uuid4(), uuid4()
    username = f"history-{suffix}"
    password = "synthetic-driver-test-password"
    first_start, last_start = polish_day(FIRST)
    _, last_end = polish_day(LAST)
    trip_start = last_start - timedelta(minutes=10)
    trip_end = last_start + timedelta(minutes=11)
    base_time = last_end + timedelta(hours=3)
    now = base_time
    fail_stops = False
    source_report = {"trips": None, "stops": None}  # None = the default synthetic report
    requests = []

    def provider(request):
        params = request.url.params
        action = params["action"]
        window_start = datetime.fromisoformat(params["rangefrom_string"])
        window_end = datetime.fromisoformat(params["rangeto_string"])
        assert params["objectuid"] == UID and params["range_pattern"] == "ud"
        assert params["useISO8601"] == "true"
        assert (window_start, window_end) in ((first_start, last_start), (last_start, last_end))
        assert not {"driveruid", "drivername", "driverno"} & set(params["columnfilter"].split(","))
        requests.append((action, window_start))
        if window_start == first_start:
            return httpx.Response(200, json=[])
        if action == "showTripReportExtern":
            trip = {
                "tripid": "101",
                "objectuid": UID,
                "start_time": trip_start.isoformat(),
                "end_time": trip_end.isoformat(),
                "distance": 12_345,
                "start_postext": "Początek syntetyczny",
                "drivername": "ignore",
            }
            if source_report["trips"] is not None:
                return httpx.Response(200, json=[{**trip, **row} for row in source_report["trips"]])
            return httpx.Response(200, json=[trip, trip, {**trip, "tripid": 102, "tripmode": 4}])
        assert action == "showStandStills"
        if fail_stops:
            return httpx.Response(429, headers={"Retry-After": "120"})
        if source_report["stops"] is not None:
            return httpx.Response(200, json=source_report["stops"])
        return httpx.Response(
            200,
            json=[
                {
                    "start_time": trip_end.isoformat(),
                    "end_time": (trip_end + timedelta(minutes=9)).isoformat(),
                    "latitude": 0,
                    "longitude": 0,
                },
                {
                    "start_time": (trip_end + timedelta(minutes=10)).isoformat(),
                    "end_time": (trip_end + timedelta(minutes=12)).isoformat(),
                },
            ],
        )

    def run(*, refresh=False):
        return import_one_day(
            engine,
            settings,
            vehicle_id,
            LAST if refresh else FIRST,
            LAST,
            refresh=refresh,
            client_factory=lambda config: WebfleetClient(
                config, transport=httpx.MockTransport(provider)
            ),
            clock=lambda: now,
        )

    try:
        with Session(engine) as session:
            session.add_all(
                [
                    User(
                        id=user_id,
                        username=username,
                        display_name="Synthetic user",
                        password_hash=password_hasher.hash(password),
                        role="editor",
                    ),
                    Driver(id=driver_id, source_account=source, display_name="Synthetic driver"),
                    Vehicle(
                        id=vehicle_id, source_account=source, external_uid=UID, name="Synthetic van"
                    ),
                ]
            )
            session.flush()
            assignment = DriverAssignment(
                driver_id=driver_id,
                vehicle_id=vehicle_id,
                started_at=trip_start - timedelta(days=1),
                recorded_at=trip_start,
            )
            session.add(assignment)
            session.flush()
            assignment_id = assignment.id
            session.commit()

        app = create_app(Settings(database_url=url, webfleet_account=account))
        with TestClient(app) as client:
            assert (
                client.post(
                    "/api/v1/auth/login",
                    headers=AUTH,
                    json={
                        "username": username,
                        "password": password,
                    },
                ).status_code
                == 200
            )
            query = {
                "vehicle_id": str(vehicle_id),
                "from": first_start.isoformat(),
                "to": last_end.isoformat(),
            }
            path = "/api/v1/trips"
            assert client.get(path, params=query).json()["coverage"]["state"] == "unavailable"

            assert run() == "imported"
            now += timedelta(seconds=30)
            assert run() == "rate_limited"
            now += timedelta(seconds=30)
            fail_stops = True
            assert run() == "degraded"
            report = client.get(path, params=query).json()
            assert report["items"] == []
            assert report["coverage"]["covered_days"] == [FIRST.isoformat()]
            assert report["coverage"]["failed_days"] == [LAST.isoformat()]
            now += timedelta(seconds=60)
            assert run() == "rate_limited"
            now += timedelta(seconds=60)
            fail_stops = False
            assert run() == "imported" and run() == "complete"
            assert len(requests) == 6

            report = client.get(path, params=query).json()
            assert report["coverage"]["state"] == "complete"
            (trip,) = report["items"]
            assert trip["distance_km"] == 12.345
            assert trip["driver_id"] == str(driver_id)
            assert trip["start_address"] == "Początek syntetyczny" and trip["end_address"] is None
            assert trip["geometry"] is None
            response = client.patch(
                f"{path}/{trip['id']}/annotation",
                headers=AUTH,
                json={
                    "version": 1,
                    "purpose": "Serwis",
                    "description": "Syntetyczny opis",
                },
            )
            assert response.status_code == 200
            annotation = response.json()
            stops = client.get(path + "/stops", params=query).json()
            assert stops["total"] == 1 and stops["items"][0]["duration_seconds"] == 540
            assert stops["items"][0]["latitude"] == 0 and stops["items"][0]["longitude"] == 0
            assert (
                client.get(path + "/stops", params={**query, "min_duration_seconds": 0}).json()[
                    "total"
                ]
                == 2
            )

            with Session(engine) as session:
                assignment = session.get(DriverAssignment, assignment_id)
                assignment.active = False
                assignment.ended_at = base_time
                session.commit()

            # Restart the application's database connections before re-fetching the same day.
            engine.dispose()
            now += timedelta(minutes=1)
            assert run(refresh=True) == "imported"
            data = client.get(path, params=query).json()
            (restored,) = data["items"]
            assert restored["id"] == trip["id"] and restored["driver_id"] == trip["driver_id"]
            assert restored["annotation"] == annotation
            assert client.get(path + "/stops", params=query).json()["total"] == 1
            assert restored["withdrawn_at"] is None

            # A later complete report drops the annotated trip and the stop, adds trip 103.
            source_report["trips"], source_report["stops"] = [{"tripid": "103"}], []
            now += timedelta(minutes=1)
            assert run(refresh=True) == "imported"
            items = {item["id"]: item for item in client.get(path, params=query).json()["items"]}
            kept = items[trip["id"]]
            assert kept["withdrawn_at"] is not None and kept["annotation"] == annotation
            assert len(items) == 2
            assert (
                client.get(path + "/stops", params={**query, "min_duration_seconds": 0}).json()[
                    "total"
                ]
                == 0
            )

            # Trip 103 had no local annotation, so its withdrawal removes it.
            source_report["trips"] = []
            now += timedelta(minutes=1)
            assert run(refresh=True) == "imported"
            (only,) = client.get(path, params=query).json()["items"]
            assert only["id"] == trip["id"] and only["withdrawn_at"] is not None

            # The trip is back in the source report: same UUID, annotation kept, flag cleared.
            source_report["trips"], source_report["stops"] = None, None
            now += timedelta(minutes=1)
            assert run(refresh=True) == "imported"
            (back,) = client.get(path, params=query).json()["items"]
            assert back["id"] == trip["id"] and back["withdrawn_at"] is None
            assert back["annotation"] == annotation

            fleet = client.get(
                path, params={k: v for k, v in query.items() if k != "vehicle_id"}
            ).json()
            assert fleet["items"][0]["vehicle_name"] == "Synthetic van"
            assert fleet["coverage"] is None
    finally:
        with Session(engine) as session:
            for model, filter_by in (
                (
                    TripAnnotation,
                    TripAnnotation.trip_id.in_(
                        select(Trip.id).where(Trip.vehicle_id == vehicle_id)
                    ),
                ),
                (TripStop, TripStop.vehicle_id == vehicle_id),
                (TripHistoryDay, TripHistoryDay.vehicle_id == vehicle_id),
                (TripHistorySource, TripHistorySource.source_account == source),
                (Trip, Trip.vehicle_id == vehicle_id),
                (DriverAssignment, DriverAssignment.vehicle_id == vehicle_id),
                (Vehicle, Vehicle.id == vehicle_id),
                (Driver, Driver.id == driver_id),
                (LoginSession, LoginSession.user_id == user_id),
                (User, User.id == user_id),
            ):
                session.execute(delete(model).where(filter_by))
            session.commit()
        engine.dispose()
