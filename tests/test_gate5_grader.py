from __future__ import annotations

import importlib.util
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


def test_trap_false_positive_is_machine_capped() -> None:
    case = {
        "case_family": "clean_trap",
        "expected_output": {
            "expected_anomaly_ids": [],
            "expected_record_ids": ["R1", "R2"],
        },
        "rubric": {
            "critical_failures": [
                {
                    "id": "trap-false-positive",
                    "condition": "false positive",
                    "score_cap": 30,
                }
            ]
        },
    }
    diagnostics = grader.deterministic_diagnostics(
        case,
        {
            "anomaly_ids": ["ANOM-001"],
            "record_ids": ["R1", "R2"],
            "answer": "存在异常",
            "citations": [],
        },
        {"status": "accepted"},
        {"timed_out": False},
        {"R1", "R2"},
    )
    failures = grader.machine_critical_failures(case, diagnostics)
    assert diagnostics["trap_false_positive"] is True
    assert failures[0]["id"] == "trap-false-positive"
    assert failures[0]["score_cap"] == 30


def test_unrelated_record_set_is_machine_capped() -> None:
    case = {
        "rubric": {
            "critical_failures": [
                {
                    "id": "fabricated-record-id",
                    "condition": "unrelated records",
                    "score_cap": 20,
                }
            ]
        }
    }
    diagnostics = {
        "unknown_record_ids": [],
        "actual_record_ids": ["R3", "R4"],
        "record_metrics": {"precision": 0.0, "extra_count": 2},
        "trap_false_positive": False,
        "trap_tokens_in_conclusion": [],
    }
    failures = grader.machine_critical_failures(case, diagnostics)
    assert failures[0]["id"] == "fabricated-record-id"
    assert failures[0]["score_cap"] == 20


def test_judge_overrides_machine_critical_failure() -> None:
    merged = grader.merge_critical_failures(
        [
            {
                "id": "fabricated-record-id",
                "triggered": True,
                "score_cap": 20,
                "source": "rule",
            }
        ],
        [
            {
                "id": "fabricated-record-id",
                "triggered": False,
                "score_cap": 20,
                "source": "llm_judge",
            }
        ],
    )
    assert merged[0]["triggered"] is False
    assert merged[0]["source"] == "llm_judge"


def test_only_failed_deterministic_criterion_needs_judge() -> None:
    criteria = [
        {"id": "record-set", "weight": 25, "evaluation_mode": "deterministic"},
        {"id": "submission", "weight": 5, "evaluation_mode": "deterministic"},
        {"id": "reasoning", "weight": 20, "evaluation_mode": "hybrid"},
    ]
    deterministic = {
        "record-set": {"id": "record-set", "score": 10, "source": "rule"},
        "submission": {"id": "submission", "score": 5, "source": "rule"},
    }
    selected = [
        criterion
        for criterion in criteria
        if criterion["evaluation_mode"] != "deterministic"
        or deterministic[criterion["id"]]["score"] < criterion["weight"]
    ]
    assert [item["id"] for item in selected] == ["record-set", "reasoning"]


def test_deterministic_submission_score() -> None:
    criterion = {
        "id": "submission",
        "weight": 5,
        "evaluation_mode": "deterministic",
    }
    result = grader.deterministic_criterion(
        criterion,
        {"submission_accepted": True, "schema_valid": True},
    )
    assert result is not None
    assert result["score"] == 5
