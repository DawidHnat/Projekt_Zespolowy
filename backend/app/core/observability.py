"""Bounded operational metrics and validated X-Correlation-ID propagation (SCRUM-114).

Never place usernames, email addresses, IP addresses, session/reset tokens,
API keys, SQL text, provider payloads, or GPS coordinates into logs or metric labels.
"""

from __future__ import annotations

import base64
import json
import logging
import math
import re
import shutil
import threading
from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.errors import ApiError
from app.core.models import Measurement, SyncState, Vehicle
from app.modules.auth.models import User
from app.modules.auth.service import aware, current_user

CORRELATION_HEADER = "X-Correlation-ID"
CORRELATION_PATTERN = re.compile(r"^[A-Za-z0-9._-]{8,64}$")
SAFE_CODE_PATTERN = re.compile(r"^[A-Za-z0-9_]{1,40}$")

ALLOWED_METHODS = frozenset({"GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS", "HEAD"})
STATUS_CLASSES = ("2xx", "3xx", "4xx", "5xx")
DURATION_BUCKETS_MS = (10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1000.0, 2500.0, 5000.0, 10000.0)
MAX_ROUTE_TEMPLATES = 64

AUTH_EVENT_CODES = (
    "login_failed",
    "rate_limited",
    "forbidden",
    "unauthenticated",
    "invalid_reset",
    "invalid_current_password",
)
SMTP_EVENT_CODES = (
    "delivered",
    "setup_failed",
    "smtp_failed",
    "state_failed",
    "notification_failed",
)
SYNC_EVENT_CODES = (
    "ok",
    "busy",
    "rate_limited",
    "timeout",
    "connection_failed",
    "provider_rate_limit",
    "local_rate_limit",
    "INVALID_RECORDS",
    "INCOMPLETE_REPORT",
    "SOURCE_DEGRADED",
    "SYNC_INTERNAL_ERROR",
    "SYNC_CONTROL_FAILED",
    "OTHER",
)

MAX_BACKUP_AGE_SECONDS = 7 * 3600
MAX_RESTORE_AGE_SECONDS = 32 * 86400

logger = logging.getLogger("fleet_flow.observability")

_correlation_id: ContextVar[str | None] = ContextVar("fleet_flow_correlation_id", default=None)
_active_metrics: ContextVar[MetricsRegistry | None] = ContextVar(
    "fleet_flow_active_metrics", default=None
)


def normalize_correlation_id(raw: str | None) -> str:
    if isinstance(raw, str) and CORRELATION_PATTERN.fullmatch(raw):
        return raw
    return uuid4().hex


def get_bound_correlation_id() -> str | None:
    return _correlation_id.get()


def current_correlation_id() -> str:
    bound = _correlation_id.get()
    if bound is not None:
        return bound
    return uuid4().hex


@contextmanager
def bind_correlation_id(raw: str | None = None):
    cid = normalize_correlation_id(raw)
    token = _correlation_id.set(cid)
    try:
        yield cid
    finally:
        _correlation_id.reset(token)


@contextmanager
def bind_metrics(registry: MetricsRegistry | None):
    token = _active_metrics.set(registry)
    try:
        yield
    finally:
        _active_metrics.reset(token)


def sanitize_code(code: str | None, allowed: tuple[str, ...], fallback: str = "OTHER") -> str:
    if isinstance(code, str) and code in allowed:
        return code
    if isinstance(code, str) and SAFE_CODE_PATTERN.fullmatch(code) and fallback in allowed:
        return fallback
    return allowed[-1]


def _percentile_95(samples: list[float]) -> float | None:
    if not samples:
        return None
    ordered = sorted(samples)
    index = max(0, min(len(ordered) - 1, math.ceil(0.95 * len(ordered)) - 1))
    return round(ordered[index], 2)


def route_template(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if isinstance(path, str) and path.startswith("/"):
        return path[:120]
    return "unmatched"


class MetricsRegistry:
    """Thread-safe, bounded-cardinality operational counters and latency windows."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._requests_total = 0
        self._errors_5xx_total = 0
        self._known_routes: set[str] = set()
        self._by_route_status: dict[tuple[str, str, str], int] = {}
        self._durations_ms: deque[float] = deque(maxlen=512)
        self._route_status_durations_ms: dict[tuple[str, str, str], deque[float]] = {}
        self._route_durations_ms: dict[str, deque[float]] = {}
        self._duration_buckets: dict[float, int] = {b: 0 for b in DURATION_BUCKETS_MS}
        self._duration_inf = 0
        self._auth_events: dict[str, int] = {code: 0 for code in AUTH_EVENT_CODES}
        self._smtp_events: dict[str, int] = {code: 0 for code in SMTP_EVENT_CODES}
        self._sync_events: dict[str, int] = {code: 0 for code in SYNC_EVENT_CODES}

    def record_http(self, method: str, route: str, status_code: int, duration_ms: float) -> None:
        safe_method = method if method in ALLOWED_METHODS else "OTHER"
        status_group = f"{min(max(status_code // 100, 2), 5)}xx"
        if status_group not in STATUS_CLASSES:
            status_group = "5xx"
        bounded_duration = max(0.0, float(duration_ms))

        with self._lock:
            safe_route = route
            if (
                safe_route not in self._known_routes
                and len(self._known_routes) >= MAX_ROUTE_TEMPLATES
            ):
                safe_route = "other"
            else:
                self._known_routes.add(safe_route)
            key = (safe_method, safe_route, status_group)
            self._requests_total += 1
            if status_code >= 500:
                self._errors_5xx_total += 1
            self._by_route_status[key] = self._by_route_status.get(key, 0) + 1
            self._durations_ms.append(bounded_duration)
            self._route_status_durations_ms.setdefault(key, deque(maxlen=128)).append(
                bounded_duration
            )
            self._route_durations_ms.setdefault(safe_route, deque(maxlen=128)).append(
                bounded_duration
            )
            for bound in DURATION_BUCKETS_MS:
                if bounded_duration <= bound:
                    self._duration_buckets[bound] += 1
            self._duration_inf += 1

    def record_auth_event(self, code: str) -> None:
        if code not in AUTH_EVENT_CODES:
            return
        with self._lock:
            self._auth_events[code] += 1

    def record_smtp_event(self, code: str) -> None:
        if code not in SMTP_EVENT_CODES:
            return
        with self._lock:
            self._smtp_events[code] += 1

    def record_sync_event(self, code: str) -> None:
        safe = sanitize_code(code, SYNC_EVENT_CODES, fallback="OTHER")
        with self._lock:
            self._sync_events[safe] += 1

    def snapshot_counters(self) -> dict[str, Any]:
        with self._lock:
            all_samples = list(self._durations_ms)
            by_route: list[dict[str, Any]] = []
            for (method, route, status_class), count in sorted(self._by_route_status.items()):
                key_samples = list(
                    self._route_status_durations_ms.get((method, route, status_class), ())
                )
                by_route.append(
                    {
                        "method": method,
                        "route": route,
                        "status_class": status_class,
                        "requests_total": count,
                        "duration_p95_ms": _percentile_95(key_samples),
                    }
                )
            route_p95 = {
                route: _percentile_95(list(samples))
                for route, samples in sorted(self._route_durations_ms.items())
            }
            return {
                "http": {
                    "requests_total": self._requests_total,
                    "errors_5xx_total": self._errors_5xx_total,
                    "duration_p95_ms": _percentile_95(all_samples),
                    "buckets_ms": {str(int(k)): v for k, v in self._duration_buckets.items()},
                    "route_p95_ms": route_p95,
                    "by_route": by_route,
                },
                "auth": dict(self._auth_events),
                "smtp": dict(self._smtp_events),
                "sync_events": dict(self._sync_events),
            }


DEFAULT_METRICS = MetricsRegistry()


def active_metrics(app: Any = None) -> MetricsRegistry:
    if app is not None:
        registry = getattr(getattr(app, "state", None), "metrics", None)
        if isinstance(registry, MetricsRegistry):
            return registry
    bound = _active_metrics.get()
    return bound if bound is not None else DEFAULT_METRICS


def log_http_server_error(method: str, route: str, status_code: int, correlation_id: str) -> None:
    safe_method = method if method in ALLOWED_METHODS else "OTHER"
    logger.error(
        json.dumps(
            {
                "event": "http_server_error",
                "method": safe_method,
                "route": route,
                "status": int(status_code),
                "correlation_id": correlation_id,
            }
        )
    )


def _read_der_tlv(data: bytes, offset: int) -> tuple[int, bytes, int]:
    if offset + 2 > len(data):
        raise ValueError("Truncated DER header")
    tag = data[offset]
    first = data[offset + 1]
    pos = offset + 2
    if first < 0x80:
        length = first
    else:
        count = first & 0x7F
        if count < 1 or count > 4 or pos + count > len(data):
            raise ValueError("Invalid DER length")
        length = int.from_bytes(data[pos : pos + count], "big")
        pos += count
    end = pos + length
    if end > len(data):
        raise ValueError("Truncated DER value")
    return tag, data[pos:end], end


def _parse_asn1_time(tag: int, raw: bytes) -> datetime:
    text_val = raw.decode("ascii")
    if not text_val.endswith("Z"):
        raise ValueError("Expected UTC ASN.1 time")
    digits = text_val[:-1]
    if tag == 0x17 and len(digits) == 12:
        yy = int(digits[0:2])
        year = 2000 + yy if yy < 50 else 1900 + yy
        rest = digits[2:]
    elif tag == 0x18 and len(digits) == 14:
        year = int(digits[0:4])
        rest = digits[4:]
    else:
        raise ValueError("Unsupported ASN.1 time format")
    return datetime(
        year,
        int(rest[0:2]),
        int(rest[2:4]),
        int(rest[4:6]),
        int(rest[6:8]),
        int(rest[8:10]),
        tzinfo=UTC,
    )


def parse_pem_certificate_expiry(pem_text: str) -> datetime:
    begin = "-----BEGIN CERTIFICATE-----"
    end = "-----END CERTIFICATE-----"
    start_idx = pem_text.find(begin)
    end_idx = pem_text.find(end)
    if start_idx < 0 or end_idx <= start_idx:
        raise ValueError("Missing PEM certificate block")
    b64 = "".join(pem_text[start_idx + len(begin) : end_idx].split())
    der = base64.b64decode(b64, validate=True)
    cert_tag, cert_body, _ = _read_der_tlv(der, 0)
    if cert_tag != 0x30:
        raise ValueError("Invalid X.509 sequence")
    tbs_tag, tbs_body, _ = _read_der_tlv(cert_body, 0)
    if tbs_tag != 0x30:
        raise ValueError("Invalid TBSCertificate sequence")
    pos = 0
    first_tag, _, next_pos = _read_der_tlv(tbs_body, pos)
    if first_tag == 0xA0:
        pos = next_pos
    for _ in range(3):
        _, _, pos = _read_der_tlv(tbs_body, pos)
    val_tag, val_body, _ = _read_der_tlv(tbs_body, pos)
    if val_tag != 0x30:
        raise ValueError("Invalid Validity sequence")
    _, _, after_offset = _read_der_tlv(val_body, 0)
    after_tag, after_raw, _ = _read_der_tlv(val_body, after_offset)
    return _parse_asn1_time(after_tag, after_raw)


def inspect_tls_certificate(
    cert_path: str, *, warning_days: int = 21, critical_days: int = 7, now: datetime | None = None
) -> dict[str, Any]:
    now = now or datetime.now(UTC)
    cleaned = cert_path.strip()
    if not cleaned:
        return {
            "status": "not_configured",
            "days_remaining": None,
            "warning_days": warning_days,
            "critical_days": critical_days,
        }
    try:
        raw = Path(cleaned).read_bytes()
        if len(raw) > 65536:
            raise ValueError("Certificate file too large")
        expires_at = parse_pem_certificate_expiry(raw.decode("ascii"))
        remaining_days = round((expires_at - now).total_seconds() / 86400.0, 2)
        if remaining_days <= critical_days:
            status = "critical"
        elif remaining_days <= warning_days:
            status = "warning"
        else:
            status = "ok"
        return {
            "status": status,
            "days_remaining": remaining_days,
            "warning_days": warning_days,
            "critical_days": critical_days,
        }
    except (OSError, UnicodeDecodeError, ValueError):
        return {
            "status": "error",
            "days_remaining": None,
            "warning_days": warning_days,
            "critical_days": critical_days,
        }


def _marker_age_snapshot(
    directory: Path, kind: str, max_age_seconds: int, now: datetime
) -> dict[str, Any]:
    marker = directory / f"last-{kind}.json"
    if not marker.is_file():
        return {
            "status": "missing",
            "deferred_to": None,
            "last_success_age_seconds": None,
            "max_age_seconds": max_age_seconds,
        }
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
        timestamp = payload.get("completed_at") if isinstance(payload, dict) else None
        if not isinstance(timestamp, str):
            raise ValueError("Missing completed_at")
        completed = datetime.fromisoformat(timestamp)
        if completed.tzinfo is None:
            raise ValueError("Naive timestamp")
        age = (now - completed.astimezone(UTC)).total_seconds()
        if age < -5:
            raise ValueError("Future timestamp")
        bounded_age = round(max(0.0, age), 2)
        return {
            "status": "stale" if age > max_age_seconds else "ok",
            "deferred_to": None,
            "last_success_age_seconds": bounded_age,
            "max_age_seconds": max_age_seconds,
        }
    except (OSError, ValueError, OverflowError):
        return {
            "status": "invalid",
            "deferred_to": None,
            "last_success_age_seconds": None,
            "max_age_seconds": max_age_seconds,
        }


def inspect_backup_and_restore(state_dir: str, *, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(UTC)
    cleaned = state_dir.strip()
    if not cleaned:
        return {
            "backup": {
                "status": "not_configured",
                "deferred_to": "SCRUM-84",
                "last_success_age_seconds": None,
                "max_age_seconds": MAX_BACKUP_AGE_SECONDS,
            },
            "restore": {
                "status": "not_configured",
                "deferred_to": "SCRUM-84",
                "last_success_age_seconds": None,
                "max_age_seconds": MAX_RESTORE_AGE_SECONDS,
            },
        }
    directory = Path(cleaned)
    return {
        "backup": _marker_age_snapshot(directory, "backup", MAX_BACKUP_AGE_SECONDS, now),
        "restore": _marker_age_snapshot(directory, "restore", MAX_RESTORE_AGE_SECONDS, now),
    }


def inspect_disk_usage(target_path: str) -> dict[str, Any]:
    try:
        usage = shutil.disk_usage(target_path.strip() or ".")
        free_ratio = round(usage.free / usage.total, 4) if usage.total > 0 else 0.0
        if free_ratio < 0.05:
            status = "critical"
        elif free_ratio < 0.15:
            status = "warning"
        else:
            status = "ok"
        return {
            "status": status,
            "total_bytes": int(usage.total),
            "used_bytes": int(usage.used),
            "free_bytes": int(usage.free),
            "free_ratio": free_ratio,
        }
    except OSError:
        return {
            "status": "error",
            "total_bytes": None,
            "used_bytes": None,
            "free_bytes": None,
            "free_ratio": None,
        }


def inspect_db_pool(engine: Any) -> dict[str, Any]:
    db_up = False
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        db_up = True
    except SQLAlchemyError:
        db_up = False
    pool = getattr(engine, "pool", None)
    return {
        "db_up": db_up,
        "pool_type": type(pool).__name__ if pool is not None else "unknown",
        "size": int(pool.size()) if hasattr(pool, "size") else None,
        "checked_in": int(pool.checkedin()) if hasattr(pool, "checkedin") else None,
        "checked_out": int(pool.checkedout()) if hasattr(pool, "checkedout") else None,
        "overflow": int(pool.overflow()) if hasattr(pool, "overflow") else None,
    }


def inspect_sync_state(app: Any, sync_events: dict[str, int], now: datetime) -> dict[str, Any]:
    from app.modules.fleet.sync import account_key

    settings = app.state.settings
    account = settings.webfleet_account.strip()
    max_age = max(180, settings.sync_interval_seconds * 3)
    if not account:
        return {
            "status": "not_configured",
            "last_success_age_seconds": None,
            "latest_measurement_age_seconds": None,
            "last_error_code": None,
            "max_age_seconds": max_age,
            "events_total": sync_events,
        }

    source = account_key(account)
    try:
        with app.state.sessions() as session:
            state = session.get(SyncState, source)
            latest_received = session.scalar(
                select(func.max(Measurement.received_at))
                .join(Vehicle, Vehicle.id == Measurement.vehicle_id)
                .where(Vehicle.source_account == source)
            )
    except SQLAlchemyError:
        return {
            "status": "unavailable",
            "last_success_age_seconds": None,
            "latest_measurement_age_seconds": None,
            "last_error_code": "DATABASE_UNAVAILABLE",
            "max_age_seconds": max_age,
            "events_total": sync_events,
        }

    measurement_age = None
    if latest_received is not None:
        measurement_age = round(max(0.0, (now - aware(latest_received)).total_seconds()), 2)

    if not state or not state.last_success_at:
        err = (
            sanitize_code(state.error_code, SYNC_EVENT_CODES)
            if state and state.error_code
            else None
        )
        return {
            "status": "degraded" if err else "unavailable",
            "last_success_age_seconds": None,
            "latest_measurement_age_seconds": measurement_age,
            "last_error_code": err,
            "max_age_seconds": max_age,
            "events_total": sync_events,
        }

    age = (now - aware(state.last_success_at)).total_seconds()
    err = sanitize_code(state.error_code, SYNC_EVENT_CODES) if state.error_code else None
    status = "degraded" if err else "ok"
    if age < -5 or age > max_age:
        status = "stale"
    return {
        "status": status,
        "last_success_age_seconds": round(max(0.0, age), 2),
        "latest_measurement_age_seconds": measurement_age,
        "last_error_code": err,
        "max_age_seconds": max_age,
        "events_total": sync_events,
    }


def collect_metrics_snapshot(app: Any, *, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(UTC)
    settings = app.state.settings
    registry = active_metrics(app)
    counters = registry.snapshot_counters()
    db_pool = inspect_db_pool(app.state.engine)
    sync_info = inspect_sync_state(app, counters["sync_events"], now)
    disk_info = inspect_disk_usage(settings.disk_path)
    backup_info = inspect_backup_and_restore(settings.backup_state_dir, now=now)
    tls_info = inspect_tls_certificate(
        settings.tls_cert_path,
        warning_days=settings.tls_warning_days,
        critical_days=settings.tls_critical_days,
        now=now,
    )
    return {
        "api_up": 1 if db_pool["db_up"] else 0,
        "collected_at": now.isoformat().replace("+00:00", "Z"),
        "http": counters["http"],
        "db_pool": db_pool,
        "sync": sync_info,
        "disk": disk_info,
        "backup": backup_info["backup"],
        "restore": backup_info["restore"],
        "tls": tls_info,
        "auth": {"events_total": counters["auth"]},
        "mail": {
            "events_total": counters["smtp"],
            "queue": {
                "status": "not_configured",
                "deferred_to": "SCRUM-73",
                "pending": None,
                "oldest_age_seconds": None,
            },
        },
    }


def _prom_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def render_prometheus(snapshot: dict[str, Any]) -> str:
    lines = [
        "# HELP fleet_flow_api_up API and database readiness (1=up, 0=degraded).",
        "# TYPE fleet_flow_api_up gauge",
        f"fleet_flow_api_up {snapshot['api_up']}",
        "# HELP fleet_flow_http_requests_total Bounded HTTP request counter.",
        "# TYPE fleet_flow_http_requests_total counter",
    ]
    for item in snapshot["http"]["by_route"]:
        labels = (
            f'method="{_prom_escape(item["method"])}",'
            f'route="{_prom_escape(item["route"])}",'
            f'status_class="{_prom_escape(item["status_class"])}"'
        )
        lines.append(f"fleet_flow_http_requests_total{{{labels}}} {item['requests_total']}")
    lines.extend(
        [
            "# HELP fleet_flow_http_5xx_total Total HTTP 5xx responses.",
            "# TYPE fleet_flow_http_5xx_total counter",
            f"fleet_flow_http_5xx_total {snapshot['http']['errors_5xx_total']}",
        ]
    )
    if snapshot["http"]["duration_p95_ms"] is not None:
        lines.extend(
            [
                "# HELP fleet_flow_http_duration_p95_ms Rolling p95 HTTP latency in ms.",
                "# TYPE fleet_flow_http_duration_p95_ms gauge",
                f"fleet_flow_http_duration_p95_ms {snapshot['http']['duration_p95_ms']}",
            ]
        )
    pool = snapshot["db_pool"]
    lines.append(f"fleet_flow_db_up {1 if pool['db_up'] else 0}")
    for field_name in ("size", "checked_in", "checked_out", "overflow"):
        if pool[field_name] is not None:
            lines.append(f"fleet_flow_db_pool_{field_name} {pool[field_name]}")

    sync = snapshot["sync"]
    lines.append(f'fleet_flow_sync_status{{status="{_prom_escape(sync["status"])}"}} 1')
    if sync["last_success_age_seconds"] is not None:
        lines.append(f"fleet_flow_sync_last_success_age_seconds {sync['last_success_age_seconds']}")
    if sync["latest_measurement_age_seconds"] is not None:
        lines.append(
            f"fleet_flow_sync_measurement_age_seconds {sync['latest_measurement_age_seconds']}"
        )
    for code, count in sorted(sync["events_total"].items()):
        lines.append(f'fleet_flow_sync_events_total{{code="{_prom_escape(code)}"}} {count}')

    disk = snapshot["disk"]
    if disk["free_bytes"] is not None:
        lines.append(f"fleet_flow_disk_free_bytes {disk['free_bytes']}")
        lines.append(f"fleet_flow_disk_used_bytes {disk['used_bytes']}")
        lines.append(f"fleet_flow_disk_total_bytes {disk['total_bytes']}")

    for kind in ("backup", "restore"):
        info = snapshot[kind]
        lines.append(f'fleet_flow_{kind}_status{{status="{_prom_escape(info["status"])}"}} 1')
        if info["last_success_age_seconds"] is not None:
            lines.append(
                f"fleet_flow_{kind}_last_success_age_seconds {info['last_success_age_seconds']}"
            )

    tls = snapshot["tls"]
    lines.append(f'fleet_flow_tls_status{{status="{_prom_escape(tls["status"])}"}} 1')
    if tls["days_remaining"] is not None:
        lines.append(f"fleet_flow_tls_days_remaining {tls['days_remaining']}")

    for code, count in sorted(snapshot["auth"]["events_total"].items()):
        lines.append(f'fleet_flow_auth_events_total{{code="{_prom_escape(code)}"}} {count}')
    for code, count in sorted(snapshot["mail"]["events_total"].items()):
        lines.append(f'fleet_flow_smtp_events_total{{code="{_prom_escape(code)}"}} {count}')
    return "\n".join(lines) + "\n"


router = APIRouter(prefix="/api/v1/observability", tags=["observability"])


def require_admin(user: Annotated[User, Depends(current_user)]) -> User:
    if user.role != "admin":
        raise ApiError(403, "FORBIDDEN", "Ta operacja wymaga uprawnień administratora")
    return user


@router.get("/metrics")
def get_observability_metrics(
    request: Request,
    _: Annotated[User, Depends(require_admin)],
    format: Annotated[Literal["json", "prometheus"], Query()] = "json",
):
    snapshot = collect_metrics_snapshot(request.app)
    if format == "prometheus":
        return PlainTextResponse(
            render_prometheus(snapshot),
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )
    return snapshot
