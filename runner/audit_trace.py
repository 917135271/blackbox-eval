from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CORE_SCRIPTS = ROOT / "domain-enhancement" / "shared-audit-core" / "scripts"
sys.path.insert(0, str(CORE_SCRIPTS))

from audit_control_core import checkpoint_context, initialize_task_state, record_event  # noqa: E402


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temp.replace(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def redact_secret_in_tree(root: Path, secret: str) -> list[str]:
    if not secret:
        return []
    root = root.resolve()
    needle = secret.encode("utf-8")
    replacement = b"[REDACTED]"
    redacted: list[str] = []
    if not root.exists():
        return redacted
    text_suffixes = {
        "",
        ".bat",
        ".cfg",
        ".cmd",
        ".env",
        ".ini",
        ".json",
        ".jsonl",
        ".log",
        ".md",
        ".ps1",
        ".sh",
        ".toml",
        ".txt",
        ".yaml",
        ".yml",
    }
    for current, directories, filenames in os.walk(root, followlinks=False):
        current_path = Path(current)
        if "codex-home" in current_path.parts:
            codex_index = current_path.parts.index("codex-home")
            codex_relative = current_path.parts[codex_index + 1 :]
            if codex_relative and codex_relative[0] in {".tmp", "skills", "agents", "tmp"}:
                directories[:] = []
                continue
        directories[:] = [
            name
            for name in directories
            if name not in {".git", "__pycache__", "node_modules", "source-artifacts"}
        ]
        for filename in filenames:
            path = current_path / filename
            if path.suffix.lower() not in text_suffixes:
                continue
            try:
                if path.is_symlink():
                    continue
                size = path.stat().st_size
                if size == 0 or size > 50 * 1024 * 1024:
                    continue
                content = path.read_bytes()
            except OSError:
                continue
            if needle not in content:
                continue
            temp = path.with_suffix(path.suffix + ".redacting")
            temp.write_bytes(content.replace(needle, replacement))
            temp.replace(path)
            redacted.append(path.relative_to(root).as_posix())
    return redacted


def _load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return value if isinstance(value, dict) else {}


def _checkpoint_is_recoverable(path: Path) -> bool:
    checkpoint = _load_json_object(path)
    retained = checkpoint.get("retained_state")
    if not isinstance(retained, dict):
        return False
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


def _governance_artifact_paths(workspace: Path) -> list[Path]:
    paths: list[Path] = []
    for relative in ("final_submission.json", "submission_receipt.json"):
        path = workspace / relative
        if path.is_file():
            paths.append(path)
    for root in (workspace / "work", workspace / "traces"):
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.name == "artifact_manifest.json":
                continue
            if path.suffix.lower() in {".json", ".jsonl", ".sql", ".py", ".md", ".txt"}:
                paths.append(path)
    return sorted(set(paths))


def ensure_final_checkpoint(
    *,
    workspace: Path,
    task_id: str,
    experiment_group: str,
    timeout_seconds: int,
    elapsed_seconds: float,
) -> dict[str, Any]:
    workspace = workspace.resolve()
    checkpoint_path = workspace / "work" / "context_checkpoint.json"
    if not experiment_group.endswith("enhanced"):
        return {"accepted": True, "code": "BASELINE_NOT_REQUIRED"}
    if _checkpoint_is_recoverable(checkpoint_path):
        return {"accepted": True, "code": "EXISTING_CHECKPOINT_RETAINED"}

    final = _load_json_object(workspace / "final_submission.json")
    receipt = _load_json_object(workspace / "submission_receipt.json")
    evidence = _load_json_object(workspace / "work" / "evidence_matrix.json")
    audit_plan_path = workspace / "work" / "audit_plan.json"
    audit_plan: Any = _load_json_object(audit_plan_path)
    if not audit_plan:
        audit_plan = "outer_runner_finalization"
    task_path = workspace / "task.md"
    task_text = (
        task_path.read_text(encoding="utf-8", errors="replace")[:4000]
        if task_path.exists()
        else task_id
    )
    citations = final.get("citations", [])
    policies = sorted(
        {
            str(citation.get("doc_id"))
            for citation in citations
            if isinstance(citation, dict) and citation.get("doc_id")
        }
    )
    artifact_paths = [
        path.relative_to(workspace).as_posix()
        for path in _governance_artifact_paths(workspace)
    ]
    retained_state = {
        "task": task_text,
        "constraints": [
            "isolated GATE3 workspace",
            "formal answer assets prohibited",
            "outer runner timeout enforced",
        ],
        "audit_plan": audit_plan,
        "applicable_policies": policies,
        "record_ids": final.get("record_ids", []),
        "evidence_status": evidence.get("status", "not_recorded"),
        "unresolved_items": evidence.get("unresolved_items", []),
        "artifact_index": artifact_paths,
        "remaining_budget": {
            "timeout_seconds": timeout_seconds,
            "elapsed_seconds": round(elapsed_seconds, 3),
            "remaining_seconds": round(max(0.0, timeout_seconds - elapsed_seconds), 3),
        },
        "submission_status": receipt.get("status", "not_submitted"),
    }
    result = checkpoint_context(
        work_dir=workspace,
        task_id=task_id,
        stage="submission_ready",
        context_usage_percent=0.0,
        retained_state=retained_state,
        artifact_paths=artifact_paths,
        compacted=False,
        estimation_method="outer_runner_finalization",
    )
    if not result.get("accepted"):
        raise RuntimeError(f"failed to create final checkpoint for {task_id}: {result}")
    return result


def write_artifact_manifest(*, workspace: Path, task_id: str) -> dict[str, Any]:
    workspace = workspace.resolve()
    artifacts = [
        {
            "path": path.relative_to(workspace).as_posix(),
            "sha256": _sha256(path),
            "size_bytes": path.stat().st_size,
            "owner": "outer_runner",
        }
        for path in _governance_artifact_paths(workspace)
    ]
    manifest = {"task_id": task_id, "artifacts": artifacts}
    _write_json(workspace / "traces" / "artifact_manifest.json", manifest)
    return manifest


def finalize_governance_artifacts(
    *,
    workspace: Path,
    task_id: str,
    experiment_group: str,
    timeout_seconds: int,
    elapsed_seconds: float,
) -> dict[str, Any]:
    checkpoint = ensure_final_checkpoint(
        workspace=workspace,
        task_id=task_id,
        experiment_group=experiment_group,
        timeout_seconds=timeout_seconds,
        elapsed_seconds=elapsed_seconds,
    )
    artifact_manifest = write_artifact_manifest(workspace=workspace, task_id=task_id)
    return {"checkpoint": checkpoint, "artifact_manifest": artifact_manifest}


def start_run(
    *,
    workspace: Path,
    task_id: str,
    framework: str,
    experiment_group: str,
    model: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    workspace = workspace.resolve()
    budget = {"timeout_seconds": timeout_seconds}
    initialize_task_state(
        work_dir=workspace,
        task_id=task_id,
        framework=framework,
        experiment_group=experiment_group,
        budget=budget,
    )
    traces = workspace / "traces"
    traces.mkdir(parents=True, exist_ok=True)
    for name in ("tool_calls.jsonl", "subagents.jsonl", "context_events.jsonl"):
        (traces / name).touch(exist_ok=True)
    manifest = {
        "task_id": task_id,
        "framework": framework,
        "experiment_group": experiment_group,
        "model": model,
        "started_at": time.time(),
        "timeout_seconds": timeout_seconds,
        "status": "running",
        "returncode": None,
        "elapsed_seconds": None,
        "workspace": str(workspace),
        "artifacts": {},
    }
    _write_json(workspace / "run_manifest.json", manifest)
    record_event(
        work_dir=workspace,
        task_id=task_id,
        event_type="task_started",
        source="outer_runner",
        framework=framework,
        experiment_group=experiment_group,
        summary={"model": model, "timeout_seconds": timeout_seconds},
    )
    return manifest


def finish_run(
    *,
    workspace: Path,
    artifacts_dir: Path,
    task_id: str,
    framework: str,
    experiment_group: str,
    returncode: int | None,
    timed_out: bool,
    elapsed_seconds: float,
) -> dict[str, Any]:
    workspace = workspace.resolve()
    artifacts_dir = artifacts_dir.resolve()
    traces = workspace / "traces"
    traces.mkdir(parents=True, exist_ok=True)
    external_tool_log = artifacts_dir / "tool_calls.jsonl"
    if external_tool_log.exists():
        shutil.copy2(external_tool_log, traces / "tool_calls.jsonl")
        for line in external_tool_log.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                call = json.loads(line)
            except json.JSONDecodeError:
                continue
            occurred_at = float(call.get("ts", time.time()))
            summary = {
                "server": call.get("server"),
                "tool": call.get("tool"),
                "argument_fields": sorted((call.get("arguments") or {}).keys()),
            }
            record_event(
                work_dir=workspace,
                task_id=task_id,
                event_type="tool_started",
                source="outer_runner_tool_log",
                framework=framework,
                experiment_group=experiment_group,
                occurred_at=occurred_at,
                summary=summary,
            )
            record_event(
                work_dir=workspace,
                task_id=task_id,
                event_type="tool_completed" if call.get("ok") else "tool_failed",
                source="outer_runner_tool_log",
                framework=framework,
                experiment_group=experiment_group,
                occurred_at=occurred_at,
                error_code=None if call.get("ok") else str(call.get("error") or "TOOL_FAILED"),
                summary={
                    **summary,
                    "ok": bool(call.get("ok")),
                    "result_type": type(call.get("result_preview")).__name__,
                },
            )
    manifest_path = workspace / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(
        {
            "completed_at": time.time(),
            "status": "timeout" if timed_out else ("completed" if returncode == 0 else "failed"),
            "returncode": returncode,
            "elapsed_seconds": round(elapsed_seconds, 3),
        }
    )
    ensure_final_checkpoint(
        workspace=workspace,
        task_id=task_id,
        experiment_group=experiment_group,
        timeout_seconds=int(manifest.get("timeout_seconds", 0)),
        elapsed_seconds=elapsed_seconds,
    )
    record_event(
        work_dir=workspace,
        task_id=task_id,
        event_type="task_timeout" if timed_out else "task_completed",
        source="outer_runner",
        framework=framework,
        experiment_group=experiment_group,
        duration_ms=int(elapsed_seconds * 1000),
        error_code=None if returncode == 0 and not timed_out else ("TIMEOUT" if timed_out else "PROCESS_FAILED"),
        summary={
            "returncode": returncode,
            "run_status": manifest["status"],
            "submission_receipt_exists": (workspace / "submission_receipt.json").exists(),
        },
    )
    write_artifact_manifest(workspace=workspace, task_id=task_id)
    for path in (
        workspace / "final_submission.json",
        workspace / "submission_receipt.json",
        artifacts_dir / "trajectory.jsonl",
        artifacts_dir / "stderr.log",
        traces / "events.jsonl",
        traces / "tool_calls.jsonl",
        traces / "subagents.jsonl",
        traces / "context_events.jsonl",
        traces / "artifact_manifest.json",
        traces / "native_events.jsonl",
    ):
        if path.exists():
            manifest["artifacts"][str(path.relative_to(workspace) if workspace in path.parents else path.name)] = {
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
            }
    _write_json(manifest_path, manifest)
    return manifest
