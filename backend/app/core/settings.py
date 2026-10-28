"""Application settings; credentials never appear in repr or error messages."""

import json
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from app.core.config import ConfigurationError, load_environment


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
    api_docs_enabled: bool = True

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
    def from_environment(cls) -> "Settings":
        values = load_environment()
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
        return cls(
            database_url=database_url,
            origins=origins,
            cookie_secure=secure,
            sync_enabled=values.get("SYNC_ENABLED", "false").lower() == "true",
            webfleet_account=values.get("WEBFLEET_ACCOUNT", ""),
            api_docs_enabled=docs == "true",
        )
