import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import MetaData, Table, create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError


def test_role_migration_preserves_accounts_and_rejects_invalid_direct_writes():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires an isolated PostgreSQL database")
    parsed = make_url(url)
    assert parsed.host in ("127.0.0.1", "localhost") and parsed.database.startswith(
        "fleet_flow_test"
    )
    environment = {**os.environ, "DATABASE_URL": url, "SYNC_ENABLED": "false"}

    def migrate(*command, success=True):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *command],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        assert (result.returncode == 0) is success, "Unexpected role migration result"
        return result

    engine = create_engine(url)
    first, dirty = uuid4(), uuid4()
    token_hash = uuid4().hex * 2
    migrate("upgrade", "head")
    migrate("downgrade", "0006_fleet_search")
    users = Table("users", MetaData(), autoload_with=engine)
    sessions = Table("login_sessions", MetaData(), autoload_with=engine)
    try:
        with engine.begin() as connection:
            for identity, role in ((first, "editor"), (dirty, "legacy-invalid")):
                connection.execute(
                    users.insert().values(
                        id=identity,
                        username="synthetic-" + identity.hex,
                        display_name="Synthetic",
                        password_hash="synthetic-hash",
                        active=True,
                        role=role,
                    )
                )
            connection.execute(
                sessions.insert().values(
                    token_hash=token_hash,
                    user_id=first,
                    expires_at=datetime.now(UTC) + timedelta(hours=1),
                )
            )
        failed = migrate("upgrade", "head", success=False)
        assert "operator review required" in failed.stderr
        assert "synthetic-" not in failed.stderr and "synthetic-hash" not in failed.stderr
        with engine.begin() as connection:
            assert (
                connection.scalar(select(users.c.role).where(users.c.id == dirty))
                == "legacy-invalid"
            )
            assert (
                connection.scalar(text("SELECT version_num FROM alembic_version"))
                == "0006_fleet_search"
            )
            # Explicit correction of a disposable fixture, never automatic production coercion.
            connection.execute(users.update().where(users.c.id == dirty).values(role="viewer"))
        migrate("upgrade", "head")
        for invalid in ("owner", "ADMIN", "", "viewer "):
            with pytest.raises(IntegrityError):
                with engine.begin() as connection:
                    connection.execute(
                        users.update().where(users.c.id == first).values(role=invalid)
                    )
        with engine.connect() as connection:
            assert connection.scalar(select(users.c.role).where(users.c.id == first)) == "editor"
            assert (
                connection.scalar(
                    select(sessions.c.user_id).where(sessions.c.token_hash == token_hash)
                )
                == first
            )
        migrate("downgrade", "0006_fleet_search")
        with engine.connect() as connection:
            assert connection.scalar(select(users.c.role).where(users.c.id == dirty)) == "viewer"
    finally:
        with engine.begin() as connection:
            connection.execute(sessions.delete().where(sessions.c.token_hash == token_hash))
            connection.execute(users.delete().where(users.c.id.in_((first, dirty))))
        migrate("upgrade", "head")
        engine.dispose()
