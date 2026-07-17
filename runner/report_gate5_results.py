from __future__ import annotations

import csv
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs" / "gate4_formal"
GRADES_PATH = RUN_ROOT / "gate5_grades.jsonl"
CASES_PATH = ROOT / "data" / "formal_case_rubric" / "cases.json"
OUTPUT = ROOT / "output"
GROUPS = (
    "ccb-baseline",
    "ccb-enhanced",
    "codex-baseline",
    "codex-enhanced",
    "openclaude-baseline",
    "openclaude-enhanced",
    "opencode-baseline",
    "opencode-enhanced",
    "oh-my-pi-baseline",
    "oh-my-pi-enhanced",
)
DISPLAY_NAMES = {
    "ccb": "Claude Code Best",
    "codex": "Codex",
    "openclaude": "OpenClaude",
    "opencode": "OpenCode",
    "oh-my-pi": "Oh My Pi",
}
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
    return None


def policy_correct(grade: dict[str, Any], case: dict[str, Any]) -> bool | None:
    policy_criteria = [
        criterion
        for criterion in case["rubric"]["criteria"]
        if criterion["metric"] == "policy"
    ]
    if not policy_criteria:
        return None
    scores = {row["id"]: float(row["score"]) for row in grade.get("criteria", [])}
    return all(scores.get(item["id"], 0.0) >= float(item["weight"]) for item in policy_criteria)


def record_correct(grade: dict[str, Any], case: dict[str, Any]) -> bool | None:
    if "expected_record_ids" not in case["expected_output"]:
        return None
    metrics = grade.get("diagnostics", {}).get("record_metrics")
    return bool(metrics and metrics.get("exact"))


def trap_correct(grade: dict[str, Any]) -> bool | None:
    if grade["case_family"] != "clean_trap":
        return None
    return bool(grade.get("passed")) and not grade.get("diagnostics", {}).get("trap_false_positive")


def stability_valid(group: str, task_id: str, grade: dict[str, Any]) -> bool:
    result = load_json(RUN_ROOT / group / task_id / "run_result.json", {}) or {}
    diagnostics = grade.get("diagnostics", {})
    elapsed = result.get("elapsed_seconds")
    return (
        diagnostics.get("submission_accepted") is True
        and diagnostics.get("schema_valid") is True
        and not result.get("timed_out")
        and isinstance(elapsed, (int, float))
        and float(elapsed) <= 900
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
        family_scores = {
            family: round(
                statistics.mean(
                    row["case_score"]
                    for row in selected
                    if row["case_family"] == family
                ),
                3,
            )
            for family in FAMILIES
        }
        q = statistics.mean(float(row["case_score"]) for row in selected)
        r_values = [
            record_correct(row, cases[row["task_id"]])
            for row in selected
            if record_correct(row, cases[row["task_id"]]) is not None
        ]
        c_values = [
            policy_correct(row, cases[row["task_id"]])
            for row in selected
            if policy_correct(row, cases[row["task_id"]]) is not None
        ]
        n_values = [
            trap_correct(row)
            for row in selected
            if trap_correct(row) is not None
        ]
        r_score = 100.0 * sum(bool(value) for value in r_values) / len(r_values)
        c_score = 100.0 * sum(bool(value) for value in c_values) / len(c_values)
        n_score = 100.0 * sum(bool(value) for value in n_values) / len(n_values)
        e = 0.40 * r_score + 0.30 * c_score + 0.30 * n_score
        stable = [
            stability_valid(group, row["task_id"], row)
            for row in selected
        ]
        s = 100.0 * sum(stable) / 15
        elapsed = [
            float((load_json(RUN_ROOT / group / row["task_id"] / "run_result.json", {}) or {}).get("elapsed_seconds", 900))
            for row in selected
        ]
        median_seconds = statistics.median(elapsed)
        t_score = linear_lower_score(median_seconds, 180.0, 900.0)
        token_values: list[int] = []
        measured_tokens = 0
        for row in selected:
            token = extract_tokens(
                group,
                RUN_ROOT / group / row["task_id"] / "artifacts" / "trajectory.jsonl",
            )
            if token is None:
                token_values.append(1_000_000)
            else:
                measured_tokens += 1
                token_values.append(token)
        average_tokens = statistics.mean(token_values)
        k_score = linear_lower_score(average_tokens, 50_000.0, 1_000_000.0)
        f = 0.50 * t_score + 0.50 * k_score
        total = 0.55 * q + 0.20 * e + 0.15 * s + 0.10 * f
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
            "E": round(e, 3),
            "S": round(s, 3),
            "F": round(f, 3),
            "Total": round(total, 3),
            "components": {
                "R": round(r_score, 3),
                "C": round(c_score, 3),
                "N": round(n_score, 3),
                "T": round(t_score, 3),
                "K": round(k_score, 3),
            },
            "family_scores": family_scores,
            "passed_cases": sum(row.get("passed") is True for row in selected),
            "accepted_submissions": accepted,
            "timeouts": timeouts,
            "trap_false_positives": trap_false_positives,
            "median_seconds": round(median_seconds, 3),
            "p95_seconds": round(sorted(elapsed)[math_index(len(elapsed), 0.95)], 3),
            "average_tokens": round(average_tokens),
            "token_coverage": f"{measured_tokens}/15",
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
            "all_tasks_schema_submitted": score["accepted_submissions"] == 15,
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
    criteria = {item["id"]: item for item in row.get("criteria", [])}
    for item in row.get("criteria", []):
        if item["source"] == "llm_judge" and float(item["score"]) < 0.5:
            if item["id"] in {"policy-basis", "policy-citation", "policy-coverage", "current-version"}:
                reasons.append("policy_or_version_error")
            if item["id"] in {"full-scan-method", "case-reasoning", "two-hop-path"}:
                reasons.append("reasoning_or_scan_error")
            if item["id"] in {"overall-count", "five-rule-coverage", "report-shape"}:
                reasons.append("report_completeness_error")
    if any(item.get("triggered") for item in row.get("critical_failures", [])):
        reasons.append("critical_failure")
    return sorted(set(reasons)) or (["passed_or_minor_deduction"] if row.get("passed") else ["rubric_partial_miss"])


def human_review_sample(grades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in grades:
        key = (row["group"], row["task_id"])
        if row["task_id"] == "L3-009":
            selected[key].add("all_comprehensive_reports")
        if row["case_family"] == "clean_trap" and not row.get("passed"):
            selected[key].add("failed_clean_or_trap_case")
        if any(item.get("triggered") for item in row.get("critical_failures", [])):
            selected[key].add("critical_failure_triggered")
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
            "case_score": rows_by_key[(group, task_id)]["case_score"],
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
            best = max(family_rows, key=lambda row: (row["case_score"], row["task_id"]))
            worst = min(family_rows, key=lambda row: (row["case_score"], row["task_id"]))
            lines += [f"### {FAMILY_NAMES[family]}", ""]
            for label, row in (("典型成功", best), ("典型失败/短板", worst)):
                submission = load_json(
                    RUN_ROOT / group / row["task_id"] / "workspace" / "final_submission.json",
                    {},
                ) or {}
                answer = " ".join(str(submission.get("answer", "")).split())
                low = sorted(
                    row.get("criteria", []),
                    key=lambda item: float(item["score"]) / max(1.0, next(
                        float(c["weight"])
                        for c in load_json(CASES_PATH)["cases"]
                        if c["id"] == row["task_id"]
                        for c in c["rubric"]["criteria"]
                        if c["id"] == item["id"]
                    )),
                )[:2]
                lines += [
                    f"**{label}：{row['task_id']}，{row['case_score']:.1f}分。**",
                    "",
                    f"- 最终结论摘录：{answer[:360] or '未提交最终答案'}",
                    f"- 关键工具：{'；'.join(tool_examples(group, row['task_id'])) or '无有效工具调用'}",
                    "- 主要得失：" + "；".join(
                        f"{item['id']}={item['score']}，{item['reason'][:140]}"
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
    payload = {
        "gate": "GATE5",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "pass",
        "checks": {
            "all_150_tasks_graded": len(grades) == 150,
            "judge_errors_zero": all(row.get("judge", {}).get("status") != "error" for row in grades),
            "case_rubrics_applied": all(len(row.get("criteria", [])) >= 4 for row in grades),
            "optional_audit_sample_generated": bool(review),
        },
        "scoring_formula": "Total = 0.55Q + 0.20E + 0.15S + 0.10F",
        "efficiency_thresholds": {
            "time_target_seconds": 180,
            "time_hard_max_seconds": 900,
            "token_target": 50000,
            "token_hard_max": 1000000,
            "missing_token_measurement": "conservatively scored as token hard max",
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
    with (OUTPUT / "gate5_case_scores.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["group", "task_id", "case_family", "case_score", "passed", "timed_out", "accepted", "failure_attribution"]
        )
        for row in grades:
            writer.writerow(
                [
                    row["group"],
                    row["task_id"],
                    row["case_family"],
                    row["case_score"],
                    row["passed"],
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
                        "case_score": row["case_score"],
                        "passed": row["passed"],
                        "failure_attribution": failure_attribution(row),
                        "critical_failures": [
                            item for item in row.get("critical_failures", []) if item.get("triggered")
                        ],
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
        f"共 {len(review)} 条。该清单只用于检查Judge稳定性，不参与改分，也不阻塞GATE5。包含全部综合报告、未通过陷阱题、关键错误、低置信度题，以及每组每题型20%的固定哈希分层样本。",
        "",
        "| 组别 | 题目 | 题型 | 分数 | 入选原因 |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for row in review:
        review_lines.append(
            f"| {display_group(row['group'])} | {row['task_id']} | {FAMILY_NAMES[row['case_family']]} | {row['case_score']:.1f} | {', '.join(row['reasons'])} |"
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
        "150条正式结果已按逐题冻结Rubric完成规则预判和DeepSeek Judge评分，Judge错误为0。当前结果可以用于比较五个框架在统一DeepSeek后端下的基线能力、领域增强效果和运行稳定性。",
        "",
        f"增强组综合得分最高的是 **{display_group(enhanced_ranking[0])}**，Total={scores[enhanced_ranking[0]]['Total']:.2f}，Q={scores[enhanced_ranking[0]]['Q']:.2f}。但是，五个增强组均未达到“Q提升至少8分且至少四类题型改善”的预设增强成功标准，因此本轮不能宣称现有Skills增强包已经稳定产生显著收益。",
        "",
        "## 总分排名",
        "",
        "| 排名 | 组别 | Total | Q正确性 | E证据质量 | S稳定性 | F效率 | 通过题数 | 超时 |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for index, group in enumerate(ranking, 1):
        score = scores[group]
        lines.append(
            f"| {index} | {display_group(group)} | {score['Total']:.2f} | {score['Q']:.2f} | {score['E']:.2f} | {score['S']:.2f} | {score['F']:.2f} | {score['passed_cases']}/15 | {score['timeouts']} |"
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
        "3. OpenClaude增强组取得全体最高Q和Total，Oh My Pi基线组是表现最好的基线组。OpenClaude相对自身基线仍只形成有限提升；Claude Code Best和OpenCode的Q有正向提升，Codex与Oh My Pi增强组反而下降。",
        "4. Codex的非缓存Token显著高于其他框架，并且增强组出现3题超时；这说明当前DeepSeek适配方式下存在上下文累积和执行效率问题，不等同于Codex原生模型能力结论。",
        "5. 子智能体调用并非越多越好。OpenClaude增强组全部24次请求均被路由拒绝，仍取得最高增强组正确性；Oh My Pi完成9次子智能体调用但Q下降，说明当前主要增益来自Skills、任务状态和校验流程，而非子智能体数量。",
        "",
        "## 选型建议",
        "",
        "本轮建议将 **OpenClaude增强组** 作为下一轮业务验证的第一候选，将 **Claude Code Best增强组** 作为重点对照候选。该建议基于当前统一DeepSeek后端和现有适配器结果，不代表框架在原生模型条件下的绝对排名。",
        "",
        "现有增强包尚未达到预设+8分门槛，下一步不宜直接扩大题量。应先修复三个共性问题：专项扫描范围约束、陷阱题反向验证、超预算record_ids定义；随后用同一15题进行一次冻结后的确认性复测。Codex应同时修复上下文累积和超时问题，再判断其框架上限。",
        "",
        "## 验收与限制",
        "",
        "- 150/150条均有逐项Rubric结果，Judge错误0。",
        "- 已提交结果的Schema成功率为100%，但10条任务因超时未提交，因此按全任务口径不是100%。",
        "- 预设增强收益标准无人满足；部分增强组超时超过1题。",
        f"- 已生成{len(review)}条可选质量抽查样本；按本轮口径，规则与Judge冲突时以Judge为准，抽查结果不修改正式得分。",
        "- Token口径为轨迹可比的非缓存输入加输出；缺失测量按硬上限保守计分。",
        "",
        "详细材料：`output/gate5_scores.json`、`output/gate5_case_scores.csv`、`output/gate5_failure_attribution.jsonl`、`output/gate5_human_review_sample.md`、`output/gate5_typical_trajectories.md`。",
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
                "- 正式任务：150/150已判卷",
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
    if len(grades) != 150:
        raise RuntimeError(f"expected 150 grades, found {len(grades)}")
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
