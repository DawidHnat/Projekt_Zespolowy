from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.seed import seed_demo
from app.main import create_app


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_demo(session, now=datetime(2026, 10, 7, 10, tzinfo=UTC))
    yield engine
    engine.dispose()


@pytest.fixture
def client(engine):
    settings = Settings(_env_file=None, database_url="sqlite://", data_source="demo")
    with TestClient(create_app(settings, engine)) as client:
        yield client
