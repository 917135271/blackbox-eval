from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "config" / "expanded_eval_plan.yaml"


def _load_plan() -> dict[str, Any]:
    value = yaml.safe_load(PLAN_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"formal evaluation plan must be an object: {PLAN_PATH}")
    return value


PLAN = _load_plan()
EXPERIMENT = PLAN["experiment"]
MODEL = PLAN["model"]
JUDGE = PLAN["judge"]
EFFICIENCY = PLAN["scoring"]["efficiency"]
SCORE_WEIGHTS = PLAN["scoring"]["total_weights"]
SCORING_VERSION = str(PLAN["scoring"]["version"])

GROUPS = tuple(str(group) for group in PLAN["groups"])
BASELINE_GROUPS = tuple(group for group in GROUPS if group.endswith("-baseline"))
ENHANCED_GROUPS = tuple(group for group in GROUPS if group.endswith("-enhanced"))
FRAMEWORK_KEYS = tuple(dict.fromkeys(group.rsplit("-", 1)[0] for group in GROUPS))
DISPLAY_NAMES = {
    "ccb": "Claude Code Best",
    "codex": "Codex",
    "openclaude": "OpenClaude",
    "opencode": "OpenCode",
    "oh-my-pi": "Oh My Pi",
    "pi-agent": "Pi Agent",
}

DEVELOPMENT_TASK_COUNT = int(EXPERIMENT["development_case_count"])
FORMAL_TASK_COUNT = int(EXPERIMENT["formal_case_count"])
TASK_TIMEOUT_SECONDS = int(EXPERIMENT["task_timeout_seconds"])
MODEL_NAME = str(MODEL["name"])
MODEL_BASE_URL = str(MODEL["base_url"]).rstrip("/")
API_KEY_ENV = str(MODEL["api_key_env"])

JUDGE_TIMEOUT_SECONDS = int(JUDGE["timeout_seconds"])
JUDGE_MAX_TOKENS = int(JUDGE["max_tokens"])
JUDGE_RETRIES = int(JUDGE["retries"])

TIME_TARGET_SECONDS = float(EFFICIENCY["time_target_seconds"])
TIME_HARD_MAX_SECONDS = float(EFFICIENCY["time_hard_max_seconds"])
TOKEN_TARGET = int(EFFICIENCY["token_target"])
TOKEN_HARD_MAX = int(EFFICIENCY["token_hard_max"])
QUALITY_WEIGHT = float(SCORE_WEIGHTS["rubric_quality"])
STABILITY_WEIGHT = float(SCORE_WEIGHTS["stability"])
EFFICIENCY_WEIGHT = float(SCORE_WEIGHTS["efficiency"])

FORMAL_RUN_COUNT = len(GROUPS) * FORMAL_TASK_COUNT
DEVELOPMENT_RUN_COUNT = len(GROUPS) * DEVELOPMENT_TASK_COUNT


def validate_plan() -> None:
    if len(GROUPS) != len(set(GROUPS)):
        raise ValueError("formal evaluation groups must be unique")
    if set(DISPLAY_NAMES) != set(FRAMEWORK_KEYS):
        raise ValueError("display names must exactly cover configured frameworks")
    if int(EXPERIMENT["framework_count"]) != len(FRAMEWORK_KEYS):
        raise ValueError("framework_count does not match configured groups")
    if int(EXPERIMENT["group_count"]) != len(GROUPS):
        raise ValueError("group_count does not match configured groups")
    if int(EXPERIMENT["formal_run_count"]) != FORMAL_RUN_COUNT:
        raise ValueError("formal_run_count does not match groups x formal cases")
    if TIME_HARD_MAX_SECONDS != TASK_TIMEOUT_SECONDS:
        raise ValueError("efficiency time hard max must equal the formal task timeout")
    if abs(QUALITY_WEIGHT + STABILITY_WEIGHT + EFFICIENCY_WEIGHT - 1.0) > 1e-9:
        raise ValueError("scoring total weights must sum to 1")
    if PLAN["scoring"]["evidence_diagnostics"].get("included_in_total") is not False:
        raise ValueError("evidence diagnostics must not be counted twice in Total")
    if SCORING_VERSION != "gate5-scoring-v2":
        raise ValueError("unsupported scoring version")


validate_plan()
