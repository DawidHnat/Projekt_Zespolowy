"""SCRUM-96: disposable, network-isolated Caddy/API/PostgreSQL test.

Run from repository root after building the supplied API image. The script only
removes containers/network it creates with a unique fleet-proxy-test-* prefix.
No production environment, published port, real credentials or external API.
"""

import argparse
import ipaddress
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]


def docker(*args, timeout=90):
    result = subprocess.run(
        ["docker", *args], capture_output=True, text=True, timeout=timeout, check=False
    )
    if result.returncode:
        # Docker errors may contain environment/connection strings; emit only the phase.
        raise RuntimeError(f"Docker test step failed: {args[0]}")
    return result.stdout.strip()


def wait_for(check, label):
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        try:
            check()
            return
        except RuntimeError:
            time.sleep(0.5)
    raise RuntimeError(f"Timed out waiting for synthetic {label}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--image", required=True, help="Locally built, synthetic-test API image"
    )
    args = parser.parse_args()
    compose = (ROOT / "infra/deploy/compose.yml").read_text()
    caddy_image = re.search(r"image: (caddy:\S+)", compose)[1]
    subnet = re.search(r"FLEET_FLOW_PROXY_SUBNET:-([^}]+)", compose)[1]
    proxy_ip = re.search(r"FLEET_FLOW_PROXY_IP:-([^}]+)", compose)[1]
    network_range = ipaddress.ip_network(subnet)
    assert ipaddress.ip_address(proxy_ip) in network_range
    assert network_range.is_private
    clients = [str(network_range[index]) for index in (4, 5, 6)]
    name = "fleet-proxy-test-" + uuid4().hex[:10]
    network = name + "-network"
    database, api, edge = (name + suffix for suffix in ("-db", "-api", "-edge"))
    containers = []
    created_network = False
    try:
        docker("network", "create", "--internal", "--subnet", subnet, network)
        created_network = True
        docker(
            "run",
            "-d",
            "--name",
            database,
            "--network",
            network,
            "--network-alias",
            "database",
            "--ip",
            str(network_range[7]),
            "-e",
            "POSTGRES_USER=proxy_test",
            "-e",
            "POSTGRES_PASSWORD=synthetic-proxy-only",
            "-e",
            "POSTGRES_DB=fleet_flow_test_proxy",
            "postgres:17-alpine",
        )
        containers.append(database)
        wait_for(
            lambda: docker("exec", database, "pg_isready", "-U", "proxy_test"),
            "database",
        )
        database_url = "postgresql+psycopg://proxy_test:synthetic-proxy-only@database:5432/fleet_flow_test_proxy"
        common = [
            "--network",
            network,
            "-e",
            f"DATABASE_URL={database_url}",
            "-e",
            "SYNC_ENABLED=false",
            "-e",
            "COOKIE_SECURE=true",
            "-e",
            "CORS_ORIGINS=https://fleet.test",
        ]
        docker(
            "run",
            "--rm",
            *common,
            "--entrypoint",
            "alembic",
            args.image,
            "upgrade",
            "head",
        )
        docker(
            "run",
            "-d",
            "--name",
            api,
            *common,
            "--network-alias",
            "api-proxy",
            "--ip",
            str(network_range[2]),
            "-e",
            f"FORWARDED_ALLOW_IPS={proxy_ip}",
            args.image,
        )
        containers.append(api)
        wait_for(
            lambda: docker(
                "exec",
                api,
                "python",
                "-c",
                "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health/ready')",
            ),
            "API",
        )
        with tempfile.TemporaryDirectory(prefix="fleet-proxy-pages-") as folder:
            pages = Path(folder)
            (pages / "index.html").write_text(
                '<html lang="pl"><title>Synthetic proxy</title></html>'
            )
            (pages / "status.html").write_text("Synthetic public status only")
            docker(
                "run",
                "-d",
                "--name",
                edge,
                "--network",
                network,
                "--ip",
                proxy_ip,
                "--network-alias",
                "edge",
                "-e",
                "APP_DOMAIN=http://:8080",
                "-v",
                f"{ROOT / 'infra/deploy/Caddyfile'}:/etc/caddy/Caddyfile:ro",
                "-v",
                f"{pages}:/srv/frontend:ro",
                caddy_image,
            )
            containers.append(edge)
            wait_for(
                lambda: docker(
                    "exec",
                    edge,
                    "wget",
                    "-q",
                    "-O",
                    "/dev/null",
                    "http://127.0.0.1:8080/api/health/live",
                ),
                "Caddy",
            )
            client_code = r"""
import json, urllib.request, urllib.error

def request(url, index=0, login=False):
    headers = {"Origin": "https://fleet.test", "Content-Type": "application/json",
        "X-Forwarded-For": f"203.0.113.{index + 1}", "X-Real-IP": f"198.51.100.{index + 1}",
        "Forwarded": f"for=192.0.2.{index + 1};proto=https", "X-Forwarded-Proto": "https"}
    body = json.dumps({"username": "synthetic-proxy-" + str(index), "password": "wrong"}).encode() if login else None
    try:
        response = urllib.request.urlopen(urllib.request.Request(url, data=body, headers=headers), timeout=5)
    except urllib.error.HTTPError as error:
        response = error
    return response.status, dict(response.headers.items())

mode = __import__("sys").argv[1]
if mode == "headers":
    for path in ("/", "/api/health/ready", "/api/v1/fleet/vehicles"):
        status, headers = request("http://edge:8080" + path)
        assert status == (401 if "fleet" in path else 200)
        h = {k.lower(): v for k, v in headers.items()}
        assert h["x-content-type-options"] == "nosniff"
        assert h["x-frame-options"] == "DENY"
        assert "frame-ancestors 'none'" in h["content-security-policy"]
        assert "worker-src 'self' blob:" in h["content-security-policy-report-only"]
        assert "https://api.mapbox.com" in h["content-security-policy-report-only"]
        assert "geolocation=()" in h["permissions-policy"]
        assert "strict-transport-security" not in h
    assert request("http://edge:80/api/v1/fleet/vehicles")[0] == 404
    assert request("http://edge:80/")[0] == 200
elif mode == "exhaust-proxy":
    assert [request("http://edge:8080/api/v1/auth/login", i, True)[0] for i in range(11)] == [401] * 10 + [429]
elif mode == "other-client":
    assert request("http://edge:8080/api/v1/auth/login", 50, True)[0] == 401
elif mode == "exhaust-direct":
    assert [request("http://api-proxy:8000/api/v1/auth/login", 100 + i, True)[0] for i in range(11)] == [401] * 10 + [429]
print("PASS: " + mode)
"""
            for client_ip, mode in (
                (clients[0], "headers"),
                (clients[0], "exhaust-proxy"),
                (clients[1], "other-client"),
                (clients[2], "exhaust-direct"),
            ):
                print(
                    docker(
                        "run",
                        "--rm",
                        "--network",
                        network,
                        "--ip",
                        client_ip,
                        "--entrypoint",
                        "python",
                        args.image,
                        "-c",
                        client_code,
                        mode,
                    )
                )
            # Prove the real client buckets reached the actual PostgreSQL limiter.
            verify = """
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.modules.auth.models import LoginAttempt
from app.modules.auth.service import digest
import os, sys
with Session(create_engine(os.environ["DATABASE_URL"])) as session:
    values = [session.get(LoginAttempt, digest("ip:" + ip)).attempts for ip in sys.argv[1:]]
    assert values == [11, 1, 11], values
print("PASS: distinct PostgreSQL client buckets")
"""
            print(docker("exec", api, "python", "-c", verify, *clients))
        print(
            json.dumps(
                {
                    "result": "PASS",
                    "environment": "isolated synthetic Docker network",
                    "caddy_image": caddy_image,
                    "api_image": args.image,
                    "checks": [
                        "headers",
                        "separate IP limits",
                        "spoofed forwarding rejected",
                        "untrusted direct API rejected",
                        "HTTP exposes no fleet API",
                    ],
                }
            )
        )
    finally:
        for container in reversed(containers):
            subprocess.run(
                ["docker", "rm", "-f", container],
                capture_output=True,
                timeout=30,
                check=False,
            )
        if created_network:
            subprocess.run(
                ["docker", "network", "rm", network],
                capture_output=True,
                timeout=30,
                check=False,
            )


if __name__ == "__main__":
    main()
