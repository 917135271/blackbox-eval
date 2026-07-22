from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "runner" / "grade_gate5_rubrics.py"
SPEC = importlib.util.spec_from_file_location("grade_gate5_rubrics", MODULE_PATH)
assert SPEC and SPEC.loader
grader = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(grader)


def test_set_metrics_exact_and_partial() -> None:
    exact = grader.set_metrics(["R1", "R2"], ["R2", "R1"])
    partial = grader.set_metrics(["R1", "R2"], ["R1", "R3"])
    assert exact["exact"] is True
    assert exact["f1"] == 1.0
    assert partial["precision"] == 0.5
    assert partial["recall"] == 0.5
    assert partial["f1"] == 0.5


def test_checklist_score_is_equal_item_pass_rate() -> None:
    passed, total, rate = grader.checklist_pass_rate(
        [{"value": 1}, {"value": 0}, {"value": 1}]
    )
    assert (passed, total, rate) == (2, 3, 66.667)


def test_grader_has_no_case_level_pass_decision() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert not hasattr(grader, "case_pass_decision")
    assert "pass_score" not in source
    assert "required_for_case_pass" not in source


def test_anomaly_ids_accept_framework_specific_prefixes() -> None:
    metrics = grader.anomaly_metrics(
        ["DUP-001", "DUP-002"],
        ["L3-001-DUP-001", "ANOM-REUSE-002"],
        "",
    )
    assert metrics["f1"] == 1.0
    assert metrics["count_exact"] is True


def test_generic_anomaly_id_infers_single_rule_from_answer() -> None:
    metrics = grader.anomaly_metrics(
        ["OVERSTD-001"],
        ["ANOM-001"],
        "该记录属于培训费超标准异常。",
    )
    assert metrics["f1"] == 1.0


def test_only_failed_deterministic_criterion_needs_judge() -> None:
    criteria = [
        {"id": "record-set", "evaluation_mode": "deterministic"},
        {"id": "submission", "evaluation_mode": "deterministic"},
        {"id": "reasoning", "evaluation_mode": "hybrid"},
    ]
    deterministic = {
        "record-set": {"id": "record-set", "value": 0, "source": "rule"},
        "submission": {"id": "submission", "value": 1, "source": "rule"},
    }
    selected = [
        criterion
        for criterion in criteria
        if criterion["evaluation_mode"] != "deterministic"
        or deterministic[criterion["id"]]["value"] == 0
    ]
    assert [item["id"] for item in selected] == ["record-set", "reasoning"]


def test_deterministic_submission_score() -> None:
    criterion = {
        "id": "submission",
        "evaluation_mode": "deterministic",
    }
    result = grader.deterministic_criterion(
        criterion,
        {"submission_accepted": True, "schema_valid": True},
    )
    assert result is not None
    assert result["value"] == 1
    assert "score" not in result


def test_finding_type_count_does_not_require_hidden_internal_id() -> None:
    criterion = {
        "id": "finding-type-count",
        "evaluation_mode": "deterministic",
    }
    result = grader.deterministic_criterion(
        criterion,
        {"anomaly_metrics": {"f1": 1.0}},
    )
    assert result is not None
    assert result["value"] == 1
    assert "score" not in result
    assert "不要求猜测隐藏内部编号" in result["reason"]


def test_comprehensive_report_excludes_clean_boundary_records() -> None:
    case = {
        "case_family": "retrieval_and_report",
        "expected_output": {
            "excluded_record_ids": ["R004233", "R004234"],
        },
        "rubric": {},
    }
    diagnostics = grader.deterministic_diagnostics(
        case,
        {
            "anomaly_ids": ["DUP-R004234"],
            "record_ids": ["R004234"],
            "answer": "重复报销异常",
            "citations": [],
        },
        {"status": "accepted"},
        {"timed_out": False},
        {"R004233", "R004234"},
    )
    criterion = {
        "id": "trap-control",
        "evaluation_mode": "deterministic",
    }
    score = grader.deterministic_criterion(criterion, diagnostics)
    assert score is not None
    assert score["value"] == 0
    assert "score" not in score
    assert diagnostics["excluded_record_ids_in_submission"] == ["R004234"]


def test_clean_case_extra_record_fails_no_unsupported_output() -> None:
    criterion = {
        "id": "no-unsupported-output",
        "evaluation_mode": "deterministic",
    }
    result = grader.deterministic_criterion(
        criterion,
        {
            "actual_anomaly_ids": [],
            "record_metrics": {"exact": False},
        },
    )
    assert result is not None
    assert result["value"] == 0
    assert "score" not in result


def test_gate5_groups_include_pi_agent() -> None:
    assert "pi-agent-baseline" in grader.GROUPS
    assert "pi-agent-enhanced" in grader.GROUPS
    assert len(grader.GROUPS) == 12


def test_judge_payload_has_no_legacy_policy_translation_table() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "POLICY_REFERENCE_GUIDANCE" not in source
    assert "policy_reference_guidance" not in source


def test_judge_rejects_partial_checklist_values() -> None:
    case = {
        "rubric": {
            "checklist": [
                {
                    "id": "fact-check",
                    "evaluation_mode": "llm",
                }
            ],
        }
    }
    try:
        grader.validate_judge_output(
            case,
            {"checklist": [{"id": "fact-check", "value": 0.5}]},
        )
    except ValueError as exc:
        assert "0 or 1" in str(exc)
    else:
        raise AssertionError("partial checklist value must be rejected")


def test_judge_accepts_single_criterion_root_object() -> None:
    rows, _, confidence, _ = grader.validate_judge_output(
        {"rubric": {"checklist": [{"id": "criterion-a"}]}},
        {"id": "criterion-a", "value": 1, "reason": "满足"},
        [{"id": "criterion-a"}],
    )
    assert rows == [
        {
            "id": "criterion-a",
            "value": 1,
            "reason": "满足",
            "answer_evidence": "",
            "trace_evidence": "",
            "source": "llm_judge",
        }
    ]
    assert confidence == 0.8


def test_atomic_record_checks_are_independent() -> None:
    diagnostics = {"actual_record_ids": ["R1", "R3"]}
    present = grader.deterministic_criterion(
        {
            "id": "records-include-r1",
            "evaluation_mode": "deterministic",
            "deterministic_rule": "expected-record-present",
            "expected": "R1",
        },
        diagnostics,
    )
    no_extra = grader.deterministic_criterion(
        {
            "id": "records-no-extra",
            "evaluation_mode": "deterministic",
            "deterministic_rule": "no-unexpected-records",
            "expected": ["R1", "R2"],
        },
        diagnostics,
    )
    assert present and present["value"] == 1
    assert no_extra and no_extra["value"] == 0


def test_record_ids_unique_check_rejects_duplicates() -> None:
    result = grader.deterministic_criterion(
        {
            "id": "records-unique",
            "evaluation_mode": "deterministic",
            "deterministic_rule": "record-ids-unique",
            "expected": "record_ids唯一",
        },
        {"actual_record_ids": ["R1", "R1"]},
    )
    assert result and result["value"] == 0


def test_atomic_anomaly_type_and_count_checks_are_independent() -> None:
    diagnostics = {
        "actual_anomaly_ids": ["DUP-A", "DUP-B"],
        "anomaly_metrics": {"actual_types": {"DUP": 2}},
    }
    rule_type = grader.deterministic_criterion(
        {
            "id": "finding-rule-type",
            "evaluation_mode": "deterministic",
            "deterministic_rule": "anomaly-rule-type-exact",
            "expected": "DUP",
        },
        diagnostics,
    )
    count = grader.deterministic_criterion(
        {
            "id": "finding-count",
            "evaluation_mode": "deterministic",
            "deterministic_rule": "anomaly-count-exact",
            "expected": 3,
        },
        diagnostics,
    )
    assert rule_type and rule_type["value"] == 1
    assert count and count["value"] == 0


def test_no_anomaly_ids_rule_is_binary() -> None:
    result = grader.deterministic_criterion(
        {
            "id": "no-anomaly-output",
            "evaluation_mode": "deterministic",
            "deterministic_rule": "no-anomaly-ids",
            "expected": {"anomaly_ids": []},
        },
        {"actual_anomaly_ids": []},
    )
    assert result and result["value"] == 1 and "score" not in result


def test_anomaly_type_count_rule_is_binary() -> None:
    criterion = {
        "id": "overall-count-type-dup",
        "evaluation_mode": "deterministic",
        "deterministic_rule": "anomaly-type-count-exact",
        "expected": {"rule_type": "DUP", "count": 2},
    }
    passed = grader.deterministic_criterion(
        criterion,
        {"anomaly_metrics": {"actual_types": {"DUP": 2, "SPLIT": 1}}},
    )
    failed = grader.deterministic_criterion(
        criterion,
        {"anomaly_metrics": {"actual_types": {"DUP": 1, "SPLIT": 1}}},
    )
    assert passed and passed["value"] == 1 and "score" not in passed
    assert failed and failed["value"] == 0 and "score" not in failed


def test_judge_batch_falls_back_to_single_criteria() -> None:
    class FakeJudge:
        model = "fake"

        def __init__(self) -> None:
            self.calls = 0

        def complete(self, messages):
            self.calls += 1
            payload = json.loads(messages[1]["content"])
            criteria = payload["case"]["checklist_to_judge"]
            checklist = []
            if len(criteria) == 1:
                checklist = [
                    {
                        "id": criteria[0]["id"],
                        "value": 1,
                        "reason": "满足",
                    }
                ]
            return (
                {"checklist": checklist, "confidence": 0.9},
                {"usage": {"total_tokens": 10}},
            )

    criteria = [
        {"id": "criterion-a", "pass_condition": "A"},
        {"id": "criterion-b", "pass_condition": "B"},
    ]
    judge = FakeJudge()
    rows, _, confidence, _, metadata = grader.judge_criteria_batch(
        judge,
        {
            "id": "CASE-1",
            "prompt": "test",
            "case_family": "test",
            "expected_output": {},
        },
        criteria,
        {},
        {},
        {},
        {},
        {},
    )
    assert [row["id"] for row in rows] == ["criterion-a", "criterion-b"]
    assert confidence == 0.9
    assert len(metadata) == 2
    assert judge.calls == 5
