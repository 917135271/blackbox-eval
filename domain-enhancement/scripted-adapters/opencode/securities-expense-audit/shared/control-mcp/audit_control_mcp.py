from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
BASE_MCP_PATH = HERE / "_base_audit_control_mcp.py"
if not BASE_MCP_PATH.exists():
    BASE_MCP_PATH = HERE.parent / "control-mcp" / "audit_control_mcp.py"

spec = importlib.util.spec_from_file_location("_scripted_base_audit_control_mcp", BASE_MCP_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load base audit control MCP: {BASE_MCP_PATH}")
base = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = base
spec.loader.exec_module(base)

SCRIPTED_ROOT = HERE.parent / "scripted-audit-core"
sys.path.insert(0, str(SCRIPTED_ROOT / "scripts"))

from scripted_workflow_core import (  # noqa: E402
    SCRIPTED_WORKFLOW_VERSION,
    prepare_submission_artifacts,
    retained_state,
)


def _resolve_result(result: dict[str, Any] | str | None, result_path: str | None) -> dict[str, Any]:
    value: dict[str, Any] | str = (
        result if result is not None else (result_path or "work/final_result.json")
    )
    if isinstance(value, str):
        return base._workspace_json(value)
    if not isinstance(value, dict):
        raise ValueError("result must be a JSON object or task-relative path")
    return value


def _prepare(result: dict[str, Any] | str | None, result_path: str | None) -> dict[str, Any]:
    base._ensure_task_initialized()
    prepared = prepare_submission_artifacts(
        work_dir=base._env_path("AUDIT_WORK_DIR"),
        task_id=base._task_id(),
        result=_resolve_result(result, result_path),
    )
    return prepared


def _checkpoint(stage: str, submission_status: str) -> None:
    work_dir = base._env_path("AUDIT_WORK_DIR")
    artifact_paths = [
        "work/scripted_workflow.json",
        "work/task_memory.json",
        "work/final_result.json",
        "work/evidence_input.json",
        "work/evidence_matrix.json",
        "work/validation_report.json",
    ]
    existing_paths = [path for path in artifact_paths if (work_dir / path).exists()]
    base.checkpoint_context(
        work_dir=work_dir,
        task_id=base._task_id(),
        stage=stage,
        context_usage_percent=0.0,
        retained_state=retained_state(work_dir, base._task_id(), submission_status),
        artifact_paths=existing_paths,
        compacted=False,
        estimation_method="external_scripted_stage",
    )


def validate_audit_result(
    result: dict[str, Any] | str | None = None,
    evidence_matrix_path: str = "work/evidence_matrix.json",
    validation_report_path: str = "work/validation_report.json",
    result_path: str | None = None,
    **_: Any,
) -> dict[str, Any]:
    """Validate model-authored evidence input and generate common submission artifacts."""
    prepared = _prepare(result, result_path)
    _checkpoint("validation_ready", "not_submitted")
    report = base.validate_audit_result(
        result=prepared["result"],
        evidence_matrix_path=evidence_matrix_path,
        validation_report_path=validation_report_path,
    )
    report["scripted_enhancement"] = {
        "workflow_version": SCRIPTED_WORKFLOW_VERSION,
        "artifacts_generated": True,
        "semantic_findings_changed": False,
    }
    return report


def submit_audit_result(
    result: dict[str, Any] | str | None = None,
    evidence_matrix_path: str = "work/evidence_matrix.json",
    validation_report_path: str = "work/validation_report.json",
    result_path: str | None = None,
) -> dict[str, Any]:
    """Regenerate checked artifacts, require a valid preflight, and submit once."""
    prepared = _prepare(result, result_path)
    preflight = base.validate_audit_result(
        result=prepared["result"],
        evidence_matrix_path=evidence_matrix_path,
        validation_report_path=validation_report_path,
    )
    if not preflight.get("valid"):
        return {
            "status": "repair_required",
            "code": "SCRIPTED_PREFLIGHT_FAILED",
            "errors": preflight.get("errors", []),
            "warnings": preflight.get("warnings", []),
            "repairable_fields": preflight.get("repairable_fields", []),
            "submission_attempt_consumed": False,
        }
    _checkpoint("submission_ready", "not_submitted")
    response = base.submit_audit_result(
        result=prepared["result"],
        evidence_matrix_path=evidence_matrix_path,
        validation_report_path=validation_report_path,
    )
    response["scripted_enhancement"] = {
        "workflow_version": SCRIPTED_WORKFLOW_VERSION,
        "artifacts_generated": True,
        "semantic_findings_changed": False,
    }
    return response


base.TOOLS = dict(base.TOOLS)
base.TOOLS["validate_audit_result"] = validate_audit_result
base.TOOLS["submit_audit_result"] = submit_audit_result

base.TOOL_SCHEMAS = copy.deepcopy(base.TOOL_SCHEMAS)
for schema in base.TOOL_SCHEMAS:
    if schema.get("name") == "validate_audit_result":
        schema["description"] = validate_audit_result.__doc__
        schema["inputSchema"].pop("oneOf", None)
    elif schema.get("name") == "submit_audit_result":
        schema["description"] = submit_audit_result.__doc__
        schema["inputSchema"].pop("oneOf", None)


if __name__ == "__main__":
    base.main()
