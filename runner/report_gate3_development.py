from __future__ import annotations

import hashlib
import json
import mmap
import os
import re
import statistics
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from formal_eval_plan import (
    BASELINE_GROUPS,
    DEVELOPMENT_RUN_COUNT,
    DEVELOPMENT_TASK_COUNT,
    ENHANCED_GROUPS,
    FORMAL_RUN_COUNT,
    FORMAL_TASK_COUNT,
    FRAMEWORK_KEYS,
    GROUPS,
    MODEL_NAME,
    TASK_TIMEOUT_SECONDS,
)


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs" / "gate3_development"
DEV = ROOT / "data" / "development"
OUTPUT_JSON = ROOT / "output" / "gate3_development.json"
OUTPUT_MD = ROOT / "output" / "gate3_development.md"
FREEZE_PATH = ROOT / "config" / "gate3_frozen_lock.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_text(value: str) -> str:
    normalized = re.sub(r"(\d+)\s*个?\s*日历日", r"\1天", value.lower())
    return re.sub(r"[\s,，。；;：:'\"“”‘’《》（）()\-_/]", "", normalized)


def set_metrics(expected: list[str], actual: list[str]) -> tuple[float, float, float, bool]:
    expected_set = set(expected)
    actual_set = set(actual)
    if not expected_set and not actual_set:
        return 1.0, 1.0, 1.0, True
    precision = len(expected_set & actual_set) / len(actual_set) if actual_set else 0.0
    recall = len(expected_set & actual_set) / len(expected_set) if expected_set else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1, expected_set == actual_set


def citation_recall(expected: list[list[str]], actual: list[dict[str, Any]]) -> float:
    if not expected:
        return 1.0
    expected_set = {(item[0], item[1]) for item in expected}
    actual_set = {
        (item.get("doc_id"), item.get("clause_no"))
        for item in actual
        if isinstance(item, dict)
    }
    return len(expected_set & actual_set) / len(expected_set)


def contains_any(path: Path, patterns: tuple[str, ...]) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return any(pattern in text for pattern in patterns)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
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


def checkpoint_retains_required_state(path: Path) -> bool:
    if not path.exists():
        return False
    checkpoint = load_json(path)
    retained = checkpoint.get("retained_state", {})
    required = {
        "task",
        "constraints",
        "audit_plan",
        "applicable_policies",
        "record_ids",
        "evidence_status",
        "unresolved_items",
        "artifact_index",
        "remaining_budget",
        "submission_status",
    }
    return checkpoint.get("stage") != "task_started" and required <= set(retained)


def grade_task(group: str, task: dict[str, Any], truth: dict[str, Any]) -> dict[str, Any]:
    base = RUN_ROOT / group / task["id"]
    run_result_path = base / "run_result.json"
    run_result = load_json(run_result_path) if run_result_path.exists() else {}
    final_path = base / "workspace" / "final_submission.json"
    final = load_json(final_path) if final_path.exists() else {
        "anomaly_ids": [], "record_ids": [], "answer": "", "citations": []
    }
    record_precision, record_recall, record_f1, record_exact = set_metrics(
        truth["record_ids"], final.get("record_ids", [])
    )
    answer_normalized = normalize_text(str(final.get("answer", "")))
    required_facts = truth.get("required_facts", [])
    fact_hits = [fact for fact in required_facts if normalize_text(str(fact)) in answer_normalized]
    fact_coverage = len(fact_hits) / len(required_facts) if required_facts else 1.0
    citations = citation_recall(truth.get("citations", []), final.get("citations", []))
    expected_positive = bool(truth.get("anomaly_ids"))
    anomaly_presence_correct = bool(final.get("anomaly_ids")) == expected_positive
    accepted = run_result.get("submission_status") == "accepted"
    correct = (
        accepted
        and record_exact
        and anomaly_presence_correct
        and fact_coverage >= 0.66
        and citations >= 0.5
    )
    state_path = base / "workspace" / ".audit-control" / "state.json"
    state = load_json(state_path) if state_path.exists() else {}
    subagent_calls = state.get("subagent_calls", {})
    trajectory = base / "artifacts" / "trajectory.jsonl"
    events = load_jsonl(base / "workspace" / "traces" / "events.jsonl")
    event_types = {str(event.get("event_type")) for event in events}
    invocations = state.get("subagent_invocations", {})
    authorized_count = len(invocations)
    completed_count = sum(
        invocation.get("status") == "completed"
        for invocation in invocations.values()
        if isinstance(invocation, dict)
    )
    context_events = load_jsonl(base / "workspace" / "traces" / "context_events.jsonl")
    required_events = {"task_started", "task_completed"}
    if accepted:
        required_events |= {
            "validation_started",
            "validation_completed",
            "submission_attempted",
            "submission_accepted",
        }
    return {
        "task_id": task["id"],
        "category": task["category"],
        "present": run_result_path.exists(),
        "accepted": accepted,
        "timed_out": bool(run_result.get("timed_out", False)),
        "elapsed_seconds": run_result.get("elapsed_seconds"),
        "submission_attempt": run_result.get("submission_attempt"),
        "record_precision": round(record_precision, 4),
        "record_recall": round(record_recall, 4),
        "record_f1": round(record_f1, 4),
        "record_exact": record_exact,
        "anomaly_presence_correct": anomaly_presence_correct,
        "fact_coverage": round(fact_coverage, 4),
        "citation_recall": round(citations, 4),
        "correct": correct,
        "actual_record_ids": final.get("record_ids", []),
        "actual_anomaly_ids": final.get("anomaly_ids", []),
        "subagent_calls": subagent_calls,
        "subagent_authorized": authorized_count,
        "subagent_completed": completed_count,
        "subagent_protocol_complete": authorized_count == completed_count,
        "event_stream_complete": required_events <= event_types,
        "event_count": len(events),
        "context_event_count": len(context_events),
        "checkpoint_count": int(state.get("context", {}).get("checkpoint_count", 0)),
        "compaction_count": int(state.get("context", {}).get("compaction_count", 0)),
        "checkpoint_retains_required_state": checkpoint_retains_required_state(
            base / "workspace" / "work" / "context_checkpoint.json"
        ),
        "artifact_manifest_present": (base / "workspace" / "traces" / "artifact_manifest.json").exists(),
        "native_hook_event_count": len(
            load_jsonl(base / "workspace" / "traces" / "native_events.jsonl")
        ),
        "preflight_used": contains_any(trajectory, ("validate_audit_result",)),
        "skill_workflow_loaded": contains_any(
            base / "workspace" / "AGENTS.md",
            ("# Enhanced Audit Workflow", "audit-query-planner"),
        )
        or contains_any(
            base / "workspace" / "CLAUDE.md",
            ("# Enhanced Audit Workflow", "audit-query-planner"),
        ),
        "skill_workflow_used": contains_any(
            trajectory,
            ("audit-query-planner", "securities-expense-audit:audit-query-planner"),
        ),
    }


def group_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    elapsed = [float(row["elapsed_seconds"]) for row in rows if row.get("elapsed_seconds") is not None]
    trap_rows = [row for row in rows if row["category"] == "clean_trap"]
    subagent_counts: dict[str, int] = {}
    for row in rows:
        for role, count in row["subagent_calls"].items():
            subagent_counts[role] = subagent_counts.get(role, 0) + int(count)
    return {
        "task_count": len(rows),
        "present": sum(row["present"] for row in rows),
        "accepted": sum(row["accepted"] for row in rows),
        "correct": sum(row["correct"] for row in rows),
        "timeouts": sum(row["timed_out"] for row in rows),
        "first_attempt_submissions": sum(row["submission_attempt"] == 1 for row in rows),
        "trap_false_positives": sum(not row["anomaly_presence_correct"] for row in trap_rows),
        "mean_record_f1": round(statistics.mean(row["record_f1"] for row in rows), 4) if rows else 0,
        "mean_seconds": round(statistics.mean(elapsed), 3) if elapsed else None,
        "p95_seconds": round(sorted(elapsed)[max(0, int(len(elapsed) * 0.95) - 1)], 3) if elapsed else None,
        "preflight_tasks": sum(row["preflight_used"] for row in rows),
        "skill_workflow_loaded_tasks": sum(row["skill_workflow_loaded"] for row in rows),
        "skill_workflow_tasks": sum(row["skill_workflow_used"] for row in rows),
        "subagent_calls": subagent_counts,
        "event_complete_tasks": sum(row["event_stream_complete"] for row in rows),
        "checkpoint_tasks": sum(row["checkpoint_count"] > 0 for row in rows),
        "checkpoint_retention_tasks": sum(row["checkpoint_retains_required_state"] for row in rows),
        "context_event_tasks": sum(row["context_event_count"] > 0 for row in rows),
        "artifact_manifest_tasks": sum(row["artifact_manifest_present"] for row in rows),
        "subagent_protocol_complete_tasks": sum(row["subagent_protocol_complete"] for row in rows),
        "native_hook_tasks": sum(row["native_hook_event_count"] > 0 for row in rows),
        "compactions": sum(row["compaction_count"] for row in rows),
    }


def run_tests() -> dict[str, Any]:
    env = os.environ.copy()
    env["GATE3_BUILDING_FREEZE"] = "1"
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
        env=env,
    )
    output = (completed.stdout + completed.stderr).strip()
    return {"ok": completed.returncode == 0, "returncode": completed.returncode, "output_tail": output[-4000:]}


def secret_scan(paths: list[Path]) -> dict[str, Any]:
    key = os.environ.get("LLM_API_KEY", "")
    if not key:
        return {"performed": False, "matches": []}
    needle = key.encode("utf-8")
    matches: list[str] = []
    for root in paths:
        if not root.exists():
            continue
        if root.is_file():
            candidates = [root]
        else:
            candidates = []
            for current, directories, filenames in os.walk(root):
                current_path = Path(current)
                if "codex-home" in current_path.parts:
                    codex_index = current_path.parts.index("codex-home")
                    codex_relative = current_path.parts[codex_index + 1 :]
                    if codex_relative and codex_relative[0] in {".tmp", "skills", "agents", "tmp"}:
                        # These are repeated copies of already-scanned adapter
                        # sources or public plugin caches. Runtime config,
                        # sessions, snapshots, state DBs and logs remain in scope.
                        directories[:] = []
                        continue
                directories[:] = [
                    name
                    for name in directories
                    if name not in {".git", "__pycache__", "node_modules"}
                    and not (current_path.name == ".tmp" and name.startswith("plugins-clone-"))
                ]
                candidates.extend(current_path / name for name in filenames)
        for path in candidates:
            try:
                size = path.stat().st_size
                if size == 0 or size > 50 * 1024 * 1024:
                    continue
                with path.open("rb") as handle, mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as data:
                    if data.find(needle) >= 0:
                        matches.append(path.relative_to(ROOT).as_posix())
            except (OSError, ValueError):
                continue
    return {"performed": True, "matches": matches}


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze_files() -> dict[str, str]:
    roots = [
        ROOT / "config" / "source_eval_lock.yaml",
        ROOT / "runner" / "run_gate3_development.py",
        ROOT / "runner" / "audit_trace.py",
        ROOT / "runner" / "report_gate3_development.py",
        ROOT / "runner" / "formal_eval_plan.py",
        ROOT / "candidates" / "codex" / "deepseek_chat_proxy.py",
        ROOT / "fixtures" / "expense_query_mcp.py",
        ROOT / "fixtures" / "policy_query_mcp.py",
        ROOT / "data" / "development",
        ROOT / "domain-enhancement" / "shared-audit-core",
        ROOT / "domain-enhancement" / "control-mcp",
        ROOT / "domain-enhancement" / "adapters" / "claude-code-best" / "securities-expense-audit" / "build_manifest.json",
        ROOT / "domain-enhancement" / "adapters" / "codex" / "securities-expense-audit" / "build_manifest.json",
        ROOT / "domain-enhancement" / "adapters" / "openclaude" / "securities-expense-audit" / "build_manifest.json",
        ROOT / "domain-enhancement" / "adapters" / "opencode" / "securities-expense-audit" / "build_manifest.json",
        ROOT / "domain-enhancement" / "adapters" / "oh-my-pi" / "securities-expense-audit" / "build_manifest.json",
        ROOT / "domain-enhancement" / "adapters" / "pi-agent" / "securities-expense-audit" / "build_manifest.json",
        ROOT / "data" / "formal_case_rubric",
        ROOT / "schemas" / "case-rubric.schema.json",
        ROOT / "config" / "expanded_eval_plan.yaml",
    ]
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            files.append(root)
        elif root.is_dir():
            files.extend(path for path in root.rglob("*") if path.is_file() and "__pycache__" not in path.parts)
    return {path.relative_to(ROOT).as_posix(): hash_file(path) for path in sorted(set(files))}


def build_report() -> dict[str, Any]:
    tasks = load_json(DEV / "evals.json")
    truth = load_json(DEV / "ground_truth.json")
    details = {
        group: [grade_task(group, task, truth[task["id"]]) for task in tasks]
        for group in GROUPS
    }
    summaries = {group: group_summary(rows) for group, rows in details.items()}
    tests = run_tests()
    security = secret_scan([ROOT / "domain-enhancement", RUN_ROOT, ROOT / "config", DEV])
    run_count = sum(summary["present"] for summary in summaries.values())
    source = (ROOT / "runner" / "run_gate3_development.py").read_text(encoding="utf-8")
    checks = {
        "configured_development_tasks_present": len(tasks) == DEVELOPMENT_TASK_COUNT,
        "all_development_runs_present": run_count == DEVELOPMENT_RUN_COUNT,
        "at_most_one_missing_submission_per_group": all(
            summary["accepted"] >= DEVELOPMENT_TASK_COUNT - 1 for summary in summaries.values()
        ),
        "timeouts_at_most_one_per_group": all(summary["timeouts"] <= 1 for summary in summaries.values()),
        "preflight_used_for_every_task": all(
            summary["preflight_tasks"] == DEVELOPMENT_TASK_COUNT for summary in summaries.values()
        ),
        "baseline_has_no_subagent_calls": all(not summaries[group]["subagent_calls"] for group in BASELINE_GROUPS),
        "enhanced_uses_controlled_subagents": all(sum(summaries[group]["subagent_calls"].values()) > 0 for group in ENHANCED_GROUPS),
        "enhanced_skill_workflow_loaded": all(
            summaries[group]["skill_workflow_loaded_tasks"] == DEVELOPMENT_TASK_COUNT for group in ENHANCED_GROUPS
        ),
        "unified_event_stream_complete": all(
            summary["event_complete_tasks"] == DEVELOPMENT_TASK_COUNT for summary in summaries.values()
        ),
        "artifact_manifest_present": all(
            summary["artifact_manifest_tasks"] == DEVELOPMENT_TASK_COUNT for summary in summaries.values()
        ),
        "enhanced_checkpoint_recorded": all(
            summaries[group]["checkpoint_tasks"] == DEVELOPMENT_TASK_COUNT for group in ENHANCED_GROUPS
        ),
        "enhanced_checkpoint_state_recoverable": all(
            summaries[group]["checkpoint_retention_tasks"] == DEVELOPMENT_TASK_COUNT for group in ENHANCED_GROUPS
        ),
        "enhanced_context_events_recorded": all(
            summaries[group]["context_event_tasks"] == DEVELOPMENT_TASK_COUNT for group in ENHANCED_GROUPS
        ),
        "subagent_completion_protocol_closed": all(
            summaries[group]["subagent_protocol_complete_tasks"] == DEVELOPMENT_TASK_COUNT for group in ENHANCED_GROUPS
        ),
        "oh_my_pi_native_hook_recorded": summaries["oh-my-pi-enhanced"]["native_hook_tasks"] == DEVELOPMENT_TASK_COUNT,
        "pi_agent_native_hook_recorded": summaries["pi-agent-enhanced"]["native_hook_tasks"] == DEVELOPMENT_TASK_COUNT,
        "trap_false_positives_at_most_one": all(summary["trap_false_positives"] <= 1 for summary in summaries.values()),
        "single_rule_scope_is_exact": all(
            next(row for row in details[group] if row["task_id"] == "DEV-003")["record_exact"]
            for group in ENHANCED_GROUPS
        ),
        "formal_assets_not_mounted": 'volume(ROOT / "data" / "ground_truth' not in source
        and 'volume(ROOT / "data" / "evals' not in source,
        "unit_tests": tests["ok"],
        "secret_not_persisted": security["performed"] and not security["matches"],
    }
    passed = all(checks.values())
    diagnostics = {
        "enhanced_correct_within_two_of_full_score": all(
            summaries[group]["correct"] >= DEVELOPMENT_TASK_COUNT - 2 for group in ENHANCED_GROUPS
        ),
        "note": "Development semantic scoring is diagnostic only; development tasks have no frozen case-by-case rubric.",
    }
    report = {
        "gate": "GATE3",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "pass" if passed else "fail",
        "allow_next_gate": passed,
        "checks": checks,
        "diagnostics": diagnostics,
        "groups": summaries,
        "tasks": details,
        "tests": tests,
        "security": security,
        "development_manifest": load_json(DEV / "manifest.json"),
    }
    if passed:
        freeze = {
            "gate": "GATE3",
            "frozen_at": report["generated_at"],
            "model": MODEL_NAME,
            "groups": list(GROUPS),
            "formal_task_count_per_group": FORMAL_TASK_COUNT,
            "task_timeout_seconds": TASK_TIMEOUT_SECONDS,
            "files": freeze_files(),
        }
        FREEZE_PATH.write_text(json.dumps(freeze, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report["freeze"] = {"path": FREEZE_PATH.relative_to(ROOT).as_posix(), "file_count": len(freeze["files"])}
    return report


def markdown(report: dict[str, Any]) -> str:
    group_rows = "\n".join(
        f"| {group} | {value['accepted']}/{DEVELOPMENT_TASK_COUNT} | {value['correct']}/{DEVELOPMENT_TASK_COUNT} | {value['trap_false_positives']} | "
        f"{value['timeouts']} | {value['mean_seconds']} | {sum(value['subagent_calls'].values())} |"
        for group, value in report["groups"].items()
    )
    check_rows = "\n".join(
        f"| {name} | {'通过' if value else '失败'} |" for name, value in report["checks"].items()
    )
    diagnostic_rows = "\n".join(
        f"| {name} | {'达到' if value else '未达到'} |"
        for name, value in report["diagnostics"].items()
        if isinstance(value, bool)
    )
    failures = []
    for group, rows in report["tasks"].items():
        for row in rows:
            if not row["correct"]:
                failures.append(
                    f"- `{group}/{row['task_id']}`：accepted={row['accepted']}，record_f1={row['record_f1']}，"
                    f"anomaly_presence={row['anomaly_presence_correct']}，facts={row['fact_coverage']}，citations={row['citation_recall']}"
                )
    failure_text = "\n".join(failures) if failures else "- 无"
    freeze = report.get("freeze", {})
    return f"""# GATE3 独立开发题试跑与配置冻结报告

## 结论

GATE3 **{'通过' if report['status'] == 'pass' else '未通过'}**。{DEVELOPMENT_TASK_COUNT}道开发题只用于执行链路调试，不设置逐题Rubric。开发集使用独立的 `R900xxx` 业务记录命名空间，候选容器未挂载{FORMAL_TASK_COUNT}道正式题、正式Ground Truth、Rubric或判卷实现。

{'允许进入 GATE4 正式运行。' if report['allow_next_gate'] else '暂不允许进入 GATE4，需修复失败项并重新试跑。'}

## {len(GROUPS)}组结果

| 实验组 | 提交成功 | 语义正确 | 陷阱误报 | 超时 | 平均秒数 | 子智能体调用 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{group_rows}

开发题异常 ID 只检查是否应为空及内部一致性，业务正确性以 `record_ids`、必要事实和制度引用为主，避免用不透明标签替代审计能力。

## 验收项

| 检查 | 结果 |
| --- | --- |
{check_rows}

## 非阻断诊断

开发题没有冻结逐题Rubric，以下语义命中只用于发现数据重叠、规则边界和框架差异，不作为GATE3准入条件。

| 诊断项 | 结果 |
| --- | --- |
{diagnostic_rows}

## 未通过任务

{failure_text}

## 冻结结果

- 冻结文件：`{freeze.get('path', '未生成')}`
- 冻结文件数量：{freeze.get('file_count', 0)}
- 正式运行单题超时：{TASK_TIMEOUT_SECONDS}秒
- 正式实验：{len(FRAMEWORK_KEYS)}个框架 × 原生基线/领域增强，共{len(GROUPS)}组，每组{FORMAL_TASK_COUNT}题，共{FORMAL_RUN_COUNT}次运行
"""


def main() -> int:
    report = build_report()
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "allow_next_gate": report["allow_next_gate"], "output": str(OUTPUT_MD)}, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
