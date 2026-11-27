"""Validate the credential-free evidence from one full browser profile."""

import argparse
import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path

# Baseline of the reviewed full suite: 89 cases per profile, of which only
# the two map-recovery cases are intentionally skipped in the tokenless build.
# Raise this floor when new mandatory cases are added; do not lower silently.
MINIMUM_TOTAL = 89
ALLOWED_SKIPS = {
    "recovers a map style after 503 on retry without losing selection": "retry",
    "recovers a map style after 503 on online without losing selection": "online",
}


def summarize(report: Path, profile: str, sha: str, outcome: str) -> dict:
    cases = ET.parse(report).findall(".//testcase") if report.is_file() else []
    identities = [
        (case.get("classname", ""), case.get("name", "")) for case in cases
    ]
    failed = 0
    skipped = 0
    allowed = []
    unexpected = 0
    for case in cases:
        if any(case.find(tag) is not None for tag in ("failure", "error")):
            failed += 1
        elif case.find("skipped") is not None:
            skipped += 1
            filename = case.get("classname", "").replace(chr(92), "/").split("/")[-1]
            title = case.get("name", "")
            label = ALLOWED_SKIPS.get(title)
            if filename == "map-provider-recovery.spec.ts" and label:
                allowed.append(label)
            else:
                unexpected += 1
    return {
        "profile": profile,
        "sha": sha,
        "outcome": outcome,
        "total": len(cases),
        "passed": len(cases) - failed - skipped,
        "failed": failed,
        "skipped": skipped,
        "allowed_skips": sorted(allowed),
        "unexpected_skips": unexpected,
        "duplicate_cases": len(identities) - len(set(identities)),
    }


def validate(evidence: dict, profile: str, sha: str) -> None:
    counts = ("total", "passed", "failed", "skipped", "unexpected_skips", "duplicate_cases")
    if any(type(evidence.get(key)) is not int or evidence[key] < 0 for key in counts):
        raise ValueError(f"Invalid counts for {profile}")
    if (
        evidence.get("profile") != profile
        or evidence.get("sha") != sha
        or evidence.get("outcome") != "success"
        or evidence["total"] < MINIMUM_TOTAL
        or evidence["total"] != evidence["passed"] + evidence["failed"] + evidence["skipped"]
        or evidence["passed"] < MINIMUM_TOTAL - len(ALLOWED_SKIPS)
        or evidence["failed"] != 0
        or evidence["skipped"] != len(ALLOWED_SKIPS)
        or evidence.get("allowed_skips") != sorted(ALLOWED_SKIPS.values())
        or evidence["unexpected_skips"] != 0
        or evidence["duplicate_cases"] != 0
    ):
        raise ValueError(f"Incomplete or unsuccessful E2E profile: {profile}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("summarize", "validate"))
    parser.add_argument("--profile", choices=("desktop", "mobile"))
    parser.add_argument("--report", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--proof", type=Path)
    args = parser.parse_args()
    sha = os.environ["GITHUB_SHA"]
    if args.mode == "summarize":
        if not args.profile or args.report is None or args.output is None:
            parser.error("summarize requires --profile, --report and --output")
        evidence = summarize(args.report, args.profile, sha, os.environ.get("TEST_OUTCOME", "skipped"))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence) + "\n", encoding="utf-8")
        print(json.dumps(evidence))
    else:
        if args.proof is None:
            parser.error("validate requires --proof")
        for profile in ("desktop", "mobile"):
            path = args.proof / f"e2e-results-{profile}-{sha}" / "summary.json"
            if not path.is_file():
                raise SystemExit(f"Missing E2E evidence for {profile}")
            evidence = json.loads(path.read_text(encoding="utf-8"))
            try:
                validate(evidence, profile, sha)
            except ValueError as error:
                raise SystemExit(str(error)) from None
            print(f"{profile}: {evidence['passed']} PASS, {evidence['skipped']} expected SKIP")


if __name__ == "__main__":
    main()
