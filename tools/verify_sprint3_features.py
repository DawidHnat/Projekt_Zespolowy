"""Check profile and driver directory using a dedicated viewer on development."""

import argparse
import json
import os
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.request import (
    HTTPCookieProcessor,
    HTTPRedirectHandler,
    Request,
    build_opener,
)

from verify_deployment import origin


class RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_json(client, base_url, path, payload=None):
    request = Request(base_url + path, headers={"Cache-Control": "no-store"})
    if payload is not None:
        request.data = json.dumps(payload).encode("utf-8")
        request.add_header("Content-Type", "application/json")
        request.add_header("Origin", base_url)
    with client.open(request, timeout=15) as response:
        if response.status != 200:
            raise ValueError("Unexpected response for authenticated smoke")
        body = response.read(65_537)
    if len(body) > 65_536:
        raise ValueError("Response exceeds smoke limit")
    value = json.loads(body)
    if not isinstance(value, dict):
        raise TypeError("Expected a JSON object")
    return value


def verify(app_origin, username, password):
    base_url = origin(app_origin, https=True)
    client = build_opener(RejectRedirects(), HTTPCookieProcessor(CookieJar()))
    login = fetch_json(
        client,
        base_url,
        "/api/v1/auth/login",
        {"username": username, "password": password},
    )
    try:
        profile = fetch_json(client, base_url, "/api/v1/auth/profile")
        if (
            profile.get("role") != "viewer"
            or profile.get("username") != login.get("username")
            or not isinstance(profile.get("username"), str)
            or not isinstance(profile.get("display_name"), str)
            or "email" not in profile
        ):
            raise ValueError("Expected the dedicated viewer profile")
        drivers = fetch_json(
            client, base_url, "/api/v1/drivers/search", {"page": 1, "page_size": 1}
        )
        if (
            not isinstance(drivers.get("items"), list)
            or type(drivers.get("total")) is not int
            or drivers.get("page") != 1
            or drivers.get("page_size") != 1
            or not isinstance(drivers.get("summary"), dict)
        ):
            raise ValueError("Expected a page of driver records")
    finally:
        fetch_json(client, base_url, "/api/v1/auth/logout", {})
    print(
        "PASS SCRUM-42 + SCRUM-49: driver directory and profile in the same viewer session"
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-origin", required=True)
    args = parser.parse_args(argv)
    username = os.environ.get("DEV_SPRINT3_SMOKE_USERNAME", "")
    password = os.environ.get("DEV_SPRINT3_SMOKE_PASSWORD", "")
    if not username or not password:
        print("FAIL SCRUM-42 + SCRUM-49: configure the dedicated development viewer")
        return 1
    try:
        verify(args.app_origin, username, password)
    except (HTTPError, URLError, ValueError, TypeError, TimeoutError):
        print("FAIL SCRUM-42 + SCRUM-49: authenticated development smoke")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
