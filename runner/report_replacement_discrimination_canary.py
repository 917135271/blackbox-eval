from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from formal_eval_plan import GROUPS, PLAN  # noqa: E402
from report_gate5_results import semantic_case_score  # noqa: E402
from run_replacement_discrimination_canary import CASE_IDS, RUN_ROOT  # noqa: E402


GRADES_PATH = RUN_ROOT / "grades_v7.jsonl"
RUN_SUMMARY_PATH = RUN_ROOT / "run_summary.json"
CASES_PATH = ROOT / "data" / "formal_case_rubric" / "cases.json"
OUTPUT_JSON = ROOT / "output" / "replacement_discrimination_canary_v7.json"
OUTPUT_MD = ROOT / "output" / "replacement_discrimination_canary_v7.md"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build_report() -> dict[str, Any]:
    dataset = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    cases = {case["id"]: case for case in dataset["cases"]}
    grades = load_jsonl(GRADES_PATH)
    expected_pairs = {(group, task_id) for group in GROUPS for task_id in CASE_IDS}
    actual_pairs = {(row.get("group"), row.get("task_id")) for row in grades}
    missing = sorted(expected_pairs - actual_pairs)
    if missing:
        raise RuntimeError(f"replacement Canary grades are incomplete: {missing[:5]}")
    run_summary = json.loads(RUN_SUMMARY_PATH.read_text(encoding="utf-8"))
    runs = {
        (row.get("group"), row.get("task_id")): row
        for row in run_summary.get("runs", [])
    }
    missing_runs = sorted(expected_pairs - set(runs))
    if missing_runs:
        raise RuntimeError(f"replacement Canary runs are incomplete: {missing_runs[:5]}")
    criteria = PLAN["replacement_discrimination_canary"]["acceptance"]
    case_rows = []
    for task_id in CASE_IDS:
        selected = [row for row in grades if row["task_id"] == task_id]
        score_by_group = {
            row["group"]: (
                round(semantic_case_score(row, cases[task_id]), 3)
                if row.get("judge", {}).get("status") == "ok"
                else None
            )
            for row in selected
        }
        scores = [score for score in score_by_group.values() if score is not None]
        complete = len(scores) == len(GROUPS)
        score_range = max(scores) - min(scores) if scores else None
        standard_deviation = statistics.pstdev(scores) if scores else None
        full_scores = sum(score >= 99.999 for score in scores)
        checks = {
            "all_groups_graded": complete,
            "score_range": score_range >= float(criteria["minimum_case_score_range"]) if complete else None,
            "standard_deviation": standard_deviation >= float(criteria["minimum_case_score_standard_deviation"]) if complete else None,
            "full_score_groups": full_scores <= int(criteria["maximum_full_score_groups_per_case"]) if complete else None,
        }
        case_rows.append(
            {
                "task_id": task_id,
                "replaces": cases[task_id]["replaces"],
                "graded_group_count": len(scores),
                "minimum": round(min(scores), 3) if scores else None,
                "maximum": round(max(scores), 3) if scores else None,
                "range": round(score_range, 3) if score_range is not None else None,
                "standard_deviation": round(standard_deviation, 3) if standard_deviation is not None else None,
                "full_score_groups": full_scores,
                "scores": score_by_group,
                "checks": checks,
                "status": "pass" if complete and all(checks.values()) else ("fail" if complete else "incomplete"),
                "passed": complete and all(checks.values()),
            }
        )
    accepted = [
        row for row in runs.values()
        if row.get("submission_status") == "accepted" and not row.get("timed_out")
    ]
    format_success_rate = len(accepted) / len(expected_pairs)
    judge_errors = sum(row.get("judge", {}).get("status") == "error" for row in grades)
    complete = judge_errors == 0
    passed = (
        complete
        and all(row["passed"] for row in case_rows)
        and format_success_rate >= float(criteria["format_success_rate"])
    )
    return {
        "dataset_id": dataset["dataset_id"],
        "rubric_version": dataset["rubric_version"],
        "run_count": len(expected_pairs),
        "format_success_rate": round(format_success_rate, 6),
        "judge_errors": judge_errors,
        "status": "pass" if passed else ("incomplete" if not complete else "fail"),
        "case_results": case_rows,
        "passed": passed,
    }


def write_report(report: dict[str, Any]) -> None:
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    status_text = {"pass": "通过", "fail": "未通过", "incomplete": "未完成"}
    lines = [
        "# 新正式题区分度Canary",
        "",
        f"结论：**{status_text[report['status']]}**。运行{report['run_count']}次，格式成功率{100 * report['format_success_rate']:.1f}%，Judge错误{report['judge_errors']}。",
        "",
        "| 新Case | 替换旧题 | 有效判分 | 最低分 | 最高分 | 极差 | 标准差 | 满分组数 | 结论 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in report["case_results"]:
        def display(value: float | None) -> str:
            return f"{value:.1f}" if value is not None else "待补判"

        lines.append(
            f"| {row['task_id']} | {row['replaces']} | {row['graded_group_count']}/12 | {display(row['minimum'])} | "
            f"{display(row['maximum'])} | {display(row['range'])} | {display(row['standard_deviation'])} | "
            f"{row['full_score_groups']}/12 | {status_text[row['status']]} |"
        )
    lines.extend([
        "",
        "判定门槛：每题12组Judge结果齐全，单题极差至少15分、总体标准差至少5分、满分不超过9组，且48次任务全部格式提交成功。Judge错误不按0分计入离散度。",
    ])
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    report = build_report()
    write_report(report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
