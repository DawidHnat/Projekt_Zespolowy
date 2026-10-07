import math
from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import ValidationError

from app.integrations.webfleet.client import WebfleetError
from app.modules.fleet.schemas import Vehicle, VehicleStatus


def optional_number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def position_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(UTC)


def map_vehicles(
    vehicle_rows: list[dict[str, Any]],
    object_rows: list[dict[str, Any]],
    now: datetime | None = None,
) -> list[Vehicle]:
    """Join documented master data and telemetry, preserving missing values.

    `offline` is our snapshot policy (last position older than 24 hours or invalid GPS),
    not an official Webfleet vehicle state. No coordinate is synthesized.
    """
    now = now or datetime.now(UTC)
    by_uid = {str(row["objectuid"]): row for row in object_rows if row.get("objectuid")}
    by_number = {str(row["objectno"]): row for row in object_rows if row.get("objectno")}
    mapped = []
    seen: set[str] = set()
    for master in vehicle_rows:
        uid = master.get("objectuid")
        number = master.get("objectno")
        if not uid and not number:
            raise WebfleetError(
                "A Webfleet vehicle is missing its identifier. No data was changed."
            )
        vehicle_id = f"wf:{uid}" if uid else f"wf-number:{number}"
        if vehicle_id in seen:
            raise WebfleetError("Duplicate Webfleet vehicle identifier. No data was changed.")
        seen.add(vehicle_id)
        telemetry = by_uid.get(str(uid)) or by_number.get(str(number)) or {}
        updated = position_time(telemetry.get("pos_time"))
        speed = optional_number(telemetry.get("speed"))
        speed = speed if speed is not None and speed >= 0 else None
        odometer_meters = optional_number(telemetry.get("odometer_long"))
        legacy_odometer = optional_number(telemetry.get("odometer"))
        odometer = (
            odometer_meters / 1000
            if odometer_meters is not None
            else legacy_odometer / 10
            if legacy_odometer is not None
            else None
        )
        odometer = odometer if odometer is not None and odometer >= 0 else None
        latitude_raw = optional_number(telemetry.get("latitude_mdeg"))
        longitude_raw = optional_number(telemetry.get("longitude_mdeg"))
        latitude = latitude_raw / 1_000_000 if latitude_raw is not None else None
        longitude = longitude_raw / 1_000_000 if longitude_raw is not None else None
        if (
            latitude is None
            or longitude is None
            or not -90 <= latitude <= 90
            or not -180 <= longitude <= 180
        ):
            latitude, longitude = None, None
        gps_status = str(telemetry.get("status", ""))
        status: VehicleStatus = "unknown"
        if updated is not None and (
            updated < now - timedelta(hours=24) or gps_status in {"0", "L"}
        ):
            status = "offline"
        elif updated is not None and gps_status in {"A", "V"} and latitude is not None:
            if speed is not None:
                status = "driving" if speed > 0 else "parked"
        if updated is None or gps_status == "0":
            latitude, longitude = None, None
        try:
            mapped.append(
                Vehicle(
                    id=vehicle_id,
                    registration=str(master.get("licenseplatenumber") or number or uid),
                    name=str(master.get("objectname") or number or uid),
                    status=status,
                    speed_kmh=speed,
                    odometer_km=odometer,
                    latitude=latitude,
                    longitude=longitude,
                    updated_at=updated or now,
                )
            )
        except ValidationError:
            raise WebfleetError("Invalid Webfleet vehicle data. No data was changed.") from None
    return mapped
