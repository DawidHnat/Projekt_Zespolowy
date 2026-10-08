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
VEHICLE_COLUMNS = ("objectuid", "objectno", "objectname", "licenseplatenumber", "vehicletype")
HISTORY_COLUMNS = {
    "showTripReportExtern": (
        "tripid",
        "objectno",
        "start_time",
        "end_time",
        "distance",
        "duration",
    ),
    "showStandStills": ("start_time", "end_time", "duration", "latitude", "longitude"),
    "showTracks": ("pos_time", "latitude", "longitude", "speed", "odometer"),
}
REQUEST_INTERVALS = {
    "showObjectReportExtern": 10,
    "showVehicleReportExtern": 10,
    "showTripReportExtern": 60,
    "showStandStills": 10,
    "showTracks": 6,
}


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
        self._last_requests: dict[str, float] = {}
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
        return await self._read("showObjectReportExtern", OBJECT_COLUMNS)

    async def fetch_vehicles(self) -> list[dict[str, Any]]:
        return await self._read("showVehicleReportExtern", VEHICLE_COLUMNS)

    async def probe_history(self, object_uid: str) -> dict[str, dict[str, Any]]:
        """One selected vehicle, today only; no personal driver fields or writes."""
        result = {}
        for action, columns in HISTORY_COLUMNS.items():
            try:
                rows = await self._read(action, columns, objectuid=object_uid, range_pattern="d0")
                result[action] = {
                    "ok": True,
                    "records": len(rows),
                    "coverage": {
                        key: sum(row.get(key) not in (None, "") for row in rows) for key in columns
                    },
                }
            except WebfleetError as error:
                result[action] = {
                    "ok": False,
                    "code": error.code,
                    "provider_code": error.provider_code,
                }
        return result

    async def _read(
        self, action: str, columns: tuple[str, ...], **parameters: str
    ) -> list[dict[str, Any]]:
        if action not in REQUEST_INTERVALS:
            raise WebfleetError("unsupported_action")
        now = self._clock()
        previous = self._last_requests.get(action)
        # Per-action limit; no sleeping, retries or implicit background jobs.
        if previous is not None and now - previous < REQUEST_INTERVALS[action]:
            raise WebfleetError("local_rate_limit")
        self._last_requests[action] = now
        try:
            response = await self._client.get(
                ENDPOINT,
                params={
                    "account": self._settings.account,
                    "apikey": self._settings.api_key,
                    "action": action,
                    "outputformat": "json",
                    "lang": "en",
                    "useUTF8": "true",
                    "useISO8601": "true",
                    "columnfilter": ",".join(columns),
                    **parameters,
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
        return [{key: item[key] for key in columns if key in item} for item in records]
