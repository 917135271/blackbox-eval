from __future__ import annotations

import json
import mmap
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from run_gate4_formal import (
    GROUPS,
    RUN_ROOT,
    ROOT,
    formal_mount_policy,
    load_tasks,
    verify_frozen_configuration,
)
from formal_eval_plan import FORMAL_RUN_COUNT, FORMAL_TASK_COUNT, TASK_TIMEOUT_SECONDS


OUTPUT_JSON = ROOT / "output" / "gate4_formal_runs.json"
OUTPUT_MD = ROOT / "output" / "gate4_formal_runs.md"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


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


def checkpoint_recoverable(path: Path) -> bool:
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
    return (
        checkpoint.get("stage") != "task_started"
        and isinstance(retained, dict)
        and required <= set(retained)
    )


def secret_scan(root: Path) -> dict[str, Any]:
    key = os.environ.get("LLM_API_KEY", "")
    if not key:
        return {"performed": False, "matches": []}
    needle = key.encode("utf-8")
    matches: list[str] = []
    for current, directories, filenames in os.walk(root):
        current_path = Path(current)
        if "codex-home" in current_path.parts:
            index = current_path.parts.index("codex-home")
            relative = current_path.parts[index + 1 :]
            if relative and relative[0] in {".tmp", "skills", "agents", "tmp"}:
                directories[:] = []
                continue
        directories[:] = [
            name
            for name in directories
            if name not in {".git", "__pycache__", "node_modules", "source-artifacts"}
        ]
        for filename in filenames:
            path = current_path / filename
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


def inspect_task(group: str, task_id: str) -> dict[str, Any]:
    base = RUN_ROOT / group / task_id
    workspace = base / "workspace"
    result_path = base / "run_result.json"
    result = load_json(result_path) if result_path.exists() else {}
    receipt_path = workspace / "submission_receipt.json"
    receipt = load_json(receipt_path) if receipt_path.exists() else {}
    events = load_jsonl(workspace / "traces" / "events.jsonl")
    event_types = {str(row.get("event_type")) for row in events}
    state_path = workspace / ".audit-control" / "state.json"
    state = load_json(state_path) if state_path.exists() else {}
    invocations = state.get("subagent_invocations", {})
    if not isinstance(invocations, dict):
        invocations = {}
    authorized = len(invocations)
    completed = sum(
        isinstance(item, dict) and item.get("status") == "completed"
        for item in invocations.values()
    )
    required_events = {
        "task_started",
        "task_timeout" if result.get("timed_out") else "task_completed",
    }
    if receipt.get("status") == "accepted":
        required_events |= {
            "validation_started",
            "validation_completed",
            "submission_attempted",
            "submission_accepted",
        }
    return {
        "group": group,
        "task_id": task_id,
        "present": result_path.exists(),
        "accepted": receipt.get("status") == "accepted",
        "timed_out": bool(result.get("timed_out")),
        "elapsed_seconds": result.get("elapsed_seconds"),
        "within_budget": (
            isinstance(result.get("elapsed_seconds"), (int, float))
            and float(result["elapsed_seconds"]) <= TASK_TIMEOUT_SECONDS
        ),
        "final_submission_present": (workspace / "final_submission.json").exists(),
        "terminal_failure_recorded": bool(result.get("timed_out"))
        or (
            result.get("returncode") is not None
            and int(result.get("returncode")) != 0
        ),
        "run_manifest_present": (workspace / "run_manifest.json").exists(),
        "artifact_manifest_present": (workspace / "traces" / "artifact_manifest.json").exists(),
        "event_stream_complete": required_events <= event_types,
        "tool_trace_present": (workspace / "traces" / "tool_calls.jsonl").exists(),
        "trajectory_present": (base / "artifacts" / "trajectory.jsonl").exists(),
        "checkpoint_recoverable": checkpoint_recoverable(
            workspace / "work" / "context_checkpoint.json"
        ),
        "subagent_protocol_closed": authorized == completed,
        "authorized_subagents": authorized,
        "completed_subagents": completed,
    }


def build_report() -> dict[str, Any]:
    freeze = verify_frozen_configuration()
    tasks = load_tasks([])
    rows = [inspect_task(group, task["id"]) for group in GROUPS for task in tasks]
    by_group: dict[str, dict[str, Any]] = {}
    for group in GROUPS:
        selected = [row for row in rows if row["group"] == group]
        by_group[group] = {
            "runs": sum(row["present"] for row in selected),
            "accepted": sum(row["accepted"] for row in selected),
            "timeouts": sum(row["timed_out"] for row in selected),
            "within_budget": sum(row["within_budget"] for row in selected),
            "event_complete": sum(row["event_stream_complete"] for row in selected),
            "artifact_manifest": sum(row["artifact_manifest_present"] for row in selected),
            "checkpoint_recoverable": sum(row["checkpoint_recoverable"] for row in selected),
            "subagent_protocol_closed": sum(row["subagent_protocol_closed"] for row in selected),
        }
    retry_attempts = list((RUN_ROOT / "retry-history").glob("*/*/attempt-*"))
    registry_path = RUN_ROOT / "retry_registry.jsonl"
    retry_registry = load_jsonl(registry_path)
    registered_paths = {str(row.get("attempt_path")) for row in retry_registry}
    actual_retry_paths = {path.relative_to(ROOT).as_posix() for path in retry_attempts}
    mount_policy = formal_mount_policy()
    security = secret_scan(RUN_ROOT)
    enhanced = [group for group in GROUPS if group.endswith("enhanced")]
    checks = {
        "frozen_configuration_verified": bool(freeze),
        "configured_formal_cases_present": len(tasks) == FORMAL_TASK_COUNT,
        "all_formal_runs_present": sum(row["present"] for row in rows) == FORMAL_RUN_COUNT,
        "every_task_has_submission_or_terminal_failure": all(
            row["final_submission_present"] or row["terminal_failure_recorded"]
            for row in rows
        ),
        "every_task_has_run_manifest": all(row["run_manifest_present"] for row in rows),
        "every_task_has_artifact_manifest": all(row["artifact_manifest_present"] for row in rows),
        "every_task_has_complete_event_stream": all(row["event_stream_complete"] for row in rows),
        "every_task_has_tool_trace": all(row["tool_trace_present"] for row in rows),
        "every_task_has_trajectory": all(row["trajectory_present"] for row in rows),
        "enhanced_checkpoints_recoverable": all(
            row["checkpoint_recoverable"]
            for row in rows
            if row["group"] in enhanced
        ),
        "subagent_protocol_enforced": all(
            row["subagent_protocol_closed"] or not row["accepted"]
            for row in rows
        ),
        "all_reruns_registered_as_infrastructure": actual_retry_paths == registered_paths
        and all(
            row.get("classification") == "infrastructure" and str(row.get("reason", "")).strip()
            for row in retry_registry
        ),
        "formal_runtime_mounts_verified": mount_policy["required_present"]
        and mount_policy["hidden_absent"],
        "secret_not_persisted": security["performed"] and not security["matches"],
    }
    status = "pass" if all(checks.values()) else "fail"
    hard_standard_diagnostics = {
        "accepted_runs": sum(row["accepted"] for row in rows),
        "timeout_runs": sum(row["timed_out"] for row in rows),
        "timeout_by_group": {
            group: by_group[group]["timeouts"]
            for group in GROUPS
        },
        "groups_exceeding_one_timeout": [
            group for group in GROUPS if by_group[group]["timeouts"] > 1
        ],
        "note": "Performance hard standards are reported here but adjudicated in GATE5.",
    }
    return {
        "gate": "GATE4",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": status,
        "allow_next_gate": status == "pass",
        "checks": checks,
        "groups": by_group,
        "retry_attempts": [path.relative_to(ROOT).as_posix() for path in retry_attempts],
        "retry_registry": retry_registry,
        "security": security,
        "mount_policy": mount_policy,
        "hard_standard_diagnostics": hard_standard_diagnostics,
        "tasks": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# GATE4 正式任务运行与轨迹完整性报告",
        "",
        "## 结论",
        "",
        f"GATE4 **{'通过' if report['status'] == 'pass' else '未通过'}**。本报告只验证{FORMAL_RUN_COUNT}次正式运行与审计轨迹是否完整，不执行逐题语义判卷；逐题Rubric判卷属于GATE5。",
        "",
        f"## {len(GROUPS)}组运行结果",
        "",
        "| 实验组 | 已运行 | 已提交 | 超时 | 事件完整 | 产物清单 | 可恢复Checkpoint |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for group, value in report["groups"].items():
        lines.append(
            f"| {group} | {value['runs']}/{FORMAL_TASK_COUNT} | {value['accepted']}/{FORMAL_TASK_COUNT} | "
            f"{value['timeouts']} | {value['event_complete']}/{FORMAL_TASK_COUNT} | "
            f"{value['artifact_manifest']}/{FORMAL_TASK_COUNT} | {value['checkpoint_recoverable']}/{FORMAL_TASK_COUNT} |"
        )
    lines.extend(["", "## 验收项", "", "| 检查 | 结果 |", "| --- | --- |"])
    for name, passed in report["checks"].items():
        lines.append(f"| {name} | {'通过' if passed else '失败'} |")
    diagnostics = report["hard_standard_diagnostics"]
    lines.extend(
        [
            "",
            "## 性能诊断",
            "",
            f"- 成功提交：{diagnostics['accepted_runs']}/{FORMAL_RUN_COUNT}",
            f"- 超时任务：{diagnostics['timeout_runs']}",
            (
                "- 超过每组1题超时标准的实验组："
                + "、".join(diagnostics["groups_exceeding_one_timeout"])
                if diagnostics["groups_exceeding_one_timeout"]
                else "- 所有实验组均满足每组最多1题超时。"
            ),
            "- 以上属于GATE5选型硬标准，不影响GATE4对运行和轨迹是否完整的验收。",
        ]
    )
    lines.extend(
        [
            "",
            "## 重跑记录",
            "",
            (
                "- 无。每个正式案例每组只运行一次。"
                if not report["retry_registry"]
                else "\n".join(
                    f"- `{row['group']}/{row['task_id']}`：{row['classification']}，{row['reason']}"
                    for row in report["retry_registry"]
                )
            ),
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    OUTPUT_JSON.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    OUTPUT_MD.write_text(render_markdown(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "allow_next_gate": report["allow_next_gate"],
                "output": str(OUTPUT_MD),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
