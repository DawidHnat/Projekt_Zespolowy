"""Convert the allowlisted history reports from WEBFLEET to local data."""

from datetime import datetime
from typing import Any

from app.integrations.webfleet.client import WebfleetError
from app.integrations.webfleet.models import _address, _coordinate, _number, _utc_time

MAX_DISTANCE_METRES = 99_999_999_999_999


def _clean_address(value):
    value = _address(value)
    if value and any(char == "\x00" or 0xD800 <= ord(char) <= 0xDFFF for char in value):
        return None
    return value


def _bounded_coordinate(value, bound):
    number = _number(value)
    if number is None or not -bound * 1_000_000 <= number <= bound * 1_000_000:
        return None
    return _coordinate(value, bound)


def report_times(row: dict[str, Any], object_uid: str) -> tuple[datetime, datetime | None]:
    try:
        start = _utc_time(row.get("start_time"))
        end = _utc_time(row.get("end_time"))
    except OverflowError:
        raise WebfleetError("INVALID_HISTORY_RECORDS") from None
    if (
        row.get("objectuid") not in (None, "", object_uid)
        or start is None
        or (end is not None and end < start)
        or (row.get("end_time") not in (None, "") and end is None)
    ):
        raise WebfleetError("INVALID_HISTORY_RECORDS")
    return start, end


def trip_values(row: dict[str, Any], object_uid: str):
    trip_id = row.get("tripid")
    if isinstance(trip_id, str):
        trip_id = trip_id.strip()
    elif type(trip_id) is int and trip_id >= 0:
        trip_id = str(trip_id)
    if not isinstance(trip_id, str) or not trip_id.isascii() or not trip_id.isdecimal():
        raise WebfleetError("INVALID_HISTORY_RECORDS")
    trip_id = trip_id.lstrip("0") or "0"
    if len(trip_id) > 200:
        raise WebfleetError("INVALID_HISTORY_RECORDS")

    start, end = report_times(row, object_uid)
    distance = _number(row.get("distance"))
    if distance is not None and (
        distance < 0 or distance > MAX_DISTANCE_METRES or distance != distance.to_integral_value()
    ):
        distance = None
    return {
        "external_uid": trip_id,
        "start_at": start,
        "end_at": end,
        "distance_km": distance.scaleb(-3) if distance is not None else None,
        "start_address": _clean_address(row.get("start_postext")),
        "end_address": _clean_address(row.get("end_postext")),
    }


def stop_values(row: dict[str, Any], object_uid: str):
    start, end = report_times(row, object_uid)
    if end is None or (end - start).total_seconds() > 2_147_483_647:
        raise WebfleetError("INVALID_HISTORY_RECORDS")
    return {
        "start_at": start,
        "end_at": end,
        "duration_seconds": int((end - start).total_seconds()),
        "latitude": _bounded_coordinate(row.get("latitude"), 90),
        "longitude": _bounded_coordinate(row.get("longitude"), 180),
        "address": _clean_address(row.get("postext")),
    }
