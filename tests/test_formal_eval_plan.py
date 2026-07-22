from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runner" / "formal_eval_plan.py"
SPEC = importlib.util.spec_from_file_location("formal_eval_plan_test", MODULE_PATH)
assert SPEC and SPEC.loader
plan = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(plan)


def test_formal_plan_is_internally_consistent() -> None:
    assert len(plan.FRAMEWORK_KEYS) == 6
    assert len(plan.GROUPS) == 12
    assert plan.FORMAL_TASK_COUNT == 15
    assert plan.FORMAL_RUN_COUNT == 180
    assert plan.DEVELOPMENT_RUN_COUNT == 144
    assert plan.TIME_HARD_MAX_SECONDS == plan.TASK_TIMEOUT_SECONDS
    assert plan.SCORING_VERSION == "gate5-scoring-v3"
    assert plan.JUDGE_AUDIT_SAMPLE_RATE == 0.20
    assert plan.JUDGE_AUDIT_REPEAT_COUNT == 2
    assert plan.DATASET_ID == "securities-expense-audit-formal-15-v9"
    assert plan.RUBRIC_VERSION == "atomic-binary-checklist-v7"
    assert plan.CHECKLIST_ITEM_COUNT == 249
    assert plan.REPLACEMENT_CANARY_CASE_IDS == (
        "PV-CASE-001",
        "RA-CASE-001",
        "RA-CASE-002",
        "RR-CASE-001",
    )
    assert plan.REPLACEMENT_CANARY_RUN_COUNT == 48


def test_display_names_exactly_cover_configured_frameworks() -> None:
    assert set(plan.DISPLAY_NAMES) == set(plan.FRAMEWORK_KEYS)
