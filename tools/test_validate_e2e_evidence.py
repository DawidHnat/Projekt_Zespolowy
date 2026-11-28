import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from validate_e2e_evidence import ALLOWED_SKIPS, summarize, validate


class EvidenceTests(unittest.TestCase):
    def evidence(self):
        return {
            "profile": "desktop",
            "sha": "a" * 40,
            "outcome": "success",
            "total": 89,
            "passed": 87,
            "failed": 0,
            "skipped": 2,
            "allowed_skips": ["online", "retry"],
            "unexpected_skips": 0,
            "duplicate_cases": 0,
        }

    def test_complete_profile_passes(self):
        validate(self.evidence(), "desktop", "a" * 40)

    def test_one_pass_and_88_skips_are_rejected(self):
        evidence = self.evidence()
        evidence.update(passed=1, skipped=88, unexpected_skips=86)
        with self.assertRaises(ValueError):
            validate(evidence, "desktop", "a" * 40)

    def test_incomplete_report_is_rejected(self):
        evidence = self.evidence()
        evidence.update(total=88, passed=86)
        with self.assertRaises(ValueError):
            validate(evidence, "desktop", "a" * 40)

    def test_wrong_skips_and_malformed_evidence_are_rejected(self):
        for changes in (
            {"allowed_skips": ["retry", "retry"]},
            {"unexpected_skips": 1},
            {"duplicate_cases": 1},
            {"passed": 88},
            {"outcome": "skipped"},
            {"outcome": "failure"},
            {"failed": 1, "passed": 86},
            {"sha": "b" * 40},
            {"profile": "mobile"},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate({**self.evidence(), **changes}, "desktop", "a" * 40)

    def test_junit_summarizes_only_expected_map_skips(self):
        suite = ET.Element("testsuite")
        for i in range(87):
            ET.SubElement(suite, "testcase", classname="critical-flow.spec.ts", name=f"test {i}")
        for title in ALLOWED_SKIPS:
            case = ET.SubElement(suite, "testcase", classname="map-provider-recovery.spec.ts", name=title)
            ET.SubElement(case, "skipped")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.xml"
            ET.ElementTree(suite).write(path)
            evidence = summarize(path, "desktop", "a" * 40, "success")
            self.assertEqual(evidence, self.evidence())
            validate(evidence, "desktop", "a" * 40)
            # Same title in another file is not an allowlisted skip.
            suite[-1].set("classname", "unexpected.spec.ts")
            ET.ElementTree(suite).write(path)
            evidence = summarize(path, "desktop", "a" * 40, "success")
            self.assertEqual(evidence["unexpected_skips"], 1)
            with self.assertRaises(ValueError):
                validate(evidence, "desktop", "a" * 40)


if __name__ == "__main__":
    unittest.main()
