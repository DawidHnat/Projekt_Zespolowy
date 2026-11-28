import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from validate_e2e_evidence import ALLOWED_SKIPS, summarize, summarize_shard, validate, validate_shards


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


    def shards(self):
        def report(shard, offset, total, skipped, labels):
            return {
                **self.evidence(),
                "shard": shard,
                "total": total,
                "passed": total - skipped,
                "skipped": skipped,
                "allowed_skips": labels,
                "case_ids": [f"{i:064x}" for i in range(offset, offset + total)],
            }
        return [report(1, 0, 45, 0, []), report(2, 45, 44, 2, ["online", "retry"])]

    def test_complete_shards_preserve_full_profile(self):
        self.assertEqual(validate_shards(self.shards(), "desktop", "a" * 40), self.evidence())

    def test_missing_shard_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_shards(self.shards()[:1], "desktop", "a" * 40)

    def test_invalid_or_overlapping_shards_are_rejected(self):
        for changes in (
            {"shard": 1},
            {"shard": True},
            {"profile": "mobile"},
            {"sha": "b" * 40},
            {"outcome": "failure"},
            {"failed": 1, "passed": 41},
            {"duplicate_cases": 1},
            {"unexpected_skips": 1},
            {"allowed_skips": ["retry", "retry"]},
            {"case_ids": ["invalid"] * 44},
            {"case_ids": [f"{i:064x}" for i in range(44)]},
            {"total": 0, "passed": 0, "skipped": 0, "allowed_skips": [], "case_ids": []},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                first, second = self.shards()
                validate_shards([first, {**second, **changes}], "desktop", "a" * 40)

    def test_shards_below_full_profile_floor_are_rejected(self):
        first, second = self.shards()
        second.update(total=43, passed=41, case_ids=second["case_ids"][:-1])
        with self.assertRaises(ValueError):
            validate_shards([first, second], "desktop", "a" * 40)

    def test_shard_summary_exports_only_hashed_test_identities(self):
        suite = ET.Element("testsuite")
        case = ET.SubElement(suite, "testcase", classname="test.spec.ts", name="case title")
        ET.SubElement(case, "system-out").text = "not exported"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.xml"
            ET.ElementTree(suite).write(path)
            report = summarize_shard(path, "desktop", "a" * 40, "success", 1)
            self.assertEqual(report["shard"], 1)
            self.assertEqual(len(report["case_ids"]), 1)
            self.assertEqual(len(report["case_ids"][0]), 64)
            self.assertNotIn("not exported", str(report))
            self.assertNotIn("case title", str(report))


if __name__ == "__main__":
    unittest.main()
