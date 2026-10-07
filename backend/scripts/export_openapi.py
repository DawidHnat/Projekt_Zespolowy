"""Export a deterministic shared contract without contacting Postgres or Webfleet."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="Fail when committed contract is stale."
    )
    args = parser.parse_args()
    target = Path(__file__).resolve().parents[2] / "contracts" / "openapi.json"
    # An exporter should work even when the developer's .env is absent or points to a live account.
    application = create_app(Settings(_env_file=None, database_url="sqlite://", data_source="demo"))
    content = json.dumps(application.openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    application.state.engine.dispose()
    if args.check:
        if not target.exists() or target.read_text(encoding="utf-8") != content:
            raise SystemExit("OpenAPI contract is stale. Run python scripts/export_openapi.py.")
        print("OpenAPI contract is up to date.")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        print(f"Exported {target.name}.")


if __name__ == "__main__":
    main()
