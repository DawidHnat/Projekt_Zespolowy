import asyncio
import json
from datetime import UTC, datetime, timedelta

import pytest

from app.core.models import SyncState
from app.modules.fleet import sync
from app.sync_control import freshness


def test_worker_logs_fixed_code_without_exception_data_and_continues(monkeypatch, caplog):
    calls = []

    def attempt(*_):
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("synthetic-secret-sql-gps")
        return "degraded"

    async def sleep(_):
        if len(calls) == 2:
            raise asyncio.CancelledError

    monkeypatch.setattr(sync, "sync_once", attempt)
    monkeypatch.setattr(sync.asyncio, "sleep", sleep)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(sync.sync_worker(None, None, 60))
    assert len(calls) == 2
    assert "synthetic-secret" not in caplog.text
    events = [json.loads(item.message) for item in caplog.records if item.name == "fleet_flow.sync"]
    assert [item["code"] for item in events] == ["SYNC_INTERNAL_ERROR", "SOURCE_DEGRADED"]
    assert all(len(item["event_id"]) == 32 for item in events)
    assert events[0]["event_id"] != events[1]["event_id"]


def test_freshness_fails_without_success_and_for_degraded_old_or_future_cache(application):
    app, _ = application
    now = datetime.now(UTC)
    with app.state.sessions() as session:
        assert freshness(session, "synthetic", 180, now=now)["status"] == "unavailable"
        state = SyncState(source_account="synthetic", last_success_at=now)
        session.add(state)
        session.flush()
        assert freshness(session, "synthetic", 180, now=now)["status"] == "ok"
        state.error_code = "timeout"
        assert freshness(session, "synthetic", 180, now=now)["status"] == "degraded"
        state.error_code = None
        state.last_success_at = now - timedelta(seconds=181)
        assert freshness(session, "synthetic", 180, now=now)["status"] == "stale"
        state.last_success_at = now + timedelta(seconds=6)
        assert freshness(session, "synthetic", 180, now=now)["status"] == "stale"
