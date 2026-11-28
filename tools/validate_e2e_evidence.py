"""Validate the credential-free evidence from one full browser profile."""

import argparse
import hashlib
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


def summarize_shard(report: Path, profile: str, sha: str, outcome: str, shard: int) -> dict:
    evidence = summarize(report, profile, sha, outcome)
    cases = ET.parse(report).findall(".//testcase") if report.is_file() else []
    # Export only hashes of static test identities, never JUnit logs or test data.
    identities = [
        hashlib.sha256(
            json.dumps([case.get("classname", ""), case.get("name", "")]).encode("utf-8")
        ).hexdigest()
        for case in cases
    ]
    return {**evidence, "shard": shard, "case_ids": sorted(identities)}


def validate_shards(reports: list[dict], profile: str, sha: str) -> dict:
    if len(reports) != 2:
        raise ValueError(f"Expected two shards for {profile}")
    counts = ("total", "passed", "failed", "skipped", "unexpected_skips", "duplicate_cases")
    seen_shards = set()
    seen_cases = set()
    combined = {key: 0 for key in counts}
    combined.update(profile=profile, sha=sha, outcome="success", allowed_skips=[])
    for report in reports:
        if not isinstance(report, dict):
            raise ValueError(f"Malformed shard for {profile}")
        shard = report.get("shard")
        if type(shard) is not int or shard not in (1, 2) or shard in seen_shards:
            raise ValueError(f"Missing, invalid or duplicate shard for {profile}")
        seen_shards.add(shard)
        if any(type(report.get(key)) is not int or report[key] < 0 for key in counts):
            raise ValueError(f"Invalid shard counts for {profile}")
        ids = report.get("case_ids")
        skips = report.get("allowed_skips")
        if (
            report.get("profile") != profile
            or report.get("sha") != sha
            or report.get("outcome") != "success"
            or report["total"] <= 0
            or report["passed"] <= 0
            or report["total"] != report["passed"] + report["failed"] + report["skipped"]
            or report["failed"] != 0
            or report["unexpected_skips"] != 0
            or report["duplicate_cases"] != 0
            or not isinstance(skips, list)
            or len(skips) != report["skipped"]
            or any(label not in ALLOWED_SKIPS.values() for label in skips)
            or not isinstance(ids, list)
            or len(ids) != report["total"]
            or any(
                not isinstance(case_id, str)
                or len(case_id) != 64
                or any(char not in "0123456789abcdef" for char in case_id)
                for case_id in ids
            )
            or len(set(ids)) != len(ids)
            or bool(seen_cases.intersection(ids))
        ):
            raise ValueError(f"Incomplete, unsuccessful or overlapping shard {profile}/{shard}")
        seen_cases.update(ids)
        for key in counts:
            combined[key] += report[key]
        combined["allowed_skips"].extend(skips)
    combined["allowed_skips"].sort()
    # The original full-profile floor and exact skip allowlist remain mandatory.
    validate(combined, profile, sha)
    return combined


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("summarize", "validate", "validate-shards"))
    parser.add_argument("--shard", type=int, choices=(1, 2))
    parser.add_argument("--profile", choices=("desktop", "mobile"))
    parser.add_argument("--report", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--proof", type=Path)
    args = parser.parse_args()
    sha = os.environ["GITHUB_SHA"]
    if args.mode == "summarize":
        if not args.profile or args.report is None or args.output is None:
            parser.error("summarize requires --profile, --report and --output")
        outcome = os.environ.get("TEST_OUTCOME", "skipped")
        if args.shard is None:
            evidence = summarize(args.report, args.profile, sha, outcome)
        else:
            evidence = summarize_shard(args.report, args.profile, sha, outcome, args.shard)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence) + "\n", encoding="utf-8")
        print(json.dumps(evidence))
    else:
        if args.proof is None:
            parser.error("validate requires --proof")
        if args.mode == "validate-shards":
            for profile in ("desktop", "mobile"):
                reports = []
                for shard in (1, 2):
                    path = args.proof / f"e2e-results-{profile}-{shard}-{sha}" / "summary.json"
                    if not path.is_file():
                        raise SystemExit(f"Missing E2E evidence for {profile}/{shard}")
                    report = json.loads(path.read_text(encoding="utf-8"))
                    if not isinstance(report, dict) or report.get("shard") != shard:
                        raise SystemExit(f"Mislabelled E2E evidence for {profile}/{shard}")
                    reports.append(report)
                try:
                    evidence = validate_shards(reports, profile, sha)
                except ValueError as error:
                    raise SystemExit(str(error)) from None
                print(f"{profile}: {evidence['passed']} PASS, {evidence['skipped']} expected SKIP")
            return
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
