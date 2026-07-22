from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "runner" / "report_gate5_results.py"
SPEC = importlib.util.spec_from_file_location("report_gate5_results", MODULE_PATH)
assert SPEC and SPEC.loader
report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(report)


def test_linear_lower_score() -> None:
    assert report.linear_lower_score(100, 180, 900) == 100
    assert report.linear_lower_score(900, 180, 900) == 0
    assert report.linear_lower_score(540, 180, 900) == 50


def test_display_group() -> None:
    assert report.display_group("ccb-enhanced") == "Claude Code Best 增强组"
    assert report.display_group("oh-my-pi-baseline") == "Oh My Pi 基线组"


def test_math_index() -> None:
    assert report.math_index(15, 0.95) == 14


def test_semantic_case_score_excludes_format() -> None:
    case = {
        "rubric": {
            "checklist": [
                {"id": "business", "metric": "conclusion"},
                {"id": "submission", "metric": "format"},
            ]
        }
    }
    grade = {
        "checklist": [
            {"id": "business", "value": 1},
            {"id": "submission", "value": 0},
        ],
    }
    assert report.semantic_case_score(grade, case) == 100


def test_evidence_metric_is_equal_item_pass_rate() -> None:
    case = {
        "rubric": {
            "checklist": [
                {"id": "policy-a", "metric": "policy"},
                {"id": "policy-b", "metric": "policy"},
                {"id": "conclusion", "metric": "conclusion"},
            ]
        }
    }
    grade = {
        "checklist": [
            {"id": "policy-a", "value": 1},
            {"id": "policy-b", "value": 0},
            {"id": "conclusion", "value": 1},
        ]
    }
    assert report.rubric_metric_score(grade, case, "policy") == 50
    assert report.rubric_metric_score(grade, case, "evidence") is None


def test_total_formula_has_no_separate_evidence_weight() -> None:
    assert report.QUALITY_WEIGHT == 0.75
    assert report.STABILITY_WEIGHT == 0.15
    assert report.EFFICIENCY_WEIGHT == 0.10
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "0.20E" not in source
    assert "E证据质量" not in source


def test_report_has_no_case_pass_count() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "passed_cases" not in source
    assert "通过题数" not in source


def test_gate_report_describes_v5_equal_weight_scoring() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "各检查项等权归一化得分，不设置关键错误封顶" in source
    assert "归一化得分，保留关键错误封顶" not in source


def test_typical_trajectory_uses_binary_checklist_value() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "item['score']" not in source
    assert "item['value']" in source
    assert "answer[:360].rstrip()" in source


def test_failure_attribution_reads_atomic_checklist_items() -> None:
    row = {
        "case_family": "policy_and_version",
        "checklist_pass_rate": 50.0,
        "diagnostics": {"submission_accepted": True, "timed_out": False},
        "checklist": [
            {
                "id": "policy-basis-expense",
                "source": "llm_judge",
                "value": 0,
            },
            {
                "id": "case-reasoning-window",
                "source": "llm_judge",
                "value": 0,
            },
        ],
    }
    assert report.failure_attribution(row) == [
        "policy_or_version_error",
        "reasoning_or_scan_error",
    ]
