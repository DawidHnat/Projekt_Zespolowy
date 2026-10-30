
"""Sprawdzanie lokalnych linków w dokumentacji Markdown."""

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


LINK_PATTERN = re.compile(r"!?\[[^\]\n]*\]\((<[^>\n]+>|[^)\n]+)\)")
FENCE_PATTERN = re.compile(r"^\s*(`{3,}|~{3,})")
REFERENCE_PATTERN = re.compile(r"^\s*\[[^\]]+\]:\s*(<[^>]+>|\S+)")


def remove_code_blocks(content):
    """Pomija przykłady wewnątrz bloków kodu Markdown."""
    lines = []
    fence_char = None
    fence_length = 0

    for line in content.splitlines():
        match = FENCE_PATTERN.match(line)

        if match:
            marker = match.group(1)

            if fence_char is None:
                fence_char = marker[0]
                fence_length = len(marker)
                lines.append("")
                continue

            if marker[0] == fence_char and len(marker) >= fence_length:
                fence_char = None
                lines.append("")
                continue

        lines.append("" if fence_char else line)

    return lines


def extract_links(line):
    """Zwraca adresy linków zwykłych i referencyjnych."""
    links = []

    for match in LINK_PATTERN.finditer(line):
        target = match.group(1).strip()

        if target.startswith("<"):
            target = target[1:-1]
        else:
            target = re.split(r"\s+[\"']", target, maxsplit=1)[0]

        links.append(target)

    reference = REFERENCE_PATTERN.match(line)
    if reference:
        links.append(reference.group(1).strip("<>"))

    return links


def check_file(markdown_file, repo_root):
    """Zwraca błędy lokalnych linków w pojedynczym pliku."""
    errors = []
    content = markdown_file.read_text(encoding="utf-8")

    for line_number, line in enumerate(remove_code_blocks(content), 1):
        for target in extract_links(line):
            if not target or target.startswith("#"):
                continue

            parsed = urlsplit(target)

            if parsed.scheme or parsed.netloc or target.startswith("//"):
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
        ["git", "ls-files", "--cached", "--others",
         "--exclude-standard", "*.md"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )

    markdown_files = sorted(set(result.stdout.splitlines()))
    errors = []

    for filename in markdown_files:
        markdown_file = repo_root / filename

        if markdown_file.is_file():
            errors.extend(check_file(markdown_file, repo_root))

    if errors:
        print("Znaleziono nieprawidłowe linki Markdown:\n")
        for error in errors:
            print(error)
        return 1

    print(f"OK — sprawdzono {len(markdown_files)} plików Markdown.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
