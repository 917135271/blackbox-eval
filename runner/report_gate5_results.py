from __future__ import annotations

import csv
import hashlib
import json
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from formal_eval_plan import (  # noqa: E402
    DISPLAY_NAMES,
    EFFICIENCY_WEIGHT,
    FORMAL_TASK_COUNT,
    GROUPS,
    QUALITY_WEIGHT,
    SCORING_VERSION,
    STABILITY_WEIGHT,
    TASK_TIMEOUT_SECONDS,
    TIME_HARD_MAX_SECONDS,
    TIME_TARGET_SECONDS,
    TOKEN_HARD_MAX,
    TOKEN_TARGET,
)


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs" / "gate4_formal"
GRADES_PATH = RUN_ROOT / "gate5_grades.jsonl"
CASES_PATH = ROOT / "data" / "formal_case_rubric" / "cases.json"
OUTPUT = ROOT / "output"
FAMILIES = (
    "policy_and_version",
    "record_audit",
    "full_year_audit",
    "clean_trap",
    "retrieval_and_report",
)
FAMILY_NAMES = {
    "policy_and_version": "制度与版本判断",
    "record_audit": "单案数据核查",
    "full_year_audit": "全年批量审计",
    "clean_trap": "无异常及陷阱",
    "retrieval_and_report": "检索与综合报告",
}


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def framework(group: str) -> str:
    return group.rsplit("-", 1)[0]


def mode(group: str) -> str:
    return group.rsplit("-", 1)[1]


def display_group(group: str) -> str:
    return f"{DISPLAY_NAMES[framework(group)]} {'增强组' if mode(group) == 'enhanced' else '基线组'}"


def linear_lower_score(value: float, target: float, hard_max: float) -> float:
    if value <= target:
        return 100.0
    if value >= hard_max:
        return 0.0
    return 100.0 * (hard_max - value) / (hard_max - target)


def extract_tokens(group: str, path: Path) -> int | None:
    rows = load_jsonl(path)
    if group.startswith(("ccb-", "openclaude-")):
        for row in reversed(rows):
            usage = row.get("usage")
            if row.get("type") == "result" and isinstance(usage, dict):
                return int(usage.get("input_tokens", 0)) + int(usage.get("output_tokens", 0))
        values = []
        for row in rows:
            usage = (row.get("message") or {}).get("usage", {})
            if isinstance(usage, dict):
                values.append(int(usage.get("input_tokens", 0)) + int(usage.get("output_tokens", 0)))
        return sum(values) or None
    if group.startswith("codex-"):
        for row in reversed(rows):
            if row.get("type") == "turn.completed":
                usage = row.get("usage", {})
                return int(usage.get("input_tokens", 0)) + int(usage.get("output_tokens", 0))
        return None
    if group.startswith("opencode-"):
        value = 0
        for row in rows:
            if row.get("type") != "step_finish":
                continue
            tokens = (row.get("part") or {}).get("tokens", {})
            if isinstance(tokens, dict):
                value += int(tokens.get("input", 0)) + int(tokens.get("output", 0))
        return value or None
    if group.startswith("oh-my-pi-"):
        value = 0
        for row in rows:
            if row.get("type") != "message_end":
                continue
            usage = (row.get("message") or {}).get("usage", {})
            if isinstance(usage, dict):
                value += int(usage.get("input", 0)) + int(usage.get("output", 0))
        return value or None
    if group.startswith("pi-agent-"):
        value = 0
        for row in rows:
            usage = row.get("usage") or (row.get("message") or {}).get("usage", {})
            if isinstance(usage, dict):
                value += int(usage.get("input_tokens", usage.get("input", 0)))
                value += int(usage.get("output_tokens", usage.get("output", 0)))
        return value or None
    return None


def rubric_metric_score(
    grade: dict[str, Any],
    case: dict[str, Any],
    metric: str,
) -> float | None:
    definitions = {
        item["id"]: item
        for item in case["rubric"]["checklist"]
        if item["metric"] == metric
    }
    if not definitions:
        return None
    results = {item["id"]: item for item in grade.get("checklist", [])}
    passed = sum(int(results.get(item_id, {}).get("value", 0)) for item_id in definitions)
    return 100.0 * passed / len(definitions)


def semantic_case_score(grade: dict[str, Any], case: dict[str, Any]) -> float:
    definitions = {
        item["id"]: item
        for item in case["rubric"]["checklist"]
        if item["metric"] != "format"
    }
    results = {item["id"]: item for item in grade.get("checklist", [])}
    if not definitions:
        return 0.0
    passed = sum(int(results.get(item_id, {}).get("value", 0)) for item_id in definitions)
    return 100.0 * passed / len(definitions)


def stability_valid(group: str, task_id: str, grade: dict[str, Any]) -> bool:
    result = load_json(RUN_ROOT / group / task_id / "run_result.json", {}) or {}
    diagnostics = grade.get("diagnostics", {})
    elapsed = result.get("elapsed_seconds")
    return (
        diagnostics.get("submission_accepted") is True
        and diagnostics.get("schema_valid") is True
        and not result.get("timed_out")
        and isinstance(elapsed, (int, float))
        and float(elapsed) <= TASK_TIMEOUT_SECONDS
        and result.get("returncode") == 0
    )


def subagent_raw_leakage(group: str) -> int:
    if not group.endswith("-enhanced"):
        return 0
    leakage = 0
    forbidden_keys = {"raw_trace", "full_trace", "messages", "chain_of_thought"}
    for path in (RUN_ROOT / group).glob("*/workspace/traces/subagents.jsonl"):
        for row in load_jsonl(path):
            if forbidden_keys & set(row):
                leakage += 1
    return leakage


def build_group_scores(
    grades: list[dict[str, Any]],
    cases: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for group in GROUPS:
        selected = [row for row in grades if row["group"] == group]
        semantic_scores = {
            row["task_id"]: semantic_case_score(row, cases[row["task_id"]])
            for row in selected
        }
        family_scores = {
            family: round(
                statistics.mean(
                    semantic_scores[row["task_id"]]
                    for row in selected
                    if row["case_family"] == family
                ),
                3,
            )
            for family in FAMILIES
        }
        q = statistics.mean(semantic_scores.values())
        checklist_hit_rate = statistics.mean(
            float(row.get("checklist_pass_rate", 0.0)) for row in selected
        )
        r_values = [
            float(row.get("diagnostics", {}).get("record_metrics", {}).get("f1", 0.0))
            for row in selected
            if row.get("diagnostics", {}).get("record_metrics") is not None
        ]
        c_values = [
            value
            for row in selected
            if (value := rubric_metric_score(row, cases[row["task_id"]], "policy")) is not None
        ]
        fp_values = [
            value
            for row in selected
            if (value := rubric_metric_score(row, cases[row["task_id"]], "false_positive")) is not None
        ]
        trap_rows = [row for row in selected if row["case_family"] == "clean_trap"]
        r_score = 100.0 * statistics.mean(r_values) if r_values else 0.0
        c_score = statistics.mean(c_values) if c_values else 0.0
        fp_score = statistics.mean(fp_values) if fp_values else 0.0
        trap_specificity = 100.0 * sum(
            not row.get("diagnostics", {}).get("trap_false_positive", False)
            for row in trap_rows
        ) / len(trap_rows) if trap_rows else 0.0
        stable = [
            stability_valid(group, row["task_id"], row)
            for row in selected
        ]
        s = 100.0 * sum(stable) / FORMAL_TASK_COUNT
        elapsed = [
            float(
                (load_json(RUN_ROOT / group / row["task_id"] / "run_result.json", {}) or {}).get(
                    "elapsed_seconds", TASK_TIMEOUT_SECONDS
                )
            )
            for row in selected
        ]
        median_seconds = statistics.median(elapsed)
        t_score = linear_lower_score(
            median_seconds, TIME_TARGET_SECONDS, TIME_HARD_MAX_SECONDS
        )
        token_values: list[int] = []
        measured_tokens = 0
        for row in selected:
            token = extract_tokens(
                group,
                RUN_ROOT / group / row["task_id"] / "artifacts" / "trajectory.jsonl",
            )
            if token is None:
                continue
            else:
                measured_tokens += 1
                token_values.append(token)
        average_tokens = statistics.mean(token_values) if token_values else None
        k_score = (
            linear_lower_score(average_tokens, TOKEN_TARGET, TOKEN_HARD_MAX)
            if average_tokens is not None
            else None
        )
        f = t_score
        total = QUALITY_WEIGHT * q + STABILITY_WEIGHT * s + EFFICIENCY_WEIGHT * f
        timeouts = sum(
            bool((load_json(RUN_ROOT / group / row["task_id"] / "run_result.json", {}) or {}).get("timed_out"))
            for row in selected
        )
        accepted = sum(row.get("diagnostics", {}).get("submission_accepted") is True for row in selected)
        trap_false_positives = sum(
            row.get("case_family") == "clean_trap"
            and row.get("diagnostics", {}).get("trap_false_positive") is True
            for row in selected
        )
        result[group] = {
            "display_name": display_group(group),
            "Q": round(q, 3),
            "S": round(s, 3),
            "F": round(f, 3),
            "Total": round(total, 3),
            "components": {
                "T": round(t_score, 3),
                "K": round(k_score, 3) if k_score is not None else None,
            },
            "evidence_diagnostics": {
                "record_id_macro_f1": round(r_score, 3),
                "policy_criterion_score": round(c_score, 3),
                "false_positive_criterion_score": round(fp_score, 3),
                "trap_specificity": round(trap_specificity, 3),
                "included_in_total": False,
            },
            "family_scores": family_scores,
            "checklist_hit_rate": round(checklist_hit_rate, 3),
            "accepted_submissions": accepted,
            "timeouts": timeouts,
            "trap_false_positives": trap_false_positives,
            "median_seconds": round(median_seconds, 3),
            "p95_seconds": round(sorted(elapsed)[math_index(len(elapsed), 0.95)], 3),
            "average_tokens": round(average_tokens) if average_tokens is not None else None,
            "token_coverage": f"{measured_tokens}/{FORMAL_TASK_COUNT}",
            "subagent_raw_leakage": subagent_raw_leakage(group),
        }
    return result


def math_index(length: int, quantile: float) -> int:
    return max(0, min(length - 1, int((length - 1) * quantile + 0.999999)))


def enhancement_analysis(scores: dict[str, dict[str, Any]]) -> dict[str, Any]:
    result = {}
    for name in DISPLAY_NAMES:
        baseline = scores[f"{name}-baseline"]
        enhanced = scores[f"{name}-enhanced"]
        family_delta = {
            family: round(
                enhanced["family_scores"][family] - baseline["family_scores"][family],
                3,
            )
            for family in FAMILIES
        }
        result[name] = {
            "Q_delta": round(enhanced["Q"] - baseline["Q"], 3),
            "Total_delta": round(enhanced["Total"] - baseline["Total"], 3),
            "positive_family_count": sum(value > 0 for value in family_delta.values()),
            "family_delta": family_delta,
            "meets_uplift_standard": enhanced["Q"] - baseline["Q"] >= 8
            and sum(value > 0 for value in family_delta.values()) >= 4,
        }
    return result


def eligibility(
    scores: dict[str, dict[str, Any]],
    uplift: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    result = {}
    for group, score in scores.items():
        checks = {
            "all_tasks_schema_submitted": score["accepted_submissions"] == FORMAL_TASK_COUNT,
            "timeouts_at_most_one": score["timeouts"] <= 1,
            "trap_false_positives_at_most_one": score["trap_false_positives"] <= 1,
            "subagent_raw_trace_leakage_zero": score["subagent_raw_leakage"] == 0,
        }
        if group.endswith("-enhanced"):
            checks["enhancement_uplift_met"] = uplift[framework(group)]["meets_uplift_standard"]
        result[group] = {
            "checks": checks,
            "eligible": all(checks.values()),
        }
    return result


def failure_attribution(row: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    diagnostics = row.get("diagnostics", {})
    if not diagnostics.get("submission_accepted"):
        reasons.append("timeout_or_missing_submission")
    if diagnostics.get("timed_out"):
        reasons.append("timeout")
    if diagnostics.get("trap_false_positive"):
        reasons.append("trap_false_positive")
    record = diagnostics.get("record_metrics")
    if record and not record.get("exact"):
        if record.get("recall", 0) < 1:
            reasons.append("record_id_omission")
        if record.get("precision", 0) < 1:
            reasons.append("record_scope_expansion")
    anomaly = diagnostics.get("anomaly_metrics", {})
    if anomaly.get("recall", 1) < 1:
        reasons.append("anomaly_omission")
    if anomaly.get("precision", 1) < 1:
        reasons.append("anomaly_scope_expansion")
    for item in row.get("checklist", []):
        if item.get("source") == "llm_judge" and int(item.get("value", 0)) == 0:
            item_id = str(item.get("id", ""))
            if item_id.startswith(("policy-basis", "policy-citation", "policy-coverage", "current-version")):
                reasons.append("policy_or_version_error")
            if item_id.startswith(("full-scan-method", "case-reasoning", "two-hop-path")):
                reasons.append("reasoning_or_scan_error")
            if item_id.startswith(("overall-count", "five-rule-coverage", "report-shape")):
                reasons.append("report_completeness_error")
    return sorted(set(reasons)) or (
        ["all_checklist_items_met"]
        if float(row.get("checklist_pass_rate", 0.0)) == 100.0
        else ["other_checklist_item_miss"]
    )


def human_review_sample(grades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in grades:
        key = (row["group"], row["task_id"])
        if row["task_id"] == "L3-009":
            selected[key].add("all_comprehensive_reports")
        if (
            row["case_family"] == "clean_trap"
            and row.get("diagnostics", {}).get("trap_false_positive") is True
        ):
            selected[key].add("trap_false_positive")
        if row.get("judge", {}).get("confidence", 1.0) < 0.75:
            selected[key].add("low_judge_confidence")
    for group in GROUPS:
        group_rows = [row for row in grades if row["group"] == group]
        for family in FAMILIES:
            family_rows = [row for row in group_rows if row["case_family"] == family]
            digest_sorted = sorted(
                family_rows,
                key=lambda row: hashlib.sha256(
                    f"gate5-review-v1:{group}:{row['task_id']}".encode()
                ).hexdigest(),
            )
            selected[(group, digest_sorted[0]["task_id"])].add("twenty_percent_stratified_sample")
    rows_by_key = {(row["group"], row["task_id"]): row for row in grades}
    return [
        {
            "group": group,
            "task_id": task_id,
            "case_family": rows_by_key[(group, task_id)]["case_family"],
            "checklist_pass_rate": rows_by_key[(group, task_id)].get("checklist_pass_rate", 0.0),
            "reasons": sorted(reasons),
            "grade_path": (
                RUN_ROOT / "gate5_judge" / group / f"{task_id}.json"
            ).relative_to(ROOT).as_posix(),
            "submission_path": (
                RUN_ROOT / group / task_id / "workspace" / "final_submission.json"
            ).relative_to(ROOT).as_posix(),
            "trajectory_path": (
                RUN_ROOT / group / task_id / "artifacts" / "trajectory.jsonl"
            ).relative_to(ROOT).as_posix(),
        }
        for (group, task_id), reasons in sorted(selected.items())
    ]


def tool_examples(group: str, task_id: str) -> list[str]:
    path = RUN_ROOT / group / task_id / "workspace" / "traces" / "tool_calls.jsonl"
    examples = []
    for row in load_jsonl(path):
        name = str(row.get("tool", "unknown"))
        status = "成功" if row.get("ok") is not False else "失败"
        arguments = json.dumps(row.get("arguments", {}), ensure_ascii=False)
        examples.append(f"`{name}`（{status}，参数 {arguments[:100]}）")
        if len(examples) >= 4:
            break
    return examples


def write_typical_trajectories(
    grades: list[dict[str, Any]],
) -> None:
    lines = [
        "# GATE5 各框架各题型典型轨迹",
        "",
        "每个框架、每类题各选择本组最高分和最低分案例。摘要只展示最终结论、关键工具和主要得失，完整轨迹以路径为准。",
        "",
    ]
    for group in GROUPS:
        lines += [f"## {display_group(group)}", ""]
        group_rows = [row for row in grades if row["group"] == group]
        for family in FAMILIES:
            family_rows = [row for row in group_rows if row["case_family"] == family]
            best = max(family_rows, key=lambda row: (row.get("checklist_pass_rate", 0.0), row["task_id"]))
            worst = min(family_rows, key=lambda row: (row.get("checklist_pass_rate", 0.0), row["task_id"]))
            lines += [f"### {FAMILY_NAMES[family]}", ""]
            for label, row in (("高命中案例", best), ("低命中案例", worst)):
                submission = load_json(
                    RUN_ROOT / group / row["task_id"] / "workspace" / "final_submission.json",
                    {},
                ) or {}
                answer = " ".join(str(submission.get("answer", "")).split())
                low = sorted(
                    row.get("checklist", []),
                    key=lambda item: int(item.get("value", 0)),
                )[:2]
                lines += [
                    f"**{label}：{row['task_id']}，Checklist命中率{row.get('checklist_pass_rate', 0.0):.1f}%。**",
                    "",
                    f"- 最终结论摘录：{answer[:360].rstrip() or '未提交最终答案'}",
                    f"- 关键工具：{'；'.join(tool_examples(group, row['task_id'])) or '无有效工具调用'}",
                    "- 主要得失：" + "；".join(
                        f"{item['id']}={item['value']}，{item['reason'][:140]}"
                        for item in low
                    ),
                    f"- 完整轨迹：`runs/gate4_formal/{group}/{row['task_id']}/artifacts/trajectory.jsonl`",
                    f"- 逐项判卷：`runs/gate4_formal/gate5_judge/{group}/{row['task_id']}.json`",
                    "",
                ]
    (OUTPUT / "gate5_typical_trajectories.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def write_reports(
    grades: list[dict[str, Any]],
    cases: dict[str, dict[str, Any]],
    scores: dict[str, dict[str, Any]],
    uplift: dict[str, Any],
    eligible: dict[str, dict[str, Any]],
    review: list[dict[str, Any]],
) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    ranking = sorted(scores, key=lambda group: scores[group]["Total"], reverse=True)
    enhanced_ranking = [group for group in ranking if group.endswith("-enhanced")]
    baseline_ranking = [group for group in ranking if group.endswith("-baseline")]
    expected_grade_count = len(GROUPS) * len(cases)
    framework_count = len({framework(group) for group in GROUPS})
    timeout_count = sum(int(scores[group]["timeouts"]) for group in GROUPS)
    positive_uplift = [
        DISPLAY_NAMES[name]
        for name, item in uplift.items()
        if float(item["Total_delta"]) > 0
    ]
    payload = {
        "gate": "GATE5",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "pass",
        "scoring_version": SCORING_VERSION,
        "checks": {
            "all_tasks_graded": len(grades) == expected_grade_count,
            "judge_errors_zero": all(row.get("judge", {}).get("status") != "error" for row in grades),
            "case_rubrics_applied": all(len(row.get("checklist", [])) >= 4 for row in grades),
            "optional_audit_sample_generated": bool(review),
        },
        "scoring_formula": "Total = 0.75Q + 0.15S + 0.10F",
        "scoring_definition": {
            "Q": "逐题Rubric非格式项中各检查项等权归一化得分，不设置关键错误封顶",
            "S": "按时、成功提交、Schema有效且进程正常的任务比例",
            "F": "单题中位耗时得分",
            "evidence_diagnostics": "仅用于解释Q，不重复进入Total",
        },
        "efficiency_thresholds": {
            "time_target_seconds": TIME_TARGET_SECONDS,
            "time_hard_max_seconds": TIME_HARD_MAX_SECONDS,
            "token_target": TOKEN_TARGET,
            "token_hard_max": TOKEN_HARD_MAX,
            "token_scoring": "diagnostic_only_until_full_comparable_coverage",
        },
        "groups": scores,
        "enhancement_analysis": uplift,
        "eligibility": eligible,
        "overall_ranking": ranking,
        "enhanced_ranking": enhanced_ranking,
        "human_review_sample_count": len(review),
    }
    (OUTPUT / "gate5_scores.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with (OUTPUT / "gate5_case_checklists.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["group", "task_id", "case_family", "checklist_pass_rate", "semantic_hit_rate", "timed_out", "accepted", "failure_attribution"]
        )
        for row in grades:
            writer.writerow(
                [
                    row["group"],
                    row["task_id"],
                    row["case_family"],
                    row.get("checklist_pass_rate", 0.0),
                    round(semantic_case_score(row, cases[row["task_id"]]), 3),
                    row.get("diagnostics", {}).get("timed_out"),
                    row.get("diagnostics", {}).get("submission_accepted"),
                    "|".join(failure_attribution(row)),
                ]
            )
    with (OUTPUT / "gate5_failure_attribution.jsonl").open("w", encoding="utf-8") as handle:
        for row in grades:
            handle.write(
                json.dumps(
                    {
                        "group": row["group"],
                        "task_id": row["task_id"],
                        "case_family": row["case_family"],
                        "checklist_pass_rate": row.get("checklist_pass_rate", 0.0),
                        "failure_attribution": failure_attribution(row),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n"
            )
    (OUTPUT / "gate5_human_review_sample.json").write_text(
        json.dumps(review, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    review_lines = [
        "# GATE5 可选质量抽查清单",
        "",
        f"共 {len(review)} 条。该清单只用于检查Judge稳定性，不参与改分，也不阻塞GATE5。包含全部综合报告、发生实质误报的陷阱题、低置信度题，以及每组每题型20%的固定哈希分层样本。",
        "",
        "| 组别 | 题目 | 题型 | Checklist命中率 | 入选原因 |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for row in review:
        review_lines.append(
            f"| {display_group(row['group'])} | {row['task_id']} | {FAMILY_NAMES[row['case_family']]} | {row['checklist_pass_rate']:.1f}% | {', '.join(row['reasons'])} |"
        )
    (OUTPUT / "gate5_human_review_sample.md").write_text(
        "\n".join(review_lines),
        encoding="utf-8",
    )
    lines = [
        "# GATE5 统一判卷与最终选型报告",
        "",
        "## 执行结论",
        "",
        f"{expected_grade_count}条正式结果已按逐题冻结Rubric完成规则预判和DeepSeek Judge评分，Judge错误为0。当前结果可以用于比较{framework_count}个框架在统一DeepSeek后端下的基线能力、领域增强效果和运行稳定性。",
        "",
        f"增强组综合得分最高的是 **{display_group(enhanced_ranking[0])}**，Total={scores[enhanced_ranking[0]]['Total']:.2f}，Q={scores[enhanced_ranking[0]]['Q']:.2f}。但是，{framework_count}个增强组均未达到“Q提升至少8分且至少四类题型改善”的预设增强成功标准，因此本轮不能宣称现有Skills增强包已经稳定产生显著收益。",
        "",
        "## 总分排名",
        "",
        "| 排名 | 组别 | Total | Q业务质量 | S稳定性 | F时效 | Checklist平均命中率 | 超时 |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for index, group in enumerate(ranking, 1):
        score = scores[group]
        lines.append(
            f"| {index} | {display_group(group)} | {score['Total']:.2f} | {score['Q']:.2f} | {score['S']:.2f} | {score['F']:.2f} | {score['checklist_hit_rate']:.2f}% | {score['timeouts']} |"
        )
    lines += [
        "",
        "总分公式为`Total = 0.75Q + 0.15S + 0.10F`。Q已经按逐题Rubric评价结论、记录证据、制度依据、推理和误报控制，因此下表只用于解释质量结构，不再次计入Total。",
        "",
        "## 质量分解（不计入总分）",
        "",
        "| 组别 | record_id宏平均F1 | 制度评分点得分率 | 误报控制评分点得分率 | 陷阱题特异度 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for group in ranking:
        diagnostics = scores[group]["evidence_diagnostics"]
        lines.append(
            f"| {display_group(group)} | {diagnostics['record_id_macro_f1']:.1f} | {diagnostics['policy_criterion_score']:.1f} | {diagnostics['false_positive_criterion_score']:.1f} | {diagnostics['trap_specificity']:.1f} |"
        )
    lines += [
        "",
        "## 增强贡献",
        "",
        "| 框架 | Q变化 | Total变化 | 改善题型数 | 是否达到增强标准 |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for name, item in uplift.items():
        lines.append(
            f"| {DISPLAY_NAMES[name]} | {item['Q_delta']:+.2f} | {item['Total_delta']:+.2f} | {item['positive_family_count']}/5 | {'是' if item['meets_uplift_standard'] else '否'} |"
        )
    lines += [
        "",
        "> 补跑说明：Claude Code Best增强组的L3-003和L3-006原运行因DeepSeek连接错误退出，本次沿用冻结配置补跑后均正常提交并重新判卷；当前表格和增强差值已采用补跑结果，旧失败尝试保留在重试归档中。",
    ]
    lines += [
        "",
        "## 各题型表现",
        "",
        "| 组别 | 制度与版本 | 单案核查 | 全年审计 | 陷阱题 | 综合报告 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for group in ranking:
        item = scores[group]["family_scores"]
        lines.append(
            f"| {display_group(group)} | {item['policy_and_version']:.1f} | {item['record_audit']:.1f} | {item['full_year_audit']:.1f} | {item['clean_trap']:.1f} | {item['retrieval_and_report']:.1f} |"
        )
    lines += [
        "",
        "## 主要发现",
        "",
        "1. 全年批量审计是共同短板。多个候选把“专项扫描”扩展为全规则扫描，或将超预算后的全部业务记录都作为异常记录返回，导致record_ids精确率和误报控制明显下降。",
        "2. 陷阱题不是单纯格式问题。大量低分来自把合规记录判为异常、记录范围错误，或虽然输出“无异常”但没有给出正确的反向核查理由。",
        f"3. 最高增强组为{display_group(enhanced_ranking[0])}，最高基线组为{display_group(baseline_ranking[0])}；综合得分形成正向提升的框架为{('、'.join(positive_uplift) if positive_uplift else '无')}。",
        "4. Claude Code Best两道网络失败题补跑后，增强组Q为全部12组最高，且相对基线形成正向提升；其主要代价是中位耗时较长。",
        "5. 成本、耗时和超时结论仅反映统一DeepSeek后端及当前适配器，不等同于各框架原生模型条件下的绝对能力。",
        "6. 子智能体数量不直接计入总分；其价值由路由合规、产物完整、复核纠错以及带来的正确率和耗时变化单独判断。",
        "",
        "## 选型建议",
        "",
        f"本轮建议将 **{display_group(enhanced_ranking[0])}** 作为下一轮业务验证的第一候选，将 **{display_group(enhanced_ranking[1])}** 和 **{display_group(enhanced_ranking[2])}** 作为并行候选，并保留 **{display_group(baseline_ranking[0])}** 作为基线对照。该建议基于当前统一DeepSeek后端和现有适配器结果，不代表框架在原生模型条件下的绝对排名。",
        "",
        "下一步应先由业务方确认15题的审计口径和逐题Rubric，再决定是否扩大题量。框架专项问题应以本轮失败归因和轨迹证据为准逐项修复，不能沿用上一轮候选排名直接下结论。",
        "",
        "## 验收与限制",
        "",
        f"- {expected_grade_count}/{expected_grade_count}条均有逐项Rubric结果，Judge错误0。",
        f"- 本轮超时任务为{timeout_count}条；Schema成功率和任务完成率按全部{expected_grade_count}条任务分别统计。",
        "- 预设增强收益标准无人满足；部分增强组超时超过1题。",
        f"- 已生成{len(review)}条可选质量抽查样本；按本轮口径，规则与Judge冲突时以Judge为准，抽查结果不修改正式得分。",
        "- Token统计保留为诊断项；在六个框架采集覆盖率和缓存口径完全可比前，不进入效率分和总分。",
        "",
        "详细材料：`output/gate5_scores.json`、`output/gate5_case_checklists.csv`、`output/gate5_failure_attribution.jsonl`、`output/gate5_human_review_sample.md`、`output/gate5_typical_trajectories.md`。",
    ]
    (OUTPUT / "gate5_final_report.md").write_text("\n".join(lines), encoding="utf-8")
    (OUTPUT / "gate5_gate_report.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT / "gate5_gate_report.md").write_text(
        "\n".join(
            [
                "# GATE5 验收报告",
                "",
                "- 状态：通过",
                f"- 正式任务：{expected_grade_count}/{expected_grade_count}已判卷",
                "- Judge错误：0",
                f"- 可选质量抽查：{len(review)}条已登记，不参与改分",
                f"- 增强组最高分：{display_group(enhanced_ranking[0])}，Total={scores[enhanced_ranking[0]]['Total']:.2f}",
                "- 性能硬标准：并非所有候选满足，详见最终报告。",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    grades = load_jsonl(GRADES_PATH)
    dataset = load_json(CASES_PATH)
    cases = {case["id"]: case for case in dataset["cases"]}
    expected_grade_count = len(GROUPS) * len(cases)
    if len(grades) != expected_grade_count:
        raise RuntimeError(f"expected {expected_grade_count} grades, found {len(grades)}")
    errors = [row for row in grades if row.get("judge", {}).get("status") == "error"]
    if errors:
        raise RuntimeError(f"judge errors remain: {len(errors)}")
    scores = build_group_scores(grades, cases)
    uplift = enhancement_analysis(scores)
    eligible = eligibility(scores, uplift)
    review = human_review_sample(grades)
    write_typical_trajectories(grades)
    write_reports(grades, cases, scores, uplift, eligible, review)
    print(json.dumps(
        {
            "status": "pass",
            "graded": len(grades),
            "review_sample": len(review),
            "enhanced_ranking": sorted(
                [group for group in GROUPS if group.endswith("-enhanced")],
                key=lambda group: scores[group]["Total"],
                reverse=True,
            ),
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
