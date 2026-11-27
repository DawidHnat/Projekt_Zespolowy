"""Synthetic SCRUM-97 benchmark; run from backend with python -m tools.benchmark_fleet_queries.

Uses an existing migrated localhost fleet_flow_test* database. All inserted records are
rolled back. No production URL, migrations, deletion or external integration is used.
"""

import json
import os
import statistics
import time
from datetime import UTC, datetime
from math import ceil
from uuid import uuid4

from sqlalchemy import create_engine, event, insert, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.models import Driver, Measurement, Vehicle
from app.modules.fleet.service import fleet_markers, fleet_page, fleet_summary, serialize_vehicle


def main():
    url = make_url(os.environ["TEST_DATABASE_URL"])
    if url.host not in ("127.0.0.1", "localhost") or not (url.database or "").startswith(
        "fleet_flow_test"
    ):
        raise SystemExit("Only an isolated localhost fleet_flow_test* database is allowed")
    engine = create_engine(url)
    results = []
    for size in (100, 1000, 10000):
        source = f"benchmark-{uuid4()}"
        now = datetime.now(UTC)
        with engine.connect() as connection, connection.begin() as transaction:
            session = Session(bind=connection)
            identities = [uuid4() for _ in range(size)]
            session.execute(
                insert(Vehicle),
                [
                    {
                        "id": identity,
                        "source_account": source,
                        "external_uid": str(index),
                        "name": f"Synthetic {index:05d}",
                    }
                    for index, identity in enumerate(identities)
                ],
            )
            session.execute(
                insert(Measurement),
                [
                    {
                        "vehicle_id": identity,
                        "latitude": 0,
                        "longitude": 0,
                        "gps_quality": "A",
                        "position_at": now,
                        "received_at": now,
                        "standing_still": False,
                    }
                    for identity in identities
                ],
            )
            session.flush()
            connection.exec_driver_sql("ANALYZE vehicles")
            connection.exec_driver_sql("ANALYZE measurements")
            # Select the mapped columns consumed by serialize_vehicle eagerly. Deferring
            # them here would benchmark one additional SQL query for each field and vehicle.
            legacy_statement = (
                select(Vehicle, Measurement, Driver)
                .outerjoin(Measurement, Measurement.vehicle_id == Vehicle.id)
                .outerjoin(Driver, Driver.id == Vehicle.driver_id)
                .where(Vehicle.source_account == source, Vehicle.active.is_(True))
                .order_by(Vehicle.name, Vehicle.id)
                .limit(10001)
            )

            def legacy(session=session, legacy_statement=legacy_statement, now=now):
                for _ in range(3):  # Previous list + map + summary each loaded the whole fleet.
                    records = session.execute(legacy_statement).all()
                    [serialize_vehicle(*row, now, 900) for row in records]
                    session.expunge_all()

            def optimized(session=session, source=source):
                fleet_page(session, source, 900, "", None, 1, 25)
                session.expunge_all()
                fleet_markers(session, source, 900, "", None)
                fleet_summary(session, source, 900)

            captured = []

            def capture(
                conn, cursor, statement, parameters, context, executemany, captured=captured
            ):
                if statement.lstrip().upper().startswith("SELECT"):
                    captured.append((statement, parameters))

            event.listen(connection, "before_cursor_execute", capture)
            legacy()
            legacy_selects = len(captured)
            captured.clear()
            optimized()
            optimized_selects = len(captured)
            event.remove(connection, "before_cursor_execute", capture)
            if legacy_selects != 3:
                raise RuntimeError(f"Expected 3 legacy queries, measured {legacy_selects}")
            plans = []
            for statement, parameters in captured:
                plan = connection.exec_driver_sql(
                    "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + statement, parameters
                ).scalar_one()[0]
                plans.append(plan)
            timings = {}
            for name, operation in (("legacy", legacy), ("sql", optimized)):
                operation()  # Warm cache and query compilation.
                samples = []
                for _ in range(20):
                    start = time.perf_counter()
                    operation()
                    samples.append((time.perf_counter() - start) * 1000)
                timings[name + "_median_ms"] = round(statistics.median(samples), 2)
                p95 = sorted(samples)[ceil(len(samples) * 0.95) - 1]
                timings[name + "_p95_ms"] = round(p95, 2)
            results.append(
                {
                    "vehicles": size,
                    "legacy_orm_rows": size * 3,
                    "legacy_selects": legacy_selects,
                    "sql_selects": optimized_selects,
                    "sql_orm_rows": 25,
                    "sql_marker_rows": size,
                    "sql_aggregate_rows": 3,
                    **timings,
                    "plans": plans,
                }
            )
            session.close()
            transaction.rollback()
    engine.dispose()
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
