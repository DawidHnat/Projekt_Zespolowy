import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.models import Measurement, Vehicle
from app.modules.fleet.service import fleet_markers, fleet_page, fleet_summary


def test_postgres_search_and_lightweight_queries():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL for an isolated PostgreSQL test database")
    assert make_url(url).database.startswith("fleet_flow_test"), "Refusing a non-test database"
    engine = create_engine(url)
    source = f"sql-test-{uuid4()}"
    now = datetime.now(UTC)
    with engine.connect() as connection, connection.begin() as transaction:
        session = Session(bind=connection)
        vehicle = Vehicle(source_account=source, external_uid="fictional", name="ŁÓDŹ 100%_A")
        session.add(vehicle)
        session.add(Vehicle(source_account=source, external_uid="unicode-casefold", name="Straße"))
        session.flush()
        session.add(
            Measurement(
                vehicle_id=vehicle.id,
                latitude=0,
                longitude=0,
                position_at=now,
                received_at=now,
                standing_still=False,
                gps_quality="A",
            )
        )
        session.flush()
        items, total = fleet_page(session, source, 900, " łódź 100%_a ", "moving", 1, 25)
        assert total == 1 and items[0]["name"] == vehicle.name
        assert fleet_page(session, source, 900, "łódź", None, 2, 25) == ([], 1)
        assert fleet_page(session, source, 900, "STRASSE", None, 1, 25)[1] == 1
        assert fleet_page(session, "another-source", 900, "", None, 1, 25) == ([], 0)
        features, total = fleet_markers(session, source, 900, "łódź", "moving")
        assert total == 1 and features[0]["geometry"]["coordinates"] == [0.0, 0.0]
        assert fleet_summary(session, source, 900) == {
            "total": 2,
            "moving": 1,
            "stopped": 0,
            "offline": 0,
            "unknown": 1,
        }
        session.close()
        transaction.rollback()
    engine.dispose()
