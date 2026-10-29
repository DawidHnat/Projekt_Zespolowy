import argparse
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import collect_sprint_evidence as evidence


class EvidenceTests(unittest.TestCase):
    def test_zero_is_grep_exit_one(self):
        self.assertEqual(evidence.commit_count(
            {"exit_code": 1, "stdout": "0\n", "stderr": ""}), 0)

    def test_bad_commits_are_counted(self):
        self.assertEqual(evidence.commit_count(
            {"exit_code": 0, "stdout": "2\n", "stderr": ""}), 2)

    def test_git_error_cannot_become_zero_pass(self):
        self.assertIsNone(evidence.commit_count(
            {"exit_code": 1, "stdout": "0\n", "stderr": "fatal: invalid revision"}))

    def test_unexpected_exit_cannot_pass(self):
        self.assertIsNone(evidence.commit_count(
            {"exit_code": 127, "stdout": "0\n", "stderr": ""}))

    def test_date_cannot_contain_shell_commands(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            evidence.protection_date('2026-10-20; echo bad')

    def test_missing_tool_is_saved_as_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(evidence.subprocess, "run", side_effect=FileNotFoundError("gh")):
                result = evidence.capture(["gh"], root, root, "missing")
            self.assertEqual(result["exit_code"], 127)
            self.assertIn("gh", (root / "missing.stderr.txt").read_text())

    @staticmethod
    def successful_command(args, _root, _output, _name):
        return {"command": " ".join(args), "exit_code": 0,
                "stdout": "ok\n", "stderr": "", "file": "example.txt"}

    def test_missing_date_collects_other_evidence_but_returns_incomplete(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "results"
            with patch.object(evidence, "capture", side_effect=self.successful_command) as run:
                result = evidence.main(["--output", str(out)])
            self.assertEqual(result, 2)
            self.assertFalse(any('git log' in ' '.join(c.args[0]) for c in run.call_args_list))
            self.assertIn("NIEKOMPLETNE", (out / "ODDANIE.md").read_text())

    def test_existing_results_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(FileExistsError):
                evidence.main(["--output", temp])

    def test_confirmed_date_accepts_grep_zero_but_still_requires_human_checks(self):
        def run(args, root, output, name):
            result = self.successful_command(args, root, output, name)
            if name == "03-commity":
                result.update(exit_code=1, stdout="0\n")
            return result

        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "results"
            with patch.object(evidence, "capture", side_effect=run):
                result = evidence.main([
                    "--output", str(out), "--protection-since", "2026-10-20"])
            self.assertEqual(result, 0)
            report = (out / "ODDANIE.md").read_text()
            self.assertIn("wymagany odbiór zespołu", report)
            self.assertIn("Pełny odbiór przynajmniej jednej Story", report)

    def test_sha_mismatch_fails_even_with_confirmed_date(self):
        def run(args, root, output, name):
            result = self.successful_command(args, root, output, name)
            if name == "01-serwer-sha":
                result.update(exit_code=1, stdout="")
            elif name == "03-commity":
                result.update(exit_code=1, stdout="0\n")
            return result

        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "results"
            with patch.object(evidence, "capture", side_effect=run):
                result = evidence.main([
                    "--output", str(out), "--protection-since", "2026-10-20"])
            self.assertEqual(result, 1)
            self.assertIn("BŁĄD", (out / "ODDANIE.md").read_text())

    def test_timeout_is_saved_as_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(evidence.subprocess, "run",
                              side_effect=subprocess.TimeoutExpired("gh", 90)):
                result = evidence.capture(["gh"], root, root, "timeout")
            self.assertEqual(result["exit_code"], 127)


if __name__ == "__main__":
    unittest.main()
