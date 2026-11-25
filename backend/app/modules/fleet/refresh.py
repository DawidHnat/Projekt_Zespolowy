"""Manual reads share the worker's account-wide lock, interval and provider backoff."""

from datetime import UTC, datetime, timedelta
from math import ceil

from sqlalchemy import text

from app.core.errors import ApiError
from app.core.models import SyncState
from app.integrations.webfleet.client import WebfleetClient
from app.modules.auth.service import aware
from app.modules.fleet.service import timestamp
from app.modules.fleet.sync import account_key, minimum_sync_interval, source_lock_id, sync_once


def refresh_state(request, session, *, now=None):
    settings = request.app.state.settings
    webfleet = request.app.state.webfleet_settings
    source = account_key(settings.webfleet_account)
    enabled = bool(settings.sync_enabled and webfleet and source == account_key(webfleet.account))
    state = session.get(SyncState, source)
    now = now or datetime.now(UTC)
    next_allowed = (
        aware(state.last_attempt_at)
        + timedelta(seconds=minimum_sync_interval(settings.sync_interval_seconds))
        if enabled and state and state.last_attempt_at
        else None
    )
    running = False
    if enabled and session.get_bind().dialect.name == "postgresql":
        # Read pg_locks without acquiring a lock that could delay the worker.
        # PostgreSQL represents a bigint key as unsigned high/low 32-bit halves.
        key = source_lock_id(source) & ((1 << 64) - 1)
        running = bool(
            session.scalar(
                text(
                    "SELECT EXISTS (SELECT 1 FROM pg_locks "
                    "WHERE locktype = 'advisory' AND granted AND mode = 'ExclusiveLock' "
                    "AND database = (SELECT oid FROM pg_database "
                    "WHERE datname = current_database()) "
                    "AND classid::bigint = :high AND objid::bigint = :low AND objsubid = 1)"
                ),
                {"high": key >> 32, "low": key & 0xFFFFFFFF},
            )
        )
    return {
        "enabled": enabled,
        "running": running,
        "server_time": timestamp(now),
        "next_allowed_at": timestamp(next_allowed),
        "retry_after_seconds": max(0, ceil((next_allowed - now).total_seconds()))
        if next_allowed
        else 0,
    }


def request_refresh(request, session):
    state = refresh_state(request, session)
    if not state["enabled"]:
        return {**state, "result": "disabled"}
    # Release the authentication read transaction before the provider request.
    session.rollback()
    try:
        result = sync_once(
            request.app.state.engine,
            request.app.state.webfleet_settings,
            client_factory=WebfleetClient,
            sync_interval_seconds=request.app.state.settings.sync_interval_seconds,
            stale_seconds=request.app.state.settings.stale_seconds,
        )
    except Exception:
        # Provider/SQL exception details can contain private telemetry or credentials.
        raise ApiError(503, "REFRESH_UNAVAILABLE", "Nie udało się odświeżyć danych floty") from None
    session.expire_all()
    return {
        **refresh_state(request, session),
        "result": {
            "ok": "updated",
            "rate_limited": "cooldown",
            "busy": "busy",
            "degraded": "failed",
        }[result],
    }
