import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import WebfleetSettings
from app.core.models import Base, Measurement, Vehicle
from app.modules.analytics.models import Alert, AlertReceipt, DailyDistance, Rule
from app.modules.analytics.service import WARSAW, evaluate_distance_rules, record_distance_interval
from app.modules.auth.models import User
from app.modules.fleet.sync import account_key, sync_once

ORIGIN = {"Origin": "http://127.0.0.1:5173"}
RULES = "/api/v1/analytics/rules"
ALERTS = "/api/v1/analytics/alerts"


def vehicle_with_reading(
    session, source, now, *, value=Decimal("2000.1"), active=True, with_distance=True
):
    vehicle = Vehicle(
        source_account=source, external_uid=str(uuid4()), name="Syntetyczny pojazd", active=active
    )
    session.add(vehicle)
    session.flush()
    measurement = Measurement(
        vehicle_id=vehicle.id, received_at=now, position_at=now, odometer_km=value
    )
    session.add(measurement)
    if with_distance:
        session.add(
            DailyDistance(
                vehicle_id=vehicle.id,
                event_day=now.astimezone(WARSAW).date(),
                distance_km=value,
                first_observed_at=now - timedelta(minutes=1),
                last_observed_at=now,
            )
        )
    session.flush()
    return vehicle, measurement


def create_rule(client, **changes):
    return client.post(RULES, headers=ORIGIN, json={"threshold_km": 2000, **changes})


def test_rule_create_edit_disable_and_preserved_alert_evidence(logged_in):
    app, client = logged_in
    source = account_key(app.state.settings.webfleet_account)
    with app.state.sessions() as session:
        vehicle, _ = vehicle_with_reading(session, source, datetime.now(UTC))
        vehicle_id = str(vehicle.id)
        session.commit()
    response = create_rule(client, vehicle_id=vehicle_id)
    assert response.status_code == 201
    rule = response.json()
    assert rule["threshold_km"] == 2000 and rule["active"] is True
    assert "source_account" not in rule
    alert = client.get(ALERTS).json()["items"][0]
    assert rule["type"] == "daily_distance_threshold"
    assert alert["threshold_km"] == 2000 and alert["distance_km"] == 2000.1
    assert alert["coverage"] == "partial"
    edited = client.patch(f"{RULES}/{rule['id']}", headers=ORIGIN, json={"threshold_km": 1999})
    assert edited.status_code == 200
    assert client.get(ALERTS).json()["total"] == 1
    assert client.get(ALERTS).json()["items"][0] == alert
    disabled = client.patch(f"{RULES}/{rule['id']}", headers=ORIGIN, json={"active": False})
    assert disabled.json()["active"] is False
    assert client.get(ALERTS).json()["total"] == 1
    assert client.get(RULES).json()["items"][0]["threshold_km"] == 1999


@pytest.mark.parametrize(
    "threshold", [0, -1, None, True, "NaN", "Infinity", "0.01", "10000000000000"]
)
def test_invalid_threshold_cannot_be_saved(logged_in, threshold):
    _, client = logged_in
    response = create_rule(client, threshold_km=threshold)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert client.get(RULES).json()["total"] == 0


@pytest.mark.parametrize(
    "patch",
    [
        {},
        {"active": None},
        {"threshold_km": None},
        {"active": "false"},
        {"source_account": "other"},
        {"type": "other"},
    ],
)
def test_invalid_patch_does_not_change_rule(logged_in, patch):
    _, client = logged_in
    rule = create_rule(client).json()
    response = client.patch(f"{RULES}/{rule['id']}", headers=ORIGIN, json=patch)
    assert response.status_code == 422
    assert client.get(RULES).json()["items"] == [rule]


def test_authorization_origin_and_account_boundaries(application):
    app, client = application
    assert client.get(RULES).status_code == 401
    assert client.get(ALERTS).status_code == 401
    assert create_rule(client).status_code == 401
    client.post(
        "/api/v1/auth/login",
        headers=ORIGIN,
        json={
            "username": "test-user",
            "password": "synthetic-test-password",
        },
    )
    assert client.post(RULES, json={"threshold_km": 1}).status_code == 403
    assert (
        client.post(
            RULES, headers={"Origin": "https://evil.example"}, json={"threshold_km": 1}
        ).status_code
        == 403
    )
    with app.state.sessions() as session:
        foreign_vehicle, _ = vehicle_with_reading(session, "other-source", datetime.now(UTC))
        rule = Rule(source_account="other-source", threshold_km=Decimal(1))
        session.add(rule)
        session.flush()
        foreign_rule_id = rule.id
        evaluate_distance_rules(session, "other-source")
        foreign_alert_id = session.scalar(select(Alert.id))
        session.commit()
        foreign_vehicle_id = foreign_vehicle.id
    assert create_rule(client, vehicle_id=str(foreign_vehicle_id)).status_code == 404
    assert create_rule(client, vehicle_id=str(uuid4())).status_code == 404
    assert client.get(RULES).json()["total"] == 0
    assert client.get(ALERTS).json()["total"] == 0
    assert (
        client.patch(
            f"{RULES}/{foreign_rule_id}", headers=ORIGIN, json={"active": False}
        ).status_code
        == 404
    )
    assert (
        client.patch(
            f"{ALERTS}/{foreign_alert_id}/receipt", headers=ORIGIN, json={"read": True}
        ).status_code
        == 404
    )
    with app.state.sessions() as session:
        user = session.scalar(select(User))
        user.role = "viewer"
        session.commit()
    assert client.get(RULES).status_code == 200
    assert create_rule(client).status_code == 403
    with app.state.sessions() as session:
        session.scalar(select(User)).role = "editor"
        session.commit()
    assert create_rule(client).status_code == 201


def test_global_rule_scope_threshold_boundary_and_disable(application):
    app, _ = application
    now = datetime.now(UTC)
    with app.state.sessions() as session:
        for source, value, active in [
            ("source", Decimal("99.9"), True),
            ("source", Decimal("100"), True),
            ("source", Decimal("100.1"), True),
            ("source", Decimal("200"), False),
            ("other", Decimal("200"), True),
        ]:
            vehicle_with_reading(session, source, now, value=value, active=active)
        rule = Rule(source_account="source", threshold_km=Decimal(100))
        session.add(rule)
        session.flush()
        assert evaluate_distance_rules(session, "source", now=now) == 1
        assert evaluate_distance_rules(session, "source", now=now) == 0
        rule.active = False
        session.flush()
        assert evaluate_distance_rules(session, "source", now=now) == 0
        session.commit()
        assert session.scalar(select(func.count()).select_from(Alert)) == 1


@pytest.mark.parametrize(
    "timestamp, day",
    [
        ("2026-01-10T22:59:00+00:00", "2026-01-10"),
        ("2026-01-10T23:00:00+00:00", "2026-01-11"),
        ("2026-07-10T21:59:00+00:00", "2026-07-10"),
        ("2026-07-10T22:00:00+00:00", "2026-07-11"),
        ("2026-03-29T00:30:00+00:00", "2026-03-29"),
        ("2026-10-25T01:30:00+00:00", "2026-10-25"),
    ],
)
def test_event_day_uses_measurement_time_in_warsaw(application, timestamp, day):
    app, _ = application
    now = datetime.fromisoformat(timestamp)
    with app.state.sessions() as session:
        vehicle_with_reading(session, "source", now)
        session.add(Rule(source_account="source", threshold_km=Decimal(100)))
        session.flush()
        assert evaluate_distance_rules(session, "source", now=now) == 1
        assert session.scalar(select(Alert)).event_day.isoformat() == day


def test_new_measurement_on_next_day_creates_one_new_alert(application):
    app, _ = application
    now = datetime(2026, 1, 10, 22, 59, tzinfo=UTC)
    with app.state.sessions() as session:
        vehicle, _ = vehicle_with_reading(session, "source", now)
        session.add(Rule(source_account="source", threshold_km=Decimal(100), vehicle_id=vehicle.id))
        session.flush()
        assert evaluate_distance_rules(session, "source", now=now) == 1
        next_reading = now + timedelta(minutes=2)
        session.add(
            DailyDistance(
                vehicle_id=vehicle.id,
                event_day=next_reading.astimezone(WARSAW).date(),
                distance_km=Decimal(200),
                first_observed_at=next_reading - timedelta(seconds=1),
                last_observed_at=next_reading,
            )
        )
        session.flush()
        assert evaluate_distance_rules(session, "source", now=next_reading) == 1
        assert evaluate_distance_rules(session, "source", now=next_reading) == 0
        assert session.scalar(select(func.count()).select_from(Alert)) == 2


@pytest.mark.parametrize(
    "case", ["missing_time", "stale", "future", "missing_odometer", "negative", "duplicate"]
)
def test_unusable_measurements_never_create_alerts(application, case):
    app, _ = application
    now = datetime.now(UTC)
    with app.state.sessions() as session:
        vehicle, previous = vehicle_with_reading(
            session, "source", now - timedelta(seconds=60), with_distance=False
        )
        reading = SimpleNamespace(position_at=now, odometer_km=Decimal(2200))
        if case == "missing_time":
            reading.position_at = None
        if case == "stale":
            previous.position_at = now - timedelta(seconds=901)
        if case == "future":
            reading.position_at = now + timedelta(seconds=1)
        if case == "missing_odometer":
            reading.odometer_km = None
        if case == "negative":
            reading.odometer_km = Decimal(-1)
        if case == "duplicate":
            reading.position_at = previous.position_at
        record_distance_interval(session, vehicle.id, previous, reading, now)
        session.add(Rule(source_account="source", threshold_km=Decimal(100)))
        session.flush()
        assert evaluate_distance_rules(session, "source", now=now) == 0
        assert session.scalar(select(func.count()).select_from(DailyDistance)) == 0


def test_distance_is_a_daily_delta_not_the_absolute_odometer(application):
    app, _ = application
    now = datetime(2026, 1, 10, 12, tzinfo=UTC)
    with app.state.sessions() as session:
        vehicle, previous = vehicle_with_reading(
            session,
            "source",
            now - timedelta(minutes=1),
            value=Decimal(100000),
            with_distance=False,
        )
        session.add(Rule(source_account="source", threshold_km=Decimal(10)))
        session.flush()
        assert evaluate_distance_rules(session, "source", now=now) == 0
        reading = SimpleNamespace(position_at=now, odometer_km=Decimal(100010))
        record_distance_interval(session, vehicle.id, previous, reading, now)
        previous.position_at, previous.odometer_km = reading.position_at, reading.odometer_km
        session.flush()
        assert evaluate_distance_rules(session, "source", now=now) == 0
        reading = SimpleNamespace(
            position_at=now + timedelta(minutes=1), odometer_km=Decimal("100010.1")
        )
        record_distance_interval(session, vehicle.id, previous, reading, reading.position_at)
        assert evaluate_distance_rules(session, "source", now=reading.position_at) == 1
        alert = session.scalar(select(Alert))
        assert alert.distance_km == Decimal("10.1")
        assert alert.threshold_km == 10
        session.commit()
    # A new session/restart preserves the accumulated distance and deduplication.
    with app.state.sessions() as session:
        assert evaluate_distance_rules(session, "source", now=reading.position_at) == 0


@pytest.mark.parametrize("offset", [-901, 1])
def test_old_and_future_daily_observations_do_not_trigger_new_alerts(application, offset):
    app, _ = application
    now = datetime(2026, 1, 10, 12, tzinfo=UTC)
    with app.state.sessions() as session:
        vehicle_with_reading(session, "source", now + timedelta(seconds=offset))
        session.add(Rule(source_account="source", threshold_km=Decimal(1)))
        session.flush()
        assert evaluate_distance_rules(session, "source", now=now) == 0


def test_intervals_crossing_midnight_and_counter_resets_are_not_invented(application):
    app, _ = application
    now = datetime(2026, 1, 10, 23, 1, tzinfo=UTC)
    with app.state.sessions() as session:
        vehicle, previous = vehicle_with_reading(
            session, "source", now - timedelta(minutes=2), with_distance=False
        )
        reading = SimpleNamespace(position_at=now, odometer_km=Decimal(2200))
        record_distance_interval(session, vehicle.id, previous, reading, now)
        assert session.scalar(select(func.count()).select_from(DailyDistance)) == 0
        previous.position_at, previous.odometer_km = now, reading.odometer_km
        reading = SimpleNamespace(position_at=now + timedelta(seconds=60), odometer_km=Decimal(100))
        record_distance_interval(session, vehicle.id, previous, reading, reading.position_at)
        assert session.scalar(select(func.count()).select_from(DailyDistance)) == 0
        previous.position_at, previous.odometer_km = reading.position_at, reading.odometer_km
        reading = SimpleNamespace(
            position_at=now + timedelta(seconds=120), odometer_km=Decimal(101)
        )
        record_distance_interval(session, vehicle.id, previous, reading, reading.position_at)
        assert session.scalar(select(DailyDistance)).distance_km == 1


def test_vehicle_rule_retargeting_and_disable_do_not_affect_other_vehicles(logged_in):
    app, client = logged_in
    source = account_key(app.state.settings.webfleet_account)
    with app.state.sessions() as session:
        first, _ = vehicle_with_reading(session, source, datetime.now(UTC))
        second, _ = vehicle_with_reading(session, source, datetime.now(UTC))
        first_id, second_id = str(first.id), str(second.id)
        session.commit()
    rule = create_rule(client, vehicle_id=first_id, active=False).json()
    assert client.get(ALERTS).json()["total"] == 0
    assert (
        client.patch(f"{RULES}/{rule['id']}", headers=ORIGIN, json={"active": True}).status_code
        == 200
    )
    assert [a["vehicle_id"] for a in client.get(ALERTS).json()["items"]] == [first_id]
    client.patch(f"{RULES}/{rule['id']}", headers=ORIGIN, json={"vehicle_id": second_id})
    assert client.get(ALERTS).json()["total"] == 2
    client.patch(f"{RULES}/{rule['id']}", headers=ORIGIN, json={"vehicle_id": None})
    assert client.get(ALERTS).json()["total"] == 2


def test_receipts_are_idempotent_and_private_per_user(logged_in):
    app, client = logged_in
    source = account_key(app.state.settings.webfleet_account)
    with app.state.sessions() as session:
        vehicle_with_reading(session, source, datetime.now(UTC))
        second_user = User(
            username="other-test-user",
            display_name="Druga osoba",
            role="viewer",
            password_hash="unused-synthetic",
        )
        session.add(second_user)
        session.flush()
        other_user_id = second_user.id
        session.commit()
    create_rule(client)
    alert_id = client.get(ALERTS).json()["items"][0]["id"]
    path = f"{ALERTS}/{alert_id}/receipt"
    assert client.patch(path, json={"read": True}).status_code == 403
    response = client.patch(path, headers=ORIGIN, json={"read": True})
    assert response.status_code == 200 and response.json()["read_at"]
    assert client.patch(path, headers=ORIGIN, json={"read": True}).json() == response.json()
    assert client.get(ALERTS, params={"read": False}).json()["total"] == 0
    assert client.get(ALERTS, params={"read": True}).json()["total"] == 1
    from app.modules.auth.service import current_user

    def other_user():
        with app.state.sessions() as session:
            return session.get(User, other_user_id)

    app.dependency_overrides[current_user] = other_user
    try:
        assert client.get(ALERTS, params={"read": False}).json()["total"] == 1
        assert client.patch(path, headers=ORIGIN, json={"read": True}).status_code == 200
        assert client.patch(path, headers=ORIGIN, json={"read": False}).json() == {"read_at": None}
    finally:
        app.dependency_overrides.clear()
    assert client.get(ALERTS, params={"read": True}).json()["total"] == 1
    with app.state.sessions() as session:
        assert session.scalar(select(func.count()).select_from(AlertReceipt)) == 1


def test_rules_and_alerts_have_stable_pagination(logged_in):
    app, client = logged_in
    source = account_key(app.state.settings.webfleet_account)
    with app.state.sessions() as session:
        vehicle_with_reading(session, source, datetime.now(UTC))
        for _ in range(26):
            session.add(Rule(source_account=source, threshold_km=Decimal(100)))
        session.flush()
        assert evaluate_distance_rules(session, source) == 26
        session.commit()
    for path in (RULES, ALERTS):
        first = client.get(path).json()
        second = client.get(path, params={"page": 2}).json()
        assert first["total"] == second["total"] == 26
        assert len(first["items"]) == 25 and len(second["items"]) == 1
        assert {x["id"] for x in first["items"]}.isdisjoint({x["id"] for x in second["items"]})
        assert client.get(path, params={"page": 0}).status_code == 422
        assert client.get(path, params={"page_size": 101}).status_code == 422


def test_postgres_parallel_evaluation_and_sync_share_deduplication():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires an isolated PostgreSQL database")
    assert make_url(url).database.startswith("fleet_flow_test"), "Refusing a non-test database"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    try:
        source = "synthetic-alerts-" + uuid4().hex
        now = datetime(2026, 1, 10, 12, tzinfo=UTC)
        with Session(engine) as session:
            vehicle, _ = vehicle_with_reading(session, source, now)
            rule = Rule(source_account=source, threshold_km=Decimal(100), vehicle_id=vehicle.id)
            session.add(rule)
            session.commit()
            rule_id = rule.id

        def evaluate(_):
            with Session(engine) as session:
                result = evaluate_distance_rules(session, source, now=now)
                session.commit()
                return result

        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sorted(pool.map(evaluate, range(2))) == [0, 1]
        with Session(engine) as session:
            assert (
                session.scalar(
                    select(func.count()).select_from(Alert).where(Alert.rule_id == rule_id)
                )
                == 1
            )

        settings = WebfleetSettings("synthetic-sync-" + uuid4().hex, "test", "test", "test")
        sync_source = account_key(settings.account)
        with Session(engine) as session:
            sync_rule = Rule(source_account=sync_source, threshold_km=Decimal(100))
            session.add(sync_rule)
            session.commit()
            sync_rule_id = sync_rule.id

        class FakeClient:
            reading_number = 0

            def __init__(self, _):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_):
                pass

            async def fetch_vehicles(self):
                return [{"objectuid": "synthetic-alert-vehicle", "objectname": "Test"}]

            async def fetch_objects(self):
                FakeClient.reading_number += 1
                reading_index = min(FakeClient.reading_number - 1, 1)
                return [
                    {
                        "objectuid": "synthetic-alert-vehicle",
                        "odometer": str(20001 + reading_index * 1001),
                        "pos_time": (now + timedelta(seconds=reading_index * 60)).isoformat(),
                    }
                ]

        assert sync_once(engine, settings, client_factory=FakeClient, now=now) == "ok"
        with Session(engine) as session:
            assert (
                session.scalar(
                    select(func.count()).select_from(Alert).where(Alert.rule_id == sync_rule_id)
                )
                == 0
            )
        assert (
            sync_once(engine, settings, client_factory=FakeClient, now=now + timedelta(seconds=60))
            == "ok"
        )
        assert (
            sync_once(engine, settings, client_factory=FakeClient, now=now + timedelta(seconds=120))
            == "ok"
        )
        with Session(engine) as session:
            assert (
                session.scalar(
                    select(func.count()).select_from(Alert).where(Alert.rule_id == sync_rule_id)
                )
                == 1
            )
            assert session.scalar(
                select(DailyDistance.distance_km)
                .join(Vehicle, Vehicle.id == DailyDistance.vehicle_id)
                .where(Vehicle.source_account == sync_source)
            ) == Decimal("100.1")
    finally:
        engine.dispose()
