"""Sprawdzanie lokalnych linków w dokumentacji Markdown."""

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


LINK_START = re.compile(r"!?\[[^\]\n]*\]\(")
FENCE_PATTERN = re.compile(r"^ {0,3}(`{3,}|~{3,})")
REFERENCE_PATTERN = re.compile(r"^ {0,3}\[[^\]]+\]:\s*(<[^>]+>|\S+)")
BACKTICKS = re.compile(r"`+")
LIST_MARKER = re.compile(r"^( *)(?:[-+*]|\d+[.)]) +")


def remove_inline_code(line):
    """Pomija kod inline, zachowując resztę linii."""
    markers = list(BACKTICKS.finditer(line))
    chars = list(line)
    index = 0

    while index < len(markers):
        opening = markers[index]
        closing_index = index + 1

        while closing_index < len(markers):
            closing = markers[closing_index]

            if len(closing.group()) == len(opening.group()):
                chars[opening.start():closing.end()] = [" "] * (
                    closing.end() - opening.start()
                )
                index = closing_index + 1
                break

            closing_index += 1
        else:
            index += 1

    return "".join(chars)


def remove_code_blocks(content):
    """Pomija kod Markdown, ale zachowuje linki w listach."""
    lines = []
    fence_char = None
    fence_length = 0
    list_content_indent = None

    for line in content.splitlines():
        if not line.strip():
            lines.append("")
            if fence_char is None:
                list_content_indent = None
            continue

        list_match = LIST_MARKER.match(line)
        indentation = len(line) - len(line.lstrip(" "))

        if fence_char is None:
            if list_match:
                list_content_indent = list_match.end()
            elif (
                list_content_indent is not None
                and indentation < list_content_indent
            ):
                list_content_indent = None

        is_list_continuation = (
            list_content_indent is not None
            and not list_match
            and indentation >= list_content_indent
        )

        if is_list_continuation:
            effective_line = line[list_content_indent:]
            effective_indent = indentation - list_content_indent
        elif list_match:
            effective_line = line
            effective_indent = 0
        else:
            effective_line = line
            effective_indent = indentation

        marker_match = FENCE_PATTERN.match(effective_line)

        if fence_char is not None:
            if marker_match:
                marker = marker_match.group(1)

                if (
                    marker[0] == fence_char
                    and len(marker) >= fence_length
                    and not effective_line[marker_match.end():].strip()
                ):
                    fence_char = None
                    fence_length = 0

            lines.append("")
            continue

        if (
            marker_match
            and not list_match
            and effective_indent < 4
        ):
            marker = marker_match.group(1)
            fence_char = marker[0]
            fence_length = len(marker)
            lines.append("")
            continue

        if (
            not list_match
            and (
                effective_line.startswith("\t")
                or effective_indent >= 4
            )
        ):
            lines.append("")
            continue

        lines.append(remove_inline_code(line))

    return lines


def parse_destination(line, start):
    """Odczytuje cel linku, ignorując nawiasy w cytowanym tytule."""
    depth = 1
    in_angle = False
    title_quote = None
    position = start

    while position < len(line):
        char = line[position]

        if char == "\\" and position + 1 < len(line):
            position += 2
            continue

        if title_quote is not None:
            if char == title_quote:
                title_quote = None
            position += 1
            continue

        if (
            not in_angle
            and depth == 1
            and char in ('"', "'")
            and position > start
            and line[position - 1].isspace()
            and line[start:position].strip()
        ):
            title_quote = char
            position += 1
            continue

        if char == "<":
            in_angle = True

        elif char == ">" and in_angle:
            in_angle = False

        elif not in_angle and char == "(":
            depth += 1

        elif not in_angle and char == ")":
            depth -= 1

            if depth == 0:
                return line[start:position]

        position += 1

    return None


def clean_destination(raw):
    """Usuwa opcjonalny tytuł linku i znaki escape Markdown."""
    raw = raw.strip()

    if not raw:
        return ""

    if raw.startswith("<"):
        ending = raw.find(">")

        if ending != -1:
            raw = raw[1:ending]
    else:
        raw = re.split(r'\s+(?=["\'])', raw, maxsplit=1)[0]

    return re.sub(
        r"\\([\\`*_{}\[\]()#+.!<>])",
        r"\1",
        raw,
    )


def extract_links(line):
    """Zwraca adresy linków i definicji referencyjnych."""
    links = []

    for match in LINK_START.finditer(line):
        raw = parse_destination(line, match.end())

        if raw is not None:
            links.append(clean_destination(raw))

    reference = REFERENCE_PATTERN.match(line)

    if reference:
        links.append(clean_destination(reference.group(1)))

    return links


def check_file(markdown_file, repo_root):
    """Zwraca błędy lokalnych linków z numerem pliku i linii."""
    errors = []
    content = markdown_file.read_text(encoding="utf-8")

    for line_number, line in enumerate(remove_code_blocks(content), 1):
        for target in extract_links(line):
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
            "--cached",
            "--others",
            "--exclude-standard",
            "*.md",
        ],
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
