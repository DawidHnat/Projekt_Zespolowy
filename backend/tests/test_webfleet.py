import asyncio
import base64
import logging

import httpx
import pytest

from app.core.config import WebfleetSettings
from app.diagnostics import check_webfleet
from app.integrations.webfleet.client import OBJECT_COLUMNS, WebfleetClient, WebfleetError

SETTINGS = WebfleetSettings("test-account", "test-user", "test-password", "test-api-key")


def run_with_response(response, *, clock=None):
    async def run():
        kwargs = {"clock": clock} if clock is not None else {}
        async with WebfleetClient(
            SETTINGS, transport=httpx.MockTransport(response), **kwargs
        ) as client:
            return await client.fetch_objects()

    return asyncio.run(run())


def test_basic_auth_https_column_filter_and_omitted_private_fields(caplog):
    def respond(request):
        assert str(request.url).startswith("https://csv.webfleet.com/extern?")
        assert (
            request.headers["Authorization"]
            == "Basic " + base64.b64encode(b"test-user:test-password").decode()
        )
        assert "username" not in request.url.params
        assert "password" not in request.url.params
        assert request.url.params["columnfilter"] == ",".join(OBJECT_COLUMNS)
        assert request.url.params["useISO8601"] == "true"
        return httpx.Response(
            200, json=[{"objectuid": "fictional-1", "drivertelmobile": "omit-me"}]
        )

    with caplog.at_level(logging.DEBUG):
        assert run_with_response(respond) == [{"objectuid": "fictional-1"}]
    assert "test-api-key" not in caplog.text
    assert "test-password" not in caplog.text
    assert "test-account" not in caplog.text


@pytest.mark.parametrize(
    ("response", "code", "provider_code"),
    [
        (httpx.Response(401, text="secret provider message"), "access_denied", None),
        (httpx.Response(403), "access_denied", None),
        (httpx.Response(429), "provider_rate_limit", None),
        (httpx.Response(503, text="secret provider message"), "http_error", None),
        (httpx.Response(302, headers={"Location": "https://example.com"}), "http_error", None),
        (httpx.Response(200, text="100,secret provider message"), "provider_error", 100),
        (
            httpx.Response(200, headers={"X-Webfleet-Errorcode": "100"}, json=[]),
            "provider_error",
            100,
        ),
        (
            httpx.Response(200, text="<html>secret provider message</html>"),
            "invalid_response",
            None,
        ),
        (
            httpx.Response(200, json={"message": "secret provider message"}),
            "invalid_response",
            None,
        ),
        (httpx.Response(200, json=["secret provider message"]), "invalid_response", None),
        (
            httpx.Response(200, headers={"X-Webfleet-Errorcode": "invalid-secret"}, json=[]),
            "invalid_response",
            None,
        ),
    ],
)
def test_error_handling_does_not_expose_provider_body(response, code, provider_code):
    with pytest.raises(WebfleetError) as error:
        run_with_response(lambda _: response)
    assert error.value.code == code
    assert error.value.provider_code == provider_code
    assert "secret provider message" not in str(error.value)


@pytest.mark.parametrize(
    ("exception", "code"),
    [
        (httpx.ReadTimeout("https://url-with-secret"), "timeout"),
        (httpx.ConnectError("https://url-with-secret"), "connection_failed"),
    ],
)
def test_transport_errors_do_not_expose_url(exception, code):
    def respond(_):
        raise exception

    with pytest.raises(WebfleetError) as error:
        run_with_response(respond)
    assert error.value.code == code
    assert "url-with-secret" not in str(error.value)


def test_empty_fleet_is_success_not_authentication_failure():
    assert run_with_response(lambda _: httpx.Response(200, json=[])) == []


def test_unrelated_httpx_logs_remain_available(caplog):
    run_with_response(lambda _: httpx.Response(200, json=[]))
    with caplog.at_level(logging.INFO):
        logging.getLogger("httpx").info("Request to https://example.invalid/health: 200")
    assert "https://example.invalid/health" in caplog.text


def test_rate_limit_and_no_automatic_retry():
    requests = []
    now = [0.0]

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json=[])

    async def run():
        async with WebfleetClient(
            SETTINGS, transport=httpx.MockTransport(respond), clock=lambda: now[0]
        ) as client:
            await client.fetch_objects()
            with pytest.raises(WebfleetError, match="local_rate_limit"):
                await client.fetch_objects()
            now[0] = 10.0
            await client.fetch_objects()

    asyncio.run(run())
    assert len(requests) == 2


def test_diagnostic_reports_only_counts(monkeypatch):
    async def fetch(_):
        return [
            {
                "objectuid": "fictional-sensitive-id",
                "objectno": "fictional-vehicle",
                "latitude_mdeg": 0,
                "longitude_mdeg": 0,
            }
        ]

    monkeypatch.setattr(WebfleetClient, "fetch_objects", fetch)
    result = asyncio.run(check_webfleet(SETTINGS))
    assert result["records"] == result["valid_snapshot_records"] == 1
    assert result["coverage"]["latitude_mdeg"] == 1
    assert "fictional-sensitive-id" not in str(result)
    assert "fictional-vehicle" not in str(result)
