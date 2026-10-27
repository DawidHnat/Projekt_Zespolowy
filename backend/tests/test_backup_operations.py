"""Synthetic backup failures must not report success, leak secrets, or prune recovery points."""

import importlib.util
import json
import os
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest

spec = importlib.util.spec_from_file_location(
    "backup_operations", Path(__file__).resolve().parents[2] / "infra/backup/backup.py"
)
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)


def test_command_errors_do_not_expose_subprocess_output(monkeypatch):
    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args, stderr=b"synthetic-secret-and-gps")

    monkeypatch.setattr(backup.subprocess, "run", fail)
    with pytest.raises(backup.BackupError, match="^command_failed$"):
        backup.run(["synthetic-secret"])


def test_repository_must_be_remote_and_password_private(tmp_path, monkeypatch):
    password = tmp_path / "password"
    password.write_text("synthetic-only")
    password.chmod(0o600)
    monkeypatch.setenv("RESTIC_PASSWORD_FILE", str(password))
    monkeypatch.setenv("RESTIC_REPOSITORY", str(tmp_path / "same-vps"))
    with pytest.raises(backup.BackupError, match="remote_repository_required"):
        backup.validate_repository()
    monkeypatch.setenv("RESTIC_REPOSITORY", "s3:https://example.invalid/bucket")
    backup.validate_repository()
    password.chmod(0o644)
    with pytest.raises(backup.BackupError, match="password_file_permissions"):
        backup.validate_repository()


def test_concurrent_operation_is_rejected(tmp_path):
    state = tmp_path / "state"
    with backup.locked_state(state):
        with pytest.raises(backup.BackupError, match="operation_in_progress"):
            with backup.locked_state(state):
                pytest.fail("Second backup acquired the same lock")


@pytest.mark.parametrize("failure", ["dump", "upload", "download", "check", "forget", None])
def test_backup_verifies_before_retention_and_cleans_plaintext(tmp_path, monkeypatch, failure):
    state = tmp_path / "state"
    state.mkdir(mode=0o700)
    calls = []
    identity = "a" * 64
    monkeypatch.setattr(backup, "compose_command", lambda: (["synthetic-docker"], "b" * 40))

    def fake_run(args, *, output=None):
        calls.append("dump")
        if failure == "dump":
            raise backup.BackupError("command_failed")
        output.write(b"synthetic-dump")

    def fake_restic(*args, output=None):
        calls.append(args[0])
        if failure in ("upload", "check", "forget") and args[0] == {"upload": "backup"}.get(
            failure, failure
        ):
            raise backup.BackupError("command_failed")
        if args[0] == "backup":
            return json.dumps({"snapshot_id": identity}).encode()

    def fake_download(snapshot, target):
        calls.append("download")
        assert snapshot == identity
        if failure == "download":
            raise backup.BackupError("checksum_mismatch")
        return target / "test", identity

    monkeypatch.setattr(backup, "run", fake_run)
    monkeypatch.setattr(backup, "restic", fake_restic)
    monkeypatch.setattr(backup, "download", fake_download)
    if failure:
        with pytest.raises(backup.BackupError):
            backup.backup(state)
        assert not (state / "last-backup.json").exists()
        if failure != "forget":
            assert "forget" not in calls
    else:
        backup.backup(state)
        assert calls == ["dump", "backup", "download", "check", "forget"]
        assert json.loads((state / "last-backup.json").read_text())["snapshot"] == identity
    assert not (state / "payload").exists()


def test_download_detects_corrupted_dump(tmp_path, monkeypatch):
    monkeypatch.setattr(backup, "snapshot_paths", lambda _: ("a" * 64, "/state/payload"))

    def fake_restic(*args, output=None):
        if args[-1].endswith("manifest.json"):
            return json.dumps({"sha256": "0" * 64}).encode()
        output.write(b"corrupted")

    monkeypatch.setattr(backup, "restic", fake_restic)
    with pytest.raises(backup.BackupError, match="checksum_mismatch"):
        backup.download("latest", tmp_path)


def test_restore_failure_cleans_container_and_does_not_mark_success(tmp_path, monkeypatch):
    dump = tmp_path / "fixture.dump"
    dump.write_bytes(b"synthetic")
    monkeypatch.setattr(backup, "download", lambda *_: (dump, "a" * 64))
    calls = []
    monkeypatch.setattr(backup, "run", lambda args, **_: calls.append(args))

    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args)

    monkeypatch.setattr(backup.subprocess, "run", fail)
    with pytest.raises(backup.BackupError, match="restore_failed"):
        backup.restore_check(tmp_path, "latest")
    assert calls[-1][:3] == ["docker", "rm", "-f"]
    assert not (tmp_path / "last-restore.json").exists()


@pytest.mark.skipif(
    os.environ.get("BACKUP_INTEGRATION_TEST") != "true",
    reason="Requires local restic and Docker; uses only a disposable synthetic database",
)
def test_real_dump_encrypted_snapshot_download_and_isolated_restore(tmp_path, monkeypatch):
    password = tmp_path / "password"
    password.write_text("synthetic-backup-test-only")
    password.chmod(0o600)
    monkeypatch.setenv("RESTIC_REPOSITORY", str(tmp_path / "repository"))
    monkeypatch.setenv("RESTIC_PASSWORD_FILE", str(password))
    # Local repo is used only by this integration fixture. Production validation rejects it.
    backup.restic("init")
    source = "fleet-flow-backup-test-" + uuid4().hex
    try:
        backup.run(
            [
                "docker",
                "run",
                "-d",
                "--rm",
                "--name",
                source,
                "--network",
                "none",
                "-e",
                "POSTGRES_HOST_AUTH_METHOD=trust",
                "postgres:17-alpine",
            ]
        )
        for _ in range(60):
            try:
                backup.run(["docker", "exec", source, "pg_isready", "-U", "postgres"])
                break
            except backup.BackupError:
                backup.time.sleep(1)
        backup.run(
            [
                "docker",
                "exec",
                source,
                "psql",
                "-U",
                "postgres",
                "-v",
                "ON_ERROR_STOP=1",
                "-c",
                "CREATE TABLE alembic_version (version_num text); "
                "INSERT INTO alembic_version VALUES ('synthetic'); "
                "CREATE TABLE vehicles (id integer PRIMARY KEY); INSERT INTO vehicles VALUES (1);",
            ]
        )
        monkeypatch.setattr(
            backup,
            "compose_command",
            lambda: (
                ["docker", "exec", source, "env", "POSTGRES_USER=postgres", "POSTGRES_DB=postgres"],
                "a" * 40,
            ),
        )
        state = tmp_path / "state"
        with backup.locked_state(state):
            backup.backup(state)
            backup.restore_check(state, "latest")
        assert (state / "last-backup.json").is_file()
        assert (state / "last-restore.json").is_file()
    finally:
        backup.run(["docker", "rm", "-f", source])
