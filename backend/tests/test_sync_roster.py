import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import WebfleetSettings
from app.core.models import Base, Measurement, Vehicle
from app.modules.fleet.service import fleet_markers, fleet_page, source_payload
from app.modules.fleet.sync import account_key, sync_once


@pytest.mark.parametrize("remaining", [0, 1])
def test_incomplete_master_report_preserves_last_complete_fleet(remaining):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires an isolated PostgreSQL database")
    parsed = make_url(url)
    assert parsed.host in ("127.0.0.1", "localhost")
    assert parsed.database.startswith("fleet_flow_test")
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    settings = WebfleetSettings(f"synthetic-roster-{uuid4()}", "test", "test", "test")
    source = account_key(settings.account)
    now = datetime.now(UTC).replace(microsecond=0)
    uids = ("synthetic-roster-1", "synthetic-roster-2")

    def run(offset, reported_uids):
        seen_at = now + timedelta(minutes=offset)

        class FakeWebfleet:
            def __init__(self, settings):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_):
                pass

            async def fetch_vehicles(self):
                return [
                    {"objectuid": uid, "objectname": f"Vehicle {index + 1}"}
                    for index, uid in enumerate(reported_uids)
                ]

            async def fetch_objects(self):
                return [
                    {
                        "objectuid": uid,
                        "pos_time": seen_at.isoformat(),
                        "status": "A",
                        "latitude_mdeg": offset * 1000000,
                        "longitude_mdeg": 0,
                    }
                    for uid in reported_uids
                ]

        return sync_once(engine, settings, client_factory=FakeWebfleet, now=seen_at)

    try:
        assert run(0, ()) == "ok"
        with Session(engine) as session:
            assert source_payload(session, source)["status"] == "ok"
            assert fleet_page(session, source, 900, "", None, 1, 25, "name-asc")[1] == 0

        assert run(1, uids) == "ok"
        assert run(2, uids[:remaining]) == "degraded"
        with Session(engine) as session:
            meta = source_payload(session, source)
            assert meta == {
                "status": "degraded",
                "last_success_at": (now + timedelta(minutes=1)).isoformat(),
                "error_code": "INCOMPLETE_REPORT",
            }
            items, total = fleet_page(
                session, source, 900, "", None, 1, 25, "name-asc", source_degraded=True
            )
            features, _ = fleet_markers(session, source, 900, "", None, source_degraded=True)
            assert total == len(features) == 2
            assert all(item["is_stale"] and item["latitude"] == 1 for item in items)
            vehicle_ids = {item["id"] for item in items}

        assert run(3, uids) == "ok"
        with Session(engine) as session:
            assert source_payload(session, source)["status"] == "ok"
            rows = session.execute(
                select(Vehicle, Measurement)
                .join(Measurement)
                .where(Vehicle.source_account == source)
            ).all()
            assert {str(vehicle.id) for vehicle, _ in rows} == vehicle_ids
            assert all(
                vehicle.active and measurement.latitude == 3 for vehicle, measurement in rows
            )
    finally:
        engine.dispose()
