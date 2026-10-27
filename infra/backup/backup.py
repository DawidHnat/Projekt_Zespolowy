#!/usr/bin/env python3
"""Encrypted PostgreSQL backups. Never print subprocess output or environment values."""

import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


class BackupError(Exception):
    pass


def run(args, *, output=None):
    try:
        result = subprocess.run(
            args, check=True, stdout=output or subprocess.PIPE, stderr=subprocess.PIPE
        )
    except (OSError, subprocess.CalledProcessError):
        raise BackupError("command_failed") from None
    return result.stdout


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def validate_repository():
    repository = os.environ.get("RESTIC_REPOSITORY", "")
    # A local directory on the same VPS cannot satisfy the off-site requirement.
    if not repository.startswith(("s3:https://", "sftp:", "rest:https://", "azure:", "gs:", "b2:")):
        raise BackupError("remote_repository_required")
    password = Path(os.environ.get("RESTIC_PASSWORD_FILE", ""))
    if not password.is_absolute() or not password.is_file():
        raise BackupError("password_file_required")
    if password.stat().st_mode & 0o077:
        raise BackupError("password_file_permissions")


def restic(*args, output=None):
    return run(["restic", "--no-cache", *args], output=output)


@contextmanager
def locked_state(path):
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink() or path.stat().st_mode & 0o077:
        raise BackupError("state_directory_permissions")
    with (path / "operation.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise BackupError("operation_in_progress") from None
        yield


def mark_success(state, operation, **extra):
    payload = {"completed_at": datetime.now(UTC).isoformat(), **extra}
    temporary = state / f".{operation}.json"
    temporary.write_text(json.dumps(payload) + "\n")
    temporary.replace(state / f"last-{operation}.json")


def compose_command():
    base = Path(os.environ.get("FLEET_FLOW_BASE", "/opt/fleet-flow"))
    release = (base / "current").resolve(strict=True)
    revision = (release / "commit").read_text().strip()
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise BackupError("invalid_release")
    os.environ["FLEET_FLOW_BUILD_SHA"] = revision
    os.environ["FLEET_FLOW_ENV_FILE"] = str(base / "shared/runtime.env")
    return [
        "docker",
        "compose",
        "-p",
        "fleet-flow",
        "--env-file",
        os.environ["FLEET_FLOW_ENV_FILE"],
        "-f",
        str(release / "infra/deploy/compose.yml"),
        "exec",
        "-T",
        "database",
    ], revision


def snapshot_paths(snapshot):
    if snapshot != "latest" and not re.fullmatch(r"[0-9a-f]{8,64}", snapshot):
        raise BackupError("invalid_snapshot")
    # Resolve latest only within this application's backup stream, also on a new host.
    snapshots = json.loads(restic("snapshots", "--json", "--tag", "fleet-flow-postgres", snapshot))
    if not snapshots:
        raise BackupError("snapshot_missing")
    selected = max(snapshots, key=lambda item: item["time"])
    if len(selected["paths"]) != 1 or not selected["paths"][0].endswith("/payload"):
        raise BackupError("invalid_snapshot_paths")
    return selected["id"], selected["paths"][0]


def download(snapshot, target):
    identity, path = snapshot_paths(snapshot)
    manifest = json.loads(restic("dump", identity, f"{path}/manifest.json"))
    expected = manifest.get("sha256", "")
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise BackupError("invalid_manifest")
    dump = target / "fleet-flow.dump"
    with dump.open("wb") as stream:
        restic("dump", identity, f"{path}/fleet-flow.dump", output=stream)
    if digest(dump) != expected:
        raise BackupError("checksum_mismatch")
    return dump, identity


def backup(state):
    command, revision = compose_command()
    payload = state / "payload"
    # Interrupted runs may leave an incomplete dump. Never reuse it.
    if payload.exists():
        shutil.rmtree(payload)
    payload.mkdir(mode=0o700)
    try:
        dump = payload / "fleet-flow.dump"
        with dump.open("wb") as stream:
            run(
                command + ["sh", "-c", 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc'],
                output=stream,
            )
        if dump.stat().st_size == 0:
            raise BackupError("empty_dump")
        (payload / "manifest.json").write_text(
            json.dumps(
                {
                    "sha256": digest(dump),
                    "revision": revision,
                    "created_at": datetime.now(UTC).isoformat(),
                }
            )
        )
        result = restic(
            "backup",
            "--json",
            "--host",
            "fleet-flow",
            "--tag",
            "fleet-flow-postgres",
            str(payload),
        )
        summaries = [json.loads(line) for line in result.splitlines() if line.strip()]
        identities = [item["snapshot_id"] for item in summaries if item.get("snapshot_id")]
        if not identities:
            raise BackupError("snapshot_not_created")
        with tempfile.TemporaryDirectory(dir=state) as directory:
            _, identity = download(identities[-1], Path(directory))
        restic("check")
        # Prune only after downloading and verifying the newly uploaded snapshot.
        restic(
            "forget",
            "--host",
            "fleet-flow",
            "--tag",
            "fleet-flow-postgres",
            "--path",
            str(payload),
            "--keep-daily",
            "7",
            "--keep-weekly",
            "4",
            "--keep-monthly",
            "6",
            "--prune",
        )
        mark_success(state, "backup", snapshot=identity, revision=revision)
    finally:
        shutil.rmtree(payload, ignore_errors=True)


def restore_check(state, snapshot):
    with tempfile.TemporaryDirectory(dir=state) as directory:
        dump, identity = download(snapshot, Path(directory))
        name = "fleet-flow-restore-" + uuid4().hex
        try:
            # Disposable PostgreSQL, no network, ports or persistent volume. Never the app DB.
            run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--rm",
                    "--name",
                    name,
                    "--network",
                    "none",
                    "--tmpfs",
                    "/var/lib/postgresql/data:rw,nosuid,noexec",
                    "-e",
                    "POSTGRES_HOST_AUTH_METHOD=trust",
                    "postgres:17-alpine",
                ]
            )
            for attempt in range(60):
                try:
                    run(["docker", "exec", name, "pg_isready", "-U", "postgres"])
                    break
                except BackupError:
                    if attempt == 59:
                        raise BackupError("restore_database_unavailable") from None
                    time.sleep(1)
            with dump.open("rb") as stream:
                try:
                    subprocess.run(
                        [
                            "docker",
                            "exec",
                            "-i",
                            name,
                            "pg_restore",
                            "--exit-on-error",
                            "--no-owner",
                            "--no-privileges",
                            "-U",
                            "postgres",
                            "-d",
                            "postgres",
                        ],
                        stdin=stream,
                        capture_output=True,
                        check=True,
                    )
                except (OSError, subprocess.CalledProcessError):
                    raise BackupError("restore_failed") from None
            run(
                [
                    "docker",
                    "exec",
                    name,
                    "psql",
                    "-U",
                    "postgres",
                    "-d",
                    "postgres",
                    "-v",
                    "ON_ERROR_STOP=1",
                    "-c",
                    "SELECT version_num FROM alembic_version; SELECT count(*) FROM vehicles;",
                ]
            )
        finally:
            # Cleanup failure must also make the operation fail (possible plaintext DB remains).
            run(["docker", "rm", "-f", name])
        mark_success(state, "restore", snapshot=identity)


def main():
    os.umask(0o077)
    try:
        if len(sys.argv) < 2 or sys.argv[1] not in ("backup", "restore-check") or len(sys.argv) > 3:
            raise BackupError("usage_backup_or_restore_check")
        validate_repository()
        state = Path(os.environ.get("FLEET_FLOW_BACKUP_STATE", "/var/lib/fleet-flow-backup"))
        with locked_state(state):
            if sys.argv[1] == "backup":
                backup(state)
            else:
                restore_check(state, sys.argv[2] if len(sys.argv) == 3 else "latest")
        print(json.dumps({"event": "backup_operation_succeeded", "operation": sys.argv[1]}))
        return 0
    except BackupError as error:
        print(
            json.dumps({"event": "backup_operation_failed", "code": str(error)}),
            file=sys.stderr,
        )
    except Exception:
        print(
            '{"event":"backup_operation_failed","code":"unexpected_error"}',
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
