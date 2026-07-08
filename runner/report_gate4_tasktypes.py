from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from gate2_candidate_check import ROOT, load_eval_config


RUNS = {
    "qwen-code": "gate4_baseline_qwen_v1",
    "goose": "gate4_baseline_goose_v1",
    "trae-agent": "gate4_baseline_trae_v1",
    "opencode": "gate4_baseline_opencode_v1",
}

AGENT_TITLES = {
    "qwen-code": "Qwen Code",
    "goose": "Goose",
    "trae-agent": "Trae Agent",
    "opencode": "OpenCode",
}

CATEGORY_NAMES = {
    "policy_qa": "纯制度问答",
    "version_check": "版本检查",
    "single_anomaly_lookup": "单条异常判断",
    "ground_truth_lookup": "异常查记录集合",
    "policy_data_comparison": "制度+业务交叉核查",
    "full_year_rule_audit": "全年专项扫描",
    "version_trap": "版本陷阱",
    "two_hop_retrieval": "双跳检索",
    "near_clause_disambiguation": "近似条款辨析",
    "audit_report": "报告式任务",
    "clean_but_suspicious": "陷阱题",
}

CATEGORY_ORDER = list(CATEGORY_NAMES)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_tasks(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        task["id"]: task
        for task in json.loads(Path(config["paths"]["evals"]).read_text(encoding="utf-8"))
    }


def pct(numerator: int, denominator: int) -> str:
    if not denominator:
        return "n/a"
    return f"{numerator / denominator:.1%}"


def short_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def grade_layer(row: dict[str, Any]) -> str:
    if row.get("timeout"):
        return "timeout"
    if row.get("format_failure"):
        return "format_failure"
    return row.get("failure_layer") or "ok"


def status_label(row: dict[str, Any]) -> str:
    if row.get("timeout"):
        return "超时"
    if row.get("score") == 1.0 and row.get("format_failure"):
        return "内容通过但格式失败"
    if row.get("score") == 1.0:
        return "通过"
    if row.get("format_failure"):
        return "格式失败且内容未通过"
    return "内容未通过"


def judgement_for_category(category: str, rows: list[dict[str, Any]]) -> str:
    total = len(rows)
    passed = sum(1 for row in rows if row.get("score") == 1.0)
    fmt = sum(1 for row in rows if row.get("format_failure"))
    timeouts = sum(1 for row in rows if row.get("timeout"))
    rate = passed / total if total else 0.0
    if category == "policy_qa":
        return "仍是最稳定题型" if rate >= 0.7 else "制度事实可做,但输出稳定性不足"
    if category in {"single_anomaly_lookup", "policy_data_comparison", "full_year_rule_audit"}:
        if rate >= 0.4:
            return "LLM judge 认可部分语义命中,但集合归并仍不稳"
        return "复杂异常识别短板明显"
    if category == "ground_truth_lookup":
        return "record_id 集合覆盖是主要瓶颈"
    if category == "clean_but_suspicious":
        return "容易把干净样本误判成异常" if rate < 0.4 else "陷阱识别有一定能力"
    if category == "audit_report":
        return "报告可读性不等于 rubric 完整满足"
    if timeouts:
        return "存在超时,需要控制搜索范围"
    if fmt > total // 2:
        return "格式约束是主要问题"
    return "中等表现"


def select_example(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pass_rows = [row for row in rows if row.get("score") == 1.0]
    pass_rate = len(pass_rows) / len(rows) if rows else 0.0
    if pass_rate >= 0.5 and pass_rows:
        clean_pass = [row for row in pass_rows if not row.get("format_failure") and not row.get("timeout")]
        return sorted(clean_pass or pass_rows, key=lambda row: (str(row.get("task_id")), str(row.get("variant"))))[0]

    failed = [row for row in rows if row.get("score") != 1.0 or row.get("timeout")]
    if not failed:
        return rows[0]
    layers = Counter(grade_layer(row) for row in failed)
    target_layer, _ = layers.most_common(1)[0]
    same_layer = [row for row in failed if grade_layer(row) == target_layer]
    return sorted(same_layer, key=lambda row: (str(row.get("task_id")), str(row.get("variant"))))[0]


def first_matching_line(path: Path, needles: list[str], fallback_first_nonempty: bool = True) -> tuple[int, str] | None:
    if not path.exists():
        return None
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for index, line in enumerate(lines, start=1):
        if any(needle in line for needle in needles):
            return index, line.strip()
    if fallback_first_nonempty:
        for index, line in enumerate(lines, start=1):
            if line.strip():
                return index, line.strip()
    return None


def clip(text: Any, limit: int = 1200) -> str:
    raw = "" if text is None else str(text)
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    if len(raw) <= limit:
        return raw
    return raw[:limit] + f"\n...[truncated {len(raw) - limit} chars]"


def answer_excerpt(row: dict[str, Any], result: dict[str, Any]) -> str:
    answer_json = result.get("answer_json")
    if isinstance(answer_json, dict):
        return json.dumps(answer_json, ensure_ascii=False)
    final_text = result.get("final_text") or ""
    return clip(final_text, 1200)


def example_block(row: dict[str, Any], tasks: dict[str, dict[str, Any]]) -> list[str]:
    result_path = ROOT / row["run_path"] / "result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    run_dir = result_path.parent
    task = tasks[row["task_id"]]
    prompt = (task.get("prompt_variants") or {}).get(row.get("variant")) or ""
    layer = grade_layer(row)
    tool_line = first_matching_line(run_dir / "tool_calls.jsonl", ["result_preview", "records", "doc_id"])
    trajectory_line = first_matching_line(
        run_dir / "trajectory.json",
        ['"answer"', '"text"', '"final_result"', "```json"],
    )
    judge_excerpt = {
        "llm_score": row.get("score"),
        "rule_score": row.get("rule_score"),
        "failure_layer": row.get("failure_layer"),
        "format_failure": row.get("format_failure"),
        "judge_reason": row.get("judge_reason"),
        "judge_missing": row.get("judge_missing"),
        "judge_extra": row.get("judge_extra"),
    }
    lines = [
        f"代表样例: `{row.get('task_id')}` / `{row.get('variant')}` / `{status_label(row)}` / "
        f"`llm_score={row.get('score')}` / `rule_score={row.get('rule_score')}` / `layer={layer}`。",
        f"题面: {prompt}",
        "",
    ]
    if tool_line:
        line_no, text = tool_line
        lines.extend(
            [
                f"工具轨迹摘录 `{short_path(run_dir / 'tool_calls.jsonl')}:{line_no}`:",
                "",
                "````text",
                clip(text),
                "````",
                "",
            ]
        )
    if trajectory_line:
        line_no, text = trajectory_line
        lines.extend(
            [
                f"最终轨迹摘录 `{short_path(run_dir / 'trajectory.json')}:{line_no}`:",
                "",
                "````text",
                clip(text),
                "````",
                "",
            ]
        )
    lines.extend(
        [
            "候选答案摘录:",
            "",
            "````text",
            clip(answer_excerpt(row, result)),
            "````",
            "",
            "LLM judge 摘录:",
            "",
            "````json",
            json.dumps(judge_excerpt, ensure_ascii=False, indent=2),
            "````",
            "",
        ]
    )
    if row.get("score") == 1.0:
        lines.append("原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。")
    elif row.get("timeout"):
        lines.append("原因分析: 该样例超时,没有形成可稳定判定的完整答案。")
    elif row.get("format_failure"):
        lines.append("原因分析: 输出未满足标准 JSON 合约; LLM judge 仍会尽量看内容,但这里语义也未过。")
    else:
        lines.append("原因分析: 输出可解析,但 LLM judge 认为关键事实、记录集合或异常判断没有语义命中。")
    return lines


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "total": len(rows),
        "llm_pass": sum(1 for row in rows if row.get("score") == 1.0),
        "rule_pass": sum(1 for row in rows if row.get("rule_score") == 1.0),
        "format_fail": sum(1 for row in rows if row.get("format_failure")),
        "llm_fail": sum(1 for row in rows if row.get("score") != 1.0),
        "timeout": sum(1 for row in rows if row.get("timeout")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Write GATE4 per-agent task type analysis.")
    parser.add_argument("--output-name", default="gate4_agent_tasktype_analysis.md")
    args = parser.parse_args()

    config = load_eval_config()
    tasks = load_tasks(config)
    output_dir = Path(config["paths"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    rows_by_agent: dict[str, list[dict[str, Any]]] = {}
    all_rows: list[dict[str, Any]] = []
    for agent, run_id in RUNS.items():
        rows = load_jsonl(Path(config["paths"]["runs_dir"]) / run_id / "grades.jsonl")
        rows_by_agent[agent] = rows
        all_rows.extend(rows)

    lines = [
        "# GATE 4 Agent Task-Type Analysis",
        "",
        f"生成时间: {datetime.now().date().isoformat()}",
        "",
        "数据来源:",
        "",
        "- `runs/*/grades.jsonl`",
        "- `runs/*/*/*/result.json`",
        "- `runs/*/*/*/trajectory.json`",
        "- 汇总报告: `output/gate4_baseline_report.md`",
        "",
        "说明: 本版 `score` 是 LLM judge 的语义判卷结果; `rule_score` 保留旧确定性规则分供对照。"
        " `格式失败` 仍单独统计,因为有些答案语义可读但没有满足标准 JSON 输出合约。",
        "",
        "## 总体结论",
        "",
        "LLM judge 放宽了“必须输出标准 anomaly_id”的硬约束后,异常识别类题目分数上升,但题型差异仍很明显:",
        "",
        "| 题型 | 总尝试 | LLM内容通过 | 旧规则通过 | 格式失败 | 主要结论 |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]

    for category in CATEGORY_ORDER:
        rows = [row for row in all_rows if row.get("category") == category]
        summary = summarize_rows(rows)
        lines.append(
            f"| `{category}` {CATEGORY_NAMES[category]} | {summary['total']} | "
            f"{summary['llm_pass']} ({pct(summary['llm_pass'], summary['total'])}) | "
            f"{summary['rule_pass']} | {summary['format_fail']} | {judgement_for_category(category, rows)} |"
        )

    for agent, rows in rows_by_agent.items():
        lines.extend(
            [
                "",
                f"## {AGENT_TITLES.get(agent, agent)}",
                "",
                "### 题型表现",
                "",
                "| 题型 | 总数 | LLM内容通过 | 旧规则通过 | 格式失败 | LLM未通过 | 超时 | 判断 |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for category in CATEGORY_ORDER:
            cat_rows = [row for row in rows if row.get("category") == category]
            summary = summarize_rows(cat_rows)
            lines.append(
                f"| {category} | {summary['total']} | {summary['llm_pass']} | "
                f"{summary['rule_pass']} | {summary['format_fail']} | {summary['llm_fail']} | "
                f"{summary['timeout']} | {judgement_for_category(category, cat_rows)} |"
            )
        lines.extend(
            [
                "",
                "### 各题型典型轨迹",
                "",
                "下面每个题型放一个代表样例。样例选择规则: 通过率较高的题型选通过样例; "
                "失败为主的题型选该题型最常见失败层。",
                "",
            ]
        )
        for category in CATEGORY_ORDER:
            cat_rows = [row for row in rows if row.get("category") == category]
            summary = summarize_rows(cat_rows)
            lines.extend(
                [
                    f"#### {category} ({CATEGORY_NAMES[category]})",
                    "",
                    f"表现: LLM内容通过 {summary['llm_pass']}/{summary['total']}, "
                    f"旧规则通过 {summary['rule_pass']}/{summary['total']}, "
                    f"格式失败 {summary['format_fail']}, 超时 {summary['timeout']}。",
                ]
            )
            lines.extend(example_block(select_example(cat_rows), tasks))
            lines.append("")

    lines.extend(
        [
            "## 按失败类型归因",
            "",
            "| agent | layer | count |",
            "| --- | --- | ---: |",
        ]
    )
    for agent, rows in rows_by_agent.items():
        for layer, count in Counter(grade_layer(row) for row in rows).most_common():
            lines.append(f"| {agent} | `{layer}` | {count} |")

    lines.extend(
        [
            "",
            "## 题型建议",
            "",
            "- 制度问答和简单双跳可以作为基本能力回归集。",
            "- 异常识别题需要同时看 `score` 和 `rule_score`: LLM judge 能识别语义命中,规则分能暴露输出 ID 命名空间不一致。",
            "- 报告式任务建议继续使用 LLM judge 或人工抽检,单纯字符串断言过硬。",
            "- 格式失败不应和内容失败混在一起: agent 产品可用性需要分别优化答案合约、工具轨迹、业务推理。",
            "",
        ]
    )

    path = output_dir / args.output_name
    normalized_lines = []
    for line in lines:
        parts = str(line).split("\n")
        normalized_lines.extend(part.rstrip() for part in parts)
    path.write_text("\n".join(normalized_lines), encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
