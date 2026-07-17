from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "data" / "formal_case_rubric" / "build_formal_dataset.py"
CASES = ROOT / "data" / "formal_case_rubric" / "cases.json"
EVALS = ROOT / "data" / "formal_case_rubric" / "evals.json"
VALIDATOR = ROOT / "runner" / "validate_case_rubrics.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_case_rubrics", VALIDATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CaseRubricTests(unittest.TestCase):
    def test_generated_case_dataset_is_current(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(BUILD), "--check"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_every_formal_case_has_a_valid_100_point_rubric(self) -> None:
        report = load_validator().validate(CASES, EVALS)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["case_count"], 15)
        self.assertGreaterEqual(report["criterion_count"], 75)

    def test_formal_set_excludes_ground_truth_lookup_tasks(self) -> None:
        dataset = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertTrue(all(case["category"] != "ground_truth_lookup" for case in dataset["cases"]))
        self.assertEqual(
            {case["case_family"] for case in dataset["cases"]},
            {
                "policy_and_version",
                "record_audit",
                "full_year_audit",
                "clean_trap",
                "retrieval_and_report",
            },
        )


if __name__ == "__main__":
    unittest.main()
