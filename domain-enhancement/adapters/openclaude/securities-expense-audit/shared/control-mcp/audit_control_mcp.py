from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable


HERE = Path(__file__).resolve().parent
CORE_ROOT = HERE.parent / "shared-audit-core"
sys.path.insert(0, str(CORE_ROOT / "scripts"))

from audit_control_core import (  # noqa: E402
    authorize_subagent,
    checkpoint_context,
    complete_subagent,
    initialize_task_state,
    record_event,
    submit_result,
    validate_submission,
)


def _env_path(name: str, default: Path | None = None) -> Path:
    raw = os.environ.get(name)
    if raw:
        return Path(raw).resolve()
    if default is not None:
        return default.resolve()
    raise ValueError(f"missing environment variable: {name}")


def _planned_subagent(role: str) -> dict[str, Any]:
    plan_path = _env_path("AUDIT_WORK_DIR") / "work" / "audit_plan.json"
    if not plan_path.exists():
        return {}
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(plan, dict):
        return {}
    subagent_plan = plan.get("subagent_plan")
    role_plan = subagent_plan.get(role, {}) if isinstance(subagent_plan, dict) else {}
    return {
        "complexity": plan.get("complexity", plan.get("complexity_score")),
        "reason_code": role_plan.get("reason_code") if isinstance(role_plan, dict) else None,
        "role_task": role_plan.get("role_task") if isinstance(role_plan, dict) else None,
    }


def _task_id() -> str:
    return os.environ.get("AUDIT_TASK_ID", "unassigned-task")


def _ensure_task_initialized() -> None:
    initialize_task_state(
        work_dir=_env_path("AUDIT_WORK_DIR"),
        task_id=_task_id(),
        framework=os.environ.get("AUDIT_FRAMEWORK", "unknown"),
        experiment_group=os.environ.get("AUDIT_EXPERIMENT_GROUP", "unknown"),
    )


def authorize_audit_subagent(
    reason_code: str | None = None,
    complexity: int | None = None,
    context: dict[str, Any] | str | None = None,
    role: str | None = None,
    artifact_paths: list[str] | None = None,
    requested_token_budget: int = 8000,
    agent_role: str | None = None,
    question: str | None = None,
    subagent_type: str | None = None,
    reason: str | None = None,
    task_summary: str | None = None,
    task_description: str | None = None,
    task: str | None = None,
    prompt: str | None = None,
    allowed_tools: list[str] | None = None,
    budget: str | int | None = None,
) -> dict[str, Any]:
    """Authorize one native audit subagent invocation and return its bounded dispatch contract."""
    _ensure_task_initialized()
    role = role or agent_role or subagent_type
    if role is None:
        raise ValueError("role is required")
    planned = _planned_subagent(role)
    reason_code = reason_code or reason or planned.get("reason_code")
    if reason_code is None:
        raise ValueError("reason_code is required")
    if complexity is None:
        complexity = planned.get("complexity")
    if not isinstance(complexity, int):
        raise ValueError("complexity is required")
    if isinstance(context, str):
        context = {"question": context}
    context = dict(context or {})
    if question:
        context.setdefault("question", question)
    if task_summary:
        context.setdefault("task_summary", task_summary)
    role_task = task_description or task or prompt or planned.get("role_task")
    if role_task:
        context.setdefault("role_task", role_task)
    if not context:
        raise ValueError("context is required")
    # Caller-supplied tool and qualitative budget hints are intentionally
    # ignored; the locked routing policy controls both capabilities and tokens.
    _ = allowed_tools, budget
    return authorize_subagent(
        work_dir=_env_path("AUDIT_WORK_DIR"),
        task_id=_task_id(),
        routing_rules_path=CORE_ROOT / "routing" / "routing_rules.json",
        role=role,
        reason_code=reason_code,
        complexity=complexity,
        context=context,
        artifact_paths=artifact_paths,
        requested_token_budget=requested_token_budget,
    )


def run_audit_subagent(**kwargs: Any) -> dict[str, Any]:
    """Compatibility alias for authorize_audit_subagent; not advertised to agents."""
    return authorize_audit_subagent(**kwargs)


def complete_audit_subagent(
    invocation_id: str,
    summary: dict[str, Any] | None = None,
    summary_path: str | None = None,
    artifact_paths: list[str] | None = None,
    token_usage: dict[str, int] | None = None,
    status: str = "completed",
) -> dict[str, Any]:
    """Register a native subagent result after validating its summary, artifacts, hash, and budget."""
    _ensure_task_initialized()
    return complete_subagent(
        work_dir=_env_path("AUDIT_WORK_DIR"),
        task_id=_task_id(),
        invocation_id=invocation_id,
        summary=summary,
        summary_path=summary_path,
        artifact_paths=artifact_paths,
        token_usage=token_usage,
        status=status,
    )


def checkpoint_audit_context(
    stage: str,
    context_usage_percent: float,
    retained_state: dict[str, Any],
    artifact_paths: list[str] | None = None,
    compacted: bool = False,
    estimation_method: str = "reported_tokens",
) -> dict[str, Any]:
    """Persist the minimum recoverable task state and record checkpoint or compaction events."""
    _ensure_task_initialized()
    return checkpoint_context(
        work_dir=_env_path("AUDIT_WORK_DIR"),
        task_id=_task_id(),
        stage=stage,
        context_usage_percent=context_usage_percent,
        retained_state=retained_state,
        artifact_paths=artifact_paths,
        compacted=compacted,
        estimation_method=estimation_method,
    )


def submit_audit_result(
    result: dict[str, Any] | str | None = None,
    evidence_matrix_path: str = "work/evidence_matrix.json",
    validation_report_path: str = "work/validation_report.json",
    result_path: str | None = None,
) -> dict[str, Any]:
    """Validate and atomically submit one audit result, allowing at most one repair."""
    _ensure_task_initialized()
    if result is None:
        result = result_path
    if result is None:
        raise ValueError("result or result_path is required")
    if isinstance(result, str):
        result = _workspace_json(result)
    return submit_result(
        work_dir=_env_path("AUDIT_WORK_DIR"),
        task_id=_task_id(),
        expense_db=_env_path("EVAL_EXPENSE_DB"),
        policy_corpus_dir=_env_path("EVAL_POLICY_CORPUS_DIR"),
        result=result,
        evidence_matrix_path=evidence_matrix_path,
        validation_report_path=validation_report_path,
    )


def _workspace_json(raw_path: str) -> dict[str, Any]:
    work_dir = _env_path("AUDIT_WORK_DIR")
    path = Path(raw_path)
    if not path.is_absolute():
        path = work_dir / path
    path = path.resolve()
    if path != work_dir and work_dir not in path.parents:
        raise ValueError(f"path escapes task workspace: {raw_path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {raw_path}")
    return value


def validate_audit_result(
    result: dict[str, Any] | str | None = None,
    evidence_matrix_path: str = "work/evidence_matrix.json",
    validation_report_path: str = "work/validation_report.json",
    result_path: str | None = None,
    evidence_matrix: dict[str, Any] | str | None = None,
    report_path: str | None = None,
    validation_report: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
    """Preflight a result and its artifacts without consuming a submission attempt."""
    _ensure_task_initialized()
    if result is None:
        result = result_path
    if result is None:
        raise ValueError("result is required")
    if isinstance(result, str):
        result = _workspace_json(result)
    evidence_value = evidence_matrix if evidence_matrix is not None else evidence_matrix_path
    report_value = validation_report if validation_report is not None else (report_path or validation_report_path)
    if isinstance(evidence_value, str):
        evidence_value = _workspace_json(evidence_value)
    if isinstance(report_value, str):
        report_value = _workspace_json(report_value)
    record_event(
        work_dir=_env_path("AUDIT_WORK_DIR"),
        task_id=_task_id(),
        event_type="validation_started",
        source="audit_control",
    )
    result_report = validate_submission(
        result=result,
        expense_db=_env_path("EVAL_EXPENSE_DB"),
        policy_corpus_dir=_env_path("EVAL_POLICY_CORPUS_DIR"),
        evidence_matrix=evidence_value,
        validation_report=report_value,
    )
    record_event(
        work_dir=_env_path("AUDIT_WORK_DIR"),
        task_id=_task_id(),
        event_type="validation_completed",
        source="audit_control",
        summary={
            "valid": result_report["valid"],
            "error_count": len(result_report["errors"]),
            "warning_count": len(result_report["warnings"]),
        },
        error_code=None if result_report["valid"] else "VALIDATION_FAILED",
    )
    return result_report


TOOLS: dict[str, Callable[..., dict[str, Any]]] = {
    "authorize_audit_subagent": authorize_audit_subagent,
    "complete_audit_subagent": complete_audit_subagent,
    "checkpoint_audit_context": checkpoint_audit_context,
    "validate_audit_result": validate_audit_result,
    "submit_audit_result": submit_audit_result,
    "run_audit_subagent": run_audit_subagent,
}

TOOL_SCHEMAS = [
    {
        "name": "authorize_audit_subagent",
        "description": authorize_audit_subagent.__doc__,
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": [],
            "properties": {
                "role": {
                    "type": "string",
                    "enum": ["policy_researcher", "data_analyst", "independent_reviewer"],
                    "description": "Native subagent role to authorize.",
                },
                "agent_role": {"type": "string", "description": "Alias for role."},
                "subagent_type": {"type": "string", "description": "Alias for role."},
                "reason_code": {"type": "string", "description": "Fixed routing reason code."},
                "reason": {"type": "string", "description": "Alias for reason_code."},
                "complexity": {"type": "integer", "minimum": 0, "maximum": 6, "description": "Planner complexity score."},
                "context": {"type": "object", "description": "Minimal role-specific task context."},
                "question": {"type": "string", "description": "Question added to context."},
                "task_summary": {"type": "string", "description": "Compact task summary added to context."},
                "task_description": {"type": "string", "description": "Bounded role task added to context."},
                "task": {"type": "string", "description": "Alias for task_description."},
                "prompt": {"type": "string", "description": "Alias for task_description."},
                "allowed_tools": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Compatibility hint; locked routing rules remain authoritative.",
                },
                "budget": {
                    "description": "Compatibility hint; locked role budget remains authoritative.",
                    "oneOf": [{"type": "string"}, {"type": "integer"}],
                },
                "artifact_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Existing task-workspace artifacts the role may read.",
                },
                "requested_token_budget": {
                    "type": "integer",
                    "minimum": 1000,
                    "maximum": 12000,
                    "default": 8000,
                    "description": "Maximum role token budget.",
                },
            },
        },
    },
    {
        "name": "complete_audit_subagent",
        "description": complete_audit_subagent.__doc__,
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["invocation_id"],
            "oneOf": [{"required": ["summary"]}, {"required": ["summary_path"]}],
            "properties": {
                "invocation_id": {"type": "string"},
                "summary": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "decision",
                        "key_findings",
                        "record_ids",
                        "citations",
                        "unresolved_items",
                        "artifact_paths"
                    ],
                    "properties": {
                        "decision": {
                            "type": "string",
                            "enum": ["pass", "reject", "needs_more_evidence"]
                        },
                        "key_findings": {"type": "array"},
                        "record_ids": {"type": "array"},
                        "citations": {"type": "array"},
                        "unresolved_items": {"type": "array"},
                        "artifact_paths": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "summary_path": {"type": "string"},
                "artifact_paths": {"type": "array", "items": {"type": "string"}},
                "token_usage": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "input_tokens": {"type": "integer", "minimum": 0},
                        "output_tokens": {"type": "integer", "minimum": 0},
                        "total_tokens": {"type": "integer", "minimum": 0}
                    }
                },
                "status": {"type": "string", "enum": ["completed"], "default": "completed"}
            }
        }
    },
    {
        "name": "checkpoint_audit_context",
        "description": checkpoint_audit_context.__doc__,
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["stage", "context_usage_percent", "retained_state"],
            "properties": {
                "stage": {
                    "type": "string",
                    "enum": [
                        "task_started",
                        "planning_completed",
                        "investigation_completed",
                        "review_ready",
                        "validation_ready",
                        "submission_ready"
                    ]
                },
                "context_usage_percent": {"type": "number", "minimum": 0, "maximum": 100},
                "retained_state": {"type": "object"},
                "artifact_paths": {"type": "array", "items": {"type": "string"}},
                "compacted": {"type": "boolean", "default": False},
                "estimation_method": {"type": "string", "default": "reported_tokens"}
            }
        }
    },
    {
        "name": "validate_audit_result",
        "description": validate_audit_result.__doc__,
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "oneOf": [{"required": ["result"]}, {"required": ["result_path"]}],
            "properties": {
                "result": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["anomaly_ids", "record_ids", "answer", "citations"],
                    "properties": {
                        "anomaly_ids": {"type": "array", "items": {"type": "string"}},
                        "record_ids": {"type": "array", "items": {"type": "string"}},
                        "answer": {"type": "string"},
                        "citations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["doc_id", "clause_no"],
                                "properties": {
                                    "doc_id": {"type": "string"},
                                    "clause_no": {"type": "string"},
                                },
                            },
                        },
                    },
                },
                "result_path": {
                    "type": "string",
                    "description": "Task-relative path to the final result JSON object.",
                },
                "evidence_matrix_path": {"type": "string", "default": "work/evidence_matrix.json"},
                "validation_report_path": {"type": "string", "default": "work/validation_report.json"},
            },
        },
    },
    {
        "name": "submit_audit_result",
        "description": submit_audit_result.__doc__,
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "oneOf": [{"required": ["result"]}, {"required": ["result_path"]}],
            "properties": {
                "result": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["anomaly_ids", "record_ids", "answer", "citations"],
                    "properties": {
                        "anomaly_ids": {"type": "array", "items": {"type": "string"}},
                        "record_ids": {"type": "array", "items": {"type": "string"}},
                        "answer": {"type": "string"},
                        "citations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["doc_id", "clause_no"],
                                "properties": {
                                    "doc_id": {"type": "string"},
                                    "clause_no": {"type": "string"},
                                },
                            },
                        },
                    },
                },
                "result_path": {
                    "type": "string",
                    "description": "Task-relative path to the final result JSON object.",
                },
                "evidence_matrix_path": {
                    "type": "string",
                    "default": "work/evidence_matrix.json",
                    "description": "Task-relative evidence matrix path.",
                },
                "validation_report_path": {
                    "type": "string",
                    "default": "work/validation_report.json",
                    "description": "Task-relative validation report path.",
                },
            },
        },
    },
]


def _subagents_enabled() -> bool:
    return os.environ.get("AUDIT_SUBAGENTS_ENABLED", "1").strip().lower() not in {"0", "false", "no"}


def _available_tool_schemas() -> list[dict[str, Any]]:
    if _subagents_enabled():
        return TOOL_SCHEMAS
    return [
        schema
        for schema in TOOL_SCHEMAS
        if schema["name"] not in {"authorize_audit_subagent", "complete_audit_subagent"}
    ]


def call_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    if name in {"authorize_audit_subagent", "complete_audit_subagent", "run_audit_subagent"} and not _subagents_enabled():
        raise ValueError("subagents are disabled for this experiment group")
    if name not in TOOLS:
        raise ValueError(f"unknown tool: {name}")
    return TOOLS[name](**(arguments or {}))


def handle_rpc(request: dict[str, Any]) -> dict[str, Any] | None:
    method = request.get("method")
    request_id = request.get("id")
    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "audit_control", "version": "0.1.0"},
            }
        elif method == "tools/list":
            result = {"tools": _available_tool_schemas()}
        elif method == "tools/call":
            params = request.get("params", {})
            value = call_tool(params["name"], params.get("arguments") or {})
            result = {
                "content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False)}],
                "isError": False,
            }
        elif method == "notifications/initialized":
            return None
        else:
            raise ValueError(f"unsupported method: {method}")
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    except Exception as exc:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32000, "message": str(exc)},
        }


def serve_stdio() -> None:
    for line in sys.stdin:
        if line.strip():
            response = handle_rpc(json.loads(line))
            if response is not None:
                print(json.dumps(response, ensure_ascii=True), flush=True)


def self_test() -> dict[str, Any]:
    listed = handle_rpc({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    return {
        "server": "audit_control",
        "tools": [item["name"] for item in listed["result"]["tools"]],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), ensure_ascii=False, indent=2))
    else:
        serve_stdio()


if __name__ == "__main__":
    main()
