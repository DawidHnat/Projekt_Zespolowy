import unittest
from datetime import date

from gitleaks_false_positives import ignore_file


class GitleaksFalsePositiveTests(unittest.TestCase):
    def test_only_one_immutable_finding_is_excluded(self):
        self.assertEqual(
            ignore_file(date(2026, 11, 18)).splitlines(),
            [
                (
                    "aee868abdc2979681fa1e113698e1bd4d473ebf0:"
                    "docs/COURSE_AGENT_HANDOFFS.md:generic-api-key:22"
                )
            ],
        )

    def test_valid_until_expiry(self):
        self.assertTrue(ignore_file(date(2026, 12, 17)))

    def test_expiry_and_later_dates_fail_closed(self):
        for today in (date(2026, 12, 18), date(2027, 1, 1)):
            with self.subTest(today=today), self.assertRaises(ValueError):
                ignore_file(today)


if __name__ == "__main__":
    unittest.main()
