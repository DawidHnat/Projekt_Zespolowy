"""Check only public release markers and readiness, without application credentials."""

import argparse
import re
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


class ReleaseMarkers(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name == "data-build-sha":
                self.values.append(value)


def origin(value, *, https=False):
    parsed = urlsplit(value)
    if (
        parsed.scheme not in ({"https"} if https else {"http", "https"})
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Expected a public origin without credentials, path or query")
    return value.rstrip("/")


def fetch(url):
    request = Request(url, headers={"Cache-Control": "no-cache"})
    with urlopen(request, timeout=15) as response:
        if response.status != 200:
            raise ValueError("Public deployment endpoint did not return HTTP 200")
        # Release pages are small; do not log their contents or download an unbounded body.
        return response.read(2_000_000).decode("utf-8")


def verify(sha, status_origin, app_origin):
    if not re.fullmatch(r"(?:[a-f0-9]{7}|[a-f0-9]{40})", sha):
        raise ValueError("Expected a 7 or 40 character lowercase commit SHA")
    revision = sha[:7]
    status_origin = origin(status_origin)
    app_origin = origin(app_origin, https=True)
    for endpoint in (status_origin + "/", app_origin + "/"):
        markers = ReleaseMarkers()
        markers.feed(fetch(endpoint))
        if not markers.values or any(value != revision for value in markers.values):
            raise ValueError(f"Deployed release differs from expected SHA {revision}")
    fetch(app_origin + "/api/health/ready")
    print(
        f"PASS deployed SHA {revision}: HTTP status, HTTPS application, API readiness"
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--status-origin", required=True)
    parser.add_argument("--app-origin", required=True)
    args = parser.parse_args(argv)
    try:
        verify(args.sha, args.status_origin, args.app_origin)
    except (ValueError, HTTPError, URLError, TimeoutError, UnicodeError):
        # No response body, credentials or request details are written to public CI logs.
        print(f"FAIL deployment verification for SHA {args.sha[:7]}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
