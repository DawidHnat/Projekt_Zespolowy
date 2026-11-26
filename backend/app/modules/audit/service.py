"""Transactional audit recording, field allowlists, and sensitive-data exclusion (SCRUM-87)."""

from __future__ import annotations

import re
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.models import Driver, Vehicle
from app.modules.audit.models import ACTOR_TYPES, ENTITY_TYPES, OUTCOMES, AuditEvent

CORRELATION_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_CARD_PAN_RE = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")

FORBIDDEN_KEYS: frozenset[str] = frozenset(
    {
        "password",
        "password_hash",
        "current_password",
        "new_password",
        "token",
        "token_hash",
        "secret",
        "api_key",
        "pin",
        "card_number",
        "pan",
        "cvv",
        "latitude",
        "longitude",
        "position_address",
        "raw_bytes",
        "content",
        "file_bytes",
        "storage_key",
        "external_uid",
    }
)

ALLOWED_FIELDS_BY_ENTITY: dict[str, frozenset[str]] = {
    "vehicle": frozenset(
        {
            "origin",
            "name",
            "number",
            "license_plate",
            "vehicle_type",
            "make",
            "model",
            "year",
            "vin",
            "fuel_type",
            "leasing_company",
            "leasing_contract_no",
            "leasing_end_on",
            "inspection_due_on",
            "insurance_due_on",
            "manual_odometer_km",
            "manual_odometer_date",
            "gross_weight_kg",
            "passenger_seats",
            "tows_heavy_trailer",
            "required_category_override",
            "archived",
            "archived_reason",
            "driver_id",
        }
    ),
    "vehicle_odometer": frozenset({"manual_odometer_km", "manual_odometer_date"}),
    "vehicle_document": frozenset(
        {
            "inspection_due_on",
            "insurance_due_on",
            "kind",
            "name",
            "mime_type",
            "size_bytes",
            "scan_status",
            "version",
            "deleted",
        }
    ),
    "driver": frozenset(
        {
            "display_name",
            "first_name",
            "last_name",
            "identifier",
            "active",
            "categories",
            "phone_configured",
            "email_configured",
        }
    ),
    "driver_assignment": frozenset({"driver_id", "vehicle_id", "active", "started_at", "ended_at"}),
    "trip_annotation": frozenset({"purpose", "description", "driver_id", "version"}),
    "user_account": frozenset({"role", "active", "password_changed", "password_reset"}),
    "user_session": frozenset({"action", "revoked_all"}),
}


def resolve_correlation_id(request: Request | None = None, explicit: str | None = None) -> str:
    if explicit and CORRELATION_ID_RE.fullmatch(explicit):
        return explicit
    if request is not None:
        state_cid = getattr(request.state, "correlation_id", None)
        if isinstance(state_cid, str) and CORRELATION_ID_RE.fullmatch(state_cid):
            return state_cid
        header_cid = request.headers.get("X-Correlation-ID", "").strip()
        if header_cid and CORRELATION_ID_RE.fullmatch(header_cid):
            return header_cid
    return uuid4().hex


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    text_val = _CARD_PAN_RE.sub("[REDACTED_CARD]", str(value))
    return text_val[:500]


def sanitize_changes(entity_type: str, raw_changes: dict[str, Any] | None) -> dict[str, Any]:
    if not raw_changes:
        return {}
    allowed = ALLOWED_FIELDS_BY_ENTITY.get(entity_type)
    if allowed is None:
        raise ValueError(f"Unknown audit entity_type: {entity_type}")
    cleaned: dict[str, Any] = {}
    for field, delta in raw_changes.items():
        lowered = field.lower()
        if lowered in FORBIDDEN_KEYS or field not in allowed:
            raise ValueError(f"Field '{field}' is not permitted in audit changes for {entity_type}")
        if not isinstance(delta, dict) or set(delta.keys()) - {"before", "after"}:
            raise ValueError(f"Audit field '{field}' must map to {{'before': ..., 'after': ...}}")
        before_val = json_safe(delta.get("before"))
        after_val = json_safe(delta.get("after"))
        cleaned[field] = {"before": before_val, "after": after_val}
    return cleaned


def build_diff(
    entity_type: str, before: dict[str, Any], after: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    allowed = ALLOWED_FIELDS_BY_ENTITY[entity_type]
    diff: dict[str, dict[str, Any]] = {}
    for key in sorted((set(before.keys()) | set(after.keys())) & allowed):
        b_val = json_safe(before.get(key))
        a_val = json_safe(after.get(key))
        if b_val != a_val:
            diff[key] = {"before": b_val, "after": a_val}
    return diff


def vehicle_card_snapshot(vehicle: Vehicle) -> dict[str, Any]:
    return {
        "origin": "manual" if vehicle.is_manual else "webfleet",
        "name": vehicle.name,
        "number": None if vehicle.is_manual else vehicle.number,
        "license_plate": vehicle.license_plate,
        "vehicle_type": vehicle.vehicle_type,
        "make": vehicle.make,
        "model": vehicle.model,
        "year": vehicle.year,
        "vin": vehicle.vin,
        "fuel_type": vehicle.fuel_type,
        "leasing_company": vehicle.leasing_company,
        "leasing_contract_no": vehicle.leasing_contract_no,
        "leasing_end_on": vehicle.leasing_end_on,
        "inspection_due_on": vehicle.inspection_due_on,
        "insurance_due_on": vehicle.insurance_due_on,
        "manual_odometer_km": vehicle.manual_odometer_km,
        "manual_odometer_date": vehicle.manual_odometer_date,
        "gross_weight_kg": vehicle.gross_weight_kg,
        "passenger_seats": vehicle.passenger_seats,
        "tows_heavy_trailer": vehicle.tows_heavy_trailer,
        "required_category_override": vehicle.required_category_override,
        "archived": vehicle.archived,
        "archived_reason": vehicle.archived_reason,
        "driver_id": vehicle.driver_id,
    }


def driver_audit_snapshot(driver: Driver, categories: list[str]) -> dict[str, Any]:
    return {
        "display_name": driver.display_name,
        "first_name": driver.first_name,
        "last_name": driver.last_name,
        "identifier": driver.identifier,
        "active": driver.active,
        "categories": list(categories),
        "phone_configured": bool(driver.phone),
        "email_configured": bool(driver.email),
    }


def record_audit_event(
    session: Session,
    *,
    entity_type: str,
    entity_id: UUID | str,
    operation: str,
    changes: dict[str, Any] | None = None,
    actor_id: UUID | None = None,
    actor_type: str = "user",
    source_account: str | None = None,
    vehicle_id: UUID | None = None,
    outcome: str = "succeeded",
    request: Request | None = None,
    correlation_id: str | None = None,
    occurred_at: datetime | None = None,
) -> AuditEvent:
    if entity_type not in ENTITY_TYPES:
        raise ValueError(f"Unsupported entity_type: {entity_type}")
    if actor_type not in ACTOR_TYPES:
        raise ValueError(f"Unsupported actor_type: {actor_type}")
    if outcome not in OUTCOMES:
        raise ValueError(f"Unsupported outcome: {outcome}")

    normalized_entity_id = str(UUID(str(entity_id)))
    safe_changes = sanitize_changes(entity_type, changes)
    event_row = AuditEvent(
        occurred_at=occurred_at or datetime.now(UTC),
        source_account=source_account,
        actor_id=actor_id,
        actor_type=actor_type,
        entity_type=entity_type,
        entity_id=normalized_entity_id,
        vehicle_id=vehicle_id,
        operation=operation,
        outcome=outcome,
        correlation_id=resolve_correlation_id(request, correlation_id),
        changes=safe_changes,
    )
    session.add(event_row)
    return event_row
