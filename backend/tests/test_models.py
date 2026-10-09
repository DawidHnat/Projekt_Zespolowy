from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.integrations.webfleet.models import ObjectSnapshot


def test_units_flags_and_timezone_are_normalized():
    record = {
        "objectuid": "fictional-unit-test",
        "objectno": "OLD-NO",
        "latitude_mdeg": 0,
        "longitude_mdeg": -1234567,
        "odometer": "1234567",
        "ignition": 0,
        "standstill": "1",
        "status": "L",
        "pos_time": "2026-10-08T16:00:00+02:00",
    }
    snapshot = ObjectSnapshot.from_record(record)
    assert snapshot.latitude == 0
    assert snapshot.longitude == -1.234567
    assert snapshot.odometer_km == Decimal("123456.7")
    assert snapshot.ignition_on is False
    assert snapshot.standing_still is True
    assert snapshot.gps_quality == "L"
    assert snapshot.position_at == datetime(2026, 10, 8, 14, tzinfo=UTC)
    assert repr(snapshot) == "ObjectSnapshot()"
    record["objectno"] = "NEW-NO"
    assert ObjectSnapshot.from_record(record).uid == snapshot.uid


def test_missing_telemetry_stays_unknown_and_is_not_filled_with_zeros():
    snapshot = ObjectSnapshot.from_record({"objectuid": "fictional-unit-test"})
    assert snapshot.odometer_km is None
    assert snapshot.latitude is None
    assert snapshot.ignition_on is None
    assert snapshot.position_at is None


@pytest.mark.parametrize("value", ["NaN", "Infinity", "broken", -1, True, ""])
def test_invalid_odometer_is_unknown(value):
    assert ObjectSnapshot.from_record({"objectuid": "test", "odometer": value}).odometer_km is None


@pytest.mark.parametrize("value", [91_000_000, -91_000_000, 0.5, "NaN", "broken"])
def test_invalid_latitude_is_not_drawn_on_a_map(value):
    assert (
        ObjectSnapshot.from_record({"objectuid": "test", "latitude_mdeg": value}).latitude is None
    )


def test_naive_time_does_not_assume_the_servers_timezone():
    assert (
        ObjectSnapshot.from_record(
            {
                "objectuid": "test",
                "pos_time": "2026-10-08T16:00:00",
            }
        ).position_at
        is None
    )


def test_missing_stable_id_is_not_replaced_with_mutable_object_number():
    with pytest.raises(ValueError, match="objectuid"):
        ObjectSnapshot.from_record({"objectno": "test"})
