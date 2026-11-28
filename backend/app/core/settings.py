"""Application settings; credentials never appear in repr or error messages."""

import json
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from app.core.config import ConfigurationError, load_environment

DEFAULT_STALE_SECONDS = 900


def _seconds(values: Mapping[str, str], name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(values.get(name, str(default)))
    except (TypeError, ValueError):
        raise ConfigurationError(
            f"{name}: wymagany czas od {minimum} do {maximum} sekund"
        ) from None
    if not minimum <= value <= maximum:
        raise ConfigurationError(f"{name}: wymagany czas od {minimum} do {maximum} sekund")
    return value


@dataclass(frozen=True)
class Settings:
    database_url: str = field(repr=False)
    origins: tuple[str, ...] = ("http://127.0.0.1:5173", "http://localhost:5173")
    cookie_secure: bool = False
    session_hours: int = 12
    sync_enabled: bool = False
    sync_interval_seconds: int = 60
    stale_seconds: int = DEFAULT_STALE_SECONDS
    webfleet_account: str = field(default="", repr=False)
    api_docs_enabled: bool = True
    upload_storage_dir: str = field(
        default_factory=lambda: str(Path(tempfile.gettempdir()) / "fleet-flow-private-uploads")
    )
    upload_max_file_bytes: int = 10 * 1024 * 1024
    upload_max_files_per_kind: int = 3
    upload_photo_max_edge_px: int = 1024
    upload_max_image_pixels: int = 40_000_000
    backup_state_dir: str = ""
    tls_cert_path: str = ""
    tls_warning_days: int = 21
    tls_critical_days: int = 7
    disk_path: str = "."

    @property
    def local_api_docs(self) -> bool:
        return (
            self.api_docs_enabled
            and bool(self.origins)
            and all(
                urlsplit(origin).hostname in ("localhost", "127.0.0.1", "::1")
                for origin in self.origins
            )
        )

    @classmethod
    def from_environment(cls, values: Mapping[str, str] | None = None) -> "Settings":
        values = values if values is not None else load_environment()
        database_url = values.get("DATABASE_URL", "")
        if not database_url.startswith("postgresql+psycopg://"):
            raise ConfigurationError("Uzupełnij DATABASE_URL (postgresql+psycopg)")
        raw_origins = values.get("CORS_ORIGINS", "http://127.0.0.1:5173")
        try:
            entries = (
                json.loads(raw_origins) if raw_origins.startswith("[") else raw_origins.split(",")
            )
            origins = tuple(item.strip().rstrip("/") for item in entries if item.strip())
        except (ValueError, AttributeError, TypeError):
            raise ConfigurationError("Niepoprawne CORS_ORIGINS") from None
        secure = values.get("COOKIE_SECURE", "false").lower() == "true"
        for origin in origins:
            parsed = urlsplit(origin)
            if parsed.scheme not in ("http", "https") or not parsed.hostname:
                raise ConfigurationError("Niepoprawne CORS_ORIGINS")
            if parsed.scheme == "http" and parsed.hostname not in ("localhost", "127.0.0.1"):
                raise ConfigurationError("Zdalny dostęp wymaga HTTPS")
            if parsed.scheme == "https" and not secure:
                raise ConfigurationError("HTTPS wymaga COOKIE_SECURE=true")
        if not origins:
            raise ConfigurationError("CORS_ORIGINS nie może być puste")
        local = all(
            urlsplit(origin).hostname in ("localhost", "127.0.0.1", "::1") for origin in origins
        )
        docs = values.get("API_DOCS_ENABLED", "true" if local else "false").lower()
        if docs not in ("true", "false"):
            raise ConfigurationError("API_DOCS_ENABLED: wymagane true albo false")
        if docs == "true" and not local:
            raise ConfigurationError("Dokumentacja API jest dostępna wyłącznie lokalnie")
        default_uploads = str(Path(tempfile.gettempdir()) / "fleet-flow-private-uploads")
        return cls(
            database_url=database_url,
            origins=origins,
            cookie_secure=secure,
            sync_enabled=values.get("SYNC_ENABLED", "false").lower() == "true",
            sync_interval_seconds=_seconds(values, "SYNC_INTERVAL_SECONDS", 60, 10, 86400),
            stale_seconds=_seconds(values, "STALE_SECONDS", DEFAULT_STALE_SECONDS, 1, 604800),
            webfleet_account=values.get("WEBFLEET_ACCOUNT", ""),
            api_docs_enabled=docs == "true",
            upload_storage_dir=values.get("FLEET_FLOW_UPLOAD_DIR", default_uploads).strip()
            or default_uploads,
            upload_max_file_bytes=_seconds(
                values, "UPLOAD_MAX_FILE_BYTES", 10 * 1024 * 1024, 1024, 50 * 1024 * 1024
            ),
            upload_max_files_per_kind=_seconds(values, "UPLOAD_MAX_FILES_PER_KIND", 3, 1, 20),
            upload_photo_max_edge_px=_seconds(values, "UPLOAD_PHOTO_MAX_EDGE_PX", 1024, 128, 4096),
            upload_max_image_pixels=_seconds(
                values, "UPLOAD_MAX_IMAGE_PIXELS", 40_000_000, 65536, 100_000_000
            ),
            backup_state_dir=values.get("FLEET_FLOW_BACKUP_STATE", "").strip(),
            tls_cert_path=values.get("TLS_CERT_PATH", "").strip(),
            tls_warning_days=_seconds(values, "TLS_WARNING_DAYS", 21, 1, 365),
            tls_critical_days=_seconds(values, "TLS_CRITICAL_DAYS", 7, 1, 365),
            disk_path=values.get("FLEET_FLOW_DISK_PATH", ".").strip() or ".",
        )
