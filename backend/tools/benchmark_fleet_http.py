"""Measure 20 warm localhost HTTP requests in a dedicated synthetic PostgreSQL database."""

import json
import os
import socket
from datetime import UTC, datetime
from math import ceil
from threading import Thread
from time import monotonic, perf_counter, sleep
from uuid import uuid4

import httpx
import uvicorn
from sqlalchemy import create_engine, delete, insert, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.models import Measurement, SyncState, Vehicle
from app.core.settings import Settings
from app.main import create_app
from app.modules.auth.models import LoginSession, User
from app.modules.auth.service import password_hasher
from app.modules.fleet.sync import account_key


def seed(engine, source, size, user_id, username, password):
    now = datetime.now(UTC)
    identities = [uuid4() for _ in range(size)]
    with Session(engine) as session:
        session.add(SyncState(source_account=source, last_success_at=now))
        session.add(
            User(
                id=user_id,
                username=username,
                display_name="Synthetic benchmark",
                role="viewer",
                password_hash=password_hasher.hash(password),
            )
        )
        session.execute(
            insert(Vehicle),
            [
                {
                    "id": uid,
                    "source_account": source,
                    "external_uid": str(index),
                    "name": f"Synthetic {index:05d}",
                }
                for index, uid in enumerate(identities)
            ],
        )
        session.execute(
            insert(Measurement),
            [
                {
                    "vehicle_id": uid,
                    "latitude": 0,
                    "longitude": 0,
                    "gps_quality": "A",
                    "position_at": now,
                    "received_at": now,
                    "standing_still": False,
                }
                for uid in identities
            ],
        )
        session.commit()


def clear(engine, source, user_id):
    with Session(engine) as session:
        vehicles = session.scalars(select(Vehicle.id).where(Vehicle.source_account == source)).all()
        for offset in range(0, len(vehicles), 1000):
            session.execute(
                delete(Measurement).where(
                    Measurement.vehicle_id.in_(vehicles[offset : offset + 1000])
                )
            )
        session.execute(delete(Vehicle).where(Vehicle.source_account == source))
        session.execute(delete(SyncState).where(SyncState.source_account == source))
        session.execute(delete(LoginSession).where(LoginSession.user_id == user_id))
        session.execute(delete(User).where(User.id == user_id))
        session.commit()


def measure_requests(server, base, username, password):
    started_by = monotonic() + 10
    while not server.started and monotonic() < started_by:
        sleep(0.025)
    if not server.started:
        raise RuntimeError("Local test server failed to start")
    endpoints = {
        "list_page_25": "/api/v1/fleet/vehicles?page_size=25",
        "map": "/api/v1/fleet/map",
        "summary": "/api/v1/fleet/summary",
    }
    result = {}
    with httpx.Client(base_url=base, timeout=10, trust_env=False) as client:
        client.post(
            "/api/v1/auth/login",
            headers={"Origin": base},
            json={"username": username, "password": password},
        ).raise_for_status()
        for name, path in endpoints.items():
            client.get(path).raise_for_status()
            times = []
            for _ in range(20):
                start = perf_counter()
                response = client.get(path)
                times.append((perf_counter() - start) * 1000)
                response.raise_for_status()
            result[name] = {
                "p95_ms": round(sorted(times)[ceil(0.95 * len(times)) - 1], 2),
                "json_bytes": len(response.content),
            }
    return result


def main():
    url = os.environ["TEST_DATABASE_URL"]
    parsed = make_url(url)
    if (
        parsed.host not in ("127.0.0.1", "localhost")
        or parsed.database != "fleet_flow_test_benchmark"
    ):
        raise SystemExit("Requires a migrated localhost fleet_flow_test_benchmark database")
    engine = create_engine(url)
    findings = []
    for size in (100, 1000, 10000):
        user_id = uuid4()
        account = f"synthetic-benchmark-{user_id.hex}"
        source = account_key(account)
        password = "synthetic-loopback-benchmark"
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            base = f"http://127.0.0.1:{listener.getsockname()[1]}"
            settings = Settings(database_url=url, webfleet_account=account, origins=(base,))
            app = create_app(settings)
            server = uvicorn.Server(uvicorn.Config(app, access_log=False, log_level="error"))
            thread = Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
            seed(engine, source, size, user_id, account, password)
            try:
                thread.start()
                findings.append(
                    {"vehicles": size, **measure_requests(server, base, account, password)}
                )
            finally:
                server.should_exit = True
                thread.join(timeout=10)
                clear(engine, source, user_id)
    engine.dispose()
    print(json.dumps(findings, indent=2))


if __name__ == "__main__":
    main()
