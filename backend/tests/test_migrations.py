import os
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import make_url


def test_postgres_migration_round_trip():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL for an isolated PostgreSQL test database")
    assert make_url(url).database.startswith("fleet_flow_test"), "Refusing a non-test database"
    environment = {**os.environ, "DATABASE_URL": url, "SYNC_ENABLED": "false"}
    for command in ("upgrade head", "check", "downgrade base", "upgrade head", "check"):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *command.split()],
            env=environment,
            capture_output=True,
            text=True,
        )
        # Never print a migration exception that may contain connection credentials.
        assert result.returncode == 0, f"Migration command failed: {command}"

def test_migrations_have_one_unique_head():
    from pathlib import Path

    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    script = ScriptDirectory.from_config(config)
    revisions = [item.revision for item in script.walk_revisions()]
    assert len(revisions) == len(set(revisions)), "Duplicate Alembic revision identifiers"
    assert len(script.get_heads()) == 1, "Alembic must have exactly one head"


def test_postgres_upgrade_from_preferences_revision_adds_vehicle_card_columns():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL for an isolated PostgreSQL test database")
    assert make_url(url).database.startswith("fleet_flow_test"), "Refusing a non-test database"
    environment = {**os.environ, "DATABASE_URL": url, "SYNC_ENABLED": "false"}

    def alembic(*arguments):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *arguments],
            env=environment,
            capture_output=True,
            text=True,
        )
        # Never print a migration exception that may contain connection credentials.
        assert result.returncode == 0, f"Migration command failed: {' '.join(arguments)}"

    engine = create_engine(url)
    try:
        alembic("downgrade", "base")
        alembic("upgrade", "0006")
        with engine.connect() as connection:
            assert inspect(connection).has_table("account_preferences")
        alembic("upgrade", "head")
        with engine.connect() as connection:
            inspector = inspect(connection)
            columns = {column["name"] for column in inspector.get_columns("vehicles")}
            assert {"make", "model", "year", "vin"} <= columns
            assert inspector.has_table("account_preferences")
    finally:
        engine.dispose()
