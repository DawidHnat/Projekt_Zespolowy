"""SCRUM-58: synthetic security, quarantine, metadata-stripping, IDOR, and persistence tests."""

import os
import struct
import subprocess
import sys
import zlib
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.models import Base, SyncState, Vehicle
from app.core.settings import Settings
from app.main import create_app
from app.modules.auth.models import User
from app.modules.auth.service import password_hasher
from app.modules.fleet.documents import (
    PNG_SIGNATURE,
    SyntheticMalwareScanner,
    UnconfiguredMalwareScanner,
)
from app.modules.fleet.sync import account_key, apply_records

ORIGIN = {"Origin": "http://127.0.0.1:5173"}


def _png_chunk(tag: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(tag + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", crc)


def make_png(
    width: int = 16,
    height: int = 16,
    *,
    rgb: tuple[int, int, int] = (20, 90, 180),
    text_meta: bytes | None = None,
) -> bytes:
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + bytes(rgb) * width for _ in range(height))
    chunks = [_png_chunk(b"IHDR", ihdr)]
    if text_meta is not None:
        chunks.append(_png_chunk(b"tEXt", b"Comment\x00" + text_meta))
        chunks.append(_png_chunk(b"eXIf", b"MM\x00*\x00\x00\x00\x08GPSLatitude-54.352"))
    chunks.append(_png_chunk(b"IDAT", zlib.compress(raw)))
    chunks.append(_png_chunk(b"IEND", b""))
    return PNG_SIGNATURE + b"".join(chunks)


def make_jpeg(
    width: int = 16,
    height: int = 16,
    *,
    exif_payload: bytes | None = b"Exif\x00\x00GPS-SECRET-54.352",
) -> bytes:
    out = bytearray(b"\xff\xd8")
    jfif = b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    out.extend(b"\xff\xe0" + struct.pack(">H", len(jfif) + 2) + jfif)
    if exif_payload:
        out.extend(b"\xff\xe1" + struct.pack(">H", len(exif_payload) + 2) + exif_payload)
        comment = b"CameraOwner=JanSyntetyczny"
        out.extend(b"\xff\xfe" + struct.pack(">H", len(comment) + 2) + comment)
    dqt = b"\x00" + bytes([16] * 64)
    out.extend(b"\xff\xdb" + struct.pack(">H", len(dqt) + 2) + dqt)
    sof = struct.pack(">BHHB", 8, height, width, 1) + b"\x01\x11\x00"
    out.extend(b"\xff\xc0" + struct.pack(">H", len(sof) + 2) + sof)
    sos = b"\x01\x01\x00\x00\x3f\x00"
    out.extend(b"\xff\xda" + struct.pack(">H", len(sos) + 2) + sos)
    out.extend(b"\x7f\x00\xff\xd9")
    return bytes(out)


def make_webp(width: int = 16, height: int = 16, *, with_exif: bool = True) -> bytes:
    vp8_payload = b"\x00\x00\x00\x9d\x01\x2a" + struct.pack("<HH", width, height) + b"\x00\x00"
    chunks = bytearray()
    chunks.extend(b"VP8 " + struct.pack("<I", len(vp8_payload)) + vp8_payload)
    if with_exif:
        exif = b"Exif\x00\x00SECRET-WEBP-GPS"
        chunks.extend(b"EXIF" + struct.pack("<I", len(exif)) + exif)
        if len(exif) & 1:
            chunks.append(0)
    return b"RIFF" + struct.pack("<I", 4 + len(chunks)) + b"WEBP" + bytes(chunks)


def make_pdf(*, active_token: bytes | None = None, compressed_token: bytes | None = None) -> bytes:
    body = b"1 0 obj\n<< /Type /Catalog "
    if active_token:
        body += active_token + b" "
    body += b">>\nendobj\n"
    if compressed_token:
        comp = zlib.compress(b"<< " + compressed_token + b" >>")
        body += (
            b"2 0 obj\n<< /Filter /FlateDecode /Length "
            + str(len(comp)).encode("ascii")
            + b" >>\nstream\n"
            + comp
            + b"\nendstream\nendobj\n"
        )
    return b"%PDF-1.4\n" + body + b"%%EOF\n"


def test_dates_quarantine_fail_closed_formats_limits_idor_and_restart_persistence(tmp_path):
    db_file = tmp_path / "docs.sqlite"
    upload_dir = tmp_path / "private_uploads"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)

    settings = Settings(
        database_url=f"sqlite:///{db_file}",
        webfleet_account="account-alpha",
        upload_storage_dir=str(upload_dir),
        upload_max_file_bytes=64 * 1024,
        upload_max_files_per_kind=3,
        upload_photo_max_edge_px=1024,
    )
    app = create_app(settings, engine=engine)
    source_a = account_key("account-alpha")
    source_b = account_key("account-bravo")
    now = datetime.now(UTC)

    with app.state.sessions() as session:
        session.add_all(
            [
                User(
                    username="editor-one",
                    display_name="Edytor Jeden",
                    role="editor",
                    password_hash=password_hasher.hash("synthetic-editor-pass"),
                ),
                User(
                    username="viewer-two",
                    display_name="Podgląd Dwa",
                    role="viewer",
                    password_hash=password_hasher.hash("synthetic-viewer-pass"),
                ),
                SyncState(source_account=source_a, last_success_at=now),
                SyncState(source_account=source_b, last_success_at=now),
            ]
        )
        v1 = Vehicle(source_account=source_a, external_uid="wf-a-1", name="Auto Alpha 1")
        v2 = Vehicle(source_account=source_a, external_uid="wf-a-2", name="Auto Alpha 2")
        foreign = Vehicle(source_account=source_b, external_uid="wf-b-1", name="Auto Obce")
        session.add_all([v1, v2, foreign])
        session.commit()
        v1_id, v2_id, foreign_id = str(v1.id), str(v2.id), str(foreign.id)

    with TestClient(app) as client_editor, TestClient(app) as client_viewer:
        # Unauthenticated requests are rejected.
        assert client_editor.get(f"/api/v1/fleet/vehicles/{v1_id}/documents").status_code == 401

        assert (
            client_editor.post(
                "/api/v1/auth/login",
                headers=ORIGIN,
                json={"username": "editor-one", "password": "synthetic-editor-pass"},
            ).status_code
            == 200
        )
        assert (
            client_viewer.post(
                "/api/v1/auth/login",
                headers=ORIGIN,
                json={"username": "viewer-two", "password": "synthetic-viewer-pass"},
            ).status_code
            == 200
        )

        # 1. Manual dates (past, future, null) survive WEBFLEET sync; viewer cannot modify dates.
        dates_res = client_editor.patch(
            f"/api/v1/fleet/vehicles/{v1_id}/documents/dates",
            headers=ORIGIN,
            json={
                "card_version": 1,
                "inspection_due_on": "2024-01-15",
                "insurance_due_on": "2027-12-31",
            },
        )
        assert dates_res.status_code == 200
        assert dates_res.json()["inspection_due_on"] == "2024-01-15"
        assert dates_res.json()["insurance_due_on"] == "2027-12-31"
        assert (
            client_viewer.patch(
                f"/api/v1/fleet/vehicles/{v1_id}/documents/dates",
                headers=ORIGIN,
                json={"card_version": 2, "inspection_due_on": None},
            ).status_code
            == 403
        )
        with app.state.sessions() as session:
            apply_records(
                session,
                source_a,
                {
                    "wf-a-1": {"objectname": "Auto Alpha 1"},
                    "wf-a-2": {"objectname": "Auto Alpha 2"},
                },
                {},
                now,
            )
            session.commit()
        after_sync = client_viewer.get(f"/api/v1/fleet/vehicles/{v1_id}/documents").json()
        assert after_sync["inspection_due_on"] == "2024-01-15"
        assert after_sync["insurance_due_on"] == "2027-12-31"

        # 2. Default UnconfiguredMalwareScanner is FAIL-CLOSED: file cannot be downloaded.
        assert isinstance(app.state.malware_scanner, UnconfiguredMalwareScanner)
        unscanned = client_editor.post(
            f"/api/v1/fleet/vehicles/{v2_id}/documents?kind=inspection",
            headers={
                **ORIGIN,
                "Content-Type": "application/pdf",
                "X-Upload-Filename": "badanie_unscanned.pdf",
            },
            content=make_pdf(),
        )
        assert unscanned.status_code == 201
        assert unscanned.json()["status"] == "scanner_unavailable"
        assert unscanned.json()["available"] is False
        blocked_dl = client_viewer.get(
            f"/api/v1/fleet/vehicles/{v2_id}/documents/{unscanned.json()['id']}/content"
        )
        assert blocked_dl.status_code == 409
        assert blocked_dl.json()["error"]["code"] == "FILE_NOT_AVAILABLE"

        # Enable deterministic synthetic scanner for upload/replace/reject QA scenarios.
        app.state.malware_scanner = SyntheticMalwareScanner()

        # 3. Format spoofing, path traversal, active PDF content, and stream cap (>64 KB).
        assert (
            client_editor.post(
                f"/api/v1/fleet/vehicles/{v1_id}/documents?kind=inspection",
                headers={
                    **ORIGIN,
                    "Content-Type": "application/pdf",
                    "X-Upload-Filename": "../traversal.pdf",
                },
                content=make_pdf(),
            ).status_code
            == 422
        )
        # PNG bytes disguised as .pdf -> rejected!
        spoof = client_editor.post(
            f"/api/v1/fleet/vehicles/{v1_id}/documents?kind=inspection",
            headers={
                **ORIGIN,
                "Content-Type": "application/pdf",
                "X-Upload-Filename": "spoofed.pdf",
            },
            content=make_png(),
        )
        assert spoof.status_code == 422
        assert spoof.json()["error"]["code"] == "INVALID_FILE_FORMAT"

        # Active PDF content (/JavaScript raw and inside compressed FlateDecode stream) -> rejected!
        for bad_pdf in (
            make_pdf(active_token=b"/JavaScript (app.alert(1))"),
            make_pdf(active_token=b"/#4aavaScript (1)"),
            make_pdf(compressed_token=b"/OpenAction << /S /Launch >>"),
        ):
            res_pdf = client_editor.post(
                f"/api/v1/fleet/vehicles/{v1_id}/documents?kind=inspection",
                headers={
                    **ORIGIN,
                    "Content-Type": "application/pdf",
                    "X-Upload-Filename": "active.pdf",
                },
                content=bad_pdf,
            )
            assert res_pdf.status_code == 422
            assert res_pdf.json()["error"]["code"] == "UNSAFE_FILE_CONTENT"

        # Oversized stream (> 64 KB configured cap) -> 413 FILE_TOO_LARGE.
        too_big = client_editor.post(
            f"/api/v1/fleet/vehicles/{v1_id}/documents?kind=inspection",
            headers={
                **ORIGIN,
                "Content-Type": "application/pdf",
                "X-Upload-Filename": "huge.pdf",
            },
            content=b"%PDF-1.4\n" + (b"A" * 70_000) + b"\n%%EOF\n",
        )
        assert too_big.status_code == 413
        assert too_big.json()["error"]["code"] == "FILE_TOO_LARGE"

        # PDF rejected on vehicle_photo endpoint.
        assert (
            client_editor.put(
                f"/api/v1/fleet/vehicles/{v1_id}/photo",
                headers={
                    **ORIGIN,
                    "Content-Type": "application/pdf",
                    "X-Upload-Filename": "skan.pdf",
                },
                content=make_pdf(),
            ).status_code
            == 422
        )

        # 4. Upload up to 3 inspection scans (multipart + raw, stripped EXIF) + 4th blocked.
        doc_ids = []
        first_doc = client_editor.post(
            f"/api/v1/fleet/vehicles/{v1_id}/documents",
            headers=ORIGIN,
            data={"kind": "inspection"},
            files={"file": ("badanie_1.jpg", make_jpeg(), "image/jpeg")},
        )
        assert first_doc.status_code == 201
        doc_ids.append(first_doc.json()["id"])

        dl_jpg = client_viewer.get(f"/api/v1/fleet/vehicles/{v1_id}/documents/{doc_ids[0]}/content")
        assert dl_jpg.status_code == 200
        assert b"GPS-SECRET" not in dl_jpg.content
        assert b"CameraOwner" not in dl_jpg.content
        assert "sandbox" in dl_jpg.headers["content-security-policy"]

        for idx in (2, 3):
            extra = client_editor.post(
                f"/api/v1/fleet/vehicles/{v1_id}/documents?kind=inspection",
                headers={
                    **ORIGIN,
                    "Content-Type": "application/pdf",
                    "X-Upload-Filename": f"badanie_{idx}.pdf",
                },
                content=make_pdf(),
            )
            assert extra.status_code == 201
            doc_ids.append(extra.json()["id"])

        fourth = client_editor.post(
            f"/api/v1/fleet/vehicles/{v1_id}/documents?kind=inspection",
            headers={
                **ORIGIN,
                "Content-Type": "application/pdf",
                "X-Upload-Filename": "badanie_4.pdf",
            },
            content=make_pdf(),
        )
        assert fourth.status_code == 409
        assert fourth.json()["error"]["code"] == "DOCUMENT_LIMIT_REACHED"

        # Insurance quota is independent of inspection quota!
        ins_doc = client_editor.post(
            f"/api/v1/fleet/vehicles/{v1_id}/documents?kind=insurance",
            headers={
                **ORIGIN,
                "Content-Type": "application/pdf",
                "X-Upload-Filename": "polisa_oc.pdf",
            },
            content=make_pdf(),
        )
        assert ins_doc.status_code == 201

        # 5. Shared vehicle photo: >1024px PNG downscaled to <=1024px & EXIF stripped;
        # viewer sees identical photo in separate session and cannot modify/delete!
        large_png = make_png(1280, 640, text_meta=b"PrivateAuthorMeta")
        photo_up = client_editor.put(
            f"/api/v1/fleet/vehicles/{v1_id}/photo",
            headers={
                **ORIGIN,
                "Content-Type": "image/png",
                "X-Upload-Filename": "auto_duze.png",
            },
            content=large_png,
        )
        assert photo_up.status_code == 200
        assert photo_up.json()["available"] is True
        assert photo_up.json()["version"] == 1
        assert photo_up.json()["width_px"] == 1024
        assert photo_up.json()["height_px"] == 512

        viewer_photo = client_viewer.get(f"/api/v1/fleet/vehicles/{v1_id}/photo/content")
        assert viewer_photo.status_code == 200
        assert b"PrivateAuthorMeta" not in viewer_photo.content
        assert b"GPSLatitude" not in viewer_photo.content
        assert (
            client_viewer.put(
                f"/api/v1/fleet/vehicles/{v1_id}/photo",
                headers={
                    **ORIGIN,
                    "Content-Type": "image/webp",
                    "X-Upload-Filename": "viewer.webp",
                },
                content=make_webp(),
            ).status_code
            == 403
        )
        assert (
            client_viewer.delete(
                f"/api/v1/fleet/vehicles/{v1_id}/photo", headers=ORIGIN
            ).status_code
            == 403
        )

        # 6. Atomic replacement: failed validation or scan error preserves old photo & doc.
        bad_malware_png = make_png(
            16, 16, rgb=(1, 2, 3)
        )  # Note: metadata stripped before scan; embed marker in PDF for doc & scanner error!
        malware_pdf = make_pdf()[:-7] + b"% FLEET-FLOW-SYNTHETIC-MALWARE-SAMPLE\n%%EOF\n"
        scanner_err_pdf = make_pdf()[:-7] + b"% FLEET-FLOW-SYNTHETIC-SCANNER-FAILURE\n%%EOF\n"
        assert (
            client_editor.put(
                f"/api/v1/fleet/vehicles/{v1_id}/documents/{doc_ids[1]}",
                headers={
                    **ORIGIN,
                    "Content-Type": "application/pdf",
                    "X-Upload-Filename": "infected.pdf",
                },
                content=malware_pdf,
            ).status_code
            == 422
        )
        assert (
            client_editor.put(
                f"/api/v1/fleet/vehicles/{v1_id}/documents/{doc_ids[1]}",
                headers={
                    **ORIGIN,
                    "Content-Type": "application/pdf",
                    "X-Upload-Filename": "scan_fail.pdf",
                },
                content=scanner_err_pdf,
            ).status_code
            == 503
        )
        # Previous clean document is still downloadable and version is still 1!
        preserved_doc = client_viewer.get(
            f"/api/v1/fleet/vehicles/{v1_id}/documents/{doc_ids[1]}/content"
        )
        assert preserved_doc.status_code == 200
        assert preserved_doc.headers["etag"] == '"doc-v1"'

        # Switch scanner to Unconfigured during photo replace -> 503 & old photo preserved.
        app.state.malware_scanner = UnconfiguredMalwareScanner()
        assert (
            client_editor.put(
                f"/api/v1/fleet/vehicles/{v1_id}/photo",
                headers={
                    **ORIGIN,
                    "Content-Type": "image/webp",
                    "X-Upload-Filename": "nowe.webp",
                },
                content=make_webp(),
            ).status_code
            == 503
        )
        still_clean_photo = client_viewer.get(f"/api/v1/fleet/vehicles/{v1_id}/photo/content")
        assert still_clean_photo.status_code == 200
        assert still_clean_photo.content == viewer_photo.content
        app.state.malware_scanner = SyntheticMalwareScanner()

        # Clean replacement with WebP strips EXIF and bumps photo_version to 2!
        webp_up = client_editor.put(
            f"/api/v1/fleet/vehicles/{v1_id}/photo",
            headers={
                **ORIGIN,
                "Content-Type": "image/webp",
                "X-Upload-Filename": "nowe.webp",
            },
            content=make_webp(with_exif=True),
        )
        assert webp_up.status_code == 200
        assert webp_up.json()["version"] == 2
        webp_dl = client_viewer.get(f"/api/v1/fleet/vehicles/{v1_id}/photo/content")
        assert webp_dl.status_code == 200
        assert b"SECRET-WEBP-GPS" not in webp_dl.content
        assert bad_malware_png is not None

        # 7. Foreign vehicle ID / cross-vehicle document ID (IDOR) returns 404!
        assert (
            client_editor.get(f"/api/v1/fleet/vehicles/{foreign_id}/documents").status_code == 404
        )
        assert (
            client_editor.get(f"/api/v1/fleet/vehicles/{foreign_id}/photo/content").status_code
            == 404
        )
        assert (
            client_editor.get(
                f"/api/v1/fleet/vehicles/{v2_id}/documents/{doc_ids[0]}/content"
            ).status_code
            == 404
        )
        assert (
            client_editor.delete(
                f"/api/v1/fleet/vehicles/{foreign_id}/photo", headers=ORIGIN
            ).status_code
            == 404
        )

    engine.dispose()

    # 8. Simulate restart: brand-new engine & FastAPI app over same SQLite file & upload_dir!
    restarted_engine = create_engine(
        f"sqlite:///{db_file}", connect_args={"check_same_thread": False}
    )
    restarted_app = create_app(settings, engine=restarted_engine)
    restarted_app.state.malware_scanner = SyntheticMalwareScanner()
    with TestClient(restarted_app) as after_restart:
        assert (
            after_restart.post(
                "/api/v1/auth/login",
                headers=ORIGIN,
                json={"username": "viewer-two", "password": "synthetic-viewer-pass"},
            ).status_code
            == 200
        )
        state = after_restart.get(f"/api/v1/fleet/vehicles/{v1_id}/documents").json()
        assert state["inspection_due_on"] == "2024-01-15"
        assert state["photo"]["available"] is True
        assert state["photo"]["version"] == 2
        assert len(state["items"]) == 4
        assert after_restart.get(f"/api/v1/fleet/vehicles/{v1_id}/photo/content").status_code == 200
        assert (
            after_restart.get(
                f"/api/v1/fleet/vehicles/{v1_id}/documents/{doc_ids[0]}/content"
            ).status_code
            == 200
        )
    restarted_engine.dispose()


def test_postgres_migration_0014_downgrade_guard():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires an isolated PostgreSQL database")
    parsed = make_url(url)
    assert parsed.host in ("127.0.0.1", "localhost")
    assert parsed.database.startswith("fleet_flow_test")

    def migrate(*args):
        return subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            env={**os.environ, "DATABASE_URL": url, "SYNC_ENABLED": "false"},
            capture_output=True,
            text=True,
        )

    assert migrate("upgrade", "head").returncode == 0
    engine = create_engine(url)
    source = account_key(f"docs-pg-{uuid4().hex}")
    try:
        with Session(engine) as session:
            car = Vehicle(
                source_account=source,
                external_uid="wf-doc-pg",
                name="Auto Dokumenty PG",
                photo_version=1,
            )
            session.add(car)
            session.commit()
            car_id = car.id

        blocked = migrate("downgrade", "0013_manual_vehicles")
        assert blocked.returncode != 0
        assert "SCRUM-58" in (blocked.stderr + blocked.stdout)

        with Session(engine) as session:
            saved = session.get(Vehicle, car_id)
            assert saved is not None and saved.photo_version == 1
    finally:
        with Session(engine) as session:
            for v in session.scalars(select(Vehicle).where(Vehicle.source_account == source)):
                session.delete(v)
            session.commit()
        engine.dispose()
