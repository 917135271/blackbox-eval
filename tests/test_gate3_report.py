from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "runner" / "report_gate3_development.py"
SPEC = importlib.util.spec_from_file_location("report_gate3_development_test", REPORT_PATH)
assert SPEC and SPEC.loader
REPORT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPORT)


class Gate3ReportNormalizationTests(unittest.TestCase):
    def test_calendar_day_wording_matches_day_fact(self) -> None:
        answer = REPORT.normalize_text("两笔费用间隔为8个日历日，无异常。")
        self.assertIn(REPORT.normalize_text("8天"), answer)

    def test_report_covers_ten_groups(self) -> None:
        self.assertEqual(len(REPORT.GROUPS), 10)
        self.assertIn("oh-my-pi-baseline", REPORT.GROUPS)
        self.assertIn("oh-my-pi-enhanced", REPORT.GROUPS)


if __name__ == "__main__":
    unittest.main()
