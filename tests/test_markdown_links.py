
import sys
import tempfile
import unittest
from pathlib import Path

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

    def test_existing_file(self):
        (self.root / "example.txt").write_text("OK", encoding="utf-8")
        self.assertEqual(self.check("[plik](example.txt)"), [])

    def test_missing_file(self):
        errors = self.check("[plik](missing.txt)")
        self.assertEqual(len(errors), 1)
        self.assertIn("missing.txt", errors[0])

    def test_path_with_spaces(self):
        (self.root / "my file.txt").write_text("OK", encoding="utf-8")
        self.assertEqual(self.check("[plik](<my file.txt>)"), [])

    def test_link_with_fragment(self):
        (self.root / "guide.md").write_text("# Start", encoding="utf-8")
        self.assertEqual(self.check("[opis](guide.md#start)"), [])

    def test_code_fence_is_ignored(self):
        content = "```markdown\n[przyklad](missing.txt)\n```"
        self.assertEqual(self.check(content), [])


if __name__ == "__main__":
    unittest.main()
