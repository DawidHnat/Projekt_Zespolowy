"""WEBFLEET.connect 1.58 HTTPS GET/JSON transport, using documented Basic Auth.

Reference: https://media.webfleet.com/fl_attachment/media/doc/documentations/webfleet.connect-doc-1.58.0
Sections: Making HTTP requests (27–29), Objects (76–84).
"""

import logging
from types import TracebackType
from typing import Any

import httpx

from app.core.config import Settings

# The documented query includes an API key. httpx's INFO request log would print that URL.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

ENDPOINT = "https://csv.webfleet.com/extern"


class WebfleetError(Exception):
    """Contains only a fixed, safe message; never provider response text or a request URL."""


class WebfleetClient:
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None) -> None:
        credentials = (
            settings.webfleet_account,
            settings.webfleet_username,
            settings.webfleet_password,
            settings.webfleet_api_key,
        )
        if any(value is None or not value.get_secret_value().strip() for value in credentials):
            raise WebfleetError("Missing Webfleet configuration. Check your local .env.")
        account, username, password, api_key = [value.get_secret_value() for value in credentials]
        self._account = account
        self._api_key = api_key
        self._http = httpx.Client(
            auth=httpx.BasicAuth(username, password),
            timeout=settings.webfleet_timeout_seconds,
            follow_redirects=False,
            transport=transport,
        )

    def __enter__(self) -> "WebfleetClient":
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._http.close()

    def _read(self, action: str) -> list[dict[str, Any]]:
        # An explicit allowlist prevents this adapter being used for provider mutations.
        if action not in {"showVehicleReportExtern", "showObjectReportExtern"}:
            raise WebfleetError("Unsupported Webfleet read operation.")
        try:
            response = self._http.get(
                ENDPOINT,
                params={
                    "account": self._account,
                    "apikey": self._api_key,
                    "action": action,
                    "lang": "en",
                    "outputformat": "json",
                    "useUTF8": "true",
                    "useISO8601": "true",
                },
            )
        except httpx.RequestError:
            raise WebfleetError("Webfleet connection failed. No data was changed.") from None
        if not response.is_success:
            raise WebfleetError(
                "Webfleet request was rejected. Check access and service availability."
            )
        if response.headers.get("X-Webfleet-Errorcode", "") not in {"", "0"}:
            raise WebfleetError("Webfleet reported an error. Check access and request limits.")
        try:
            data = response.json()
        except ValueError:
            raise WebfleetError(
                "Webfleet returned an invalid response. No data was changed."
            ) from None
        if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
            raise WebfleetError("Webfleet returned an unexpected response. No data was changed.")
        return data

    def vehicles(self) -> list[dict[str, Any]]:
        return self._read("showVehicleReportExtern")

    def objects(self) -> list[dict[str, Any]]:
        return self._read("showObjectReportExtern")
