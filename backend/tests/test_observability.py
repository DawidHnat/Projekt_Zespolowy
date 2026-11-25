"""SCRUM-114: bounded operational metrics and validated X-Correlation-ID in API and worker."""

import asyncio
import base64
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool

from app.core.models import Base, Measurement, SyncState, Vehicle
from app.core.observability import (
    CORRELATION_HEADER,
    MetricsRegistry,
    inspect_backup_and_restore,
    inspect_tls_certificate,
)
from app.core.settings import Settings
from app.main import create_app
from app.modules.auth.models import User
from app.modules.auth.reset import deliver_reset
from app.modules.auth.service import password_hasher
from app.modules.fleet import sync
from app.modules.fleet.sync import account_key

ORIGIN = {"Origin": "http://127.0.0.1:5173"}


def _der_tlv(tag: int, body: bytes) -> bytes:
    length = len(body)
    if length < 0x80:
        header = bytes([tag, length])
    else:
        encoded = length.to_bytes((length.bit_length() + 7) // 8, "big")
        header = bytes([tag, 0x80 | len(encoded)]) + encoded
    return header + body


def build_synthetic_pem_cert(not_before: datetime, not_after: datetime) -> str:
    nb = _der_tlv(0x18, not_before.astimezone(UTC).strftime("%Y%m%d%H%M%SZ").encode("ascii"))
    na = _der_tlv(0x18, not_after.astimezone(UTC).strftime("%Y%m%d%H%M%SZ").encode("ascii"))
    validity = _der_tlv(0x30, nb + na)
    version = _der_tlv(0xA0, _der_tlv(0x02, b"\x02"))
    serial = _der_tlv(0x02, b"\x01")
    alg = _der_tlv(0x30, _der_tlv(0x06, b"\x2a\x86\x48\x86\xf7\x0d\x01\x01\x0b"))
    dn = _der_tlv(0x30, b"")
    tbs = _der_tlv(0x30, version + serial + alg + dn + validity + dn + alg)
    cert = _der_tlv(0x30, tbs + alg + _der_tlv(0x03, b"\x00"))
    b64 = base64.b64encode(cert).decode("ascii")
    return f"-----BEGIN CERTIFICATE-----\n{b64}\n-----END CERTIFICATE-----\n"


def test_correlation_id_validation_generation_and_no_secret_leak(logged_in, caplog):
    app, client = logged_in

    # Valid bounded correlation ID is preserved in response header (and in 5xx JSON error body).
    valid_cid = "req-2026_11_25.abc-XYZ-99"
    not_found = client.get(
        "/api/v1/trips/11111111-1111-4111-8111-111111111111",
        headers={CORRELATION_HEADER: valid_cid},
    )
    assert not_found.status_code == 404
    assert not_found.headers[CORRELATION_HEADER] == valid_cid
    unavailable = client.get(
        "/api/v1/fleet/vehicles",
        headers={CORRELATION_HEADER: valid_cid},
    )
    assert unavailable.status_code == 503
    assert unavailable.headers[CORRELATION_HEADER] == valid_cid
    assert unavailable.json()["error"]["correlation_id"] == valid_cid

    # Invalid, short, overlong, or CRLF/secret-bearing headers are replaced with safe 32-hex IDs.
    for unsafe in (
        "",
        "short",
        "x" * 65,
        "bad space id",
        "inject\r\nSet-Cookie: evil=1",
        "secret-token?apikey=SUPERSECRET123",
    ):
        resp = client.get("/api/health/live", headers={CORRELATION_HEADER: unsafe})
        assert resp.status_code == 200
        returned = resp.headers[CORRELATION_HEADER]
        assert returned != unsafe
        assert len(returned) == 32 and all(ch in "0123456789abcdef" for ch in returned)

    # Unhandled 500 logs correlation_id and route template without query secrets or exception text.
    @app.get("/api/v1/_synthetic_crash")
    def synthetic_crash():
        raise RuntimeError("synthetic-db-password-and-gps-54.352,18.646")

    crash = client.get(
        "/api/v1/_synthetic_crash?apikey=TOPSECRET_KEY&email=driver@example.com",
        headers={CORRELATION_HEADER: "incident-corr-0001"},
    )
    assert crash.status_code == 500
    assert crash.headers[CORRELATION_HEADER] == "incident-corr-0001"
    assert crash.json()["error"] == {
        "code": "INTERNAL_ERROR",
        "message": "Wystąpił błąd serwera",
        "correlation_id": "incident-corr-0001",
    }
    assert "TOPSECRET_KEY" not in caplog.text
    assert "driver@example.com" not in caplog.text
    assert "synthetic-db-password" not in caplog.text
    obs_logs = [
        json.loads(r.message) for r in caplog.records if r.name == "fleet_flow.observability"
    ]
    assert obs_logs == [
        {
            "event": "http_server_error",
            "method": "GET",
            "route": "/api/v1/fleet/vehicles",
            "status": 503,
            "correlation_id": valid_cid,
        },
        {
            "event": "http_server_error",
            "method": "GET",
            "route": "/api/v1/_synthetic_crash",
            "status": 500,
            "correlation_id": "incident-corr-0001",
        },
    ]


def test_metrics_endpoint_rbac_bounded_labels_sync_auth_smtp_and_no_pii(tmp_path, monkeypatch):
    now = datetime.now(UTC)
    cert_file = tmp_path / "cert.pem"
    cert_file.write_text(
        build_synthetic_pem_cert(now - timedelta(days=10), now + timedelta(days=14)),
        encoding="utf-8",
    )

    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    settings = Settings(
        database_url="sqlite://",
        webfleet_account="synthetic-secret-webfleet-account",
        tls_cert_path=str(cert_file),
        disk_path=str(tmp_path),
    )
    app = create_app(settings, engine=engine)
    source = account_key(settings.webfleet_account)

    with app.state.sessions() as session:
        admin = User(
            username="admin-obs",
            display_name="Admin Obs",
            email="private-admin@example.com",
            role="admin",
            password_hash=password_hasher.hash("synthetic-admin-password"),
        )
        session.add(admin)
        session.add(
            SyncState(
                source_account=source,
                last_success_at=now - timedelta(seconds=25),
                error_code="timeout",
            )
        )
        vehicle = Vehicle(
            source_account=source,
            external_uid="private-webfleet-uid-999",
            name="Poufny Pojazd",
            license_plate="GD SECRET1",
        )
        session.add(vehicle)
        session.flush()
        session.add(
            Measurement(
                vehicle_id=vehicle.id,
                latitude=54.35205,
                longitude=18.64637,
                gps_quality="A",
                standing_still=True,
                position_at=now - timedelta(seconds=15),
                received_at=now - timedelta(seconds=15),
                odometer_km=Decimal("42000.0"),
            )
        )
        session.commit()

    with TestClient(app) as client:
        # Unauthenticated cannot scrape metrics.
        assert client.get("/api/v1/observability/metrics").status_code == 401

        # Trigger failed login, forbidden Origin, and unmatched 404 with sensitive URL segment.
        client.post(
            "/api/v1/auth/login",
            headers=ORIGIN,
            json={"username": "private-admin@example.com", "password": "wrong-secret-password"},
        )
        client.post(
            "/api/v1/auth/login",
            headers={"Origin": "https://evil.invalid"},
            json={"username": "admin-obs", "password": "synthetic-admin-password"},
        )
        client.get("/api/v1/unknown/secret-path-token-12345?gps=54.35205,18.64637")

        # Simulate failed SMTP password reset delivery without real network.
        monkeypatch.setattr(
            "app.modules.auth.reset.SmtpSettings.from_environment",
            lambda _env: object(),
        )

        def fail_smtp(*_args, **_kwargs):
            raise OSError("smtp-secret-password-leak")

        monkeypatch.setattr("app.modules.auth.reset.send_password_reset", fail_smtp)
        deliver_reset(app, "admin-obs", "http://127.0.0.1:5173", "reset-corr-12345678")

        # Log in as admin.
        assert (
            client.post(
                "/api/v1/auth/login",
                headers=ORIGIN,
                json={"username": "admin-obs", "password": "synthetic-admin-password"},
            ).status_code
            == 200
        )

        # Editor and viewer are denied access to operator metrics (403 FORBIDDEN).
        for role in ("editor", "viewer"):
            with app.state.sessions() as session:
                user = session.scalar(select(User).where(User.username == "admin-obs"))
                user.role = role
                session.commit()
            assert client.get("/api/v1/observability/metrics").status_code == 403

        with app.state.sessions() as session:
            user = session.scalar(select(User).where(User.username == "admin-obs"))
            user.role = "admin"
            session.commit()

        res = client.get("/api/v1/observability/metrics")
        assert res.status_code == 200
        snap = res.json()
        serialized = json.dumps(snap)

        assert snap["api_up"] == 1
        assert snap["db_pool"]["db_up"] is True
        assert snap["http"]["requests_total"] >= 5
        assert snap["http"]["duration_p95_ms"] is not None
        # Unmatched 404 paths collapse to "unmatched" — never leaking path tokens.
        routes = {item["route"] for item in snap["http"]["by_route"]}
        assert "unmatched" in routes
        assert not any("secret-path-token" in r for r in routes)

        # Sync age & error code reported without leaking account, UID, plate, or GPS.
        assert snap["sync"]["status"] == "degraded"
        assert snap["sync"]["last_error_code"] == "timeout"
        assert snap["sync"]["last_success_age_seconds"] is not None
        assert snap["sync"]["latest_measurement_age_seconds"] is not None

        # Backup and restore explicitly show not_configured -> deferred_to SCRUM-84 (no fake dates).
        assert snap["backup"] == {
            "status": "not_configured",
            "deferred_to": "SCRUM-84",
            "last_success_age_seconds": None,
            "max_age_seconds": 25200,
        }
        assert snap["restore"]["status"] == "not_configured"
        assert snap["restore"]["deferred_to"] == "SCRUM-84"

        # TLS certificate remaining days (~14d <= 21d warning threshold -> warning).
        assert snap["tls"]["status"] == "warning"
        assert 13.5 <= snap["tls"]["days_remaining"] <= 14.5

        # Disk bytes reported without leaking tmp_path.
        assert snap["disk"]["free_bytes"] > 0
        assert str(tmp_path) not in serialized

        # Auth and SMTP counters incremented with fixed codes only.
        assert snap["auth"]["events_total"]["login_failed"] >= 1
        assert snap["auth"]["events_total"]["forbidden"] >= 3
        assert snap["auth"]["events_total"]["unauthenticated"] >= 1
        assert snap["mail"]["events_total"]["smtp_failed"] == 1
        assert snap["mail"]["queue"]["status"] == "not_configured"
        assert snap["mail"]["queue"]["deferred_to"] == "SCRUM-73"

        # Zero secrets, PII, emails, tokens, or GPS in JSON or Prometheus output.
        prom = client.get("/api/v1/observability/metrics?format=prometheus")
        assert prom.status_code == 200
        assert "fleet_flow_api_up 1" in prom.text
        assert 'fleet_flow_auth_events_total{code="login_failed"}' in prom.text
        assert 'fleet_flow_smtp_events_total{code="smtp_failed"} 1' in prom.text
        for forbidden_text in (
            "synthetic-secret-webfleet-account",
            "private-webfleet-uid-999",
            "GD SECRET1",
            "54.35205",
            "18.64637",
            "private-admin@example.com",
            "wrong-secret-password",
            "smtp-secret-password-leak",
            "secret-path-token-12345",
        ):
            assert forbidden_text not in serialized
            assert forbidden_text not in prom.text


def test_backup_tls_and_worker_correlation_helpers(tmp_path, monkeypatch, caplog):
    now = datetime(2026, 11, 25, 20, 0, 0, tzinfo=UTC)

    # Configured backup markers distinguish ok, stale, and missing without leaking repository URL.
    (tmp_path / "last-backup.json").write_text(
        json.dumps(
            {
                "completed_at": (now - timedelta(hours=2)).isoformat(),
                "repository": "s3:https://secret-bucket.invalid",
            }
        ),
        encoding="utf-8",
    )
    state = inspect_backup_and_restore(str(tmp_path), now=now)
    assert state["backup"]["status"] == "ok"
    assert state["backup"]["last_success_age_seconds"] == 7200.0
    assert state["restore"]["status"] == "missing"
    assert "secret-bucket" not in json.dumps(state)

    # TLS critical & ok thresholds.
    crit = tmp_path / "crit.pem"
    crit.write_text(build_synthetic_pem_cert(now - timedelta(days=1), now + timedelta(days=3)))
    assert inspect_tls_certificate(str(crit), now=now)["status"] == "critical"
    ok_cert = tmp_path / "ok.pem"
    ok_cert.write_text(build_synthetic_pem_cert(now - timedelta(days=1), now + timedelta(days=60)))
    assert inspect_tls_certificate(str(ok_cert), now=now)["status"] == "ok"

    # Worker binds distinct correlation_id per cycle inside existing SCRUM-64 log without duplicate.
    metrics = MetricsRegistry()
    calls = []

    def fake_sync_once(*_args, **_kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("secret-worker-exception")
        return "degraded"

    async def stop_after_two(_):
        if len(calls) == 2:
            raise asyncio.CancelledError

    monkeypatch.setattr(sync, "sync_once", fake_sync_once)
    monkeypatch.setattr(sync.asyncio, "sleep", stop_after_two)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(sync.sync_worker(None, None, 60, metrics=metrics))

    records = [json.loads(r.message) for r in caplog.records if r.name == "fleet_flow.sync"]
    assert len(records) == 2
    assert records[0]["code"] == "SYNC_INTERNAL_ERROR"
    assert records[1]["code"] == "SOURCE_DEGRADED"
    assert len(records[0]["correlation_id"]) == 32
    assert len(records[1]["correlation_id"]) == 32
    assert records[0]["correlation_id"] != records[1]["correlation_id"]
    snap = metrics.snapshot_counters()["sync_events"]
    assert snap["SYNC_INTERNAL_ERROR"] == 1
    assert snap["SOURCE_DEGRADED"] == 1
