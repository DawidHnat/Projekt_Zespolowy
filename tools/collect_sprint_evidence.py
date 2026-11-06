#!/usr/bin/env python3
"""Collect course evidence without changing GitHub, Jira or the development server."""

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shlex
import subprocess


TUTORIAL_JQ = (
    r'.[] | .author.login as $a | "#\(.number) \(.headRefName) author=\($a) '
    r'reviewers=\([.reviews[].author.login] | unique | map(select(. != $a)) | '
    r'join(",")) key_in_body=\(.body | test("[A-Z]+-[0-9]+"))"'
)
COMMIT_PATTERN = (
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert|breaking)"
    r"(\([^)]+\))?!?: .+"
)
SERVER_COMMAND = (
    'git fetch && curl -s --max-time 25 http://57.129.179.53/ '
    '| grep "$(git rev-parse --short=7 origin/main)"'
)
HUMAN_CHECKS = """## Nadal do potwierdzenia przez zespół

- Pełny odbiór przynajmniej jednej Story Sprintu 1 według DEFINITION_OF_DONE.md.
- Każdy członek jako autor scalonego PR i recenzent cudzego scalonego PR;
  klucze Jiry w opisach i nazwach gałęzi oraz wymagane aktualne Approved.
- Rzeczywisty konflikt tych samych linii kodu, opis rozwiązania i zielone CI
  ostatniego commita wskazanego PR: **uzupełnić numer i link**.
- Faktyczne Review i retro; zapis trzech części i działań z właścicielami
  w docs/retro/sprint-1.md, po review scalony do main.
- Aktywny Sprint 2: **uzupełnić nazwę i cel z Jiry** oraz działanie SCRUM-65.

Każdy oddaje osobno. Ten raport zbiera dowody techniczne i nie potwierdza
wykonania spotkań, QA, niezależnego review ani zakończenia Sprintu 1.
"""


def protection_date(value):
    try:
        dt.datetime.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Podaj potwierdzoną datę ISO, np. RRRR-MM-DD.") from exc
    return value


def capture(args, root, output, name):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GH_PROMPT_DISABLED="1")
    try:
        result = subprocess.run(
            args, cwd=root, env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=90,
        )
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except (OSError, subprocess.TimeoutExpired) as exc:
        code, stdout, stderr = 127, "", str(exc)
    (output / f"{name}.txt").write_text(stdout, encoding="utf-8")
    (output / f"{name}.stderr.txt").write_text(stderr, encoding="utf-8")
    return {"command": shlex.join(args), "exit_code": code,
            "stdout": stdout, "stderr": stderr, "file": f"{name}.txt"}


def commit_count(result):
    """grep returns 1 for zero selected lines; other failures are not a pass."""
    value = result["stdout"].strip()
    if result["stderr"].strip() or not value.isdecimal():
        return None
    count = int(value)
    expected_code = 1 if count == 0 else 0
    return count if result["exit_code"] == expected_code else None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protection-since", type=protection_date,
                        help="Potwierdzona data włączenia ochrony main; bez zgadywania.")
    parser.add_argument("--output", type=Path,
                        help="Nowy katalog wynikowy; istniejący nie zostanie nadpisany.")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    now = dt.datetime.now(dt.timezone.utc)
    output = (args.output or root / ".local" / "sprint-evidence" /
              now.strftime("%Y%m%dT%H%M%S%fZ")).resolve()
    output.mkdir(parents=True, exist_ok=False)
    checks = {}
    checks["server_sha"] = capture(
        ["bash", "-o", "pipefail", "-c", SERVER_COMMAND], root, output, "01-serwer-sha")
    checks["main"] = capture(
        ["git", "rev-parse", "--short=7", "origin/main"], root, output, "01-main")
    checks["health"] = capture(
        ["curl", "-fsS", "--max-time", "25",
         "https://vps-9171bf52.vps.ovh.net/api/health/ready"],
        root, output, "01-health")
    checks["pull_requests"] = capture(
        ["gh", "pr", "list", "--repo", "DawidHnat/Projekt_Zespolowy",
         "--state", "merged", "--limit", "100", "--json",
         "number,headRefName,author,reviews,body", "--jq", TUTORIAL_JQ],
        root, output, "02-pr-krok6")
    checks["fetch_for_commits"] = capture(
        ["git", "fetch"], root, output, "03-git-fetch")
    count = None
    if args.protection_since and checks["fetch_for_commits"]["exit_code"] == 0:
        # The supplied date is a positional argument, never interpolated as shell code.
        command = ('git log --no-merges --since="$1" --format=%s origin/main '
                   '| grep -vcE ' + shlex.quote(COMMIT_PATTERN))
        checks["commits"] = capture(
            ["bash", "-c", command, "evidence", args.protection_since],
            root, output, "03-commity")
        count = commit_count(checks["commits"])
    failures = [name for name, result in checks.items()
                if name != "commits" and result["exit_code"] != 0]
    if "commits" in checks and (count is None or count > 0):
        failures.append("commits")
    state = "BŁĄD — sprawdź wyniki" if failures else (
        "NIEKOMPLETNE — brak potwierdzonej daty ochrony main"
        if not args.protection_since else "ZEBRANO — wymagany odbiór zespołu")
    manifest = {"collected_at_utc": now.isoformat(), "repository": "DawidHnat/Projekt_Zespolowy",
                "protection_since": args.protection_since, "state": state,
                "nonconventional_commits": count, "checks": checks}
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sections = ["# Dowody Sprintu 1\n", f"Stan zbierania: **{state}**.\n",
                f"Czas UTC: {now.isoformat()}.\n",
                "Aplikacja: https://vps-9171bf52.vps.ovh.net/ .\n"]
    for name, result in checks.items():
        sections.extend([f"## {name}\n", "```sh\n" + result["command"] + "\n```\n",
                         f"Kod wyjścia: {result['exit_code']}.\n",
                         "```text\n" + result["stdout"].rstrip() + "\n```\n"])
        if result["stderr"]:
            sections.append("stderr:\n```text\n" + result["stderr"].rstrip() + "\n```\n")
    if not args.protection_since:
        sections.append("Nie wykonano kontroli `--since`: właściciel musi potwierdzić datę ochrony.\n")
    sections.append(HUMAN_CHECKS)
    (output / "ODDANIE.md").write_text("\n".join(sections), encoding="utf-8")
    print(f"{state}\nWyniki: {output / 'ODDANIE.md'}")
    return 1 if failures else (2 if not args.protection_since else 0)


if __name__ == "__main__":
    raise SystemExit(main())
