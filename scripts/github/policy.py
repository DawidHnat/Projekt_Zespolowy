"""Pure, testable decisions for the GitHub automation. No network or secrets."""

import json
import re
from pathlib import PurePosixPath

TEAM = frozenset({"jczaja51", "dawidhnat", "jnazarewiczs", "mglowacki0"})
BRANCH = re.compile(
    r"^(feat|fix|docs|chore|refactor|test)/([A-Z][A-Z0-9]*-\d+)-[a-z0-9][a-z0-9-]*$"
)
SHA = re.compile(r"^[0-9a-f]{40}$")
MAX_FILES = 8
MAX_LINES = 200
MAX_REVIEW_FILES = 50
MAX_DIFF_BYTES = 100_000
HUNK = re.compile(r"^@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@(?:.*)$")

REVIEW_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "verdict": {
            "type": "string",
            "enum": ["approve", "request_changes", "human_review"],
        },
        "risk": {"type": "string", "enum": ["low", "medium", "high"]},
        "summary": {"type": "string"},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "path": {"type": "string"},
                    "line": {"type": "integer"},
                    "severity": {
                        "type": "string",
                        "enum": ["blocker", "warning", "note"],
                    },
                    "message": {"type": "string"},
                },
                "required": ["path", "line", "severity", "message"],
            },
        },
    },
    "required": ["verdict", "risk", "summary", "findings"],
}


def allowed_path(name):
    """Only user guides and existing UI styles can be merged automatically."""
    path = PurePosixPath(name)
    if name != str(path) or path.is_absolute() or ".." in path.parts:
        return False
    if len(path.parts) >= 3 and path.parts[:2] in (
        ("docs", "user"),
        ("docs", "guides"),
    ):
        return path.suffix == ".md"
    return (
        len(path.parts) >= 3
        and path.parts[:2] == ("frontend", "src")
        and path.suffix == ".css"
    )


def complete_patch(file):
    """Match hunk lengths and changed-line counts; never accept a clipped patch."""
    patch = file.get("patch")
    if not isinstance(patch, str) or not patch.strip():
        return False
    expected = None
    old = new = additions = deletions = 0
    for line in patch.splitlines():
        match = HUNK.fullmatch(line)
        if match:
            if expected is not None and (old, new) != expected:
                return False
            expected = (int(match[1] or "1"), int(match[2] or "1"))
            old = new = 0
        elif expected is None:
            return False
        elif line.startswith("+"):
            new += 1
            additions += 1
        elif line.startswith("-"):
            old += 1
            deletions += 1
        elif line.startswith(" "):
            old += 1
            new += 1
        elif line != "\\ No newline at end of file":
            return False
    return (
        expected is not None
        and (old, new) == expected
        and additions == file.get("additions")
        and deletions == file.get("deletions")
    )


def regular_file_modes(files, head_tree, base_tree):
    for file in files:
        name = file["filename"]
        trees = []
        if file["status"] != "removed":
            trees.append(head_tree)
        if file["status"] != "added":
            trees.append(base_tree)
        if any(tree.get(name) != ("blob", "100644") for tree in trees):
            return False
    return True


def simple_change(files, expected_count):
    if expected_count != len(files) or not 1 <= len(files) <= MAX_FILES:
        return False, "Automatyczny merge wymaga kompletnego diffu 1–8 plików."
    if any(f.get("status") not in {"modified", "added", "removed"} for f in files):
        return False, "Zmiana nazw lub nietypowy typ zmiany wymaga osoby sprawdzającej."
    if any(not allowed_path(f.get("filename", "")) for f in files):
        return (
            False,
            "Zakres wykracza poza docs/user, docs/guides i frontend/src/**/*.css.",
        )
    try:
        counts = [f["additions"] + f["deletions"] for f in files]
        if any(
            type(f["additions"]) is not int or type(f["deletions"]) is not int
            for f in files
        ):
            raise ValueError("invalid counts")
        if any(c < 0 for c in counts) or sum(counts) > MAX_LINES:
            return (
                False,
                "Automatyczny merge obejmuje najwyżej 200 dodanych/usuniętych linii.",
            )
    except (KeyError, TypeError, ValueError):
        return False, "Brak poprawnej informacji o rozmiarze diffu."
    if any(not complete_patch(f) for f in files):
        return False, "Brak pełnej tekstowej łatki co najmniej jednego pliku."
    return True, "Mała zmiana w dozwolonym zakresie."


def review_input(files, expected_count, title):
    if expected_count != len(files) or not 1 <= len(files) <= MAX_REVIEW_FILES:
        raise ValueError(
            "Diff jest niekompletny albo zawiera ponad 50 plików; potrzebny przegląd człowieka."
        )
    if any(not complete_patch(f) for f in files):
        raise ValueError(
            "GitHub nie udostępnił tekstowej łatki każdego pliku; potrzebny przegląd człowieka."
        )
    data = json.dumps({"title": title, "files": files}, ensure_ascii=False)
    if len(data.encode("utf-8")) > MAX_DIFF_BYTES:
        raise ValueError(
            "Diff przekracza 100 kB; nie jest obcinany i wymaga przeglądu człowieka."
        )
    return data


def unique_object(pairs):
    value = {}
    for name, item in pairs:
        if name in value:
            raise ValueError("Powtórzony klucz w odpowiedzi AI.")
        value[name] = item
    return value


def parse_review(response, files):
    if response.get("status") != "completed":
        raise ValueError("Model nie ukończył przeglądu.")
    chunks = []
    for output in response.get("output", []):
        if output.get("type") == "message":
            for content in output.get("content", []):
                if content.get("type") == "refusal":
                    raise ValueError("Model odmówił przeglądu.")
                if content.get("type") == "output_text":
                    chunks.append(content.get("text", ""))
    result = json.loads("".join(chunks), object_pairs_hook=unique_object)
    if not isinstance(result, dict) or set(result) != {
        "verdict",
        "risk",
        "summary",
        "findings",
    }:
        raise ValueError("Niepoprawny format decyzji AI.")
    if result["verdict"] not in {"approve", "request_changes", "human_review"}:
        raise ValueError("Nieznana decyzja AI.")
    if result["risk"] not in {"low", "medium", "high"}:
        raise ValueError("Nieznany poziom ryzyka.")
    if (
        not isinstance(result["summary"], str)
        or not 1 <= len(result["summary"]) <= 2000
    ):
        raise ValueError("Niepoprawne podsumowanie AI.")
    if not isinstance(result["findings"], list) or len(result["findings"]) > 20:
        raise ValueError("Niepoprawna lista uwag AI.")
    names = {f["filename"] for f in files}
    for finding in result["findings"]:
        if not isinstance(finding, dict) or set(finding) != {
            "path",
            "line",
            "severity",
            "message",
        }:
            raise ValueError("Niepoprawny format uwagi AI.")
        if (
            finding["path"] not in names
            or type(finding["line"]) is not int
            or finding["line"] < 1
        ):
            raise ValueError("Uwaga AI wskazuje niepoprawny plik lub linię.")
        if finding["severity"] not in {"blocker", "warning", "note"}:
            raise ValueError("Niepoprawna waga uwagi AI.")
        if (
            not isinstance(finding["message"], str)
            or not 1 <= len(finding["message"]) <= 1500
        ):
            raise ValueError("Niepoprawna treść uwagi AI.")
    return result


def changes_requested(reviews):
    latest = {}
    for review in reviews:
        if review.get("user", {}).get("type") != "User":
            continue
        if review.get("state") in {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}:
            latest[review["user"]["login"].lower()] = review["state"]
    return "CHANGES_REQUESTED" in latest.values()


def merge_gate(
    pr, run, snapshot, files, reviews, decision, repository, base_sha, base_ref="main"
):
    """Every condition is required; a model recommendation cannot bypass policy."""
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        return False, "CI nie zakończyło się sukcesem."
    if not isinstance(snapshot, dict):
        return False, "Niepoprawny format dowodu CI."
    if run.get("event") not in {"push", "pull_request"}:
        return False, "Nieobsługiwany rodzaj uruchomienia CI."
    if run.get("actor", {}).get("login", "").lower() not in TEAM:
        return False, "Uruchomienie nie pochodzi od członka zespołu."
    if (
        run.get("triggering_actor", run.get("actor", {})).get("login", "").lower()
        not in TEAM
    ):
        return False, "Ponowne uruchomienie nie pochodzi od członka zespołu."
    if run.get("head_repository", {}).get("full_name") != repository:
        return False, "Gałąź pochodzi z innego repozytorium."
    author = pr.get("user", {}).get("login", "").lower()
    if author not in TEAM | {"github-actions[bot]"}:
        return False, "Autor PR nie należy do zespołu ani automatyzacji repozytorium."
    if pr.get("head", {}).get("repo", {}).get("full_name") != repository:
        return False, "PR z forka wymaga przeglądu człowieka."
    if pr.get("state") != "open" or pr.get("draft") or pr.get("merged"):
        return False, "PR jest zamknięty, scalony lub w trybie draft."
    if "human-review" in {label.get("name") for label in pr.get("labels", [])}:
        return False, "Etykieta human-review wyłącza automatyczny merge."
    if not BRANCH.fullmatch(pr.get("head", {}).get("ref", "")):
        return False, "Gałąź nie ma nazwy typu feat/KLUCZ-123-opis."
    if pr.get("head", {}).get("ref") != run.get("head_branch"):
        return False, "PR zmienił gałąź źródłową po rozpoczęciu CI."
    if pr.get("base", {}).get("ref") != base_ref:
        return False, "PR zmienił gałąź docelową po rozpoczęciu CI."
    head_sha = pr.get("head", {}).get("sha")
    if not isinstance(head_sha, str) or not SHA.fullmatch(head_sha):
        return False, "Niepoprawny commit PR."
    if run.get("head_sha") != head_sha or snapshot.get("head_sha") != head_sha:
        return False, "PR zmienił się po uruchomieniu CI."
    if (
        snapshot.get("base_sha") != base_sha
        or pr.get("base", {}).get("sha") != base_sha
    ):
        return (
            False,
            "Gałąź docelowa zmieniła się po rozpoczęciu CI. Zaktualizuj gałąź i wykonaj push.",
        )
    if snapshot.get("repository") != repository or snapshot.get("run_id") != run.get(
        "id"
    ):
        return False, "Dowód CI nie pasuje do repozytorium lub uruchomienia."
    if (
        type(run.get("run_attempt")) is not int
        or run["run_attempt"] < 1
        or snapshot.get("run_attempt") != run["run_attempt"]
    ):
        return (
            False,
            "CI zostało ponownie uruchomione; wymagany jest aktualny dowód testów.",
        )
    if snapshot.get("event") != run.get("event") or snapshot.get("version") != 1:
        return False, "Niepoprawny dowód CI."
    if pr.get("mergeable") is not True or pr.get("mergeable_state") not in {
        "clean",
        "has_hooks",
    }:
        return False, "GitHub nie potwierdził gotowości PR do scalania."
    if changes_requested(reviews):
        return False, "Osoba sprawdzająca zażądała zmian."
    eligible, reason = simple_change(files, pr.get("changed_files"))
    if not eligible:
        return False, reason
    if (
        not decision
        or decision.get("verdict") != "approve"
        or decision.get("risk") != "low"
    ):
        return False, "AI nie potwierdziło akceptacji i niskiego ryzyka."
    if decision.get("findings"):
        return False, "AI zgłosiło uwagi; potrzebna poprawka lub przegląd człowieka."
    return True, "Aktualne CI, pełny diff, dozwolony zakres i akceptacja AI."
