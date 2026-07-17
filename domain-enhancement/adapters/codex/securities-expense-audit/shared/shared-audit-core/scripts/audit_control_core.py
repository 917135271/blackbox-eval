from __future__ import annotations

import json
import hashlib
import os
import re
import sqlite3
import time
import uuid
from copy import deepcopy
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


RECORD_ID_RE = re.compile(r"^R\d{6}$")
SECRET_RE = re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b")
FORBIDDEN_CONTEXT_MARKERS = (
    "ground_truth.yaml",
    "evals.json",
    "judge.py",
    "historical_answer",
    "prior_trajectory",
)
FINAL_FIELDS = {"anomaly_ids", "record_ids", "answer", "citations"}
SUMMARY_FIELDS = (
    "decision",
    "key_findings",
    "record_ids",
    "citations",
    "unresolved_items",
    "artifact_paths",
)
SUMMARY_DECISIONS = {"pass", "reject", "needs_more_evidence"}
EVENT_TYPES = {
    "task_started",
    "skill_selected",
    "tool_started",
    "tool_completed",
    "tool_failed",
    "subagent_requested",
    "subagent_authorized",
    "subagent_rejected",
    "subagent_completed",
    "artifact_written",
    "context_checkpoint",
    "context_compacted",
    "validation_started",
    "validation_completed",
    "submission_attempted",
    "submission_accepted",
    "submission_rejected",
    "task_completed",
    "task_timeout",
}
CONTEXT_STAGES = {
    "task_started",
    "planning_completed",
    "investigation_completed",
    "review_ready",
    "validation_ready",
    "submission_ready",
}


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def _atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temp, path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _redact(value: Any) -> Any:
    if isinstance(value, str):
        return SECRET_RE.sub("[REDACTED]", value)
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _redact(item) for key, item in value.items()}
    return value


@contextmanager
def _state_lock(control_dir: Path) -> Iterator[None]:
    control_dir.mkdir(parents=True, exist_ok=True)
    lock_path = control_dir / "state.lock"
    handle = lock_path.open("a+b")
    handle.seek(0, os.SEEK_END)
    if handle.tell() == 0:
        handle.write(b"0")
        handle.flush()
    try:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _control_paths(work_dir: Path) -> tuple[Path, Path]:
    control_dir = work_dir / ".audit-control"
    return control_dir, control_dir / "state.json"


def _read_state(state_path: Path, task_id: str) -> dict[str, Any]:
    if not state_path.exists():
        return {
            "task_id": task_id,
            "phase": "initialized",
            "event_sequence": 0,
            "subagent_calls": {},
            "subagent_invocations": {},
            "submission_attempts": 0,
            "submission_status": "not_submitted",
            "context": {
                "last_checkpoint_stage": None,
                "last_usage_percent": 0,
                "checkpoint_count": 0,
                "compaction_count": 0,
            },
        }
    state = _load_json(state_path)
    if state.get("task_id") != task_id:
        raise ValueError("workspace state belongs to a different task")
    return state


def record_event(
    *,
    work_dir: Path,
    task_id: str,
    event_type: str,
    source: str,
    role: str = "main_agent",
    reason_code: str | None = None,
    summary: dict[str, Any] | None = None,
    artifact_paths: list[str] | None = None,
    token_usage: dict[str, int] | None = None,
    duration_ms: int | None = None,
    error_code: str | None = None,
    framework: str | None = None,
    experiment_group: str | None = None,
    occurred_at: float | None = None,
) -> dict[str, Any]:
    if event_type not in EVENT_TYPES:
        raise ValueError(f"unsupported audit event type: {event_type}")
    work_dir = work_dir.resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    checked_artifacts: list[str] = []
    for raw_path in artifact_paths or []:
        path = _inside_workspace(work_dir, raw_path)
        checked_artifacts.append(path.relative_to(work_dir).as_posix())
    control_dir, state_path = _control_paths(work_dir)
    with _state_lock(control_dir):
        state = _read_state(state_path, task_id)
        sequence = int(state.get("event_sequence", 0)) + 1
        state["event_sequence"] = sequence
        _atomic_write_json(state_path, state)
        payload = {
            "task_id": task_id,
            "framework": framework or os.environ.get("AUDIT_FRAMEWORK", "unknown"),
            "experiment_group": experiment_group or os.environ.get("AUDIT_EXPERIMENT_GROUP", "unknown"),
            "role": role,
            "timestamp": occurred_at if occurred_at is not None else time.time(),
            "sequence": sequence,
            "event_type": event_type,
            "source": source,
            "reason_code": reason_code,
            "summary": _redact(summary or {}),
            "artifact_paths": checked_artifacts,
            "token_usage": token_usage or {},
            "duration_ms": duration_ms,
            "error_code": error_code,
        }
        traces = work_dir / "traces"
        traces.mkdir(parents=True, exist_ok=True)
        event_paths = [traces / "events.jsonl"]
        if event_type.startswith("subagent_"):
            event_paths.append(traces / "subagents.jsonl")
        if event_type.startswith("context_"):
            event_paths.append(traces / "context_events.jsonl")
        for event_path in event_paths:
            with event_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    return payload


def initialize_task_state(
    *,
    work_dir: Path,
    task_id: str,
    framework: str = "unknown",
    experiment_group: str = "unknown",
    budget: dict[str, Any] | None = None,
) -> dict[str, Any]:
    work_dir = work_dir.resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    control_dir, state_path = _control_paths(work_dir)
    with _state_lock(control_dir):
        state = _read_state(state_path, task_id)
        state.setdefault("phase", "task_started")
        if state["phase"] == "initialized":
            state["phase"] = "task_started"
        state.setdefault("framework", framework)
        state.setdefault("experiment_group", experiment_group)
        state.setdefault("budget", budget or {})
        _atomic_write_json(state_path, state)
    work = work_dir / "work"
    initial_files = {
        "task_state.json": {
            "task_id": task_id,
            "phase": "task_started",
            "scope": {},
            "budget": budget or {},
            "completed_steps": [],
            "pending_steps": [],
            "unresolved_items": [],
            "submission_status": "not_submitted",
        },
        "evidence_index.json": {
            "task_id": task_id,
            "records": {},
            "policies": {},
            "findings": {},
        },
        "context_checkpoint.json": {
            "task_id": task_id,
            "stage": "task_started",
            "context_usage_percent": 0,
            "compacted": False,
            "retained_state": {},
            "artifact_paths": [],
        },
        "artifact_index.json": {"task_id": task_id, "artifacts": []},
    }
    for name, value in initial_files.items():
        path = work / name
        if not path.exists():
            _atomic_write_json(path, value)
    decision_log = work / "decision_log.jsonl"
    decision_log.parent.mkdir(parents=True, exist_ok=True)
    decision_log.touch(exist_ok=True)
    return state


def _inside_workspace(work_dir: Path, raw_path: str, *, must_exist: bool = True) -> Path:
    work_root = work_dir.resolve()
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = work_root / candidate
    candidate = candidate.resolve()
    if candidate != work_root and work_root not in candidate.parents:
        raise ValueError(f"path escapes task workspace: {raw_path}")
    if must_exist and not candidate.exists():
        raise ValueError(f"required artifact does not exist: {raw_path}")
    return candidate


def _complexity_band(score: int) -> str:
    if score <= 1:
        return "0-1"
    if score <= 3:
        return "2-3"
    return "4-6"


def authorize_subagent(
    *,
    work_dir: Path,
    task_id: str,
    routing_rules_path: Path,
    role: str,
    reason_code: str,
    complexity: int,
    context: dict[str, Any],
    artifact_paths: list[str] | None = None,
    requested_token_budget: int = 8000,
) -> dict[str, Any]:
    work_dir = work_dir.resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    rules = _load_json(routing_rules_path)
    roles = rules.get("roles", {})
    record_event(
        work_dir=work_dir,
        task_id=task_id,
        event_type="subagent_requested",
        source="audit_control",
        role=role,
        reason_code=reason_code,
        summary={"complexity": complexity, "requested_token_budget": requested_token_budget},
        artifact_paths=artifact_paths or [],
    )
    def reject(code: str, message: str) -> dict[str, Any]:
        result = {"authorized": False, "code": code, "message": message}
        record_event(
            work_dir=work_dir,
            task_id=task_id,
            event_type="subagent_rejected",
            source="audit_control",
            role=role,
            reason_code=reason_code,
            error_code=code,
            summary={"complexity": complexity},
        )
        return result

    if role not in roles:
        return reject("UNKNOWN_ROLE", role)
    if not isinstance(complexity, int) or complexity < 0 or complexity > 6:
        return reject("INVALID_COMPLEXITY", "Use 0-6.")
    role_rule = roles[role]
    requested_token_budget = min(
        int(requested_token_budget),
        int(role_rule.get("max_token_budget", 12000)),
    )
    if reason_code not in role_rule.get("allowed_reason_codes", []):
        return reject("INVALID_REASON_CODE", f"{reason_code} is not allowed for {role}")
    if complexity < int(role_rule.get("minimum_complexity", 0)):
        return reject(
            "COMPLEXITY_TOO_LOW",
            f"{role} requires complexity >= {role_rule['minimum_complexity']}",
        )
    context_text = json.dumps(context, ensure_ascii=False, sort_keys=True)
    lowered = context_text.lower()
    marker = next((item for item in FORBIDDEN_CONTEXT_MARKERS if item in lowered), None)
    if marker:
        return reject(
            "FORBIDDEN_CONTEXT",
            f"Subagent context references forbidden asset: {marker}",
        )
    if SECRET_RE.search(context_text):
        return reject("SECRET_IN_CONTEXT", "Remove credentials.")
    if len(context_text) > 16000:
        return reject("CONTEXT_TOO_LARGE", "Reduce context to task facts and artifact paths.")
    if not 1000 <= int(requested_token_budget) <= 12000:
        return reject("INVALID_TOKEN_BUDGET", "Use a token budget from 1000 to 12000.")

    checked_artifacts: list[str] = []
    try:
        for raw_path in artifact_paths or []:
            path = _inside_workspace(work_dir, raw_path)
            checked_artifacts.append(path.relative_to(work_dir).as_posix())
        for required in role_rule.get("requires_artifacts", []):
            required_path = _inside_workspace(work_dir, required)
            rel = required_path.relative_to(work_dir).as_posix()
            if rel not in checked_artifacts:
                checked_artifacts.append(rel)
    except ValueError as exc:
        return reject("INVALID_ARTIFACT_PATH", str(exc))

    control_dir, state_path = _control_paths(work_dir)
    with _state_lock(control_dir):
        state = _read_state(state_path, task_id)
        calls = state.setdefault("subagent_calls", {})
        if int(calls.get(role, 0)) >= int(role_rule.get("max_calls", 1)):
            result = {
                "authorized": False,
                "code": "ROLE_CALL_LIMIT",
                "message": f"{role} has already been authorized for this task.",
            }
        else:
            band = _complexity_band(complexity)
            band_rule = rules["complexity_limits"][band]
            professional = {"policy_researcher", "data_analyst"}
            used_professional = sum(1 for name in professional if int(calls.get(name, 0)) > 0)
            if role in professional and used_professional >= int(band_rule["max_professional_roles"]):
                result = {
                    "authorized": False,
                    "code": "COMPLEXITY_ROLE_LIMIT",
                    "message": f"Complexity band {band} does not permit another professional role.",
                }
            elif role == "independent_reviewer" and not band_rule["reviewer_allowed"]:
                result = {
                    "authorized": False,
                    "code": "REVIEWER_NOT_ALLOWED",
                    "message": f"Complexity band {band} does not permit a reviewer.",
                }
            else:
                invocation_id = str(uuid.uuid4())
                calls[role] = int(calls.get(role, 0)) + 1
                state.setdefault("subagent_invocations", {})[invocation_id] = {
                    "invocation_id": invocation_id,
                    "role": role,
                    "reason_code": reason_code,
                    "complexity": complexity,
                    "token_budget": int(requested_token_budget),
                    "status": "authorized",
                    "authorized_at": time.time(),
                    "artifact_paths": checked_artifacts,
                }
                _atomic_write_json(state_path, state)
                role_dir = work_dir / "work" / "subagents" / role
                role_dir.mkdir(parents=True, exist_ok=True)
                result = {
                    "authorized": True,
                    "code": "AUTHORIZED",
                    "invocation_id": invocation_id,
                    "role": role,
                    "reason_code": reason_code,
                    "complexity": complexity,
                    "token_budget": int(requested_token_budget),
                    "artifact_paths": checked_artifacts,
                    "role_work_dir": role_dir.relative_to(work_dir).as_posix(),
                    "required_summary_fields": list(SUMMARY_FIELDS),
                    "summary_max_chars": int(rules.get("summary_max_chars", 6000)),
                    "instruction": (
                        "Invoke the framework-native subagent for this role. Give it only the supplied "
                        "context and artifact paths. It must not create another subagent."
                    ),
                }
    record_event(
        work_dir=work_dir,
        task_id=task_id,
        event_type="subagent_authorized" if result["authorized"] else "subagent_rejected",
        source="audit_control",
        role=role,
        reason_code=reason_code,
        summary={
            "invocation_id": result.get("invocation_id"),
            "complexity": complexity,
            "token_budget": result.get("token_budget"),
        },
        artifact_paths=result.get("artifact_paths", []),
        error_code=None if result["authorized"] else result["code"],
    )
    return result


def _validate_subagent_summary(summary: Any, max_chars: int) -> list[str]:
    errors: list[str] = []
    if not isinstance(summary, dict):
        return ["summary must be a JSON object"]
    missing = sorted(set(SUMMARY_FIELDS) - set(summary))
    extra = sorted(set(summary) - set(SUMMARY_FIELDS))
    if missing:
        errors.append(f"missing fields: {missing}")
    if extra:
        errors.append(f"unsupported fields: {extra}")
    if summary.get("decision") not in SUMMARY_DECISIONS:
        errors.append(f"decision must be one of {sorted(SUMMARY_DECISIONS)}")
    for field in SUMMARY_FIELDS[1:]:
        if not isinstance(summary.get(field), list):
            errors.append(f"{field} must be an array")
    text = json.dumps(summary, ensure_ascii=False, sort_keys=True)
    if len(text) > max_chars:
        errors.append(f"summary exceeds {max_chars} characters")
    if SECRET_RE.search(text):
        errors.append("summary contains a credential-like value")
    return errors


def complete_subagent(
    *,
    work_dir: Path,
    task_id: str,
    invocation_id: str,
    summary: dict[str, Any] | None = None,
    summary_path: str | None = None,
    artifact_paths: list[str] | None = None,
    token_usage: dict[str, int] | None = None,
    status: str = "completed",
) -> dict[str, Any]:
    work_dir = work_dir.resolve()
    if (summary is None) == (summary_path is None):
        return {
            "completed": False,
            "code": "SUMMARY_INPUT_ERROR",
            "message": "Provide exactly one of summary or summary_path.",
        }
    if summary_path is not None:
        try:
            summary_file = _inside_workspace(work_dir, summary_path)
            summary = _load_json(summary_file)
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            return {"completed": False, "code": "INVALID_SUMMARY_PATH", "message": str(exc)}
    assert summary is not None

    control_dir, state_path = _control_paths(work_dir)
    with _state_lock(control_dir):
        state = _read_state(state_path, task_id)
        invocation = state.setdefault("subagent_invocations", {}).get(invocation_id)
        if invocation is None:
            return {"completed": False, "code": "UNKNOWN_INVOCATION", "message": invocation_id}
        if invocation.get("status") == "completed":
            return {
                "completed": False,
                "code": "ALREADY_COMPLETED",
                "message": invocation_id,
            }
        role = str(invocation["role"])
        max_chars = int(_load_json(
            Path(__file__).resolve().parents[1] / "routing" / "routing_rules.json"
        ).get("summary_max_chars", 6000))
        summary_errors = _validate_subagent_summary(summary, max_chars)
        if summary_errors:
            return {
                "completed": False,
                "code": "INVALID_SUMMARY",
                "errors": summary_errors,
            }
        submitted_paths = list(dict.fromkeys((artifact_paths or []) + list(summary["artifact_paths"])))
        checked: list[dict[str, Any]] = []
        role_root = (work_dir / "work" / "subagents" / role).resolve()
        try:
            for raw_path in submitted_paths:
                path = _inside_workspace(work_dir, raw_path)
                if path != role_root and role_root not in path.parents:
                    raise ValueError(f"subagent artifact is outside role directory: {raw_path}")
                checked.append(
                    {
                        "path": path.relative_to(work_dir).as_posix(),
                        "sha256": _sha256(path),
                        "size_bytes": path.stat().st_size,
                    }
                )
        except ValueError as exc:
            return {"completed": False, "code": "INVALID_ARTIFACT_PATH", "message": str(exc)}
        if not checked:
            return {
                "completed": False,
                "code": "MISSING_ARTIFACT",
                "message": "At least one role artifact is required.",
            }
        token_usage = token_usage or {}
        total_tokens = int(token_usage.get("total_tokens", 0))
        if total_tokens < 0 or total_tokens > int(invocation["token_budget"]):
            return {
                "completed": False,
                "code": "TOKEN_BUDGET_EXCEEDED",
                "message": f"{total_tokens} exceeds {invocation['token_budget']}",
            }
        if status != "completed":
            return {"completed": False, "code": "INVALID_STATUS", "message": status}
        invocation.update(
            {
                "status": "completed",
                "completed_at": time.time(),
                "summary": summary,
                "artifacts": checked,
                "token_usage": token_usage,
            }
        )
        _atomic_write_json(state_path, state)

    manifest_path = work_dir / "traces" / "artifact_manifest.json"
    manifest = _load_json(manifest_path) if manifest_path.exists() else {"task_id": task_id, "artifacts": []}
    known = {item.get("path") for item in manifest["artifacts"] if isinstance(item, dict)}
    for item in checked:
        if item["path"] not in known:
            manifest["artifacts"].append({**item, "owner": role, "invocation_id": invocation_id})
    _atomic_write_json(manifest_path, manifest)
    artifact_index_path = work_dir / "work" / "artifact_index.json"
    artifact_index = (
        _load_json(artifact_index_path)
        if artifact_index_path.exists()
        else {"task_id": task_id, "artifacts": []}
    )
    indexed = {item.get("path") for item in artifact_index["artifacts"] if isinstance(item, dict)}
    for item in checked:
        if item["path"] not in indexed:
            artifact_index["artifacts"].append(
                {**item, "owner": role, "invocation_id": invocation_id}
            )
    _atomic_write_json(artifact_index_path, artifact_index)
    with (work_dir / "work" / "decision_log.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "ts": time.time(),
                    "actor": role,
                    "decision": summary["decision"],
                    "invocation_id": invocation_id,
                    "unresolved_items": summary["unresolved_items"],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n"
        )
    for item in checked:
        record_event(
            work_dir=work_dir,
            task_id=task_id,
            event_type="artifact_written",
            source="audit_control",
            role=role,
            reason_code=invocation["reason_code"],
            summary={
                "invocation_id": invocation_id,
                "sha256": item["sha256"],
                "size_bytes": item["size_bytes"],
            },
            artifact_paths=[item["path"]],
        )
    record_event(
        work_dir=work_dir,
        task_id=task_id,
        event_type="subagent_completed",
        source="audit_control",
        role=role,
        reason_code=invocation["reason_code"],
        summary={
            "invocation_id": invocation_id,
            "decision": summary["decision"],
            "key_findings_count": len(summary["key_findings"]),
            "unresolved_count": len(summary["unresolved_items"]),
        },
        artifact_paths=[item["path"] for item in checked],
        token_usage=token_usage,
    )
    return {
        "completed": True,
        "code": "COMPLETED",
        "invocation_id": invocation_id,
        "role": role,
        "summary": summary,
        "artifacts": checked,
    }


def checkpoint_context(
    *,
    work_dir: Path,
    task_id: str,
    stage: str,
    context_usage_percent: float,
    retained_state: dict[str, Any],
    artifact_paths: list[str] | None = None,
    compacted: bool = False,
    estimation_method: str = "reported_tokens",
) -> dict[str, Any]:
    if stage not in CONTEXT_STAGES:
        return {"accepted": False, "code": "INVALID_STAGE", "message": stage}
    if not 0 <= float(context_usage_percent) <= 100:
        return {
            "accepted": False,
            "code": "INVALID_CONTEXT_USAGE",
            "message": "context_usage_percent must be 0-100",
        }
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
    missing = sorted(required - set(retained_state))
    if missing:
        return {"accepted": False, "code": "INCOMPLETE_RETAINED_STATE", "missing": missing}
    work_dir = work_dir.resolve()
    checked_paths: list[str] = []
    try:
        for raw_path in artifact_paths or []:
            path = _inside_workspace(work_dir, raw_path)
            checked_paths.append(path.relative_to(work_dir).as_posix())
    except ValueError as exc:
        return {"accepted": False, "code": "INVALID_ARTIFACT_PATH", "message": str(exc)}
    checkpoint = {
        "task_id": task_id,
        "stage": stage,
        "context_usage_percent": float(context_usage_percent),
        "compacted": bool(compacted),
        "estimation_method": estimation_method,
        "retained_state": retained_state,
        "artifact_paths": checked_paths,
        "created_at": time.time(),
    }
    _atomic_write_json(work_dir / "work" / "context_checkpoint.json", checkpoint)
    task_state_path = work_dir / "work" / "task_state.json"
    task_state = (
        _load_json(task_state_path)
        if task_state_path.exists()
        else {
            "task_id": task_id,
            "phase": stage,
            "scope": {},
            "budget": {},
            "completed_steps": [],
            "pending_steps": [],
            "unresolved_items": [],
            "submission_status": "not_submitted",
        }
    )
    task_state["phase"] = stage
    task_state["unresolved_items"] = retained_state["unresolved_items"]
    task_state["submission_status"] = retained_state["submission_status"]
    _atomic_write_json(task_state_path, task_state)
    control_dir, state_path = _control_paths(work_dir)
    with _state_lock(control_dir):
        state = _read_state(state_path, task_id)
        context_state = state.setdefault("context", {})
        context_state["last_checkpoint_stage"] = stage
        context_state["last_usage_percent"] = float(context_usage_percent)
        context_state["checkpoint_count"] = int(context_state.get("checkpoint_count", 0)) + 1
        if compacted:
            context_state["compaction_count"] = int(context_state.get("compaction_count", 0)) + 1
        state["phase"] = stage
        _atomic_write_json(state_path, state)
    record_event(
        work_dir=work_dir,
        task_id=task_id,
        event_type="context_compacted" if compacted else "context_checkpoint",
        source="audit_control",
        reason_code=stage,
        summary={
            "context_usage_percent": float(context_usage_percent),
            "estimation_method": estimation_method,
        },
        artifact_paths=checked_paths,
    )
    return {"accepted": True, "code": "CHECKPOINT_RECORDED", "checkpoint": checkpoint}


def _error(code: str, field: str, message: str) -> dict[str, str]:
    return {"code": code, "field": field, "message": message}


def _duplicates(values: list[Any]) -> list[Any]:
    duplicates: list[Any] = []
    seen: set[str] = set()
    for value in values:
        key = json.dumps(value, ensure_ascii=False, sort_keys=True)
        if key in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(key)
    return duplicates


def _pass_value(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"pass", "passed", "true", "ok", "complete", "completed"}
    if isinstance(value, dict):
        return any(_pass_value(value.get(key)) for key in ("status", "result", "passed", "pass", "complete"))
    return False


def _normalized_evidence_matrix(value: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(value)
    aliases = {
        "coverage_percent": ("coverage", "coverage_pct"),
        "submitted_record_ids": ("submitted_records", "final_record_ids", "record_ids"),
        "candidate_record_ids": ("candidate_records", "matched_record_ids"),
        "unowned_record_ids": ("unowned_records",),
        "unused_candidate_record_ids": ("unused_candidates", "unused_candidate_records"),
    }
    for canonical, alternatives in aliases.items():
        if canonical not in normalized:
            for alternative in alternatives:
                if alternative in normalized:
                    normalized[canonical] = normalized[alternative]
                    break
    for field in ("unowned_record_ids", "unused_candidate_record_ids", "unused_citations", "missing_evidence", "unresolved_items"):
        if normalized.get(field) is None:
            normalized[field] = []
    no_anomaly = normalized.get("no_anomaly_coverage")
    if not isinstance(no_anomaly, dict):
        search_proof = normalized.get("search_proof")
        if isinstance(search_proof, str) and search_proof.strip():
            normalized["no_anomaly_coverage"] = {
                "complete": True,
                "search_proof": search_proof.strip(),
            }
    elif no_anomaly and "complete" not in no_anomaly:
        no_anomaly["complete"] = True
    rows = normalized.get("evidence_rows", [])
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            if not row.get("citations") and isinstance(row.get("policy"), dict):
                policy = row["policy"]
                if policy.get("doc_id") and policy.get("clause_no"):
                    row["citations"] = [{"doc_id": policy["doc_id"], "clause_no": policy["clause_no"]}]
            if "fact_supported" not in row and row.get("facts"):
                row["fact_supported"] = True
            elif "fact_supported" in row:
                row["fact_supported"] = _pass_value(row["fact_supported"])
            if "rule_supported" not in row and row.get("citations"):
                row["rule_supported"] = True
            elif "rule_supported" in row:
                row["rule_supported"] = _pass_value(row["rule_supported"])
            if "coverage_status" not in row and row.get("fact_supported") and row.get("rule_supported"):
                row["coverage_status"] = "pass"
    return normalized


def _normalized_validation_report(value: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(value)
    if "submission_allowed" not in normalized and "submission_permission" in normalized:
        normalized["submission_allowed"] = _pass_value(normalized["submission_permission"])
    return normalized


def _existing_record_ids(db_path: Path, record_ids: list[str]) -> set[str]:
    if not record_ids:
        return set()
    uri = f"file:{db_path.resolve().as_posix()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        placeholders = ",".join("?" for _ in record_ids)
        rows = connection.execute(
            f"SELECT record_id FROM expense_records WHERE record_id IN ({placeholders})",
            record_ids,
        ).fetchall()
    return {row[0] for row in rows}


def _policy_documents(corpus_dir: Path) -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in corpus_dir.glob("*.md")
        if path.is_file()
    }


def validate_submission(
    *,
    result: Any,
    expense_db: Path,
    policy_corpus_dir: Path,
    evidence_matrix: dict[str, Any],
    validation_report: dict[str, Any],
) -> dict[str, Any]:
    evidence_matrix = _normalized_evidence_matrix(evidence_matrix)
    validation_report = _normalized_validation_report(validation_report)
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    repairable_fields: set[str] = set()

    if not isinstance(result, dict):
        return {
            "valid": False,
            "errors": [_error("TYPE_ERROR", "$", "Final result must be a JSON object.")],
            "warnings": [],
            "repairable_fields": ["$"],
        }
    missing = sorted(FINAL_FIELDS - set(result))
    extra = sorted(set(result) - FINAL_FIELDS)
    for field in missing:
        errors.append(_error("MISSING_FIELD", field, "Required field is missing."))
        repairable_fields.add(field)
    for field in extra:
        errors.append(_error("EXTRA_FIELD", field, "Remove unsupported top-level field."))
        repairable_fields.add(field)

    anomaly_ids = result.get("anomaly_ids", [])
    record_ids = result.get("record_ids", [])
    citations = result.get("citations", [])
    answer = result.get("answer", "")
    for field, value in (("anomaly_ids", anomaly_ids), ("record_ids", record_ids), ("citations", citations)):
        if not isinstance(value, list):
            errors.append(_error("TYPE_ERROR", field, "Field must be an array."))
            repairable_fields.add(field)
    if not isinstance(answer, str) or not answer.strip():
        errors.append(_error("TYPE_ERROR", "answer", "Answer must be a non-empty string."))
        repairable_fields.add("answer")
    elif SECRET_RE.search(answer):
        errors.append(_error("SECRET_DETECTED", "answer", "Answer contains a credential-like value."))
        repairable_fields.add("answer")

    if not all(isinstance(value, list) for value in (anomaly_ids, record_ids, citations)):
        return {
            "valid": False,
            "errors": errors,
            "warnings": warnings,
            "repairable_fields": sorted(repairable_fields),
        }

    for field, values in (("anomaly_ids", anomaly_ids), ("record_ids", record_ids), ("citations", citations)):
        duplicates = _duplicates(values)
        if duplicates:
            errors.append(_error("DUPLICATE_VALUE", field, f"Duplicate values: {duplicates}"))
            repairable_fields.add(field)
    invalid_anomalies = [value for value in anomaly_ids if not isinstance(value, str) or not value.strip()]
    invalid_records = [value for value in record_ids if not isinstance(value, str) or not RECORD_ID_RE.fullmatch(value)]
    if invalid_anomalies:
        errors.append(_error("INVALID_ID_FORMAT", "anomaly_ids", f"Invalid IDs: {invalid_anomalies}"))
        repairable_fields.add("anomaly_ids")
    if invalid_records:
        errors.append(_error("INVALID_ID_FORMAT", "record_ids", f"Invalid IDs: {invalid_records}"))
        repairable_fields.add("record_ids")

    valid_record_ids = [value for value in record_ids if isinstance(value, str) and RECORD_ID_RE.fullmatch(value)]
    existing = _existing_record_ids(expense_db, valid_record_ids)
    unknown_records = sorted(set(valid_record_ids) - existing)
    if unknown_records:
        errors.append(_error("UNKNOWN_RECORD_ID", "record_ids", f"Unknown record IDs: {unknown_records}"))
        repairable_fields.add("record_ids")

    documents = _policy_documents(policy_corpus_dir)
    normalized_citations: list[tuple[str, str]] = []
    for index, citation in enumerate(citations):
        field = f"citations[{index}]"
        if not isinstance(citation, dict) or set(citation) != {"doc_id", "clause_no"}:
            errors.append(_error("INVALID_CITATION", field, "Citation must contain only doc_id and clause_no."))
            repairable_fields.add("citations")
            continue
        doc_id = citation.get("doc_id")
        clause_no = citation.get("clause_no")
        if not isinstance(doc_id, str) or not doc_id.strip() or not isinstance(clause_no, str) or not clause_no.strip():
            errors.append(_error("INVALID_CITATION", field, "Citation values must be non-empty strings."))
            repairable_fields.add("citations")
            continue
        if doc_id not in documents:
            errors.append(_error("UNKNOWN_POLICY_ID", field + ".doc_id", f"Unknown policy document: {doc_id}"))
            repairable_fields.add("citations")
            continue
        if clause_no not in documents[doc_id]:
            errors.append(_error("UNKNOWN_POLICY_CLAUSE", field + ".clause_no", f"Clause not found in {doc_id}: {clause_no}"))
            repairable_fields.add("citations")
            continue
        normalized_citations.append((doc_id, clause_no))

    answer_text = answer.strip().lower() if isinstance(answer, str) else ""
    no_anomaly_phrases = ("未发现异常", "无异常", "no anomaly", "no anomalies")
    positive_phrases = ("确认存在异常", "发现存在异常", "confirmed anomaly")
    if anomaly_ids and any(phrase in answer_text for phrase in no_anomaly_phrases):
        errors.append(_error("ANSWER_CONTRADICTION", "answer", "Answer says no anomaly but anomaly_ids is not empty."))
        repairable_fields.add("answer")
    if not anomaly_ids and any(phrase in answer_text for phrase in positive_phrases):
        errors.append(_error("ANSWER_CONTRADICTION", "answer", "Answer confirms an anomaly but anomaly_ids is empty."))
        repairable_fields.update(("answer", "anomaly_ids"))

    if evidence_matrix.get("status") != "pass" or evidence_matrix.get("coverage_percent") != 100:
        errors.append(_error("EVIDENCE_NOT_PASSED", "evidence_matrix", "Evidence status must be pass with 100 percent coverage."))
    for field in ("unowned_record_ids", "unused_candidate_record_ids", "missing_evidence", "unresolved_items"):
        if evidence_matrix.get(field):
            errors.append(_error("EVIDENCE_GAP", f"evidence_matrix.{field}", "Evidence matrix contains an unresolved gap."))

    matrix_records = evidence_matrix.get("submitted_record_ids")
    if not isinstance(matrix_records, list) or set(matrix_records) != set(record_ids):
        errors.append(_error("RECORD_SET_MISMATCH", "record_ids", "Final record_ids do not match the evidence matrix."))
        repairable_fields.add("record_ids")

    rows = evidence_matrix.get("evidence_rows", [])
    row_anomalies = {row.get("anomaly_id") for row in rows if isinstance(row, dict) and row.get("anomaly_id")}
    if set(anomaly_ids) != row_anomalies:
        errors.append(_error("ANOMALY_SET_MISMATCH", "anomaly_ids", "Final anomaly_ids do not match evidence rows."))
        repairable_fields.add("anomaly_ids")
    row_records: set[str] = set()
    row_citations: set[tuple[str, str]] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(_error("INVALID_EVIDENCE_ROW", f"evidence_rows[{index}]", "Evidence row must be an object."))
            continue
        row_records.update(value for value in row.get("record_ids", []) if isinstance(value, str))
        for citation in row.get("citations", []):
            if isinstance(citation, dict) and isinstance(citation.get("doc_id"), str) and isinstance(citation.get("clause_no"), str):
                row_citations.add((citation["doc_id"], citation["clause_no"]))
        if row.get("anomaly_id") and not row.get("record_ids"):
            errors.append(_error("MISSING_FINDING_RECORD", f"evidence_rows[{index}].record_ids", "An anomaly requires at least one supporting record."))
        if row.get("anomaly_id") and not row.get("citations"):
            errors.append(_error("MISSING_FINDING_CITATION", f"evidence_rows[{index}].citations", "An anomaly requires at least one supporting policy citation."))
        if row.get("anomaly_id") and not row.get("facts"):
            errors.append(_error("MISSING_FINDING_FACT", f"evidence_rows[{index}].facts", "An anomaly requires verified facts."))
        if row.get("fact_supported") is not True or row.get("rule_supported") is not True or row.get("coverage_status") != "pass":
            errors.append(_error("INCOMPLETE_EVIDENCE_ROW", f"evidence_rows[{index}]", "Finding lacks passed fact or rule evidence."))
    if anomaly_ids and set(record_ids) != row_records:
        errors.append(_error("EVIDENCE_RECORD_MISMATCH", "record_ids", "Finding evidence rows do not cover the final record set."))
        repairable_fields.add("record_ids")
    if anomaly_ids and set(normalized_citations) != row_citations:
        errors.append(_error("EVIDENCE_CITATION_MISMATCH", "citations", "Finding evidence rows do not match final citations."))
        repairable_fields.add("citations")
    if not anomaly_ids:
        no_anomaly = evidence_matrix.get("no_anomaly_coverage")
        if not isinstance(no_anomaly, dict) or no_anomaly.get("complete") is not True:
            errors.append(_error("NO_ANOMALY_COVERAGE_MISSING", "evidence_matrix.no_anomaly_coverage", "No-anomaly result lacks complete search proof."))

    if validation_report.get("status") != "pass" or validation_report.get("submission_allowed") is not True:
        errors.append(_error("VALIDATION_NOT_PASSED", "validation_report", "Validation report must explicitly allow submission."))
    repair_count = validation_report.get("repair_count")
    if not isinstance(repair_count, int) or repair_count < 0 or repair_count > 1:
        errors.append(_error("INVALID_REPAIR_COUNT", "validation_report.repair_count", "Repair count must be 0 or 1."))
    if validation_report.get("errors"):
        errors.append(_error("VALIDATION_ERRORS_PRESENT", "validation_report.errors", "Passed validation report cannot contain errors."))

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "repairable_fields": sorted(repairable_fields),
        "checks": {
            "record_ids_checked": len(valid_record_ids),
            "citations_checked": len(citations),
            "evidence_rows_checked": len(rows),
            "hidden_answer_mapping_used": False,
        },
    }


def submit_result(
    *,
    work_dir: Path,
    task_id: str,
    expense_db: Path,
    policy_corpus_dir: Path,
    result: Any,
    evidence_matrix_path: str = "work/evidence_matrix.json",
    validation_report_path: str = "work/validation_report.json",
) -> dict[str, Any]:
    work_dir = work_dir.resolve()
    record_event(
        work_dir=work_dir,
        task_id=task_id,
        event_type="submission_attempted",
        source="audit_control",
        summary={
            "anomaly_count": len(result.get("anomaly_ids", [])) if isinstance(result, dict) else None,
            "record_count": len(result.get("record_ids", [])) if isinstance(result, dict) else None,
        },
    )
    control_dir, state_path = _control_paths(work_dir)
    with _state_lock(control_dir):
        state = _read_state(state_path, task_id)
        pending = [
            invocation_id
            for invocation_id, invocation in state.get("subagent_invocations", {}).items()
            if invocation.get("status") != "completed"
        ]
    if pending:
        response = {
            "status": "rejected",
            "code": "SUBAGENT_COMPLETION_REQUIRED",
            "message": "Authorized subagents must be completed before submission.",
            "pending_invocation_ids": pending,
        }
        record_event(
            work_dir=work_dir,
            task_id=task_id,
            event_type="submission_rejected",
            source="audit_control",
            error_code=response["code"],
            summary={"pending_invocation_ids": pending},
        )
        return response
    evidence_path = _inside_workspace(work_dir, evidence_matrix_path)
    validation_path = _inside_workspace(work_dir, validation_report_path)
    evidence_matrix = _load_json(evidence_path)
    validation_report = _load_json(validation_path)
    report = validate_submission(
        result=result,
        expense_db=expense_db,
        policy_corpus_dir=policy_corpus_dir,
        evidence_matrix=evidence_matrix,
        validation_report=validation_report,
    )

    with _state_lock(control_dir):
        state = _read_state(state_path, task_id)
        if state.get("submission_status") == "accepted":
            response = {
                "status": "rejected",
                "code": "ALREADY_SUBMITTED",
                "message": "A final result was already accepted for this task.",
            }
        else:
            state["submission_attempts"] = int(state.get("submission_attempts", 0)) + 1
            attempt = state["submission_attempts"]
            if attempt > 2:
                state["submission_status"] = "rejected"
                response = {
                    "status": "rejected",
                    "code": "REPAIR_LIMIT_EXCEEDED",
                    "attempt": attempt,
                    "errors": report["errors"],
                }
            elif report["valid"]:
                state["submission_status"] = "accepted"
                final_path = work_dir / "final_submission.json"
                _atomic_write_json(final_path, result)
                receipt = {
                    "task_id": task_id,
                    "status": "accepted",
                    "attempt": attempt,
                    "submitted_at": time.time(),
                    "final_submission": final_path.relative_to(work_dir).as_posix(),
                    "checks": report.get("checks", {}),
                }
                _atomic_write_json(work_dir / "submission_receipt.json", receipt)
                response = receipt
            elif attempt == 1:
                state["submission_status"] = "repair_required"
                response = {
                    "status": "repair_required",
                    "code": "VALIDATION_FAILED",
                    "attempt": attempt,
                    "remaining_repair_attempts": 1,
                    "errors": report["errors"],
                    "warnings": report["warnings"],
                    "repairable_fields": report["repairable_fields"],
                }
            else:
                state["submission_status"] = "rejected"
                response = {
                    "status": "rejected",
                    "code": "VALIDATION_FAILED_AFTER_REPAIR",
                    "attempt": attempt,
                    "remaining_repair_attempts": 0,
                    "errors": report["errors"],
                    "warnings": report["warnings"],
                }
            _atomic_write_json(state_path, state)

    record_event(
        work_dir=work_dir,
        task_id=task_id,
        event_type="submission_accepted" if response["status"] == "accepted" else "submission_rejected",
        source="audit_control",
        summary={
            "status": response["status"],
            "attempt": response.get("attempt"),
            "anomaly_count": len(result.get("anomaly_ids", [])) if isinstance(result, dict) else None,
            "record_count": len(result.get("record_ids", [])) if isinstance(result, dict) else None,
        },
        artifact_paths=["final_submission.json", "submission_receipt.json"]
        if response["status"] == "accepted"
        else [],
        error_code=response.get("code") if response["status"] != "accepted" else None,
    )
    task_state_path = work_dir / "work" / "task_state.json"
    if task_state_path.exists():
        task_state = _load_json(task_state_path)
        task_state["submission_status"] = response["status"]
        if response["status"] == "accepted":
            task_state["phase"] = "completed"
        _atomic_write_json(task_state_path, task_state)
    return response
