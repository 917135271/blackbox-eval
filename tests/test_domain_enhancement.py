from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOMAIN = ROOT / "domain-enhancement"
CORE_SCRIPTS = DOMAIN / "shared-audit-core" / "scripts"
sys.path.insert(0, str(CORE_SCRIPTS))

from audit_control_core import (  # noqa: E402
    authorize_subagent,
    checkpoint_context,
    complete_subagent,
    initialize_task_state,
    submit_result,
    validate_submission,
)


DB_PATH = ROOT / "data" / "expense.db"
CORPUS_PATH = ROOT / "data" / "corpus"
ROUTING_PATH = DOMAIN / "shared-audit-core" / "routing" / "routing_rules.json"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def valid_result() -> dict[str, object]:
    return {
        "anomaly_ids": ["A001"],
        "record_ids": ["R000001"],
        "answer": "确认存在异常。记录R000001使用同一发票重复报销，违反第十条。",
        "citations": [
            {
                "doc_id": "01_expense_reimbursement_2025.md",
                "clause_no": "第十条",
            }
        ],
    }


def valid_evidence() -> dict[str, object]:
    citation = {
        "doc_id": "01_expense_reimbursement_2025.md",
        "clause_no": "第十条",
    }
    return {
        "status": "pass",
        "coverage_percent": 100,
        "evidence_rows": [
            {
                "anomaly_id": "A001",
                "record_ids": ["R000001"],
                "citations": [citation],
                "facts": ["R000001 is a verified expense record."],
                "fact_supported": True,
                "rule_supported": True,
                "coverage_status": "pass",
            }
        ],
        "candidate_record_ids": ["R000001"],
        "submitted_record_ids": ["R000001"],
        "unowned_record_ids": [],
        "unused_candidate_record_ids": [],
        "unused_citations": [],
        "missing_evidence": [],
        "no_anomaly_coverage": {},
        "reconciled_figures": {},
        "unresolved_items": [],
    }


def valid_validation_report(repair_count: int = 0) -> dict[str, object]:
    return {
        "status": "pass",
        "errors": [],
        "warnings": [],
        "field_checks": {"status": "pass"},
        "id_checks": {"status": "pass"},
        "evidence_checks": {"status": "pass"},
        "answer_consistency_checks": {"status": "pass"},
        "repair_count": repair_count,
        "repairable_fields": [],
        "submission_allowed": True,
    }


class SubmissionValidationTests(unittest.TestCase):
    def test_valid_submission_uses_public_business_assets_only(self) -> None:
        report = validate_submission(
            result=valid_result(),
            expense_db=DB_PATH,
            policy_corpus_dir=CORPUS_PATH,
            evidence_matrix=valid_evidence(),
            validation_report=valid_validation_report(),
        )
        self.assertTrue(report["valid"], report["errors"])
        self.assertFalse(report["checks"]["hidden_answer_mapping_used"])

    def test_public_dataset_anomaly_id_formats_are_not_rejected(self) -> None:
        result = valid_result()
        result["anomaly_ids"] = ["DUP-002"]
        evidence = valid_evidence()
        evidence["evidence_rows"][0]["anomaly_id"] = "DUP-002"
        report = validate_submission(
            result=result,
            expense_db=DB_PATH,
            policy_corpus_dir=CORPUS_PATH,
            evidence_matrix=evidence,
            validation_report=valid_validation_report(),
        )
        self.assertTrue(report["valid"], report["errors"])

    def test_common_evidence_aliases_are_normalized_before_submission(self) -> None:
        evidence = valid_evidence()
        evidence["coverage"] = evidence.pop("coverage_percent")
        evidence["submitted_records"] = evidence.pop("submitted_record_ids")
        evidence["unowned_records"] = evidence.pop("unowned_record_ids")
        evidence["unused_candidates"] = evidence.pop("unused_candidate_record_ids")
        row = evidence["evidence_rows"][0]
        row.pop("fact_supported")
        row.pop("rule_supported")
        row.pop("coverage_status")
        validation = valid_validation_report()
        validation["submission_permission"] = validation.pop("submission_allowed")
        report = validate_submission(
            result=valid_result(),
            expense_db=DB_PATH,
            policy_corpus_dir=CORPUS_PATH,
            evidence_matrix=evidence,
            validation_report=validation,
        )
        self.assertTrue(report["valid"], report["errors"])

    def test_no_anomaly_search_proof_is_normalized(self) -> None:
        result = valid_result()
        result["anomaly_ids"] = []
        result["answer"] = "已核查目标记录，未发现异常。"
        evidence = valid_evidence()
        evidence["evidence_rows"][0].pop("anomaly_id")
        evidence["record_ids"] = evidence.pop("submitted_record_ids")
        evidence.pop("no_anomaly_coverage")
        evidence["search_proof"] = "Scanned the complete target population and checked the applicable rule."

        report = validate_submission(
            result=result,
            expense_db=DB_PATH,
            policy_corpus_dir=CORPUS_PATH,
            evidence_matrix=evidence,
            validation_report=valid_validation_report(),
        )

        self.assertTrue(report["valid"], report["errors"])

    def test_unknown_ids_clause_and_evidence_gap_are_rejected(self) -> None:
        result = valid_result()
        result["record_ids"] = ["R999999"]
        result["citations"] = [
            {
                "doc_id": "01_expense_reimbursement_2025.md",
                "clause_no": "第九十九条",
            }
        ]
        evidence = valid_evidence()
        evidence["coverage_percent"] = 80
        evidence["missing_evidence"] = ["missing record support"]
        report = validate_submission(
            result=result,
            expense_db=DB_PATH,
            policy_corpus_dir=CORPUS_PATH,
            evidence_matrix=evidence,
            validation_report=valid_validation_report(),
        )
        codes = {item["code"] for item in report["errors"]}
        self.assertIn("UNKNOWN_RECORD_ID", codes)
        self.assertIn("UNKNOWN_POLICY_CLAUSE", codes)
        self.assertIn("EVIDENCE_NOT_PASSED", codes)
        self.assertIn("EVIDENCE_GAP", codes)

    def test_anomaly_requires_record_citation_and_fact(self) -> None:
        result = valid_result()
        result["record_ids"] = []
        result["citations"] = []
        evidence = valid_evidence()
        evidence["submitted_record_ids"] = []
        evidence["evidence_rows"][0]["record_ids"] = []
        evidence["evidence_rows"][0]["citations"] = []
        evidence["evidence_rows"][0]["facts"] = []
        report = validate_submission(
            result=result,
            expense_db=DB_PATH,
            policy_corpus_dir=CORPUS_PATH,
            evidence_matrix=evidence,
            validation_report=valid_validation_report(),
        )
        codes = {item["code"] for item in report["errors"]}
        self.assertIn("MISSING_FINDING_RECORD", codes)
        self.assertIn("MISSING_FINDING_CITATION", codes)
        self.assertIn("MISSING_FINDING_FACT", codes)

    def test_one_repair_can_be_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            work_dir = Path(temp)
            write_json(work_dir / "work/evidence_matrix.json", valid_evidence())
            write_json(work_dir / "work/validation_report.json", valid_validation_report())
            bad = valid_result()
            bad["record_ids"] = ["R999999"]
            first = submit_result(
                work_dir=work_dir,
                task_id="repair-task",
                expense_db=DB_PATH,
                policy_corpus_dir=CORPUS_PATH,
                result=bad,
            )
            self.assertEqual(first["status"], "repair_required")
            write_json(work_dir / "work/validation_report.json", valid_validation_report(1))
            second = submit_result(
                work_dir=work_dir,
                task_id="repair-task",
                expense_db=DB_PATH,
                policy_corpus_dir=CORPUS_PATH,
                result=valid_result(),
            )
            self.assertEqual(second["status"], "accepted")
            self.assertEqual(json.loads((work_dir / "final_submission.json").read_text(encoding="utf-8")), valid_result())

    def test_second_failed_attempt_is_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            work_dir = Path(temp)
            write_json(work_dir / "work/evidence_matrix.json", valid_evidence())
            write_json(work_dir / "work/validation_report.json", valid_validation_report())
            bad = valid_result()
            bad["record_ids"] = ["R999999"]
            first = submit_result(
                work_dir=work_dir,
                task_id="terminal-task",
                expense_db=DB_PATH,
                policy_corpus_dir=CORPUS_PATH,
                result=bad,
            )
            second = submit_result(
                work_dir=work_dir,
                task_id="terminal-task",
                expense_db=DB_PATH,
                policy_corpus_dir=CORPUS_PATH,
                result=bad,
            )
            self.assertEqual(first["status"], "repair_required")
            self.assertEqual(second["status"], "rejected")
            self.assertFalse((work_dir / "final_submission.json").exists())


class SubagentRoutingTests(unittest.TestCase):
    def authorize(self, work_dir: Path, **overrides: object) -> dict[str, object]:
        values: dict[str, object] = {
            "work_dir": work_dir,
            "task_id": "routing-task",
            "routing_rules_path": ROUTING_PATH,
            "role": "policy_researcher",
            "reason_code": "MULTI_POLICY_VERSION_CHECK",
            "complexity": 3,
            "context": {"question": "Which policy version applies?"},
            "artifact_paths": [],
            "requested_token_budget": 6000,
        }
        values.update(overrides)
        return authorize_subagent(**values)

    def test_complexity_and_role_call_limits(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            work_dir = Path(temp)
            low = self.authorize(work_dir, complexity=1)
            self.assertEqual(low["code"], "COMPLEXITY_TOO_LOW")
            first = self.authorize(work_dir)
            self.assertTrue(first["authorized"])
            duplicate = self.authorize(work_dir)
            self.assertEqual(duplicate["code"], "ROLE_CALL_LIMIT")
            data = self.authorize(
                work_dir,
                role="data_analyst",
                reason_code="AGGREGATION_REQUIRED",
            )
            self.assertEqual(data["code"], "COMPLEXITY_ROLE_LIMIT")

    def test_reviewer_requires_evidence_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            work_dir = Path(temp)
            missing = self.authorize(
                work_dir,
                role="independent_reviewer",
                reason_code="NO_ANOMALY_RECHECK",
                artifact_paths=[],
            )
            self.assertEqual(missing["code"], "INVALID_ARTIFACT_PATH")
            write_json(work_dir / "work/evidence_matrix.json", valid_evidence())
            allowed = self.authorize(
                work_dir,
                role="independent_reviewer",
                reason_code="NO_ANOMALY_RECHECK",
                artifact_paths=["work/evidence_matrix.json"],
            )
            self.assertTrue(allowed["authorized"])

    def test_role_token_budget_is_capped(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = self.authorize(
                Path(temp),
                role="data_analyst",
                reason_code="AGGREGATION_REQUIRED",
                requested_token_budget=8000,
            )
            self.assertTrue(result["authorized"])
            self.assertEqual(result["token_budget"], 5000)

    def test_forbidden_or_oversized_context_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            work_dir = Path(temp)
            forbidden = self.authorize(work_dir, context={"path": "data/ground_truth.yaml"})
            self.assertEqual(forbidden["code"], "FORBIDDEN_CONTEXT")
            oversized = self.authorize(work_dir, context={"question": "x" * 17000})
            self.assertEqual(oversized["code"], "CONTEXT_TOO_LARGE")

    def test_invalid_reason_returns_role_options_and_caps_retries(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            work_dir = Path(temp)
            first = self.authorize(work_dir, reason_code="analysis")
            self.assertEqual(first["code"], "INVALID_REASON_CODE")
            self.assertTrue(first["retryable"])
            self.assertIn("MULTI_POLICY_VERSION_CHECK", first["allowed_reason_codes"])

            second = self.authorize(work_dir, reason_code="policy_review")
            self.assertEqual(second["code"], "INVALID_REASON_CODE")
            self.assertFalse(second["retryable"])

            third = self.authorize(work_dir, reason_code="compliance")
            self.assertEqual(third["code"], "ROLE_REJECTION_LIMIT")
            self.assertFalse(third["retryable"])

    def test_authorized_subagent_requires_valid_completion_before_submission(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            work_dir = Path(temp)
            write_json(work_dir / "work/evidence_matrix.json", valid_evidence())
            write_json(work_dir / "work/validation_report.json", valid_validation_report())
            authorization = self.authorize(work_dir)
            blocked = submit_result(
                work_dir=work_dir,
                task_id="routing-task",
                expense_db=DB_PATH,
                policy_corpus_dir=CORPUS_PATH,
                result=valid_result(),
            )
            self.assertEqual(blocked["code"], "SUBAGENT_COMPLETION_REQUIRED")

            role_dir = work_dir / "work/subagents/policy_researcher"
            role_dir.mkdir(parents=True, exist_ok=True)
            write_json(role_dir / "summary.json", {
                "decision": "pass",
                "key_findings": ["第十条适用"],
                "record_ids": ["R000001"],
                "citations": [{
                    "doc_id": "01_expense_reimbursement_2025.md",
                    "clause_no": "第十条",
                }],
                "unresolved_items": [],
                "artifact_paths": ["work/subagents/policy_researcher/policy_applicability.json"],
            })
            write_json(role_dir / "policy_applicability.json", {"status": "pass"})
            completion = complete_subagent(
                work_dir=work_dir,
                task_id="routing-task",
                invocation_id=authorization["invocation_id"],
                summary_path="work/subagents/policy_researcher/summary.json",
                token_usage={"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
            )
            self.assertTrue(completion["completed"], completion)
            accepted = submit_result(
                work_dir=work_dir,
                task_id="routing-task",
                expense_db=DB_PATH,
                policy_corpus_dir=CORPUS_PATH,
                result=valid_result(),
            )
            self.assertEqual(accepted["status"], "accepted")
            events = [
                json.loads(line)
                for line in (work_dir / "traces/events.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertIn("subagent_completed", {event["event_type"] for event in events})

    def test_context_checkpoint_requires_recoverable_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            work_dir = Path(temp)
            initialize_task_state(work_dir=work_dir, task_id="checkpoint-task")
            incomplete = checkpoint_context(
                work_dir=work_dir,
                task_id="checkpoint-task",
                stage="planning_completed",
                context_usage_percent=60,
                retained_state={"task": "test"},
            )
            self.assertEqual(incomplete["code"], "INCOMPLETE_RETAINED_STATE")
            retained = {
                "task": "test",
                "constraints": [],
                "audit_plan": {},
                "applicable_policies": [],
                "record_ids": [],
                "evidence_status": "pending",
                "unresolved_items": [],
                "artifact_index": [],
                "remaining_budget": {},
                "submission_status": "not_submitted",
            }
            accepted = checkpoint_context(
                work_dir=work_dir,
                task_id="checkpoint-task",
                stage="planning_completed",
                context_usage_percent=76,
                retained_state=retained,
                compacted=True,
            )
            self.assertTrue(accepted["accepted"])
            state = json.loads((work_dir / ".audit-control/state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["context"]["compaction_count"], 1)

    def test_parallel_first_calls_initialize_workspace_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            work_dir = Path(temp)

            def initialize(_: int) -> str:
                return initialize_task_state(
                    work_dir=work_dir,
                    task_id="parallel-init-task",
                    framework="test",
                    experiment_group="enhanced",
                )["task_id"]

            with ThreadPoolExecutor(max_workers=8) as executor:
                task_ids = list(executor.map(initialize, range(24)))

            self.assertEqual(set(task_ids), {"parallel-init-task"})
            for path in (work_dir / ".audit-control" / "state.json", *(work_dir / "work").glob("*.json")):
                with self.subTest(path=path):
                    json.loads(path.read_text(encoding="utf-8"))


class PackagingTests(unittest.TestCase):
    def test_build_produces_six_identical_skill_sets(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(DOMAIN / "build_adapters.py")],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual([item["skill_count"] for item in payload["adapters"]], [7, 7, 7, 7, 7, 7])
        manifests = []
        for adapter in ("claude-code-best", "codex", "openclaude", "opencode", "oh-my-pi", "pi-agent"):
            path = DOMAIN / "adapters" / adapter / "securities-expense-audit" / "build_manifest.json"
            manifests.append(json.loads(path.read_text(encoding="utf-8"))["canonical_skill_hashes"])
        self.assertEqual(manifests[0], manifests[1])

    def test_all_schemas_and_manifests_parse(self) -> None:
        paths = list((DOMAIN / "shared-audit-core" / "schemas").glob("*.json"))
        paths += [
            DOMAIN / "adapters" / "claude-code-best" / "securities-expense-audit" / ".claude-plugin" / "plugin.json",
            DOMAIN / "adapters" / "codex" / "securities-expense-audit" / ".codex-plugin" / "plugin.json",
            DOMAIN / "adapters" / "openclaude" / "securities-expense-audit" / ".claude-plugin" / "plugin.json",
            DOMAIN / "adapters" / "opencode" / "securities-expense-audit" / "opencode.fragment.json",
        ]
        self.assertGreaterEqual(len(paths), 10)
        for path in paths:
            with self.subTest(path=path):
                json.loads(path.read_text(encoding="utf-8"))

    def test_all_six_adapters_publish_governance_tools(self) -> None:
        expected = {
            "authorize_audit_subagent",
            "complete_audit_subagent",
            "checkpoint_audit_context",
            "validate_audit_result",
            "submit_audit_result",
        }
        for adapter in ("claude-code-best", "codex", "openclaude", "opencode", "oh-my-pi", "pi-agent"):
            module_path = (
                DOMAIN
                / "adapters"
                / adapter
                / "securities-expense-audit"
                / "shared"
                / "control-mcp"
                / "audit_control_mcp.py"
            )
            spec = importlib.util.spec_from_file_location(f"audit_control_{adapter}", module_path)
            module = importlib.util.module_from_spec(spec)
            assert spec and spec.loader
            spec.loader.exec_module(module)
            response = module.handle_rpc({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
            names = {item["name"] for item in response["result"]["tools"]}
            self.assertEqual(names, expected, adapter)

    def test_control_mcp_lists_common_tools(self) -> None:
        module_path = DOMAIN / "control-mcp" / "audit_control_mcp.py"
        spec = importlib.util.spec_from_file_location("audit_control_mcp", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        response = module.handle_rpc({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        names = [item["name"] for item in response["result"]["tools"]]
        self.assertEqual(
            names,
            [
                "authorize_audit_subagent",
                "complete_audit_subagent",
                "checkpoint_audit_context",
                "validate_audit_result",
                "submit_audit_result",
            ],
        )

    def test_authorize_tool_schema_exposes_fixed_routing_contract(self) -> None:
        module_path = DOMAIN / "control-mcp" / "audit_control_mcp.py"
        spec = importlib.util.spec_from_file_location("audit_control_mcp_schema", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        response = module.handle_rpc({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        tool = next(
            item
            for item in response["result"]["tools"]
            if item["name"] == "authorize_audit_subagent"
        )
        schema = tool["inputSchema"]
        self.assertEqual(schema["required"], ["role", "reason_code", "complexity"])
        self.assertIn("MULTI_POLICY_VERSION_CHECK", schema["properties"]["reason_code"]["enum"])
        self.assertIn("NO_ANOMALY_RECHECK", schema["properties"]["reason_code"]["enum"])
        self.assertNotIn("reason", schema["properties"])
        self.assertNotIn("subagent_type", schema["properties"])

    def test_baseline_control_mcp_hides_subagent_tool(self) -> None:
        module_path = DOMAIN / "control-mcp" / "audit_control_mcp.py"
        spec = importlib.util.spec_from_file_location("audit_control_mcp_baseline", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        with mock.patch.dict(os.environ, {"AUDIT_SUBAGENTS_ENABLED": "0"}):
            response = module.handle_rpc({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        names = [item["name"] for item in response["result"]["tools"]]
        self.assertEqual(names, ["checkpoint_audit_context", "validate_audit_result", "submit_audit_result"])

    def test_control_mcp_recovers_subagent_aliases_from_written_plan(self) -> None:
        module_path = DOMAIN / "control-mcp" / "audit_control_mcp.py"
        spec = importlib.util.spec_from_file_location("audit_control_mcp_aliases", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            work_dir = Path(temp)
            write_json(
                work_dir / "work/audit_plan.json",
                {
                    "complexity": 4,
                    "subagent_plan": {
                        "data_analyst": {
                            "reason_code": "AGGREGATION_REQUIRED",
                            "role_task": "Reconcile the complete expense population.",
                        }
                    },
                },
            )
            with mock.patch.dict(
                os.environ,
                {"AUDIT_WORK_DIR": str(work_dir), "AUDIT_TASK_ID": "alias-task"},
            ):
                result = module.authorize_audit_subagent(
                    subagent_type="data_analyst",
                    task_summary="Full population audit",
                    allowed_tools=["Read", "Write"],
                    budget="sufficient",
                )
        self.assertTrue(result["authorized"])
        self.assertEqual(result["reason_code"], "AGGREGATION_REQUIRED")
        self.assertEqual(result["token_budget"], 5000)


class DevelopmentDatasetTests(unittest.TestCase):
    def test_development_dataset_is_isolated_from_formal_records(self) -> None:
        dev_dir = ROOT / "data" / "development"
        subprocess.run([sys.executable, str(dev_dir / "build_dev_dataset.py")], cwd=ROOT, check=True, capture_output=True)
        tasks = json.loads((dev_dir / "evals.json").read_text(encoding="utf-8"))
        truth = json.loads((dev_dir / "ground_truth.json").read_text(encoding="utf-8"))
        self.assertEqual(len(tasks), 12)
        self.assertEqual({task["id"] for task in tasks}, set(truth))
        with sqlite3.connect(dev_dir / "expense_dev.db") as connection:
            dev_ids = {row[0] for row in connection.execute("SELECT record_id FROM expense_records")}
            year_end_dates = connection.execute(
                "SELECT expense_date, reimburse_date FROM expense_records WHERE record_id='R900012'"
            ).fetchone()
        with sqlite3.connect(DB_PATH) as connection:
            formal_overlap = connection.execute(
                "SELECT COUNT(*) FROM expense_records WHERE record_id LIKE 'R900%'"
            ).fetchone()[0]
        self.assertEqual(formal_overlap, 0)
        self.assertEqual(len(dev_ids), 21)
        self.assertTrue(all(record_id.startswith("R900") for record_id in dev_ids))
        self.assertEqual(year_end_dates, ("2025-12-20", "2026-01-10"))


if __name__ == "__main__":
    unittest.main()
