from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from runner.audit_trace import finalize_governance_artifacts, redact_secret_in_tree, start_run


class AuditTraceGovernanceTests(unittest.TestCase):
    def test_runtime_secret_redaction_preserves_file_and_removes_exact_value(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            snapshot = root / "codex-home" / "shell_snapshots" / "snapshot.sh"
            snapshot.parent.mkdir(parents=True)
            snapshot.write_text("export LLM_API_KEY='secret-value'\n", encoding="utf-8")

            changed = redact_secret_in_tree(root, "secret-value")

            self.assertEqual(changed, ["codex-home/shell_snapshots/snapshot.sh"])
            self.assertEqual(
                snapshot.read_text(encoding="utf-8"),
                "export LLM_API_KEY='[REDACTED]'\n",
            )

    def test_enhanced_finalization_creates_recoverable_checkpoint_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / "workspace"
            start_run(
                workspace=workspace,
                task_id="DEV-001",
                framework="codex",
                experiment_group="codex-enhanced",
                model="test-model",
                timeout_seconds=900,
            )
            (workspace / "task.md").write_text("核查测试记录。", encoding="utf-8")
            (workspace / "work").mkdir(exist_ok=True)
            (workspace / "work" / "audit_plan.json").write_text(
                json.dumps({"scope": ["R1"]}),
                encoding="utf-8",
            )
            (workspace / "work" / "evidence_matrix.json").write_text(
                json.dumps({"status": "pass", "unresolved_items": []}),
                encoding="utf-8",
            )
            (workspace / "final_submission.json").write_text(
                json.dumps(
                    {
                        "record_ids": ["R1"],
                        "citations": [{"doc_id": "policy.md", "clause_no": "第一条"}],
                    }
                ),
                encoding="utf-8",
            )
            (workspace / "submission_receipt.json").write_text(
                json.dumps({"status": "accepted"}),
                encoding="utf-8",
            )

            result = finalize_governance_artifacts(
                workspace=workspace,
                task_id="DEV-001",
                experiment_group="codex-enhanced",
                timeout_seconds=900,
                elapsed_seconds=120.0,
            )

            self.assertTrue(result["checkpoint"]["accepted"])
            checkpoint = json.loads(
                (workspace / "work" / "context_checkpoint.json").read_text(encoding="utf-8")
            )
            self.assertEqual(checkpoint["stage"], "submission_ready")
            self.assertEqual(checkpoint["retained_state"]["submission_status"], "accepted")
            self.assertEqual(checkpoint["retained_state"]["record_ids"], ["R1"])

            manifest = json.loads(
                (workspace / "traces" / "artifact_manifest.json").read_text(encoding="utf-8")
            )
            paths = {item["path"] for item in manifest["artifacts"]}
            self.assertIn("final_submission.json", paths)
            self.assertIn("work/context_checkpoint.json", paths)
            self.assertNotIn("run_manifest.json", paths)
            self.assertTrue(all(len(item["sha256"]) == 64 for item in manifest["artifacts"]))

    def test_baseline_finalization_skips_checkpoint_but_writes_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / "workspace"
            start_run(
                workspace=workspace,
                task_id="DEV-001",
                framework="codex",
                experiment_group="codex-baseline",
                model="test-model",
                timeout_seconds=900,
            )

            result = finalize_governance_artifacts(
                workspace=workspace,
                task_id="DEV-001",
                experiment_group="codex-baseline",
                timeout_seconds=900,
                elapsed_seconds=20.0,
            )

            self.assertEqual(result["checkpoint"]["code"], "BASELINE_NOT_REQUIRED")
            checkpoint = json.loads(
                (workspace / "work" / "context_checkpoint.json").read_text(encoding="utf-8")
            )
            self.assertEqual(checkpoint["stage"], "task_started")
            self.assertTrue((workspace / "traces" / "artifact_manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
