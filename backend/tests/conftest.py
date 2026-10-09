import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.core.models import Base
from app.core.settings import Settings
from app.main import create_app
from app.modules.auth.models import User
from app.modules.auth.service import password_hasher


@pytest.fixture
def application():
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    app = create_app(Settings("sqlite://"), engine=engine)
    with app.state.sessions() as session:
        session.add(
            User(
                username="test-user",
                display_name="Osoba testowa",
                role="admin",
                password_hash=password_hasher.hash("synthetic-test-password"),
            )
        )
        session.commit()
    with TestClient(app) as client:
        yield app, client


@pytest.fixture
def logged_in(application):
    app, client = application
    response = client.post(
        "/api/v1/auth/login",
        headers={"Origin": "http://127.0.0.1:5173"},
        json={"username": "test-user", "password": "synthetic-test-password"},
    )
    assert response.status_code == 200
    return app, client
