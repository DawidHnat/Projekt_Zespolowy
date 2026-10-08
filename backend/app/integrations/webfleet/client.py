"""Read-only WEBFLEET.connect adapter. No provider writes or implicit polling."""

import json
import logging
import re
from collections.abc import Callable
from time import monotonic
from typing import Any

import httpx

from app.core.config import WebfleetSettings

ENDPOINT = "https://csv.webfleet.com/extern"
OBJECT_COLUMNS = (
    "objectuid",
    "objectno",
    "latitude_mdeg",
    "longitude_mdeg",
    "status",
    "speed",
    "odometer",
    "ignition",
    "standstill",
    "pos_time",
    "msgtime",
)


class WebfleetError(Exception):
    def __init__(self, code: str, *, provider_code: int | None = None):
        self.code = code
        self.provider_code = provider_code
        # Never include a request URL, response body, account or credentials.
        super().__init__(
            f"WEBFLEET: {code}"
            + (f" (kod dostawcy {provider_code})" if provider_code is not None else "")
        )


class _HideRequestDetails(logging.Filter):
    """HTTPX otherwise logs complete URLs containing the provider's API key."""

    def filter(self, record: logging.LogRecord) -> bool:
        # Keep ordinary HTTPX messages for unrelated integrations unchanged.
        message = record.getMessage().lower()
        if not any(token in message for token in ("csv.webfleet.com", "/extern?", "authorization")):
            return True
        record.msg = "WEBFLEET transport: szczegóły żądania ukryte"
        record.args = ()
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        return True


def protect_transport_logs() -> None:
    for name in (
        "httpx",
        "httpcore.connection",
        "httpcore.http11",
        "httpcore.http2",
        "httpcore.proxy",
        "httpcore.socks",
    ):
        logger = logging.getLogger(name)
        if not any(isinstance(item, _HideRequestDetails) for item in logger.filters):
            logger.addFilter(_HideRequestDetails())


def _provider_code(response: httpx.Response) -> int | None:
    candidate = response.headers.get("X-Webfleet-Errorcode", "")
    if not candidate:
        match = re.match(r"^\s*(\d{1,9})\s*,", response.text)
        candidate = match.group(1) if match else ""
    if not candidate:
        return None
    if candidate.isascii() and candidate.isdigit() and len(candidate) <= 9:
        return int(candidate)
    raise WebfleetError("invalid_response")


class WebfleetClient:
    def __init__(
        self,
        settings: WebfleetSettings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        clock: Callable[[], float] = monotonic,
    ):
        protect_transport_logs()
        self._settings = settings
        self._clock = clock
        self._last_request: float | None = None
        self._client = httpx.AsyncClient(
            auth=httpx.BasicAuth(settings.username, settings.password),
            timeout=settings.timeout_seconds,
            follow_redirects=False,
            trust_env=False,
            transport=transport,
        )

    async def __aenter__(self) -> "WebfleetClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self._client.aclose()

    async def fetch_objects(self) -> list[dict[str, Any]]:
        now = self._clock()
        # One request per >=10 s per client. No sleeping, retries or background jobs.
        if self._last_request is not None and now - self._last_request < 10:
            raise WebfleetError("local_rate_limit")
        self._last_request = now
        try:
            response = await self._client.get(
                ENDPOINT,
                params={
                    "account": self._settings.account,
                    "apikey": self._settings.api_key,
                    "action": "showObjectReportExtern",
                    "outputformat": "json",
                    "lang": "en",
                    "useUTF8": "true",
                    "useISO8601": "true",
                    "columnfilter": ",".join(OBJECT_COLUMNS),
                },
            )
        except httpx.TimeoutException:
            raise WebfleetError("timeout") from None
        except httpx.HTTPError:
            raise WebfleetError("connection_failed") from None
        if response.status_code in (401, 403):
            raise WebfleetError("access_denied")
        if response.status_code == 429:
            raise WebfleetError("provider_rate_limit")
        if response.status_code != 200:
            raise WebfleetError("http_error")
        code = _provider_code(response)
        if code is not None:
            raise WebfleetError("provider_error", provider_code=code)
        try:
            records = response.json()
        except (json.JSONDecodeError, UnicodeError):
            raise WebfleetError("invalid_response") from None
        if not isinstance(records, list) or any(not isinstance(item, dict) for item in records):
            raise WebfleetError("invalid_response")
        # Even if columnfilter is ignored, do not retain unsolicited personal fields.
        return [{key: item[key] for key in OBJECT_COLUMNS if key in item} for item in records]
