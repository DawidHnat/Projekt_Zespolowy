"""Import a vehicle's historical report with the shared account rate limit."""

import argparse
import json
from datetime import date
from uuid import UUID

from app.core.config import WebfleetSettings, load_environment
from app.core.database import make_engine
from app.core.settings import Settings
from app.modules.fleet.sync import log_sync_failure
from app.modules.trips.importer import import_one_day


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vehicle", required=True, type=UUID, help="Fleet-Flow vehicle UUID")
    parser.add_argument("--from", dest="first", required=True, type=date.fromisoformat)
    parser.add_argument("--through", type=date.fromisoformat, help="Inclusive; defaults to --from")
    parser.add_argument("--refresh", action="store_true", help="Re-read one imported day")
    args = parser.parse_args()
    engine = None
    try:
        config = load_environment()
        settings = Settings.from_environment(config)
        source = WebfleetSettings.from_environment(config)
        engine = make_engine(settings)
        result = import_one_day(
            engine,
            source,
            args.vehicle,
            args.first,
            args.through or args.first,
            refresh=args.refresh,
        )
    except Exception:
        log_sync_failure("TRIP_HISTORY_FAILED")
        result = "failed"
    finally:
        if engine is not None:
            engine.dispose()
    print(json.dumps({"status": result}))
    return 0 if result in ("imported", "complete") else 1


if __name__ == "__main__":
    raise SystemExit(main())
