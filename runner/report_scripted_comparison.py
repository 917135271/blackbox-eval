from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "domain-enhancement" / "scripted-audit-core" / "scripts"))

from formal_eval_plan import (  # noqa: E402
    EFFICIENCY_WEIGHT,
    FORMAL_TASK_COUNT,
    QUALITY_WEIGHT,
    STABILITY_WEIGHT,
    TASK_TIMEOUT_SECONDS,
    TIME_HARD_MAX_SECONDS,
    TIME_TARGET_SECONDS,
)
from scripted_workflow_core import SCRIPTED_WORKFLOW_VERSION  # noqa: E402


FORMAL_RUN_ROOT = ROOT / "runs" / "gate4_formal"
SCRIPTED_RUN_ROOT = ROOT / "runs" / "gate4_scripted"
CASES_PATH = ROOT / "data" / "formal_case_rubric" / "cases.json"
OUTPUT_JSON = ROOT / "output" / "gate5_v6" / "scripted_enhancement_comparison.json"
OUTPUT_MD = ROOT / "output" / "gate5_v6" / "scripted_enhancement_comparison.md"
FRAMEWORKS = ("ccb", "codex", "openclaude", "opencode", "oh-my-pi", "pi-agent")
DISPLAY_NAMES = {
    "ccb": "Claude Code Best",
    "codex": "Codex",
    "openclaude": "OpenClaude",
    "opencode": "OpenCode",
    "oh-my-pi": "Oh My Pi",
    "pi-agent": "Pi Agent",
}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"missing grade file: {path}")
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if isinstance(value, dict):
                rows.append(value)
    return rows


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _load_dataset() -> dict[str, Any]:
    return _load_json(CASES_PATH)


def _load_cases(dataset: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(case["id"]): case for case in dataset.get("cases", [])}


def _validate_grade_versions(rows: list[dict[str, Any]], dataset: dict[str, Any]) -> None:
    expected = (dataset.get("dataset_id"), dataset.get("rubric_version"))
    mismatches = [
        row
        for row in rows
        if (row.get("dataset_id"), row.get("rubric_version")) != expected
    ]
    if mismatches:
        actual = (
            mismatches[0].get("dataset_id"),
            mismatches[0].get("rubric_version"),
        )
        raise ValueError(f"grade version mismatch: expected {expected}, got {actual}")


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def _linear_lower_score(value: float, target: float, hard_max: float) -> float:
    if value <= target:
        return 100.0
    if value >= hard_max:
        return 0.0
    return 100.0 * (hard_max - value) / (hard_max - target)


def _criterion_map(row: dict[str, Any]) -> dict[str, int]:
    return {
        str(item["id"]): int(item.get("value", 0))
        for item in row.get("checklist", [])
        if isinstance(item, dict) and item.get("id")
    }


def _semantic_ids(case: dict[str, Any]) -> set[str]:
    return {
        str(item["id"])
        for item in case["rubric"]["checklist"]
        if item.get("metric") != "format"
    }


def _semantic_case_score(row: dict[str, Any], case: dict[str, Any]) -> float:
    ids = _semantic_ids(case)
    values = _criterion_map(row)
    raw_score = 100.0 * sum(values.get(item_id, 0) for item_id in ids) / len(ids) if ids else 0.0
    score_cap = row.get("score_cap")
    return min(raw_score, float(score_cap)) if isinstance(score_cap, (int, float)) else raw_score


def _validate_group_rows(
    group: str,
    rows: list[dict[str, Any]],
    cases: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    selected = [row for row in rows if row.get("group") == group]
    task_ids = [str(row.get("task_id")) for row in selected]
    errors: list[str] = []
    if len(selected) != FORMAL_TASK_COUNT or len(set(task_ids)) != FORMAL_TASK_COUNT:
        errors.append(f"expected {FORMAL_TASK_COUNT} unique grades, got {len(selected)} rows/{len(set(task_ids))} tasks")
    if set(task_ids) != set(cases):
        errors.append(f"task set mismatch missing={sorted(set(cases) - set(task_ids))} extra={sorted(set(task_ids) - set(cases))}")
    for row in selected:
        task_id = str(row.get("task_id"))
        if row.get("judge", {}).get("status") == "error":
            errors.append(f"{task_id}: judge error")
        if task_id not in cases:
            continue
        expected_ids = {str(item["id"]) for item in cases[task_id]["rubric"]["checklist"]}
        actual_ids = set(_criterion_map(row))
        if actual_ids != expected_ids:
            errors.append(
                f"{task_id}: rubric checklist mismatch missing={sorted(expected_ids - actual_ids)} extra={sorted(actual_ids - expected_ids)}"
            )
    if errors:
        raise ValueError(f"invalid comparison input for {group}: " + "; ".join(errors))
    return selected


def _group_metrics(
    group: str,
    rows: list[dict[str, Any]],
    run_root: Path,
    cases: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    selected = _validate_group_rows(group, rows, cases)
    semantic_scores = [
        _semantic_case_score(row, cases[str(row["task_id"])]) for row in selected
    ]
    run_results = {
        str(row["task_id"]): _load_json(run_root / group / str(row["task_id"]) / "run_result.json")
        for row in selected
    }
    stable: list[bool] = []
    elapsed: list[float] = []
    for row in selected:
        task_id = str(row["task_id"])
        result = run_results[task_id]
        diagnostics = row.get("diagnostics", {})
        seconds = result.get("elapsed_seconds")
        if isinstance(seconds, (int, float)):
            elapsed.append(float(seconds))
        stable.append(
            diagnostics.get("submission_accepted") is True
            and diagnostics.get("schema_valid") is True
            and result.get("returncode") == 0
            and not result.get("timed_out")
            and isinstance(seconds, (int, float))
            and float(seconds) <= TASK_TIMEOUT_SECONDS
        )
    q = statistics.mean(semantic_scores)
    s = 100.0 * sum(stable) / FORMAL_TASK_COUNT
    median_seconds = statistics.median(elapsed) if elapsed else TASK_TIMEOUT_SECONDS
    f = _linear_lower_score(median_seconds, TIME_TARGET_SECONDS, TIME_HARD_MAX_SECONDS)
    total_score = QUALITY_WEIGHT * q + STABILITY_WEIGHT * s + EFFICIENCY_WEIGHT * f
    checklist_passed = sum(int(row.get("checklist_passed", 0)) for row in selected)
    checklist_total = sum(int(row.get("checklist_total", 0)) for row in selected)
    return {
        "group": group,
        "case_count": len(selected),
        "Q": round(q, 3),
        "S": round(s, 3),
        "F": round(f, 3),
        "Total": round(total_score, 3),
        "checklist_micro_rate_diagnostic": round(100 * checklist_passed / checklist_total, 3),
        "completed": sum(stable),
        "timeouts": sum(bool(value.get("timed_out")) for value in run_results.values()),
        "median_seconds": round(median_seconds, 3),
        "p95_seconds": round(_p95(elapsed), 3),
    }


def _case_rows(
    framework: str,
    formal_rows: list[dict[str, Any]],
    scripted_rows: list[dict[str, Any]],
    cases: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    groups = {
        "baseline": f"{framework}-baseline",
        "original": f"{framework}-enhanced",
        "scripted": f"{framework}-scripted-enhanced",
    }
    indexed = {
        (str(row.get("group")), str(row.get("task_id"))): row
        for row in formal_rows + scripted_rows
    }
    result: list[dict[str, Any]] = []
    for task_id in sorted(cases):
        baseline = indexed[(groups["baseline"], task_id)]
        original = indexed[(groups["original"], task_id)]
        scripted = indexed[(groups["scripted"], task_id)]
        semantic_ids = _semantic_ids(cases[task_id])
        original_items = _criterion_map(original)
        scripted_items = _criterion_map(scripted)
        scores = {
            "baseline": _semantic_case_score(baseline, cases[task_id]),
            "original": _semantic_case_score(original, cases[task_id]),
            "scripted": _semantic_case_score(scripted, cases[task_id]),
        }
        result.append(
            {
                "task_id": task_id,
                "case_family": cases[task_id]["case_family"],
                "baseline_Q": round(scores["baseline"], 3),
                "original_Q": round(scores["original"], 3),
                "scripted_Q": round(scores["scripted"], 3),
                "scripted_minus_original_Q": round(scores["scripted"] - scores["original"], 3),
                "fixed_items": sorted(
                    item_id for item_id in semantic_ids
                    if scripted_items.get(item_id) == 1 and original_items.get(item_id) == 0
                ),
                "regressed_items": sorted(
                    item_id for item_id in semantic_ids
                    if scripted_items.get(item_id) == 0 and original_items.get(item_id) == 1
                ),
            }
        )
    return result


def build_report() -> dict[str, Any]:
    dataset = _load_dataset()
    cases = _load_cases(dataset)
    if len(cases) != FORMAL_TASK_COUNT:
        raise ValueError(f"expected {FORMAL_TASK_COUNT} cases, got {len(cases)}")
    formal_rows = _load_jsonl(FORMAL_RUN_ROOT / "gate5_grades_v6.jsonl")
    scripted_rows = _load_jsonl(SCRIPTED_RUN_ROOT / "gate5_grades_v6.jsonl")
    _validate_grade_versions(formal_rows, dataset)
    _validate_grade_versions(scripted_rows, dataset)
    frameworks: list[dict[str, Any]] = []
    for framework in FRAMEWORKS:
        baseline = _group_metrics(f"{framework}-baseline", formal_rows, FORMAL_RUN_ROOT, cases)
        original = _group_metrics(f"{framework}-enhanced", formal_rows, FORMAL_RUN_ROOT, cases)
        scripted = _group_metrics(
            f"{framework}-scripted-enhanced", scripted_rows, SCRIPTED_RUN_ROOT, cases
        )
        frameworks.append(
            {
                "framework": framework,
                "display_name": DISPLAY_NAMES[framework],
                "baseline": baseline,
                "original_enhanced": original,
                "scripted_enhanced": scripted,
                "deltas": {
                    "original_minus_baseline_Q": round(original["Q"] - baseline["Q"], 3),
                    "scripted_minus_original_Q": round(scripted["Q"] - original["Q"], 3),
                    "scripted_minus_baseline_Q": round(scripted["Q"] - baseline["Q"], 3),
                    "original_minus_baseline_Total": round(original["Total"] - baseline["Total"], 3),
                    "scripted_minus_original_Total": round(scripted["Total"] - original["Total"], 3),
                    "scripted_minus_baseline_Total": round(scripted["Total"] - baseline["Total"], 3),
                },
                "cases": _case_rows(framework, formal_rows, scripted_rows, cases),
            }
        )
    return {
        "comparison_version": SCRIPTED_WORKFLOW_VERSION,
        "scoring_formula": "Total = 0.75Q + 0.15S + 0.10F",
        "interpretation": {
            "original_minus_baseline": "original Skills enhancement bundle difference",
            "scripted_minus_original": "scripted-downshift bundle difference; not a single-factor causal effect",
            "scripted_minus_baseline": "net scripted-downshift bundle difference",
        },
        "validation": {
            "formal_cases_per_group": FORMAL_TASK_COUNT,
            "judge_errors": 0,
            "rubric_checklists_complete": True,
        },
        "frameworks": frameworks,
    }


def write_report(report: dict[str, Any]) -> None:
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# 脚本下沉增强组对比报告",
        "",
        "三组均使用同一批15道正式题和逐题Rubric。Q排除格式项并按题宏平均；S衡量按时、正常进程、Schema有效和成功提交；F按中位耗时评分。证据指标只解释Q，不重复计分。C-B是整个脚本下沉增强包的差值，不能归因于单一脚本因素。",
        "",
        "| 框架 | A组Q/Total | B组Q/Total | C组Q/Total | C-B Q | C-B Total | C组稳定 | 超时 | 中位耗时 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in report["frameworks"]:
        baseline = item["baseline"]
        original = item["original_enhanced"]
        scripted = item["scripted_enhanced"]
        delta = item["deltas"]
        lines.append(
            f"| {item['display_name']} | {baseline['Q']:.1f}/{baseline['Total']:.1f} | "
            f"{original['Q']:.1f}/{original['Total']:.1f} | {scripted['Q']:.1f}/{scripted['Total']:.1f} | "
            f"{delta['scripted_minus_original_Q']:+.1f} | {delta['scripted_minus_original_Total']:+.1f} | "
            f"{scripted['completed']}/15 | {scripted['timeouts']} | {scripted['median_seconds']:.1f}s |"
        )
    for item in report["frameworks"]:
        delta = item["deltas"]
        lines.extend(
            [
                "",
                f"## {item['display_name']}",
                "",
                f"B-A：Q {delta['original_minus_baseline_Q']:+.1f}，Total {delta['original_minus_baseline_Total']:+.1f}；"
                f"C-B：Q {delta['scripted_minus_original_Q']:+.1f}，Total {delta['scripted_minus_original_Total']:+.1f}；"
                f"C-A：Q {delta['scripted_minus_baseline_Q']:+.1f}，Total {delta['scripted_minus_baseline_Total']:+.1f}。",
                "",
                "| 题目 | 题型 | A组Q | B组Q | C组Q | C-B | 修复项 | 回退项 |",
                "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for case in item["cases"]:
            lines.append(
                f"| {case['task_id']} | {case['case_family']} | {case['baseline_Q']:.1f} | "
                f"{case['original_Q']:.1f} | {case['scripted_Q']:.1f} | "
                f"{case['scripted_minus_original_Q']:+.1f} | {len(case['fixed_items'])} | "
                f"{len(case['regressed_items'])} |"
            )
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    value = build_report()
    write_report(value)
    print(json.dumps({"status": "pass", "json": str(OUTPUT_JSON), "markdown": str(OUTPUT_MD)}, ensure_ascii=False))
