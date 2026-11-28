import os
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, inspect, text
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


def test_postgres_upgrade_from_preferences_adds_vehicle_columns_and_preserves_email_alias():
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
        with engine.begin() as connection:
            assert inspect(connection).has_table("account_preferences")
            connection.execute(
                text(
                    "INSERT INTO users "
                    "(id, username, display_name, email, password_hash, role, active) "
                    "VALUES ('20000000-0000-4000-8000-000000000001', 'legacy-alias', 'Test', "
                    "'İstanbul@example.com', 'synthetic-placeholder', 'viewer', true)"
                )
            )
        alembic("upgrade", "head")
        with engine.connect() as connection:
            inspector = inspect(connection)
            columns = {column["name"] for column in inspector.get_columns("vehicles")}
            assert {"make", "model", "year", "vin"} <= columns
            assert inspector.has_table("account_preferences")
            email, identifier = connection.execute(
                text("SELECT email, email_identifier FROM users WHERE username = 'legacy-alias'")
            ).one()
            assert email == "İstanbul@example.com"
            assert identifier == email.lower()
    finally:
        engine.dispose()
