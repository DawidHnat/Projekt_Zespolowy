#!/usr/bin/env python3
"""Walidacja aktualności wydania przed wdrożeniem (SCRUM-137).

Odrzuca próby wdrożenia starszych commitów przy ponowieniu historycznych runów CI.
Wymusza monotoniczny postęp wdrożeń na gałęzi main, idempotentne ponowienie
bieżącego wydania oraz jawną autoryzację celowego rollbacku.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DEFAULT_REPO_URL = "https://github.com/DawidHnat/Projekt_Zespolowy.git"
DEFAULT_REPO_DIR = "/opt/fleet-flow/shared/repo.git"


def run_git(repo_dir: str, *args: str) -> subprocess.CompletedProcess[str]:
    """Wykonaj polecenie git w zadanym repozytorium bare."""
    cmd = ["git", f"--git-dir={repo_dir}", *args]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def ensure_repo(repo_dir: str, repo_url: str, offline: bool = False) -> None:
    """Upewnij się, że lokalny cache repozytorium bare istnieje i jest zaktualizowany."""
    if not os.path.exists(repo_dir):
        if offline:
            raise RuntimeError(f"Repozytorium {repo_dir} nie istnieje w trybie offline.")
        os.makedirs(os.path.dirname(os.path.abspath(repo_dir)), exist_ok=True)
        res = subprocess.run(
            ["git", "clone", "--bare", repo_url, repo_dir],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode != 0:
            raise RuntimeError(
                f"Nie udało się sklonować repozytorium {repo_url}: {res.stderr.strip()}"
            )

    if not offline:
        # Pobierz gałąź main z repozytorium źródłowego
        run_git(repo_dir, "fetch", "--quiet", "origin", "refs/heads/main:refs/heads/main")


def is_ancestor(repo_dir: str, ancestor_sha: str, descendant_sha: str) -> bool:
    """Zwraca True, jeśli ancestor_sha jest przodkiem descendant_sha."""
    res = run_git(repo_dir, "merge-base", "--is-ancestor", ancestor_sha, descendant_sha)
    return res.returncode == 0


def commit_exists(repo_dir: str, sha: str, offline: bool = False) -> bool:
    """Sprawdza, czy commit istnieje w repozytorium; w razie potrzeby pobiera."""
    res = run_git(repo_dir, "cat-file", "-e", f"{sha}^{{commit}}")
    if res.returncode == 0:
        return True
    if offline:
        return False
    run_git(repo_dir, "fetch", "--quiet", "origin", sha)
    res = run_git(repo_dir, "cat-file", "-e", f"{sha}^{{commit}}")
    return res.returncode == 0


def validate_release(
    target_sha: str,
    current_sha: str | None = None,
    repo_dir: str = DEFAULT_REPO_DIR,
    repo_url: str = DEFAULT_REPO_URL,
    allow_rollback: bool = False,
    offline: bool = False,
) -> tuple[int, str]:
    """Waliduje, czy target_sha może zostać wdrożony względem current_sha."""
    if not SHA_RE.match(target_sha):
        return 1, f"Niepoprawny format SHA celu: {target_sha}"

    if current_sha and not SHA_RE.match(current_sha):
        return 1, f"Niepoprawny format SHA bieżącego wydania: {current_sha}"

    # Przypadek 1: Pierwsze wdrożenie na czystym serwerze
    if not current_sha:
        return 0, f"Pierwsze wdrożenie na serwerze: zatwierdzono {target_sha[:7]}."

    # Przypadek 2: Idempotentne ponowienie bieżącego wydania
    if target_sha == current_sha:
        return 0, f"Ponowienie bieżącego wydania {target_sha[:7]} jest dozwolone i idempotentne."

    # Upewnij się, że repozytorium istnieje
    try:
        ensure_repo(repo_dir, repo_url, offline=offline)
    except Exception as err:
        return 1, f"Błąd przygotowania repozytorium Git: {err}"

    # Sprawdź, czy target_sha istnieje w Git
    if not commit_exists(repo_dir, target_sha, offline=offline):
        return 1, f"Commit {target_sha} nie istnieje w repozytorium {repo_dir}."

    # Przypadek 3: target_sha jest starszy od current_sha (próba wdrożenia przeszłości)
    if is_ancestor(repo_dir, target_sha, current_sha):
        if allow_rollback:
            return (
                0,
                f"ROLLBACK: Celowy powrót do wcześniejszego wydania {target_sha[:7]} "
                f"(bieżące: {current_sha[:7]}) został zatwierdzony przez operatora.",
            )
        return (
            1,
            f"ODRZUCONO: Próba wdrożenia przestarzałego wydania {target_sha[:7]}. "
            f"Commit jest przodkiem bieżącego wdrożenia {current_sha[:7]}. "
            "Ponowienie historycznego CI nie może cofać serwera. "
            "Użyj --allow-rollback, jeśli jest to celowa decyzja.",
        )

    # Przypadek 4: target_sha nie jest bezpośrednim potomkiem current_sha (rozbieżność)
    if not is_ancestor(repo_dir, current_sha, target_sha):
        if allow_rollback:
            return (
                0,
                f"ROLLBACK: Celowe wdrożenie rozbieżnego wydania {target_sha[:7]} "
                f"(bieżące: {current_sha[:7]}) zostało zatwierdzone przez operatora.",
            )
        return (
            1,
            f"ODRZUCONO: Commit {target_sha[:7]} nie wywodzi się "
            f"bezpośrednio z {current_sha[:7]} (rozbieżna historia).",
        )

    # Przypadek 5: Sprawdzenie, czy target_sha znajduje się na gałęzi main
    # Sprawdzamy refs/heads/main lub main
    on_main = is_ancestor(repo_dir, target_sha, "refs/heads/main") or is_ancestor(
        repo_dir, target_sha, "main"
    )
    if not on_main:
        return (
            1,
            f"ODRZUCONO: Commit {target_sha[:7]} nie znajduje się na gałęzi main.",
        )

    return (
        0,
        f"ZATWIERDZONO: Commit {target_sha[:7]} jest poprawnym nowym wydaniem "
        f"względem {current_sha[:7]}.",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Walidator monotoniczności wydań fleet-flow (SCRUM-137)"
    )
    parser.add_argument("--target-sha", required=True, help="40-znakowy SHA commitu do wdrożenia")
    parser.add_argument(
        "--current-sha",
        default=os.environ.get("FLEET_FLOW_CURRENT_SHA"),
        help="40-znakowy SHA bieżącego wydania na serwerze",
    )
    parser.add_argument(
        "--repo-dir",
        default=os.environ.get("FLEET_FLOW_REPO_DIR", DEFAULT_REPO_DIR),
        help="Ścieżka do lokalnego repozytorium bare Git",
    )
    parser.add_argument(
        "--repo-url",
        default=os.environ.get("FLEET_FLOW_REPO_URL", DEFAULT_REPO_URL),
        help="Adres URL repozytorium źródłowego Git",
    )
    parser.add_argument(
        "--allow-rollback",
        action="store_true",
        default=os.environ.get("FLEET_FLOW_ALLOW_ROLLBACK", "").lower() in ("1", "true", "yes"),
        help="Zezwól na celowy rollback do starszego lub rozbieżnego commita",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        default=os.environ.get("FLEET_FLOW_VALIDATE_OFFLINE", "").lower() in ("1", "true", "yes"),
        help="Tryb offline (nie wykonuj poleceń sieciowych git fetch/clone)",
    )

    args = parser.parse_args(argv)
    code, message = validate_release(
        target_sha=args.target_sha,
        current_sha=args.current_sha,
        repo_dir=args.repo_dir,
        repo_url=args.repo_url,
        allow_rollback=args.allow_rollback,
        offline=args.offline,
    )
    if code == 0:
        print(message)
    else:
        print(message, file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
