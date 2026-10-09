import os
import subprocess
import sys

import pytest
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
