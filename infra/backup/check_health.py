"""Report safe, machine-readable operational signals for the monitored environment."""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

SOURCE_STATUSES = {"ok", "stale", "degraded", "unavailable"}


def read_object(stream):
    try:
        value = json.load(stream)
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def read_status(directory, kind):
    try:
        with (directory / f"last-{kind}.json").open(encoding="utf-8") as stream:
            return read_object(stream)
    except OSError:
        return {}


def age_status(timestamp, now, maximum):
    if not isinstance(timestamp, str):
        return "missing"
    try:
        completed = datetime.fromisoformat(timestamp)
        if completed.tzinfo is None:
            return "invalid"
        age = (now - completed.astimezone(UTC)).total_seconds()
    except (ValueError, OverflowError):
        return "invalid"
    if age < -5:
        return "invalid"
    return "stale" if age > maximum else "ok"


def operational_health(source, directory, *, now, source_age, backup_age, restore_age):
    source_state = source.get("status")
    if not isinstance(source_state, str) or source_state not in SOURCE_STATUSES:
        source_state = "missing"
    elif source_state == "ok":
        source_state = age_status(source.get("last_success_at"), now, source_age)
    states = {
        "source": source_state,
        "backup": age_status(
            read_status(directory, "backup").get("completed_at"), now, backup_age
        ),
        "restore": age_status(
            read_status(directory, "restore").get("completed_at"), now, restore_age
        ),
    }
    signals = [f"{kind}_{state}" for kind, state in states.items() if state != "ok"]
    return {"status": "critical" if signals else "ok", "signals": signals}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state-dir", type=Path, default=Path("/var/lib/fleet-flow-backup")
    )
    parser.add_argument("--max-source-age", type=int, default=180)
    parser.add_argument("--max-backup-age", type=int, default=7 * 3600)
    parser.add_argument("--max-restore-age", type=int, default=32 * 86400)
    args = parser.parse_args()
    if min(args.max_source_age, args.max_backup_age, args.max_restore_age) < 1:
        parser.error("Age thresholds must be positive seconds")
    result = operational_health(
        read_object(sys.stdin),
        args.state_dir,
        now=datetime.now(UTC),
        source_age=args.max_source_age,
        backup_age=args.max_backup_age,
        restore_age=args.max_restore_age,
    )
    print(json.dumps(result))
    return int(result["status"] != "ok")


if __name__ == "__main__":
    raise SystemExit(main())
