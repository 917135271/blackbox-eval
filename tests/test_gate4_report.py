from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "runner" / "report_gate4_formal_runs.py"


def load_report():
    spec = importlib.util.spec_from_file_location("report_gate4_formal_runs_test", REPORT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class Gate4ReportTests(unittest.TestCase):
    def test_checkpoint_recoverability_requires_all_retained_fields(self) -> None:
        report = load_report()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "checkpoint.json"
            retained = {
                "task": "x",
                "constraints": [],
                "audit_plan": {},
                "applicable_policies": [],
                "record_ids": [],
                "evidence_status": "pass",
                "unresolved_items": [],
                "artifact_index": [],
                "remaining_budget": {},
                "submission_status": "accepted",
            }
            path.write_text(
                json.dumps(
                    {
                        "stage": "submission_ready",
                        "retained_state": retained,
                    }
                ),
                encoding="utf-8",
            )
            self.assertTrue(report.checkpoint_recoverable(path))
            retained.pop("record_ids")
            path.write_text(
                json.dumps(
                    {
                        "stage": "submission_ready",
                        "retained_state": retained,
                    }
                ),
                encoding="utf-8",
            )
            self.assertFalse(report.checkpoint_recoverable(path))


if __name__ == "__main__":
    unittest.main()
