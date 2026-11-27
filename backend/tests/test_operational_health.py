import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "infra/backup/check_health.py"


def test_synthetic_sync_and_backup_marks_emit_only_fixed_operational_signals(tmp_path):
    now = datetime.now(UTC)
    recent = (now - timedelta(seconds=4)).isoformat()
    for kind in ("backup", "restore"):
        (tmp_path / f"last-{kind}.json").write_text(json.dumps({"completed_at": recent}))

    def check(source):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--state-dir", str(tmp_path)],
            input=json.dumps(source),
            capture_output=True,
            text=True,
        )
        return result.returncode, json.loads(result.stdout)

    assert check({"status": "ok", "last_success_at": recent}) == (
        0,
        {"status": "ok", "signals": []},
    )
    (tmp_path / "last-backup.json").write_text(
        json.dumps(
            {
                "completed_at": (now - timedelta(hours=8)).isoformat(),
                "repository": "synthetic confidential value",
            }
        )
    )
    (tmp_path / "last-restore.json").write_text("malformed")
    status, payload = check(
        {"status": "degraded", "private_details": "synthetic confidential value"}
    )
    assert status == 1
    assert payload == {
        "status": "critical",
        "signals": ["source_degraded", "backup_stale", "restore_missing"],
    }
    expired = (now - timedelta(minutes=4)).isoformat()
    assert "source_stale" in check({"status": "ok", "last_success_at": expired})[1]["signals"]
