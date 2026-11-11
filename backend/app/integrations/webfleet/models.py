"""Internal snapshot model, independent of the future REST contract (SCRUM-36)."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


MAX_ODOMETER_KM = Decimal("9999999999999.9")
MAX_ODOMETER_RAW = Decimal("99999999999999")


def _number(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def _odometer(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, str) and not value.strip():
        return None
    number = _number(value)
    if number is None or number < 0:
        return None
    # Maximum value permitted by PostgreSQL column Numeric(14, 1):
    # Absolute value must be strictly less than 10^13 km.
    if number > MAX_ODOMETER_RAW:
        raise ValueError(f"Wartość odometru przekracza limit Numeric(14,1): {number}")
    km = number / 10
    if km > MAX_ODOMETER_KM:
        raise ValueError(f"Wartość odometru przekracza limit Numeric(14,1): {km}")
    try:
        return km.quantize(Decimal("0.1"))
    except InvalidOperation:
        raise ValueError(f"Niepoprawny wykładnik dziesiętny odometru: {km}") from None


def _coordinate(value: Any, limit: int) -> float | None:
    number = _number(value)
    if number is None or number != number.to_integral_value():
        return None
    degrees = number / 1_000_000
    return float(degrees) if -limit <= degrees <= limit else None


def _binary(value: Any) -> bool | None:
    return {"0": False, "1": True}.get(str(value))


def _utc_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        timestamp = datetime.fromisoformat(value)
    except ValueError:
        return None
    return timestamp.astimezone(UTC) if timestamp.tzinfo else None


@dataclass(frozen=True)
class ObjectSnapshot:
    """Sensitive data stays in memory; repr hides identity and telemetry."""

    uid: str = field(repr=False)
    number: str | None = field(repr=False)
    latitude: float | None = field(repr=False)
    longitude: float | None = field(repr=False)
    odometer_km: Decimal | None = field(repr=False)
    ignition_on: bool | None = field(repr=False)
    standing_still: bool | None = field(repr=False)
    gps_quality: str | None = field(repr=False)
    position_at: datetime | None = field(repr=False)

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "ObjectSnapshot":
        # objectno can change. Never silently substitute it for the stable UID.
        uid = record.get("objectuid")
        if not isinstance(uid, str) or not uid.strip():
            raise ValueError("Brak stabilnego objectuid w rekordzie WEBFLEET")
        return cls(
            uid=uid,
            number=record.get("objectno") or None,
            latitude=_coordinate(record.get("latitude_mdeg"), 90),
            longitude=_coordinate(record.get("longitude_mdeg"), 180),
            odometer_km=_odometer(record.get("odometer")),
            ignition_on=_binary(record.get("ignition")),
            standing_still=_binary(record.get("standstill")),
            gps_quality=record.get("status")
            if record.get("status") in ("A", "V", "L", "0")
            else None,
            position_at=_utc_time(record.get("pos_time")),
        )
