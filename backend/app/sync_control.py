"""Operator-only canary and freshness check. No public endpoint or credential output."""

import argparse
import json
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import WebfleetSettings, load_environment
from app.core.database import make_engine
from app.core.models import SyncState
from app.core.settings import Settings
from app.modules.auth.service import aware
from app.modules.fleet.sync import account_key, log_sync_failure, sync_once


def freshness(session, source, max_age, *, now=None):
    state = session.get(SyncState, source)
    if not state or not state.last_success_at:
        return {"status": "unavailable", "last_success_at": None}
    now = now or datetime.now(UTC)
    age = (now - aware(state.last_success_at)).total_seconds()
    status = "degraded" if state.error_code else "ok"
    if age < -5 or age > max_age:
        status = "stale"
    return {"status": status, "last_success_at": aware(state.last_success_at).isoformat()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["once", "status"])
    parser.add_argument("--max-age", type=int, default=180)
    args = parser.parse_args()
    if not 60 <= args.max_age <= 86400:
        parser.error("--max-age: od 60 do 86400 sekund")
    engine = None
    try:
        settings = Settings.from_environment()
        if not settings.webfleet_account.strip():
            print('{"status":"configuration_required"}')
            return 1
        engine = make_engine(settings)
        if args.operation == "once":
            webfleet = WebfleetSettings.from_environment(load_environment())
            result = sync_once(engine, webfleet)
            print(json.dumps({"status": result}))
            return 0 if result == "ok" else 1
        with Session(engine) as session:
            payload = freshness(session, account_key(settings.webfleet_account), args.max_age)
        print(json.dumps(payload))
        return 0 if payload["status"] == "ok" else 1
    except Exception:
        log_sync_failure("SYNC_CONTROL_FAILED")
        print('{"status":"failed"}')
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
