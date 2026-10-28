"""SCRUM-108: validate real synthetic API responses against the one SCRUM-36 source."""

import copy
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry
from referencing.exceptions import NoSuchResource
from sqlalchemy import select

from app.core.models import Driver, Measurement, SyncState, Vehicle
from app.modules.analytics.models import Alert, Rule
from app.modules.auth.models import PasswordReset, User
from app.modules.auth.service import digest
from app.modules.fleet.sync import account_key
from app.modules.trips.models import Trip

CONTRACT = json.loads(
    (Path(__file__).resolve().parents[2] / "contracts/api-design.json").read_text()
)
OPERATIONS = {
    (op["method"], op["path"]): op
    for op in CONTRACT["operations"]
    if op["implementation_status"] == "implemented"
}
ORIGIN = {"Origin": "http://127.0.0.1:5173"}
FORMATS = FormatChecker()


@FORMATS.checks("date-time", raises=(ValueError, TypeError))
def utc_datetime(value):
    if not isinstance(value, str):
        return True
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.tzinfo is not None and parsed.utcoffset() == timedelta(0)


@FORMATS.checks("uuid", raises=(ValueError, TypeError, AttributeError))
def uuid_string(value):
    return not isinstance(value, str) or str(UUID(value)) == value.lower()


def reject_remote_schema(uri):
    raise NoSuchResource(ref=uri)


def validator(reference):
    schema = {"$schema": CONTRACT["$schema"], "$defs": CONTRACT["$defs"], **reference}
    return Draft202012Validator(
        schema, format_checker=FORMATS, registry=Registry(retrieve=reject_remote_schema)
    )


def validate_response(method, path, response, expected=200):
    assert response.status_code == expected, (method, path, response.status_code)
    validator(OPERATIONS[method, path]["response_schema"]).validate(response.json())
    return response.json()


def validate_error(response, expected, code):
    assert response.status_code == expected
    validator({"$ref": "#/$defs/Error"}).validate(response.json())
    assert response.json()["error"]["code"] == code


def seed_contract(app):
    now = datetime.now(UTC)
    with app.state.sessions() as session:
        source = account_key(app.state.settings.webfleet_account)
        session.add(SyncState(source_account=source, last_success_at=now))
        driver = Driver(display_name="Syntetyczny kierowca kontraktu")
        session.add(driver)
        session.flush()
        vehicle = Vehicle(
            source_account=source,
            external_uid="contract-private-id",
            name="Kontrakt",
            number="SYN-1",
            driver_id=driver.id,
        )
        missing = Vehicle(source_account=source, external_uid="contract-no-gps", name="Bez GPS")
        session.add_all([vehicle, missing])
        session.flush()
        session.add(
            Measurement(
                vehicle_id=vehicle.id,
                latitude=0,
                longitude=0,
                gps_quality="A",
                standing_still=True,
                position_at=now,
                received_at=now,
                odometer_km=Decimal("1234.5"),
            )
        )
        trip = Trip(
            vehicle_id=vehicle.id,
            external_uid="contract-trip",
            start_at=now - timedelta(minutes=30),
            end_at=now - timedelta(minutes=20),
            distance_km=Decimal("12.5"),
        )
        rule = Rule(source_account=source, threshold_km=Decimal("10.0"), vehicle_id=vehicle.id)
        session.add_all([trip, rule])
        session.flush()
        alert = Alert(
            rule_id=rule.id,
            vehicle_id=vehicle.id,
            occurred_at=now,
            created_at=now,
            event_day=now.astimezone(ZoneInfo("Europe/Warsaw")).date(),
            threshold_km=Decimal("10.0"),
            distance_km=Decimal("12.5"),
        )
        session.add(alert)
        session.flush()
        identities = str(vehicle.id), str(trip.id), str(rule.id), str(alert.id)
        session.commit()
    return identities, now


@pytest.mark.parametrize("key", OPERATIONS)
def test_canonical_examples_match_the_same_response_schemas(key):
    operation = OPERATIONS[key]
    Draft202012Validator.check_schema({"$defs": CONTRACT["$defs"]})
    validator(operation["response_schema"]).validate(operation["response_example"])
    if "error_example" in operation:
        validator(operation["error_schema"]).validate(operation["error_example"]["body"])


def test_every_implemented_operation_has_a_real_success_response(logged_in, monkeypatch):
    app, client = logged_in

    # Even an accidental fixture change cannot call live SMTP from this suite.
    smtp_calls = []

    def no_smtp(*args, **kwargs):
        smtp_calls.append(True)
        raise AssertionError("Contract suite must not call SMTP")

    monkeypatch.setattr("app.modules.auth.reset.send_password_reset", no_smtp)
    (vehicle, trip, rule, alert), now = seed_contract(app)
    seen = set()

    def check(method, path, actual=None, expected=200, **options):
        response = client.request(method, "/api/v1" + (actual or path), headers=ORIGIN, **options)
        seen.add((method, path))
        return validate_response(method, path, response, expected)

    check(
        "POST", "/auth/login", json={"username": "test-user", "password": "synthetic-test-password"}
    )
    check("GET", "/auth/me")
    payload = check("GET", "/fleet/vehicles")
    assert payload["total"] == 2
    assert "contract-private-id" not in json.dumps(payload)
    assert any(item["latitude"] is None for item in payload["items"])
    detail = check("GET", "/fleet/vehicles/{id}", f"/fleet/vehicles/{vehicle}")
    assert detail["latitude"] == detail["longitude"] == 0
    assert detail["odometer_km"] == 1234.5 and detail["speed_kmh"] is None
    check("GET", "/fleet/map")
    check("GET", "/fleet/summary")
    check(
        "GET",
        "/trips",
        params={
            "vehicle_id": vehicle,
            "from": (now - timedelta(hours=1)).isoformat(),
            "to": now.isoformat(),
            "page_size": 1,
        },
    )
    detail = check("GET", "/trips/{id}", f"/trips/{trip}")
    assert detail["duration_seconds"] == 600 and detail["distance_km"] == 12.5
    assert detail["annotation"]["updated_at"] is None and detail["geometry"] is None
    check(
        "PATCH",
        "/trips/{id}/annotation",
        f"/trips/{trip}/annotation",
        json={"version": 1, "purpose": "Cel syntetyczny"},
    )
    # Validate non-null author/timestamp as well as the initial empty annotation.
    check("GET", "/trips/{id}", f"/trips/{trip}")
    check(
        "POST",
        "/analytics/rules",
        expected=201,
        json={"type": "daily_distance_threshold", "threshold_km": 100.1, "vehicle_id": None},
    )
    check("GET", "/analytics/rules")
    check("PATCH", "/analytics/rules/{id}", f"/analytics/rules/{rule}", json={"active": False})
    check("GET", "/analytics/alerts")
    check(
        "PATCH",
        "/analytics/alerts/{id}/receipt",
        f"/analytics/alerts/{alert}/receipt",
        json={"read": True},
    )
    check("GET", "/analytics/alerts")
    check(
        "PATCH",
        "/analytics/alerts/{id}/receipt",
        f"/analytics/alerts/{alert}/receipt",
        json={"read": False},
    )
    profile = check(
        "POST",
        "/drivers",
        expected=201,
        json={"first_name": "Jan", "last_name": "Kontrakt", "identifier": "contract-driver"},
    )
    driver_id = profile["id"]
    check("GET", "/drivers/categories")
    check("GET", "/drivers/summary")
    check("GET", "/drivers")
    check("POST", "/drivers/search", json={"q": "Kontrakt"})
    check("GET", "/drivers/{id}", f"/drivers/{driver_id}")
    updated = check(
        "PATCH", "/drivers/{id}", f"/drivers/{driver_id}", json={"version": 1, "categories": ["B"]}
    )
    assigned = check(
        "POST",
        "/drivers/{id}/assignments",
        f"/drivers/{driver_id}/assignments",
        expected=201,
        json={"version": updated["version"], "vehicle_id": vehicle},
    )
    check("GET", "/drivers/{id}/assignments", f"/drivers/{driver_id}/assignments")
    check(
        "PATCH",
        "/drivers/{id}/assignments/{assignment_id}/close",
        f"/drivers/{driver_id}/assignments/{assigned['assignment']['id']}/close",
        json={"version": assigned["driver_version"]},
    )
    check("POST", "/auth/logout")
    check(
        "POST", "/auth/password/request", json={"username": "nonexistent-synthetic-contract-user"}
    )
    token = "synthetic-contract-reset-token"
    with app.state.sessions() as session:
        user = session.scalar(select(User).where(User.username == "test-user"))
        session.add(
            PasswordReset(
                token_hash=digest(token), user_id=user.id, expires_at=now + timedelta(minutes=10)
            )
        )
        session.commit()
    check(
        "POST",
        "/auth/password/confirm",
        json={"token": token, "password": "synthetic-new-contract-password"},
    )
    assert not smtp_calls
    assert seen == set(OPERATIONS), (
        "Add real response coverage when an operation becomes implemented"
    )


def test_auth_validation_conflict_and_dependency_errors_have_the_contract_shape(logged_in):
    app, client = logged_in
    validate_error(client.get("/api/v1/fleet/vehicles"), 503, "SOURCE_UNAVAILABLE")
    (vehicle, trip, _, _), now = seed_contract(app)
    validate_error(client.get("/api/v1/fleet/vehicles?page=0"), 422, "VALIDATION_ERROR")
    validate_error(client.get(f"/api/v1/trips/{uuid4()}"), 404, "NOT_FOUND")
    first = client.patch(
        f"/api/v1/trips/{trip}/annotation",
        headers=ORIGIN,
        json={"version": 1, "description": "Syntetyczna zmiana"},
    )
    assert first.status_code == 200
    validate_error(
        client.patch(
            f"/api/v1/trips/{trip}/annotation",
            headers=ORIGIN,
            json={"version": 1, "description": "Konflikt"},
        ),
        409,
        "VERSION_CONFLICT",
    )
    validate_error(
        client.patch(
            f"/api/v1/trips/{trip}/annotation",
            headers={"Origin": "https://untrusted.invalid"},
            json={"version": 2, "purpose": "Origin"},
        ),
        403,
        "FORBIDDEN",
    )
    with app.state.sessions() as session:
        user = session.scalar(select(User).where(User.username == "test-user"))
        user.role = "viewer"
        session.commit()
    validate_error(
        client.patch(
            f"/api/v1/trips/{trip}/annotation",
            headers=ORIGIN,
            json={"version": 2, "purpose": "Role"},
        ),
        403,
        "FORBIDDEN",
    )
    validate_error(
        client.post(
            "/api/v1/auth/password/confirm",
            headers=ORIGIN,
            json={
                "token": "synthetic-nonexistent-reset-token",
                "password": "synthetic-new-password",
            },
        ),
        400,
        "INVALID_RESET",
    )
    client.post("/api/v1/auth/logout", headers=ORIGIN)
    for path in (
        "/auth/me",
        "/fleet/vehicles",
        "/fleet/map",
        "/fleet/summary",
        f"/fleet/vehicles/{vehicle}",
        f"/trips/{trip}",
        "/analytics/rules",
        "/analytics/alerts",
    ):
        validate_error(client.get("/api/v1" + path), 401, "UNAUTHENTICATED")


def test_contract_rejects_breaking_changes_and_accepts_compatible_extensions():
    sample = copy.deepcopy(OPERATIONS["GET", "/fleet/vehicles"]["response_example"])
    check = validator({"$ref": "#/$defs/VehicleList"})
    for mutation in ("rename", "type", "remove"):
        changed = copy.deepcopy(sample)
        if mutation == "rename":
            changed["count"] = changed.pop("total")
        elif mutation == "type":
            changed["total"] = "1"
        else:
            del changed["total"]
        with pytest.raises(ValidationError):
            check.validate(changed)
    extended = {**sample, "optional_future_field": "synthetic"}
    check.validate(extended)
    for field, wrong in (
        ("id", "not-a-uuid"),
        ("latitude", 100),
        ("longitude", "0"),
        ("position_at", "2026-01-10T12:00:00"),
        ("is_stale", "false"),
    ):
        changed = copy.deepcopy(sample)
        changed["items"][0][field] = wrong
        with pytest.raises(ValidationError):
            check.validate(changed)
