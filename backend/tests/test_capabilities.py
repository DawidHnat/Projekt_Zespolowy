import asyncio

import httpx

from app.core.config import WebfleetSettings
from app.integrations.webfleet.client import WebfleetClient


def test_master_and_history_never_request_or_retain_driver_data():
    requests = []

    def respond(request):
        requests.append(request)
        columns = request.url.params["columnfilter"].split(",")
        assert not any("driver" in column.lower() for column in columns)
        assert "driver" not in request.url.params
        return httpx.Response(200, json=[{"objectuid": "synthetic", "drivername": "discard"}])

    async def run():
        async with WebfleetClient(
            WebfleetSettings("a", "u", "p", "k"), transport=httpx.MockTransport(respond)
        ) as client:
            masters = await client.fetch_vehicles()
            assert masters == [{"objectuid": "synthetic"}]
            await client.probe_history("synthetic")

    asyncio.run(run())
    assert len(requests) == 4
    assert all(request.url.params["action"] != "showDriverReportExtern" for request in requests)
    assert all(request.url.params.get("range_pattern") == "d0" for request in requests[1:])
