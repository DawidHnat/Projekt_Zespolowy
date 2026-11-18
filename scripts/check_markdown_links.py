
"""Sprawdzanie lokalnych linków w dokumentacji Markdown."""

import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt


def extract_links(content):
    """Zwraca numery linii i adresy aktywnych linków."""
    environment = {}
    tokens = MarkdownIt("commonmark").parse(content, environment)
    reference_targets = set()

    # Sprawdź definicje referencyjne, także te bez użycia.
    for reference in environment.get("references", {}).values():
        target = reference["href"]
        reference_targets.add(target)
        yield reference["map"][0] + 1, target

    for token in tokens:
        if token.type != "inline" or token.map is None:
            continue

        first_line = token.map[0] + 1

        for child in token.children or []:
            if child.type == "link_open":
                target = child.attrGet("href")
            elif child.type == "image":
                target = child.attrGet("src")
            else:
                continue

            # Cel definicji referencyjnej sprawdzono już powyżej.
            if not target or target in reference_targets:
                continue

            line_number = first_line

            # Token inline może obejmować kilka linii,
            # np. przy zagnieżdżonych listach Markdown.
            if "\n" in token.content:
                for offset, text in enumerate(
                    token.content.splitlines()
                ):
                    plain = re.sub(
                        r"\\([\\()\[\]])",
                        r"\1",
                        text,
                    )

                    if (
                        target in plain
                        or unquote(target) in plain
                    ):
                        line_number += offset
                        break

            yield line_number, target


def check_file(markdown_file, repo_root):
    """Zwraca błędy lokalnych linków z numerem pliku i linii."""
    errors = []
    content = markdown_file.read_text(encoding="utf-8")

    for line_number, target in extract_links(content):
        if not target or target.startswith("#"):
            continue

        parsed = urlsplit(target)

        if (
            parsed.scheme
            or parsed.netloc
            or target.startswith("//")
        ):
            continue

        path = unquote(parsed.path)

        if not path:
            continue

        if path.startswith("/"):
            destination = repo_root / path.lstrip("/")
        else:
            destination = markdown_file.parent / path

        if not destination.exists():
            relative_file = markdown_file.relative_to(repo_root)

            errors.append(
                f"{relative_file}:{line_number}: "
                f"nie istnieje: {target}"
            )

    return errors


def main():
    repo_root = Path(__file__).resolve().parent.parent

    result = subprocess.run(
        [
            "git",
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
            "*.md",
        ],
        cwd=repo_root,
        capture_output=True,
        check=True,
    )

    # Git zwraca nazwy oddzielone bajtem NUL.
    # Nie korzystamy z cytowanych nazw core.quotePath.
    markdown_files = sorted(
        {
            os.fsdecode(filename)
            for filename in result.stdout.split(b"\0")
            if filename
        }
    )

    errors = []
    checked = 0

    for filename in markdown_files:
        markdown_file = repo_root / filename

        if markdown_file.is_file():
            checked += 1
            errors.extend(check_file(markdown_file, repo_root))

    if errors:
        print("Znaleziono nieprawidłowe linki Markdown:\n")

        for error in errors:
            print(error)

        return 1

    print(f"OK — sprawdzono {checked} plików Markdown.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
