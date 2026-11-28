"""Private vehicle documents and shared photo storage, validation, and quarantine (SCRUM-58).

All files live outside any public webroot under random UUID storage keys:
- `quarantine/<storage_key>` before positive malware scan verdict,
- `clean/<storage_key>` exclusively after `scan_status == "clean"`.
Any non-clean status (`quarantined`, `scanner_unavailable`, `rejected`) is fail-closed
and never served to callers. Never log file contents or raw client paths.
"""

from __future__ import annotations

import email.policy
import hashlib
import os
import re
import struct
import zlib
from dataclasses import dataclass
from datetime import UTC, datetime
from email.parser import BytesParser
from pathlib import Path
from typing import Protocol
from uuid import UUID, uuid4

from fastapi import Request
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.errors import ApiError
from app.core.models import Base

DOCUMENT_KINDS = ("inspection", "insurance")
ALL_ATTACHMENT_KINDS = ("inspection", "insurance", "vehicle_photo")
SCAN_STATUSES = ("quarantined", "clean", "rejected", "scanner_unavailable")

DOCUMENT_MIMES = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}
PHOTO_MIMES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}

DANGEROUS_PDF_TOKENS = (
    b"/js",
    b"/javascript",
    b"/launch",
    b"/embeddedfile",
    b"/embeddedfiles",
    b"/openaction",
    b"/aa",
    b"/richmedia",
    b"/xfa",
    b"/submitform",
    b"/importdata",
    b"javascript:",
)

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_SAFE_CHUNKS = frozenset({b"IHDR", b"PLTE", b"tRNS", b"IDAT", b"IEND"})


class VehicleAttachment(Base):
    __tablename__ = "vehicle_attachments"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('inspection', 'insurance', 'vehicle_photo')",
            name="ck_vehicle_attachments_kind",
        ),
        CheckConstraint(
            "scan_status IN ('quarantined', 'clean', 'rejected', 'scanner_unavailable')",
            name="ck_vehicle_attachments_scan_status",
        ),
        CheckConstraint(
            "size_bytes > 0 AND size_bytes <= 52428800",
            name="ck_vehicle_attachments_size",
        ),
        CheckConstraint("version >= 1", name="ck_vehicle_attachments_version"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    vehicle_id: Mapped[UUID] = mapped_column(ForeignKey("vehicles.id"), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    original_name: Mapped[str] = mapped_column(String(120))
    mime_type: Mapped[str] = mapped_column(String(50))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    storage_key: Mapped[str | None] = mapped_column(String(80), unique=True)
    scan_status: Mapped[str] = mapped_column(String(30), default="quarantined")
    scan_code: Mapped[str | None] = mapped_column(String(60))
    width_px: Mapped[int | None] = mapped_column(Integer)
    height_px: Mapped[int | None] = mapped_column(Integer)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    uploaded_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


@dataclass(frozen=True)
class ScanVerdict:
    status: str  # "clean" | "quarantined" | "rejected" | "scanner_unavailable"
    code: str | None = None


class MalwareScanner(Protocol):
    def scan(self, path: Path, *, mime_type: str) -> ScanVerdict: ...


class UnconfiguredMalwareScanner:
    """Default fail-closed scanner until owner approves production scanner and cost."""

    def scan(self, path: Path, *, mime_type: str) -> ScanVerdict:
        return ScanVerdict(status="scanner_unavailable", code="SCANNER_NOT_CONFIGURED")


class SyntheticMalwareScanner:
    """Deterministic synthetic scanner for automated tests and QA (never uses real malware)."""

    MALWARE_MARKER = b"FLEET-FLOW-SYNTHETIC-MALWARE-SAMPLE"
    QUARANTINE_MARKER = b"FLEET-FLOW-SYNTHETIC-QUARANTINE-PENDING"
    ERROR_MARKER = b"FLEET-FLOW-SYNTHETIC-SCANNER-FAILURE"

    def scan(self, path: Path, *, mime_type: str) -> ScanVerdict:
        data = path.read_bytes()
        if self.ERROR_MARKER in data:
            raise RuntimeError("Synthetic scanner failure")
        if self.MALWARE_MARKER in data:
            return ScanVerdict(status="rejected", code="MALWARE_DETECTED")
        if self.QUARANTINE_MARKER in data:
            return ScanVerdict(status="quarantined", code="SCAN_PENDING")
        return ScanVerdict(status="clean", code=None)


@dataclass(frozen=True)
class ValidatedUpload:
    safe_name: str
    mime_type: str
    payload: bytes
    sha256: str
    width_px: int | None
    height_px: int | None


def sanitize_filename(raw_name: str | None, *, allowed_exts: dict[str, str]) -> tuple[str, str]:
    if not isinstance(raw_name, str):
        raise ApiError(422, "INVALID_FILENAME", "Podaj poprawną nazwę pliku")
    trimmed = raw_name.strip()
    if (
        not trimmed
        or len(trimmed) > 120
        or "/" in trimmed
        or "\\" in trimmed
        or ".." in trimmed
        or trimmed.startswith(".")
        or any(ord(ch) < 32 or 0xD800 <= ord(ch) <= 0xDFFF for ch in trimmed)
    ):
        raise ApiError(422, "INVALID_FILENAME", "Niedozwolona nazwa lub ścieżka pliku")
    stem, dot, ext = trimmed.rpartition(".")
    if not dot or not stem.strip():
        raise ApiError(422, "INVALID_FILE_FORMAT", "Plik musi posiadać dozwolone rozszerzenie")
    lower_ext = "." + ext.lower()
    expected_mime = allowed_exts.get(lower_ext)
    if expected_mime is None:
        raise ApiError(422, "INVALID_FILE_FORMAT", "Niedozwolony format pliku")
    safe_stem = re.sub(r"[^\w\-.ąćęłńóśźżĄĆĘŁŃÓŚŹŻ ]+", "_", stem).strip(" ._")[:95]
    if not safe_stem:
        safe_stem = "dokument"
    canonical_ext = ".jpg" if lower_ext == ".jpeg" else lower_ext
    return f"{safe_stem}{canonical_ext}", expected_mime


def _normalize_declared_mime(content_type: str | None) -> str | None:
    if not content_type:
        return None
    media = content_type.split(";", 1)[0].strip().lower()
    if media in ("", "application/octet-stream"):
        return None
    if media == "image/jpg":
        return "image/jpeg"
    return media


async def read_bounded_upload(
    request: Request, *, max_bytes: int
) -> tuple[str | None, str | None, bytes, dict[str, str]]:
    content_type = request.headers.get("content-type", "")
    media_type = content_type.split(";", 1)[0].strip().lower()
    stream_cap = max_bytes + (32768 if media_type == "multipart/form-data" else 0)
    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > stream_cap:
            raise ApiError(413, "FILE_TOO_LARGE", "Plik przekracza maksymalny dozwolony rozmiar")
        chunks.append(chunk)
    raw_body = b"".join(chunks)
    if not raw_body:
        raise ApiError(422, "EMPTY_FILE", "Przesłany plik jest pusty")

    if media_type == "multipart/form-data":
        header_bytes = f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode(
            "latin-1", errors="ignore"
        )
        msg = BytesParser(policy=email.policy.HTTP).parsebytes(header_bytes + raw_body)
        if not msg.is_multipart():
            raise ApiError(422, "VALIDATION_ERROR", "Niepoprawne żądanie multipart")
        fields: dict[str, str] = {}
        file_payload: bytes | None = None
        filename: str | None = None
        part_mime: str | None = None
        for part in msg.iter_parts():
            if part.get_content_disposition() != "form-data":
                continue
            field_name = part.get_param("name", header="content-disposition")
            part_filename = part.get_filename()
            payload = part.get_payload(decode=True) or b""
            if part_filename is not None or field_name == "file":
                if file_payload is not None:
                    raise ApiError(422, "VALIDATION_ERROR", "Prześlij pojedynczy plik w żądaniu")
                file_payload = payload
                filename = part_filename
                part_mime = part.get_content_type()
            elif isinstance(field_name, str) and len(payload) <= 200:
                fields[field_name] = payload.decode("utf-8", errors="replace").strip()
        if file_payload is None:
            raise ApiError(422, "EMPTY_FILE", "Brak pliku w żądaniu")
        if len(file_payload) == 0:
            raise ApiError(422, "EMPTY_FILE", "Przesłany plik jest pusty")
        if len(file_payload) > max_bytes:
            raise ApiError(413, "FILE_TOO_LARGE", "Plik przekracza maksymalny dozwolony rozmiar")
        return filename, part_mime, file_payload, fields

    if len(raw_body) > max_bytes:
        raise ApiError(413, "FILE_TOO_LARGE", "Plik przekracza maksymalny dozwolony rozmiar")
    filename = request.headers.get("x-upload-filename")
    return filename, media_type or None, raw_body, {}


def _validate_and_sanitize_pdf(data: bytes, *, max_bytes: int) -> bytes:
    if not (data.startswith(b"%PDF-1.") or data.startswith(b"%PDF-2.")):
        raise ApiError(422, "INVALID_FILE_FORMAT", "Plik nie jest poprawnym dokumentem PDF")
    eof_idx = data.rfind(b"%%EOF")
    if eof_idx < 0 or len(data) - eof_idx > 1024:
        raise ApiError(422, "INVALID_FILE_FORMAT", "Uszkodzona struktura dokumentu PDF")
    if b" obj" not in data or b"endobj" not in data:
        raise ApiError(422, "INVALID_FILE_FORMAT", "Niepełna struktura obiektów PDF")

    lowered = re.sub(rb"#([0-9A-Fa-f]{2})", lambda m: bytes([int(m.group(1), 16)]), data).lower()
    for token in DANGEROUS_PDF_TOKENS:
        if token in lowered:
            raise ApiError(
                422, "UNSAFE_FILE_CONTENT", "Dokument PDF zawiera niedozwoloną aktywną zawartość"
            )

    # Also inspect compressed FlateDecode streams with bounded decompression against zip bombs.
    for match in re.finditer(rb"stream\r?\n", data):
        start = match.end()
        end = data.find(b"endstream", start)
        if end < 0:
            raise ApiError(422, "INVALID_FILE_FORMAT", "Niezamknięty strumień w dokumencie PDF")
        raw_stream = data[start:end].rstrip(b"\r\n")
        header_window = data[max(0, match.start() - 256) : match.start()].lower()
        if b"/flatedecode" in header_window and raw_stream:
            try:
                decomp = zlib.decompressobj()
                expanded = decomp.decompress(raw_stream, max_bytes * 2 + 1)
                if len(expanded) > max_bytes * 2 or decomp.unconsumed_tail:
                    raise ApiError(
                        422, "UNSAFE_FILE_CONTENT", "Przekroczono limit dekompresji strumienia PDF"
                    )
            except zlib.error:
                raise ApiError(
                    422, "INVALID_FILE_FORMAT", "Uszkodzony strumień FlateDecode w PDF"
                ) from None
            lowered_stream = expanded.lower()
            for token in DANGEROUS_PDF_TOKENS:
                if token in lowered_stream:
                    raise ApiError(
                        422,
                        "UNSAFE_FILE_CONTENT",
                        "Dokument PDF zawiera ukrytą aktywną zawartość",
                    )

    trimmed_end = eof_idx + len(b"%%EOF")
    return data[:trimmed_end] + b"\n"


def _png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(chunk_type + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + chunk_type + payload + struct.pack(">I", crc)


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _downscale_png_8bit(
    raw_scanlines: bytes, width: int, height: int, channels: int, color_type: int, max_edge: int
) -> tuple[bytes, int, int]:
    scale = min(1.0, max_edge / max(width, height))
    new_w = max(1, round(width * scale))
    new_h = max(1, round(height * scale))
    stride = width * channels
    prev = bytearray(stride)
    pixels = bytearray(width * height * channels)
    pos = 0
    for y in range(height):
        filt = raw_scanlines[pos]
        pos += 1
        row = bytearray(raw_scanlines[pos : pos + stride])
        pos += stride
        if filt == 1:
            for i in range(channels, stride):
                row[i] = (row[i] + row[i - channels]) & 0xFF
        elif filt == 2:
            for i in range(stride):
                row[i] = (row[i] + prev[i]) & 0xFF
        elif filt == 3:
            for i in range(stride):
                left = row[i - channels] if i >= channels else 0
                row[i] = (row[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif filt == 4:
            for i in range(stride):
                left = row[i - channels] if i >= channels else 0
                up_left = prev[i - channels] if i >= channels else 0
                row[i] = (row[i] + _paeth(left, prev[i], up_left)) & 0xFF
        elif filt != 0:
            raise ApiError(422, "INVALID_FILE_FORMAT", "Nieobsługiwany filtr obrazu PNG")
        pixels[y * stride : (y + 1) * stride] = row
        prev = row

    out = bytearray()
    for ny in range(new_h):
        sy = min(height - 1, (ny * height) // new_h)
        out.append(0)
        row_offset = sy * stride
        for nx in range(new_w):
            sx = min(width - 1, (nx * width) // new_w)
            px_offset = row_offset + sx * channels
            out.extend(pixels[px_offset : px_offset + channels])

    ihdr = struct.pack(">IIBBBBB", new_w, new_h, 8, color_type, 0, 0, 0)
    idat = zlib.compress(bytes(out), level=6)
    rebuilt = (
        PNG_SIGNATURE
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", idat)
        + _png_chunk(b"IEND", b"")
    )
    return rebuilt, new_w, new_h


def _validate_and_strip_png(
    data: bytes, *, max_pixels: int, max_edge: int | None
) -> tuple[bytes, int, int]:
    if not data.startswith(PNG_SIGNATURE):
        raise ApiError(422, "INVALID_FILE_FORMAT", "Plik nie jest poprawnym obrazem PNG")
    pos = len(PNG_SIGNATURE)
    width = height = bit_depth = color_type = interlace = -1
    kept_chunks: list[tuple[bytes, bytes]] = []
    idat_parts: list[bytes] = []
    seen_iend = False

    while pos < len(data):
        if seen_iend or pos + 8 > len(data):
            raise ApiError(422, "INVALID_FILE_FORMAT", "Uszkodzona struktura chunków PNG")
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        end_data = pos + 8 + length
        if end_data + 4 > len(data):
            raise ApiError(422, "INVALID_FILE_FORMAT", "Niepełny chunk w obrazie PNG")
        chunk_data = data[pos + 8 : end_data]
        expected_crc = struct.unpack(">I", data[end_data : end_data + 4])[0]
        actual_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise ApiError(422, "INVALID_FILE_FORMAT", "Błąd sumy kontrolnej CRC w obrazie PNG")
        pos = end_data + 4

        if not kept_chunks and chunk_type != b"IHDR":
            raise ApiError(422, "INVALID_FILE_FORMAT", "Brak nagłówka IHDR w obrazie PNG")
        if chunk_type == b"IHDR":
            if len(chunk_data) != 13 or width != -1:
                raise ApiError(422, "INVALID_FILE_FORMAT", "Niepoprawny nagłówek IHDR w PNG")
            width, height, bit_depth, color_type, comp, filt, interlace = struct.unpack(
                ">IIBBBBB", chunk_data
            )
            if (
                width <= 0
                or height <= 0
                or comp != 0
                or filt != 0
                or interlace not in (0, 1)
                or bit_depth not in (1, 2, 4, 8, 16)
            ):
                raise ApiError(422, "INVALID_FILE_FORMAT", "Nieobsługiwane parametry obrazu PNG")
            if width * height > max_pixels or width > 10000 or height > 10000:
                raise ApiError(
                    422, "IMAGE_DIMENSIONS_EXCEEDED", "Wymiary obrazu przekraczają dozwolony limit"
                )
        elif chunk_type == b"IDAT":
            idat_parts.append(chunk_data)
        elif chunk_type == b"IEND":
            seen_iend = True

        if chunk_type in PNG_SAFE_CHUNKS:
            kept_chunks.append((chunk_type, chunk_data))

    if not seen_iend or not idat_parts or width <= 0:
        raise ApiError(422, "INVALID_FILE_FORMAT", "Niekompletny strumień danych obrazu PNG")

    channels_map = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
    channels = channels_map.get(color_type)
    if channels is None:
        raise ApiError(422, "INVALID_FILE_FORMAT", "Nieobsługiwany typ koloru PNG")
    row_bits = width * channels * bit_depth
    expected_scanline_bytes = height * (1 + (row_bits + 7) // 8)
    # Interlaced Adam7 can have slightly more filter bytes; cap safely at 2x + 64 bytes.
    decompress_cap = expected_scanline_bytes if interlace == 0 else expected_scanline_bytes * 2 + 64
    try:
        decomp = zlib.decompressobj()
        raw_pixels = decomp.decompress(b"".join(idat_parts), decompress_cap + 1)
        if len(raw_pixels) > decompress_cap or decomp.unconsumed_tail:
            raise ApiError(
                422, "IMAGE_DIMENSIONS_EXCEEDED", "Przekroczono limit dekompresji pikseli PNG"
            )
        tail = decomp.flush()
        raw_pixels += tail
    except zlib.error:
        raise ApiError(422, "INVALID_FILE_FORMAT", "Nie udało się zdekodować pikseli PNG") from None

    if interlace == 0 and len(raw_pixels) != expected_scanline_bytes:
        raise ApiError(422, "INVALID_FILE_FORMAT", "Niezgodny rozmiar zdekodowanych linii PNG")

    if max_edge is not None and max(width, height) > max_edge:
        if interlace == 0 and bit_depth == 8 and color_type in (0, 2, 4, 6):
            return _downscale_png_8bit(raw_pixels, width, height, channels, color_type, max_edge)
        raise ApiError(
            422,
            "IMAGE_DIMENSIONS_EXCEEDED",
            f"Zdjęcie pojazdu przekracza maksymalny bok {max_edge} px",
        )

    stripped = PNG_SIGNATURE + b"".join(_png_chunk(t, d) for t, d in kept_chunks)
    return stripped, width, height


def _validate_and_strip_jpeg(
    data: bytes, *, max_pixels: int, max_edge: int | None
) -> tuple[bytes, int, int]:
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        raise ApiError(422, "INVALID_FILE_FORMAT", "Plik nie jest poprawnym obrazem JPEG")
    out = bytearray(b"\xff\xd8")
    pos = 2
    width = height = -1
    has_dqt = False
    has_sos = False

    while pos < len(data):
        if data[pos] != 0xFF:
            raise ApiError(422, "INVALID_FILE_FORMAT", "Uszkodzona struktura znaczników JPEG")
        while pos < len(data) and data[pos] == 0xFF:
            pos += 1
        if pos >= len(data):
            raise ApiError(422, "INVALID_FILE_FORMAT", "Nieoczekiwany koniec pliku JPEG")
        marker = data[pos]
        pos += 1

        if marker == 0xD9:  # EOI
            if not has_sos or width <= 0:
                raise ApiError(422, "INVALID_FILE_FORMAT", "Niepełny obraz JPEG bez danych obrazu")
            out.extend(b"\xff\xd9")
            return bytes(out), width, height
        if marker == 0x00 or 0xD0 <= marker <= 0xD8:
            out.extend(bytes([0xFF, marker]))
            continue
        if pos + 2 > len(data):
            raise ApiError(422, "INVALID_FILE_FORMAT", "Uszkodzony nagłówek segmentu JPEG")
        seg_len = struct.unpack(">H", data[pos : pos + 2])[0]
        if seg_len < 2 or pos + seg_len > len(data):
            raise ApiError(422, "INVALID_FILE_FORMAT", "Niepoprawna długość segmentu JPEG")
        seg_payload = data[pos + 2 : pos + seg_len]
        pos += seg_len

        if marker == 0xDB:
            has_dqt = True
        elif marker in (0xC0, 0xC1, 0xC2):
            if len(seg_payload) < 6:
                raise ApiError(422, "INVALID_FILE_FORMAT", "Uszkodzony nagłówek SOF w JPEG")
            precision, height, width, components = struct.unpack(">BHHB", seg_payload[:6])
            if precision != 8 or width <= 0 or height <= 0 or components not in (1, 3, 4):
                raise ApiError(422, "INVALID_FILE_FORMAT", "Nieobsługiwane parametry obrazu JPEG")
            if width * height > max_pixels or width > 10000 or height > 10000:
                raise ApiError(
                    422, "IMAGE_DIMENSIONS_EXCEEDED", "Wymiary obrazu przekraczają dozwolony limit"
                )
            if max_edge is not None and max(width, height) > max_edge:
                raise ApiError(
                    422,
                    "IMAGE_DIMENSIONS_EXCEEDED",
                    f"Zdjęcie pojazdu przekracza maksymalny bok {max_edge} px",
                )

        # Strip EXIF/XMP/IPTC/ICC metadata (APP1..APP15) and comments (COM 0xFE).
        if 0xE1 <= marker <= 0xEF or marker == 0xFE:
            continue

        out.extend(bytes([0xFF, marker]) + struct.pack(">H", seg_len) + seg_payload)

        if marker == 0xDA:  # Start of Scan — entropy-coded data follows until EOI
            if not has_dqt or width <= 0:
                raise ApiError(422, "INVALID_FILE_FORMAT", "Brak tablic kwantyzacji lub SOF w JPEG")
            has_sos = True
            eoi_idx = data.rfind(b"\xff\xd9", pos)
            if eoi_idx < pos or eoi_idx == pos:
                raise ApiError(422, "INVALID_FILE_FORMAT", "Brak znacznika końca obrazu EOI w JPEG")
            out.extend(data[pos : eoi_idx + 2])
            return bytes(out), width, height

    raise ApiError(422, "INVALID_FILE_FORMAT", "Niezamknięty strumień obrazu JPEG")


def _validate_and_strip_webp(
    data: bytes, *, max_pixels: int, max_edge: int | None
) -> tuple[bytes, int, int]:
    if len(data) < 20 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise ApiError(422, "INVALID_FILE_FORMAT", "Plik nie jest poprawnym obrazem WebP")
    riff_size = struct.unpack("<I", data[4:8])[0]
    if riff_size + 8 > len(data):
        raise ApiError(422, "INVALID_FILE_FORMAT", "Niepełny kontener RIFF obrazu WebP")
    limit = riff_size + 8
    pos = 12
    width = height = -1
    kept_chunks = bytearray()
    has_image_data = False

    while pos + 8 <= limit:
        fourcc = data[pos : pos + 4]
        chunk_size = struct.unpack("<I", data[pos + 4 : pos + 8])[0]
        end = pos + 8 + chunk_size
        if end > limit:
            raise ApiError(422, "INVALID_FILE_FORMAT", "Uszkodzony chunk w obrazie WebP")
        chunk_payload = bytearray(data[pos + 8 : end])
        pos = end + (chunk_size & 1)

        if fourcc == b"VP8X":
            if len(chunk_payload) != 10:
                raise ApiError(422, "INVALID_FILE_FORMAT", "Niepoprawny chunk VP8X w WebP")
            w_minus_1 = int.from_bytes(chunk_payload[4:7], "little")
            h_minus_1 = int.from_bytes(chunk_payload[7:10], "little")
            width, height = w_minus_1 + 1, h_minus_1 + 1
            # Clear EXIF (0x08) and XMP (0x04) metadata flags.
            chunk_payload[0] &= ~(0x08 | 0x04)
        elif fourcc == b"VP8 ":
            if len(chunk_payload) < 10 or chunk_payload[3:6] != b"\x9d\x01\x2a":
                raise ApiError(422, "INVALID_FILE_FORMAT", "Uszkodzony strumień VP8 w WebP")
            has_image_data = True
            w_raw, h_raw = struct.unpack("<HH", chunk_payload[6:10])
            w_cand, h_cand = w_raw & 0x3FFF, h_raw & 0x3FFF
            if width <= 0:
                width, height = w_cand, h_cand
        elif fourcc == b"VP8L":
            if len(chunk_payload) < 5 or chunk_payload[0] != 0x2F:
                raise ApiError(422, "INVALID_FILE_FORMAT", "Uszkodzony strumień VP8L w WebP")
            has_image_data = True
            bits = struct.unpack("<I", chunk_payload[1:5])[0]
            w_cand = (bits & 0x3FFF) + 1
            h_cand = ((bits >> 14) & 0x3FFF) + 1
            if width <= 0:
                width, height = w_cand, h_cand
        elif fourcc in (b"EXIF", b"XMP "):
            continue

        kept_chunks.extend(fourcc + struct.pack("<I", len(chunk_payload)) + chunk_payload)
        if len(chunk_payload) & 1:
            kept_chunks.append(0)

    if not has_image_data or width <= 0 or height <= 0:
        raise ApiError(422, "INVALID_FILE_FORMAT", "Brak poprawnych danych obrazu w WebP")
    if width * height > max_pixels or width > 10000 or height > 10000:
        raise ApiError(
            422, "IMAGE_DIMENSIONS_EXCEEDED", "Wymiary obrazu przekraczają dozwolony limit"
        )
    if max_edge is not None and max(width, height) > max_edge:
        raise ApiError(
            422,
            "IMAGE_DIMENSIONS_EXCEEDED",
            f"Zdjęcie pojazdu przekracza maksymalny bok {max_edge} px",
        )

    rebuilt = b"RIFF" + struct.pack("<I", 4 + len(kept_chunks)) + b"WEBP" + bytes(kept_chunks)
    return rebuilt, width, height


def validate_and_prepare_upload(
    *,
    kind: str,
    raw_filename: str | None,
    declared_mime: str | None,
    raw_bytes: bytes,
    max_bytes: int,
    max_pixels: int,
    photo_max_edge_px: int,
) -> ValidatedUpload:
    if kind not in ALL_ATTACHMENT_KINDS:
        raise ApiError(422, "VALIDATION_ERROR", "Nieznany rodzaj załącznika")
    allowed_exts = PHOTO_MIMES if kind == "vehicle_photo" else DOCUMENT_MIMES
    safe_name, expected_mime = sanitize_filename(raw_filename, allowed_exts=allowed_exts)
    normalized_declared = _normalize_declared_mime(declared_mime)
    if normalized_declared is not None and normalized_declared != expected_mime:
        raise ApiError(
            422, "INVALID_FILE_FORMAT", "Deklarowany typ MIME nie zgadza się z rozszerzeniem pliku"
        )
    if len(raw_bytes) == 0:
        raise ApiError(422, "EMPTY_FILE", "Przesłany plik jest pusty")
    if len(raw_bytes) > max_bytes:
        raise ApiError(413, "FILE_TOO_LARGE", "Plik przekracza maksymalny dozwolony rozmiar")

    max_edge = photo_max_edge_px if kind == "vehicle_photo" else None
    width_px: int | None = None
    height_px: int | None = None
    if expected_mime == "application/pdf":
        sanitized = _validate_and_sanitize_pdf(raw_bytes, max_bytes=max_bytes)
    elif expected_mime == "image/png":
        sanitized, width_px, height_px = _validate_and_strip_png(
            raw_bytes, max_pixels=max_pixels, max_edge=max_edge
        )
    elif expected_mime == "image/jpeg":
        sanitized, width_px, height_px = _validate_and_strip_jpeg(
            raw_bytes, max_pixels=max_pixels, max_edge=max_edge
        )
    elif expected_mime == "image/webp":
        sanitized, width_px, height_px = _validate_and_strip_webp(
            raw_bytes, max_pixels=max_pixels, max_edge=max_edge
        )
    else:
        raise ApiError(422, "INVALID_FILE_FORMAT", "Niedozwolony format pliku")

    digest = hashlib.sha256(sanitized).hexdigest()
    return ValidatedUpload(
        safe_name=safe_name,
        mime_type=expected_mime,
        payload=sanitized,
        sha256=digest,
        width_px=width_px,
        height_px=height_px,
    )


class PrivateAttachmentStore:
    """Private filesystem store with quarantine/clean separation outside webroot."""

    def __init__(self, root: str | Path) -> None:
        base = Path(root)
        if base.is_symlink():
            raise RuntimeError("Upload storage directory must not be a symlink")
        base.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.root = base.resolve()
        repo_root = Path(__file__).resolve().parents[4]
        for forbidden in (repo_root / "frontend", repo_root / "backend" / "app"):
            if self.root == forbidden or forbidden in self.root.parents:
                raise RuntimeError("Upload storage directory must reside outside webroot and code")
        self.quarantine_dir = self.root / "quarantine"
        self.clean_dir = self.root / "clean"
        self.quarantine_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.clean_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

    def _safe_key(self, storage_key: str) -> str:
        if not re.fullmatch(r"[0-9a-f]{32}", storage_key):
            raise ValueError("Invalid storage key")
        return storage_key

    def write_quarantine(self, payload: bytes) -> tuple[str, Path]:
        key = uuid4().hex
        target = self.quarantine_dir / key
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
        fd = os.open(target, flags, 0o600)
        try:
            os.write(fd, payload)
        finally:
            os.close(fd)
        return key, target

    def promote_to_clean(self, storage_key: str) -> Path:
        key = self._safe_key(storage_key)
        src = self.quarantine_dir / key
        dst = self.clean_dir / key
        src.replace(dst)
        return dst

    def read_clean(self, storage_key: str) -> bytes:
        key = self._safe_key(storage_key)
        target = self.clean_dir / key
        if not target.is_file() or target.is_symlink():
            raise FileNotFoundError(key)
        return target.read_bytes()

    def remove(self, storage_key: str | None) -> None:
        if not storage_key:
            return
        key = self._safe_key(storage_key)
        for folder in (self.quarantine_dir, self.clean_dir):
            candidate = folder / key
            try:
                if candidate.exists() or candidate.is_symlink():
                    candidate.unlink()
            except OSError:
                pass


def serialize_document_item(item: VehicleAttachment) -> dict:
    return {
        "id": str(item.id),
        "vehicle_id": str(item.vehicle_id),
        "kind": item.kind,
        "name": item.original_name,
        "mime_type": item.mime_type,
        "size_bytes": item.size_bytes,
        "status": item.scan_status,
        "available": item.scan_status == "clean" and item.storage_key is not None,
        "code": item.scan_code,
        "version": item.version,
        "created_at": item.created_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "updated_at": item.updated_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
    }


def serialize_photo_state(vehicle_photo_version: int, photo: VehicleAttachment | None) -> dict:
    if photo is None:
        return {
            "available": False,
            "version": vehicle_photo_version,
            "status": "none",
            "code": None,
            "mime_type": None,
            "size_bytes": None,
            "width_px": None,
            "height_px": None,
            "updated_at": None,
        }
    return {
        "available": photo.scan_status == "clean" and photo.storage_key is not None,
        "version": vehicle_photo_version,
        "status": photo.scan_status,
        "code": photo.scan_code,
        "mime_type": photo.mime_type,
        "size_bytes": photo.size_bytes,
        "width_px": photo.width_px,
        "height_px": photo.height_px,
        "updated_at": photo.updated_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
    }
