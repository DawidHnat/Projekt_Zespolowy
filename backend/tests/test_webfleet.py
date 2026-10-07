import base64
import logging
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.integrations.webfleet.client import WebfleetClient, WebfleetError
from app.integrations.webfleet.mapper import map_vehicles
from app.integrations.webfleet.sync import store_snapshot
from app.modules.fleet.models import VehicleRecord
from app.modules.trips.models import TripRecord

NOW = datetime(2026, 10, 7, 10, tzinfo=UTC)
MASTER = [
    {"objectuid": "123", "objectno": "001", "objectname": "Van", "licenseplatenumber": "GD 1"}
]
TELEMETRY = [
    {
        "objectuid": "123",
        "objectno": "001",
        "status": "A",
        "pos_time": "2026-10-07T09:58:00Z",
        "speed": "45",
        "odometer_long": "74210000",
        "odometer": "742100",
        "latitude_mdeg": "54352000",
        "longitude_mdeg": "18646600",
    }
]


@pytest.fixture
def configured():
    return Settings(
        _env_file=None,
        webfleet_account=SecretStr("private-account"),
        webfleet_username=SecretStr("private-user"),
        webfleet_password=SecretStr("private-password"),
        webfleet_api_key=SecretStr("private-key"),
    )


def test_documented_readonly_get_basic_auth_and_json(configured, caplog):
    requests = []

    def handler(request):
        requests.append(request)
        assert request.method == "GET"
        assert request.url.host == "csv.webfleet.com" and request.url.scheme == "https"
        assert "username" not in request.url.params and "password" not in request.url.params
        assert (
            request.headers["Authorization"]
            == "Basic " + base64.b64encode(b"private-user:private-password").decode()
        )
        assert request.url.params["account"] == "private-account"
        assert request.url.params["apikey"] == "private-key"
        assert request.url.params["outputformat"] == "json"
        assert request.url.params["useISO8601"] == "true"
        assert request.url.params["useUTF8"] == "true"
        data = MASTER if request.url.params["action"] == "showVehicleReportExtern" else TELEMETRY
        return httpx.Response(200, json=data)

    with caplog.at_level(logging.INFO):
        with WebfleetClient(configured, httpx.MockTransport(handler)) as client:
            mapped = map_vehicles(client.vehicles(), client.objects(), now=NOW)
    assert len(requests) == 2
    vehicle = mapped[0]
    assert vehicle.status == "driving"
    assert vehicle.latitude == 54.352 and vehicle.longitude == 18.6466
    assert vehicle.odometer_km == 74210 and vehicle.speed_kmh == 45
    assert vehicle.updated_at.tzinfo == UTC
    assert "private-" not in caplog.text


@pytest.mark.parametrize("failure", ["network", "status", "header", "plain-text", "shape"])
def test_failures_never_expose_credentials_or_raw_provider_errors(configured, caplog, failure):
    def handler(request):
        secret = str(request.url) + " private-password private-user"
        if failure == "network":
            raise httpx.ConnectError(secret, request=request)
        if failure == "status":
            return httpx.Response(401, text=secret)
        if failure == "header":
            return httpx.Response(
                200,
                json=[],
                headers={"X-Webfleet-Errorcode": "1", "X-Webfleet-Errormessage": secret},
            )
        if failure == "plain-text":
            return httpx.Response(200, text=secret)
        return httpx.Response(200, json={"error": secret})

    with caplog.at_level(logging.INFO):
        with WebfleetClient(configured, httpx.MockTransport(handler)) as client:
            with pytest.raises(WebfleetError) as error:
                client.vehicles()
    assert "private-" not in str(error.value)
    assert "https:" not in str(error.value)
    assert "private-" not in caplog.text


def test_client_rejects_missing_credentials():
    settings = Settings(
        _env_file=None,
        webfleet_account=None,
        webfleet_username=None,
        webfleet_password=None,
        webfleet_api_key=None,
    )
    with pytest.raises(WebfleetError, match="Missing Webfleet"):
        WebfleetClient(settings)


def test_adapter_cannot_send_mutating_action(configured):
    handler = Mock()
    with WebfleetClient(configured, httpx.MockTransport(handler)) as client:
        with pytest.raises(WebfleetError, match="Unsupported Webfleet read operation"):
            client._read("updateVehicle")
    handler.assert_not_called()


def test_missing_and_stale_data_are_not_invented():
    missing = map_vehicles(MASTER, [], NOW)[0]
    assert missing.status == "unknown"
    assert missing.speed_kmh is None and missing.odometer_km is None
    assert missing.latitude is None and missing.longitude is None
    stale = [{**TELEMETRY[0], "pos_time": (NOW - timedelta(days=2)).isoformat()}]
    assert map_vehicles(MASTER, stale, NOW)[0].status == "offline"
    legacy = [{**TELEMETRY[0], "odometer_long": "", "odometer": "1000"}]
    assert map_vehicles(MASTER, legacy, NOW)[0].odometer_km == 100
    unfamiliar = [{**TELEMETRY[0], "status": "unexpected"}]
    assert map_vehicles(MASTER, unfamiliar, NOW)[0].status == "unknown"
    invalid_coordinates = [{**TELEMETRY[0], "latitude_mdeg": 999000000}]
    assert map_vehicles(MASTER, invalid_coordinates, NOW)[0].latitude is None


def test_sync_keeps_demo_separate_preserves_trip_annotations_and_marks_missing_offline(engine):
    snapshot = map_vehicles(MASTER, TELEMETRY, NOW)
    with Session(engine) as session:
        assert store_snapshot(session, snapshot) == 1
        session.add(
            TripRecord(
                id="wf-trip-test",
                vehicle_id="wf:123",
                source="webfleet",
                started_at=NOW,
                ended_at=NOW + timedelta(minutes=10),
                distance_km=10,
                start_address="Origin",
                end_address="Destination",
                purpose="Business",
                notes="Keep me",
            )
        )
        session.commit()
        updated = map_vehicles(MASTER, [{**TELEMETRY[0], "speed": "0"}], NOW)
        assert store_snapshot(session, updated) == 1
        assert session.get(VehicleRecord, "wf:123").status == "parked"
        assert session.get(TripRecord, "wf-trip-test").notes == "Keep me"
        assert session.get(TripRecord, "wf-trip-test").purpose == "Business"
        demo_count = len(
            session.scalars(select(VehicleRecord).where(VehicleRecord.source == "demo")).all()
        )
        assert demo_count == 4
        store_snapshot(session, [])
        assert session.get(VehicleRecord, "wf:123").status == "offline"
        assert session.get(TripRecord, "wf-trip-test").notes == "Keep me"


def test_live_cli_requires_explicit_source_and_no_calls_on_wrong_mode(monkeypatch):
    from app.integrations.webfleet import sync

    monkeypatch.setattr(sync, "get_settings", lambda: Settings(_env_file=None, data_source="demo"))
    client = Mock()
    monkeypatch.setattr(sync, "WebfleetClient", client)
    with pytest.raises(SystemExit, match="DATA_SOURCE=webfleet"):
        sync.main()
    client.assert_not_called()
