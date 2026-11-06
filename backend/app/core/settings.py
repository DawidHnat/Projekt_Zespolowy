"""Application settings; credentials never appear in repr or error messages."""

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from app.core.config import ConfigurationError, load_environment


def _seconds(
    values: Mapping[str, str], name: str, default: int, minimum: int, maximum: int
) -> int:
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
    stale_seconds: int = 900
    webfleet_account: str = field(default="", repr=False)

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
        return cls(
            database_url=database_url,
            origins=origins,
            cookie_secure=secure,
            sync_enabled=values.get("SYNC_ENABLED", "false").lower() == "true",
            sync_interval_seconds=_seconds(values, "SYNC_INTERVAL_SECONDS", 60, 10, 86400),
            stale_seconds=_seconds(values, "STALE_SECONDS", 900, 1, 604800),
            webfleet_account=values.get("WEBFLEET_ACCOUNT", ""),
        )
