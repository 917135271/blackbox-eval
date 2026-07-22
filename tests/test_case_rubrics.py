from __future__ import annotations

import importlib.util
import json
import os
import re
import sqlite3
import subprocess
import sys
import unittest
from collections import Counter
from pathlib import Path

import yaml
import jsonschema


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "data" / "formal_case_rubric" / "build_formal_dataset.py"
BUILD_DB = ROOT / "data" / "formal_case_rubric" / "build_formal_db.py"
CASES = ROOT / "data" / "formal_case_rubric" / "cases.json"
EVALS = ROOT / "data" / "formal_case_rubric" / "evals.json"
VALIDATOR = ROOT / "runner" / "validate_case_rubrics.py"
SCHEMA = ROOT / "schemas" / "case-rubric.schema.json"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_case_rubrics", VALIDATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CaseRubricTests(unittest.TestCase):
    def test_dataset_matches_v7_json_schema(self) -> None:
        jsonschema.validate(
            json.loads(CASES.read_text(encoding="utf-8")),
            json.loads(SCHEMA.read_text(encoding="utf-8")),
        )

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

    def test_every_formal_case_has_a_valid_equal_weight_checklist(self) -> None:
        report = load_validator().validate(CASES, EVALS)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["case_count"], 15)
        self.assertGreaterEqual(report["checklist_item_count"], 75)
        self.assertEqual(
            report["semantic_recomputation"],
            {
                "duplicate_findings": 6,
                "split_findings": 6,
                "direct_overstandard_findings": 6,
                "budget_findings": 6,
                "overdue_findings": 6,
            },
        )

    def test_every_rubric_is_a_strict_binary_checklist(self) -> None:
        dataset = json.loads(CASES.read_text(encoding="utf-8"))
        for case in dataset["cases"]:
            rubric = case["rubric"]
            self.assertEqual(dataset["rubric_version"], "atomic-binary-checklist-v7")
            self.assertEqual(rubric["scoring_method"], "binary_checklist")
            self.assertEqual(rubric["item_result_values"], [0, 1])
            self.assertEqual(rubric["normalization"], "equal_item_ratio")
            self.assertNotIn("max_score", rubric)
            self.assertNotIn("pass_score", rubric)
            for item in rubric["checklist"]:
                self.assertNotIn("anchors", item)
                self.assertNotIn("weight", item)
                self.assertNotIn("points", item)
                self.assertNotIn("score", item)
                self.assertNotIn("required_for_case_pass", item)
                self.assertTrue(item["pass_condition"])
                self.assertTrue(item["fail_condition"])

    def test_checklists_are_bounded_and_batch_precision_recall_are_balanced(self) -> None:
        dataset = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertEqual(
            sum(len(case["rubric"]["checklist"]) for case in dataset["cases"]),
            251,
        )
        for case in dataset["cases"]:
            item_ids = {item["id"] for item in case["rubric"]["checklist"]}
            self.assertIn("submission", item_ids, case["id"])
            self.assertLessEqual(len(item_ids), 30, case["id"])
            self.assertFalse(
                any(
                    item.get("deterministic_rule") == "record-ids-unique"
                    for item in case["rubric"]["checklist"]
                ),
                case["id"],
            )
            if case["case_family"] == "full_year_audit" or case["id"] == "L3-009":
                self.assertTrue(all(not item_id.startswith("all-record-ids-include-") for item_id in item_ids), case["id"])
                for prefix in ("record-recall", "record-precision", "finding-recall", "finding-precision"):
                    self.assertTrue({f"{prefix}-50", f"{prefix}-80", f"{prefix}-100"} <= item_ids, case["id"])

    def test_comprehensive_case_requires_complete_record_evidence(self) -> None:
        dataset = json.loads(CASES.read_text(encoding="utf-8"))
        case = next(item for item in dataset["cases"] if item["id"] == "L3-009")
        self.assertEqual(len(case["expected_output"]["expected_record_ids"]), 44)
        self.assertEqual(len(case["rubric"]["checklist"]), 27)
        item_ids = {item["id"] for item in case["rubric"]["checklist"]}
        self.assertFalse(any(item_id.startswith("all-record-ids-include-") for item_id in item_ids))
        self.assertIn("clean-boundary-control", item_ids)
        for rule_type in ("dup", "split", "overstd", "budget", "overdue"):
            self.assertIn(f"representative-evidence-{rule_type}", item_ids)

    def test_full_year_methods_are_case_specific_atomic_checks(self) -> None:
        dataset = json.loads(CASES.read_text(encoding="utf-8"))
        cases = {case["id"]: case for case in dataset["cases"]}
        expected_ids = {
            "L3-001": {"full-scan-method-scope", "full-scan-method-invoice-key", "full-scan-method-grouping", "full-scan-method-reconcile"},
            "L3-003": {"full-scan-method-office", "full-scan-method-communication", "full-scan-method-training", "full-scan-method-entertainment", "full-scan-method-travel", "full-scan-method-transport", "full-scan-method-approval"},
            "L3-004": {"full-scan-method-grouping", "full-scan-method-ordering", "full-scan-method-cumulative", "full-scan-method-crossing"},
        }
        for case_id, required in expected_ids.items():
            actual = {item["id"] for item in cases[case_id]["rubric"]["checklist"]}
            self.assertTrue(required <= actual, case_id)

    def test_clean_cases_use_one_nonduplicative_process_check(self) -> None:
        dataset = json.loads(CASES.read_text(encoding="utf-8"))
        for case in dataset["cases"]:
            if case["case_family"] != "clean_trap":
                continue
            item_ids = {item["id"] for item in case["rubric"]["checklist"]}
            self.assertFalse(any(item_id.startswith("reverse-check-") for item_id in item_ids))
            self.assertIn("independent-verification", item_ids)
            process = next(item for item in case["rubric"]["checklist"] if item["id"] == "independent-verification")
            self.assertNotIn("final_answer", process["evidence_sources"])

    def test_formal_database_is_current_and_has_no_answer_labels(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(BUILD_DB), "--check"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_formal_database_exposes_business_code_mappings(self) -> None:
        with sqlite3.connect(ROOT / "data" / "formal_case_rubric" / "expense_formal.db") as connection:
            mappings = dict(
                connection.execute(
                    "SELECT code, display_name FROM business_codebook WHERE field_name = 'employee_level'"
                )
            )
        self.assertEqual(
            mappings,
            {"E1": "员工级", "M1": "经理级", "D1": "部门负责人级", "X1": "高管级"},
        )

    def test_positive_and_clean_record_prompts_are_neutral_and_matched(self) -> None:
        dataset = json.loads(CASES.read_text(encoding="utf-8"))
        cases = {case["id"]: case for case in dataset["cases"]}
        for case_id in (
            "PV-CASE-001",
            "RA-CASE-001",
            "RA-CASE-002",
            "RR-CASE-001",
            "L2-013",
            "TRAP-002",
            "TRAP-003",
            "TRAP-005",
        ):
            case = cases[case_id]
            prompt = case["prompt"]
            exposed = [record_id for record_id in case["expected_output"]["expected_record_ids"] if record_id in prompt]
            self.assertEqual(len(exposed), 1, case_id)
            self.assertNotIn("若不构成异常", prompt)
            self.assertNotIn("必须核对", prompt)
            self.assertNotRegex(prompt, r"重复报销异常|拆分报销异常|超标准异常")

    def test_rubrics_do_not_expose_or_require_internal_anomaly_labels(self) -> None:
        dataset = json.loads(CASES.read_text(encoding="utf-8"))
        hidden_label = re.compile(r"\b(?:DUP|SPLIT|OVERSTD|BUDGET|OVERDUE)-\d{3}\b")
        for case in dataset["cases"]:
            if "expected_anomaly_ids" in case["expected_output"]:
                self.assertEqual(case["expected_output"]["expected_anomaly_ids"], [])
            for criterion in case["rubric"]["checklist"]:
                self.assertIsNone(
                    hidden_label.search(json.dumps(criterion, ensure_ascii=False)),
                    f"{case['id']}/{criterion['id']}",
                )

    def test_formal_policy_references_use_real_documents_and_clauses(self) -> None:
        dataset = json.loads(CASES.read_text(encoding="utf-8"))
        legacy_ref = re.compile(r"(?:费用报销管理办法-6\.[1-4]|预算管理办法-4\.1)")
        for case in dataset["cases"]:
            refs = case["ground_truth_refs"]
            self.assertFalse(any(legacy_ref.search(ref) for ref in refs), case["id"])
            for citation in case["expected_output"].get("required_citations", []):
                doc_id = citation["doc_id"]
                clause_no = citation["clause_no"]
                self.assertIn(f"document:{doc_id}", refs, case["id"])
                self.assertIn(f"clause:{doc_id}#{clause_no}", refs, case["id"])

    def test_split_threshold_is_unambiguous_in_candidate_visible_policy(self) -> None:
        policy = (ROOT / "data" / "corpus" / "01_expense_reimbursement_2025.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("附件二所列部门总经理审批线", policy)

    def test_every_required_citation_is_represented_in_the_case_rubric(self) -> None:
        dataset = json.loads(CASES.read_text(encoding="utf-8"))
        for case in dataset["cases"]:
            rubric_text = json.dumps(case["rubric"]["checklist"], ensure_ascii=False)
            for citation in case["expected_output"].get("required_citations", []):
                self.assertIn(citation["doc_id"], rubric_text, case["id"])

    def test_comprehensive_expectations_are_derived_from_ground_truth(self) -> None:
        dataset = json.loads(CASES.read_text(encoding="utf-8"))
        case = next(item for item in dataset["cases"] if item["id"] == "L3-009")
        ground_truth = yaml.safe_load(
            (ROOT / "data" / "ground_truth.yaml").read_text(encoding="utf-8")
        )
        source_task = next(
            item
            for item in json.loads((ROOT / "data" / "evals.json").read_text(encoding="utf-8"))
            if item["id"] == "L3-009"
        )
        selected_anomaly_ids = [
            str(ref).removeprefix("ground_truth:")
            for ref in source_task["ground_truth_refs"]
            if str(ref).startswith("ground_truth:")
        ]
        expected = case["expected_output"]
        anomaly_types = list(
            dict.fromkeys(
                anomaly_id.split("-", 1)[0] for anomaly_id in selected_anomaly_ids
            )
        )
        excluded_records = list(
            dict.fromkeys(
                str(record_id)
                for trap in ground_truth["traps"]
                for record_id in trap["record_ids"]
            )
        )
        self.assertEqual(expected["expected_anomaly_count"], len(selected_anomaly_ids))
        self.assertEqual(expected["expected_rule_types"], anomaly_types)
        self.assertEqual(
            expected["expected_findings_by_type"],
            dict(Counter(anomaly_id.split("-", 1)[0] for anomaly_id in selected_anomaly_ids)),
        )
        self.assertEqual(expected["excluded_record_ids"], excluded_records)

    def test_trap_facts_are_explicit_and_reproducible(self) -> None:
        dataset = json.loads(CASES.read_text(encoding="utf-8"))
        cases = {case["id"]: case for case in dataset["cases"]}
        trap_003_ids = {item["id"] for item in cases["TRAP-003"]["rubric"]["checklist"]}
        trap_005_ids = {item["id"] for item in cases["TRAP-005"]["rubric"]["checklist"]}
        self.assertIn("case-specific-reason-sum", trap_003_ids)
        self.assertIn("case-specific-reason-threshold", trap_003_ids)
        self.assertIn("case-specific-reason-business-context", trap_005_ids)
        self.assertIn("independent-verification", trap_005_ids)
        self.assertTrue(
            any(
                citation["doc_id"] == "06_business_entertainment.md"
                and "第四条" in citation["clause_no"]
                for citation in cases["TRAP-005"]["expected_output"]["required_citations"]
            )
        )

    def test_full_year_rubrics_preserve_finding_record_mapping(self) -> None:
        dataset = json.loads(CASES.read_text(encoding="utf-8"))
        cases = {case["id"]: case for case in dataset["cases"]}
        for case_id in ("L3-001", "L3-003", "L3-004"):
            expected_groups = cases[case_id]["expected_output"]["expected_finding_groups"]
            mapping_ids = {
                item["id"]
                for item in cases[case_id]["rubric"]["checklist"]
                if item["id"] == "finding-record-mapping-sample"
            }
            self.assertTrue(expected_groups, case_id)
            self.assertEqual(mapping_ids, {"finding-record-mapping-sample"}, case_id)

    def test_material_false_positives_have_score_caps(self) -> None:
        dataset = json.loads(CASES.read_text(encoding="utf-8"))
        for case in dataset["cases"]:
            failures = case["rubric"].get("critical_failures", [])
            rules = {failure["deterministic_rule"] for failure in failures}
            if case["expected_output"].get("scoring_kind") == "no_anomaly":
                self.assertIn("unexpected-anomaly-reported", rules, case["id"])
            if case["case_family"] == "full_year_audit" or case["id"] == "L3-009":
                self.assertIn("record-precision-below", rules, case["id"])
                self.assertIn("anomaly-precision-below", rules, case["id"])

    def test_policy_pass_conditions_do_not_render_python_dicts(self) -> None:
        dataset = json.loads(CASES.read_text(encoding="utf-8"))
        for case in dataset["cases"]:
            for criterion in case["rubric"]["checklist"]:
                self.assertNotIn("准确引用{", criterion["pass_condition"], f"{case['id']}/{criterion['id']}")

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

    def test_zero_discrimination_cases_are_replaced_with_new_business_cases(self) -> None:
        dataset = json.loads(CASES.read_text(encoding="utf-8"))
        cases = {case["id"]: case for case in dataset["cases"]}
        replacements = {
            "L1-001": "PV-CASE-001",
            "L2-003": "RA-CASE-001",
            "L2-008": "RA-CASE-002",
            "L3-010": "RR-CASE-001",
        }
        self.assertEqual(dataset["replacements"], replacements)
        self.assertFalse(set(replacements) & set(cases))
        self.assertTrue(set(replacements.values()) <= set(cases))
        for old_id, new_id in replacements.items():
            self.assertEqual(cases[new_id]["replaces"], old_id)
        self.assertEqual(cases["PV-CASE-001"]["expected_output"]["expected_record_ids"], ["R004233"])
        self.assertEqual(
            cases["RA-CASE-001"]["expected_output"]["expected_record_ids"],
            ["R000028", "R004204"],
        )
        self.assertEqual(
            cases["RA-CASE-002"]["expected_output"]["expected_record_ids"],
            ["R004209", "R004210", "R004211"],
        )
        self.assertEqual(
            cases["RR-CASE-001"]["expected_output"]["expected_record_ids"],
            ["R000465", "R000561", "R000888", "R001354"],
        )


if __name__ == "__main__":
    unittest.main()
