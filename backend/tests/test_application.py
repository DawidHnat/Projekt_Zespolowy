from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.core.settings import Settings
from app.main import create_app


def test_health_and_private_cache_headers():
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    with TestClient(create_app(Settings("sqlite://"), engine=engine)) as client:
        assert client.get("/api/health/live").json() == {"status": "ok"}
        result = client.get("/api/health/ready")
        assert result.status_code == 200
        assert result.headers["cache-control"] == "no-store"


def test_readiness_does_not_expose_database_errors(monkeypatch):
    from sqlalchemy.exc import OperationalError

    engine = create_engine("sqlite://")

    def fail():
        raise OperationalError("secret-sql", {}, Exception("secret-host-password"))

    monkeypatch.setattr(engine, "connect", fail)
    with TestClient(create_app(Settings("sqlite://"), engine=engine)) as client:
        response = client.get("/api/health/ready")
        assert response.status_code == 503
        assert response.json() == {"status": "unavailable"}
