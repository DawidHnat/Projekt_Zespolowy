"""Opt-in diagnostics: counts and field coverage only, no customer data output."""

import argparse
import asyncio
import json
from pathlib import Path

from app.core.config import ConfigurationError, SmtpSettings, WebfleetSettings, load_environment
from app.integrations.mail.client import SmtpError, check_smtp
from app.integrations.webfleet.client import OBJECT_COLUMNS, WebfleetClient, WebfleetError
from app.integrations.webfleet.models import ObjectSnapshot


async def check_webfleet(settings: WebfleetSettings) -> dict:
    async with WebfleetClient(settings) as client:
        records = await client.fetch_objects()
    valid = 0
    for record in records:
        try:
            ObjectSnapshot.from_record(record)
            valid += 1
        except ValueError:
            pass
    return {
        "integration": "webfleet",
        "ok": True,
        "records": len(records),
        "valid_snapshot_records": valid,
        "coverage": {
            name: sum(record.get(name) not in (None, "") for record in records)
            for name in OBJECT_COLUMNS
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sprawdzenie integracji bez wypisywania danych floty"
    )
    parser.add_argument("integration", choices=("webfleet", "smtp"))
    parser.add_argument(
        "--env-file", type=Path, help="Ścieżka do lokalnego .env (domyślnie katalog projektu)"
    )
    args = parser.parse_args()
    try:
        values = load_environment(args.env_file)
        if args.integration == "webfleet":
            result = asyncio.run(check_webfleet(WebfleetSettings.from_environment(values)))
        else:
            check_smtp(SmtpSettings.from_environment(values))
            result = {"integration": "smtp", "ok": True, "email_sent": False}
    except (ConfigurationError, WebfleetError, SmtpError) as error:
        print(
            json.dumps(
                {"integration": args.integration, "ok": False, "error": str(error)},
                ensure_ascii=False,
            )
        )
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
