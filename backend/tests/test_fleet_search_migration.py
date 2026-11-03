import os
import subprocess
import sys
from uuid import uuid4

import pytest
from sqlalchemy import MetaData, Table, create_engine, select
from sqlalchemy.engine import make_url


def test_search_migration_backfills_unicode_without_changing_vehicle_ownership():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires an isolated PostgreSQL database")
    assert make_url(url).database.startswith("fleet_flow_test"), "Refusing a non-test database"
    environment = {**os.environ, "DATABASE_URL": url, "SYNC_ENABLED": "false"}

    def migrate(*command):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *command],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, "Failed synthetic search migration"

    engine = create_engine(url)
    identity, driver_id = uuid4(), uuid4()
    source = "migration-search-" + uuid4().hex
    migrate("upgrade", "head")
    migrate("downgrade", "0005")
    metadata = MetaData()
    vehicles = Table("vehicles", metadata, autoload_with=engine)
    drivers = Table("drivers", metadata, autoload_with=engine)
    try:
        with engine.begin() as connection:
            connection.execute(
                drivers.insert().values(id=driver_id, display_name="Synthetic", active=True)
            )
            connection.execute(
                vehicles.insert().values(
                    id=identity,
                    source_account=source,
                    external_uid="fixed-source-id",
                    name="Straße",
                    number=None,
                    license_plate="ß%_",
                    active=True,
                    driver_id=driver_id,
                )
            )
        migrate("upgrade", "head")
        updated = Table("vehicles", MetaData(), autoload_with=engine)
        with engine.connect() as connection:
            row = (
                connection.execute(select(updated).where(updated.c.id == identity)).mappings().one()
            )
            assert row["search_name"] == "strasse" and row["search_number"] == ""
            assert row["search_license_plate"] == "ss%_"
            assert row["name"] == "Straße" and row["external_uid"] == "fixed-source-id"
            assert row["driver_id"] == driver_id and row["id"] == identity
        migrate("downgrade", "0005")
        with engine.connect() as connection:
            row = (
                connection.execute(select(vehicles).where(vehicles.c.id == identity))
                .mappings()
                .one()
            )
            assert row["driver_id"] == driver_id and row["name"] == "Straße"
    finally:
        migrate("upgrade", "head")
        with engine.begin() as connection:
            connection.execute(vehicles.delete().where(vehicles.c.id == identity))
            connection.execute(drivers.delete().where(drivers.c.id == driver_id))
        engine.dispose()
