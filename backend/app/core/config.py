"""Backend-only integration settings; never import this module into the frontend."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from math import isfinite
from pathlib import Path

from dotenv import dotenv_values


class ConfigurationError(Exception):
    """A validation error containing setting names, never their values."""


def load_environment(env_file: Path | None = None) -> dict[str, str]:
    path = env_file if env_file is not None else Path(__file__).resolve().parents[3] / ".env"
    if env_file is not None and not path.is_file():
        raise ConfigurationError("Nie znaleziono pliku podanego w --env-file")
    # Credentials can contain literal ${...}; dotenv must not rewrite them.
    try:
        values = dotenv_values(path, interpolate=False) if path.is_file() else {}
    except OSError:
        raise ConfigurationError("Nie można odczytać lokalnego pliku .env") from None
    return {key: value for key, value in {**values, **os.environ}.items() if value is not None}


def _required(values: Mapping[str, str], names: tuple[str, ...]) -> list[str]:
    missing = [name for name in names if not values.get(name, "").strip()]
    if missing:
        raise ConfigurationError("Brak ustawień: " + ", ".join(missing))
    return [values[name] for name in names]


def _timeout(values: Mapping[str, str], name: str) -> float:
    try:
        value = float(values.get(name, "20"))
    except ValueError:
        raise ConfigurationError(f"{name}: wymagany czas od 1 do 120 sekund") from None
    if not isfinite(value) or not 1 <= value <= 120:
        raise ConfigurationError(f"{name}: wymagany czas od 1 do 120 sekund")
    return value


@dataclass(frozen=True)
class WebfleetSettings:
    account: str = field(repr=False)
    username: str = field(repr=False)
    password: str = field(repr=False)
    api_key: str = field(repr=False)
    timeout_seconds: float = 20

    @classmethod
    def from_environment(cls, values: Mapping[str, str]) -> "WebfleetSettings":
        credentials = _required(
            values,
            (
                "WEBFLEET_ACCOUNT",
                "WEBFLEET_USERNAME",
                "WEBFLEET_PASSWORD",
                "WEBFLEET_API_KEY",
            ),
        )
        if ":" in credentials[1]:
            raise ConfigurationError("WEBFLEET_USERNAME nie może zawierać dwukropka")
        return cls(*credentials, timeout_seconds=_timeout(values, "WEBFLEET_TIMEOUT_SECONDS"))


@dataclass(frozen=True)
class SmtpSettings:
    username: str = field(repr=False)
    password: str = field(repr=False)
    host: str = "smtp.mail.ovh.net"
    port: int = 465
    timeout_seconds: float = 20

    @classmethod
    def from_environment(cls, values: Mapping[str, str]) -> "SmtpSettings":
        credentials = _required(values, ("SMTP_USERNAME", "SMTP_PASSWORD"))
        # This diagnostic is intentionally scoped to the purchased OVH mailbox.
        if values.get("SMTP_HOST", cls.host) not in ("smtp.mail.ovh.net", "ssl0.ovh.net"):
            raise ConfigurationError("SMTP_HOST: wymagany serwer poczty OVH")
        if values.get("SMTP_PORT", "465") != "465":
            raise ConfigurationError("SMTP_PORT: dla tej konfiguracji wymagany port TLS 465")
        return cls(
            *credentials,
            host=values.get("SMTP_HOST", cls.host),
            timeout_seconds=_timeout(values, "SMTP_TIMEOUT_SECONDS"),
        )
