
"""Izolowane testy lokalnych linków w dokumentacji Markdown."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import scripts.check_markdown_links as checker
from scripts.check_markdown_links import check_file


class MarkdownLinksTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.doc = self.root / "README.md"

    def check(self, content):
        self.doc.write_text(content, encoding="utf-8")
        return check_file(self.doc, self.root)

    # Dotychczasowe 21 testów

    def test_existing_file(self):
        (self.root / "example.txt").write_text(
            "OK", encoding="utf-8"
        )
        self.assertEqual(self.check("[plik](example.txt)"), [])

    def test_missing_file(self):
        errors = self.check("[plik](missing.txt)")
        self.assertEqual(len(errors), 1)
        self.assertIn("missing.txt", errors[0])

    def test_path_with_spaces(self):
        (self.root / "my file.txt").write_text(
            "OK", encoding="utf-8"
        )
        self.assertEqual(
            self.check("[plik](<my file.txt>)"), []
        )

    def test_link_with_fragment(self):
        (self.root / "guide.md").write_text(
            "# Start", encoding="utf-8"
        )
        self.assertEqual(
            self.check("[opis](guide.md#start)"), []
        )

    def test_code_fence_is_ignored(self):
        content = "```markdown\n[przyklad](missing.txt)\n```"
        self.assertEqual(self.check(content), [])

    def test_indented_code_block_is_ignored(self):
        content = (
            "Przykład:\n\n"
            "    [plik](nieistnieje.md)\n"
            "\n"
            "[prawdziwy](brak.md)"
        )

        errors = self.check(content)

        self.assertEqual(len(errors), 1)
        self.assertIn("brak.md", errors[0])

    def test_tab_indented_code_is_ignored(self):
        self.assertEqual(
            self.check("\t[przykład](missing.md)"),
            [],
        )

    def test_inline_code_is_ignored_but_real_link_is_checked(self):
        errors = self.check(
            "Przykład `[plik](ignoruj.md)` "
            "i [link](missing.md)."
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("missing.md", errors[0])

    def test_multiple_backticks_in_inline_code(self):
        self.assertEqual(
            self.check("Kod: `` `[plik](missing.md)` ``"),
            [],
        )

    def test_encoded_space_and_fragment(self):
        (self.root / "raport 2026.md").write_text(
            "# Podsumowanie",
            encoding="utf-8",
        )

        self.assertEqual(
            self.check(
                "[raport](raport%202026.md#podsumowanie)"
            ),
            [],
        )

    def test_parentheses_in_filename(self):
        (self.root / "raport(2026).md").write_text(
            "OK",
            encoding="utf-8",
        )

        self.assertEqual(
            self.check("[raport](raport(2026).md)"),
            [],
        )

    def test_external_links_and_anchor_are_ignored(self):
        content = (
            "[www](https://example.com/a.md) "
            "[e-mail](mailto:qa@example.com) "
            "[nagłówek](#sekcja)"
        )

        self.assertEqual(self.check(content), [])

    def test_error_reports_correct_line(self):
        errors = self.check(
            "# Wstęp\n\n[brak](missing.md)"
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("README.md:3:", errors[0])

    def test_reference_definition(self):
        errors = self.check(
            "[odnośnik]: missing.md"
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("missing.md", errors[0])

    def test_tilde_fence_is_ignored(self):
        self.assertEqual(
            self.check(
                "~~~md\n[plik](missing.md)\n~~~"
            ),
            [],
        )

    def test_real_link_after_fence_is_checked(self):
        content = (
            "```\n"
            "[ignore](missing1.md)\n"
            "```\n"
            "[real](missing2.md)"
        )

        errors = self.check(content)

        self.assertEqual(len(errors), 1)
        self.assertIn("missing2.md", errors[0])

    def test_escaped_parentheses_in_filename(self):
        (self.root / "report(1).md").write_text(
            "OK",
            encoding="utf-8",
        )

        self.assertEqual(
            self.check(r"[plik](report\(1\).md)"),
            [],
        )

    def test_nested_list_link_is_checked(self):
        content = (
            "- Element nadrzędny\n"
            "  - Element podrzędny\n"
            "    [dokument](brak.md)"
        )

        errors = self.check(content)

        self.assertEqual(len(errors), 1)
        self.assertIn("brak.md", errors[0])
        self.assertIn("README.md:3:", errors[0])

    def test_parenthesis_inside_link_title(self):
        content = '[dokument](brak.md "Zobacz (szczegóły")'

        errors = self.check(content)

        self.assertEqual(len(errors), 1)
        self.assertIn("brak.md", errors[0])

    def test_nested_list_link_after_blank_line(self):
        content = (
            "- Element nadrzędny\n"
            "  - Element podrzędny\n"
            "\n"
            "    [dokument](brak.md)"
        )

        errors = self.check(content)

        self.assertEqual(len(errors), 1)
        self.assertIn("README.md:4:", errors[0])
        self.assertIn("brak.md", errors[0])

    def test_fenced_code_inside_list(self):
        content = (
            "- ```md\n"
            "  [przykład](brak.md)\n"
            "  ```\n"
            "\n"
            "[rzeczywisty](drugi-brak.md)"
        )

        errors = self.check(content)

        self.assertEqual(
            errors,
            ["README.md:5: nie istnieje: drugi-brak.md"],
        )

    # Dziewięć regresji z najnowszego review Jakuba Czai

    def test_indented_list_is_code(self):
        self.assertEqual(
            self.check(
                "Przykład:\n\n"
                "    - [plik](missing.md)\n"
            ),
            [],
        )

    def test_quoted_fence_is_code(self):
        self.assertEqual(
            self.check(
                "> ```md\n"
                "> [przykład](missing.md)\n"
                "> ```\n"
            ),
            [],
        )

    def test_fence_ends_when_list_container_ends(self):
        self.assertEqual(
            self.check(
                "- ```md\n"
                "  przykład\n"
                "\n"
                "[real](missing.md)\n"
            ),
            ["README.md:4: nie istnieje: missing.md"],
        )

    def test_multiline_code_span_is_ignored(self):
        self.assertEqual(
            self.check(
                "Kod: `przykład\n"
                "[plik](missing.md)\n"
                "koniec`\n"
            ),
            [],
        )

    def test_parenthesized_title_is_not_part_of_destination(self):
        self.assertEqual(
            self.check(
                "[plik](README.md (Opis pliku))\n"
            ),
            [],
        )

    def test_nested_brackets_in_label(self):
        self.assertEqual(
            self.check(
                "[dokument [v1]](missing.md)\n"
            ),
            ["README.md:1: nie istnieje: missing.md"],
        )

    def test_reference_definition_in_nested_list(self):
        errors = self.check(
            "- Element\n"
            "  - Podpunkt\n"
            "\n"
            "    [ref]: missing.md\n"
            "\n"
            "    [dokument][ref]\n"
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("README.md:", errors[0])
        self.assertIn("missing.md", errors[0])

    def test_escaped_opening_bracket_is_not_a_link(self):
        self.assertEqual(
            self.check(
                r"\[example](missing.md)" + "\n"
            ),
            [],
        )

    def test_cli_checks_unicode_filename_with_default_git_quoting(self):
        subprocess.run(
            ["git", "init", "-q", str(self.root)],
            check=True,
        )

        subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "config",
                "core.quotePath",
                "true",
            ],
            check=True,
        )

        scripts = self.root / "scripts"
        scripts.mkdir()

        shutil.copy(
            Path(checker.__file__),
            scripts / "check_markdown_links.py",
        )

        (self.root / "zażółć.md").write_text(
            "[brak](missing.md)\n",
            encoding="utf-8",
        )

        result = subprocess.run(
            [sys.executable, "scripts/check_markdown_links.py"],
            cwd=self.root,
            capture_output=True,
            text=True,
        )

        self.assertEqual(
            result.returncode,
            1,
            result.stdout + result.stderr,
        )
        self.assertIn("zażółć.md:1:", result.stdout)
        self.assertIn("missing.md", result.stdout)


if __name__ == "__main__":
    unittest.main()
