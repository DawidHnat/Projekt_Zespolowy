"""SCRUM-24: downgrading below 0012_trip_history must not drop imported history."""

import os
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

VEHICLE = "24242424-2424-4424-8424-242424242424"


def test_migration_0012_trip_history_blocks_lossy_downgrade_on_postgres():
    db_url = os.environ.get("TEST_DATABASE_URL")
    if not db_url or not db_url.startswith("postgresql"):
        pytest.skip("PostgreSQL migration check")
    assert make_url(db_url).database.startswith("fleet_flow_test")
    environment = {**os.environ, "DATABASE_URL": db_url, "SYNC_ENABLED": "false"}

    def run_alembic(*args):
        return subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            env=environment,
            capture_output=True,
            text=True,
        )

    def delete_history():
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM trip_history_days WHERE vehicle_id = :id"), {"id": VEHICLE}
            )
            conn.execute(text("DELETE FROM vehicles WHERE id = :id"), {"id": VEHICLE})

    engine = create_engine(db_url)
    assert run_alembic("downgrade", "base").returncode == 0
    assert run_alembic("upgrade", "head").returncode == 0
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO vehicles (id, source_account, external_uid, name, active, "
                    "locally_edited, manual_name, manual_license_plate, manual_vehicle_type, "
                    "card_version) VALUES (:id, 'syn', 'wf-24', 'Historia', true, false, false, "
                    "false, false, 1)"
                ),
                {"id": VEHICLE},
            )
            conn.execute(
                text(
                    "INSERT INTO trip_history_days (vehicle_id, report_day, imported_at) "
                    "VALUES (:id, DATE '2026-11-20', now())"
                ),
                {"id": VEHICLE},
            )
        failed = run_alembic("downgrade", "0011_vehicle_card_ownership")
        assert failed.returncode != 0
        assert "SCRUM-24" in (failed.stderr + failed.stdout)
        with engine.connect() as conn:
            assert conn.scalar(text("SELECT count(*) FROM trip_history_days")) == 1
        delete_history()
        assert run_alembic("downgrade", "0011_vehicle_card_ownership").returncode == 0
        assert run_alembic("upgrade", "head").returncode == 0
    finally:
        try:
            delete_history()
        except Exception:
            pass
        run_alembic("downgrade", "base")
        run_alembic("upgrade", "head")
        engine.dispose()
