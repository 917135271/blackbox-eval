from __future__ import annotations

import json
import re
import time
from copy import deepcopy
from pathlib import Path
from typing import Any


SCRIPTED_WORKFLOW_VERSION = "scripted-enhancement-v1.2"

ROUTES: dict[str, dict[str, Any]] = {
    "policy_exception": {
        "route": "policy_exception_analysis",
        "skills": ["policy-version-check", "false-positive-review"],
        "subagent_role": "policy_researcher",
        "reason": "The conclusion depends on policy period, transition, or explicit exception handling.",
    },
    "policy_qa": {
        "route": "direct_policy_retrieval",
        "skills": [],
        "subagent_role": None,
        "reason": "Single policy fact lookup; no full audit workflow is required.",
    },
    "version_trap": {
        "route": "policy_version_analysis",
        "skills": ["policy-version-check"],
        "subagent_role": "policy_researcher",
        "reason": "Policy applicability and historical version selection are material.",
    },
    "near_clause_disambiguation": {
        "route": "targeted_policy_disambiguation",
        "skills": ["policy-version-check"],
        "subagent_role": None,
        "reason": "The task needs precise clause selection but not broad orchestration.",
    },
    "two_hop_retrieval": {
        "route": "targeted_cross_reference",
        "skills": ["policy-version-check"],
        "subagent_role": None,
        "reason": "Follow the explicit policy cross-reference and stop after resolving it.",
    },
    "policy_data_comparison": {
        "route": "focused_record_audit",
        "skills": ["batch-expense-analysis"],
        "subagent_role": None,
        "reason": "A focused record-to-rule comparison does not need the full workflow.",
    },
    "single_anomaly": {
        "route": "focused_record_audit",
        "skills": ["batch-expense-analysis"],
        "subagent_role": None,
        "reason": "Follow the clue record only through the relational scope required by the requested rule.",
    },
    "full_year_rule_audit": {
        "route": "batch_rule_audit",
        "skills": ["audit-query-planner", "batch-expense-analysis"],
        "subagent_role": "data_analyst",
        "reason": "Complete population coverage and reproducible aggregation are required.",
    },
    "batch_analysis": {
        "route": "batch_rule_audit",
        "skills": ["audit-query-planner", "batch-expense-analysis"],
        "subagent_role": "data_analyst",
        "reason": "Complete population coverage and reproducible aggregation are required.",
    },
    "clean_but_suspicious": {
        "route": "reverse_check",
        "skills": ["false-positive-review"],
        "subagent_role": "independent_reviewer",
        "reason": "The task is designed around boundary, exception, or no-anomaly verification.",
    },
    "clean_trap": {
        "route": "reverse_check",
        "skills": ["false-positive-review"],
        "subagent_role": "independent_reviewer",
        "reason": "The task requires a deliberate reverse check before reporting an anomaly.",
    },
    "aggregate_budget": {
        "route": "cumulative_budget_audit",
        "skills": ["audit-query-planner", "batch-expense-analysis", "false-positive-review"],
        "subagent_role": "data_analyst",
        "reason": "Ordered cumulative calculation and approval exception handling are required.",
    },
    "audit_report": {
        "route": "comprehensive_audit_report",
        "skills": [
            "audit-query-planner",
            "policy-version-check",
            "batch-expense-analysis",
            "false-positive-review",
            "audit-report",
        ],
        "subagent_role": "data_analyst",
        "reason": "A comprehensive report needs planning, complete analysis, review, and synthesis.",
    },
}

DEFAULT_ROUTE = {
    "route": "focused_audit",
    "skills": ["batch-expense-analysis"],
    "subagent_role": None,
    "reason": "Unknown public category; use a focused audit without mandatory delegation.",
}


def _atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _dedupe(values: list[Any]) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()
    for value in values:
        key = json.dumps(value, ensure_ascii=False, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


_DOC_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.md")
_CLAUSE_PATTERN = re.compile(
    r"第[零〇一二三四五六七八九十百0-9]+条|附件[零〇一二三四五六七八九十百0-9]+"
)


def _citations_from_text(text: str) -> list[dict[str, str]]:
    """Extract only explicit document/clause pairs already written by the model."""
    documents = list(_DOC_ID_PATTERN.finditer(text))
    citations: list[dict[str, str]] = []
    for index, document in enumerate(documents):
        segment_end = documents[index + 1].start() if index + 1 < len(documents) else len(text)
        segment = text[document.end():segment_end]
        clauses = _CLAUSE_PATTERN.findall(segment)
        for clause in clauses:
            citations.append({"doc_id": document.group(0), "clause_no": clause})
    return citations


def _normalized_result(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    anomaly_ids = [
        item.strip() for item in value.get("anomaly_ids", [])
        if isinstance(item, str) and item.strip()
    ]
    record_ids = [
        item.strip() for item in value.get("record_ids", [])
        if isinstance(item, str) and item.strip()
    ]
    citations: list[dict[str, str]] = []
    for citation in value.get("citations", []):
        if isinstance(citation, str):
            citations.extend(_citations_from_text(citation))
        elif isinstance(citation, dict):
            doc_id = citation.get("doc_id")
            clause_no = citation.get("clause_no")
            if (
                isinstance(doc_id, str)
                and doc_id.strip()
                and isinstance(clause_no, str)
                and clause_no.strip()
            ):
                citations.append({"doc_id": doc_id.strip(), "clause_no": clause_no.strip()})
    answer = value.get("answer", "")
    normalized_answer = answer.strip() if isinstance(answer, str) else ""
    if not citations and normalized_answer:
        citations.extend(_citations_from_text(normalized_answer))
    return {
        "anomaly_ids": _dedupe(anomaly_ids),
        "record_ids": _dedupe(record_ids),
        "answer": normalized_answer,
        "citations": _dedupe(citations),
    }


def _citation_key(value: dict[str, Any]) -> tuple[str, str]:
    return (str(value.get("doc_id", "")), str(value.get("clause_no", "")))


def _normalized_evidence_input(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        value = {}
    rows: list[dict[str, Any]] = []
    for raw in value.get("evidence_rows", []):
        if not isinstance(raw, dict):
            continue
        anomaly_id = raw.get("anomaly_id", "")
        record_ids = raw.get("record_ids", [])
        facts = raw.get("facts", [])
        citations = _normalized_result({"citations": raw.get("citations", [])})["citations"]
        rows.append(
            {
                "anomaly_id": anomaly_id.strip() if isinstance(anomaly_id, str) else "",
                "record_ids": _dedupe(
                    [item.strip() for item in record_ids if isinstance(item, str) and item.strip()]
                ),
                "citations": citations,
                "facts": _dedupe(
                    [item.strip() for item in facts if isinstance(item, str) and item.strip()]
                ),
            }
        )
    raw_no_anomaly = value.get("no_anomaly_coverage", {})
    no_anomaly = raw_no_anomaly if isinstance(raw_no_anomaly, dict) else {}
    checked_rules = _normalized_result({"citations": no_anomaly.get("checked_rules", [])})[
        "citations"
    ]
    population_count = no_anomaly.get("population_count", 0)
    if not isinstance(population_count, int) or isinstance(population_count, bool) or population_count < 0:
        population_count = 0
    return {
        "evidence_rows": rows,
        "no_anomaly_coverage": {
            "complete": no_anomaly.get("complete") is True,
            "searched_population": str(no_anomaly.get("searched_population", "")).strip(),
            "query_conditions": str(no_anomaly.get("query_conditions", "")).strip(),
            "checked_rules": checked_rules,
            "population_count": population_count,
            "conclusion": str(no_anomaly.get("conclusion", "")).strip(),
        },
    }


def route_for(category: str) -> dict[str, Any]:
    route = deepcopy(ROUTES.get(category, DEFAULT_ROUTE))
    route["category"] = category
    route["workflow_version"] = SCRIPTED_WORKFLOW_VERSION
    route["subagent_is_mandatory"] = False
    return route


def initialize_scripted_task(
    *,
    work_dir: Path,
    task_id: str,
    category: str,
    question: str,
    framework: str,
    experiment_group: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    work_dir = work_dir.resolve()
    work = work_dir / "work"
    work.mkdir(parents=True, exist_ok=True)
    route = route_for(category)
    workflow = {
        "task_id": task_id,
        "question": question,
        "framework": framework,
        "experiment_group": experiment_group,
        "route": route,
        "model_responsibilities": [
            "retrieve policy and business evidence",
            "interpret policy applicability and exceptions",
            "decide audit findings",
            "produce the four-field final result",
            "map each finding to its actual records, policy clauses, and verified facts",
            "record the searched population and query conditions for no-anomaly conclusions",
        ],
        "script_responsibilities": [
            "workflow routing",
            "initial and final task-state snapshots",
            "stage checkpoints",
            "evidence input normalization and consistency checks",
            "schema and identifier validation",
            "submission preparation",
        ],
        "created_at": time.time(),
    }
    _atomic_write_json(work / "scripted_workflow.json", workflow)

    task_state_path = work / "task_state.json"
    task_state = _load_json_object(task_state_path)
    task_state.update(
        {
            "task_id": task_id,
            "phase": "workflow_ready",
            "scope": {"category": category, "route": route["route"]},
            "budget": {"timeout_seconds": timeout_seconds},
            "completed_steps": ["workspace_initialized", "workflow_routed"],
            "pending_steps": ["investigation", "decision", "scripted_validation", "submission"],
            "unresolved_items": [],
            "submission_status": "not_submitted",
        }
    )
    _atomic_write_json(task_state_path, task_state)

    memory = {
        "task_id": task_id,
        "question": question,
        "constraints": [
            "single isolated task",
            "read-only policy corpus and expense database",
            "no evaluation answers or historical trajectories",
        ],
        "route": route,
        "applicable_policies": [],
        "record_ids": [],
        "findings": [],
        "unresolved_items": [],
        "artifact_paths": [
            "work/scripted_workflow.json",
            "work/task_state.json",
            "work/evidence_input.json",
        ],
        "submission_status": "not_submitted",
        "updated_at": time.time(),
    }
    _atomic_write_json(work / "task_memory.json", memory)
    _atomic_write_json(
        work / "evidence_input.json",
        {
            "evidence_rows": [],
            "no_anomaly_coverage": {
                "complete": False,
                "searched_population": "",
                "query_conditions": "",
                "checked_rules": [],
                "population_count": 0,
                "conclusion": "",
            },
        },
    )
    return workflow


def prepare_submission_artifacts(
    *,
    work_dir: Path,
    task_id: str,
    result: Any,
    evidence_input: Any | None = None,
) -> dict[str, Any]:
    """Validate model-authored evidence ownership and generate common artifacts."""
    work_dir = work_dir.resolve()
    work = work_dir / "work"
    normalized = _normalized_result(result)
    original_citations = result.get("citations", []) if isinstance(result, dict) else []
    had_structured_citation = any(
        isinstance(item, dict)
        and isinstance(item.get("doc_id"), str)
        and bool(item.get("doc_id", "").strip())
        and isinstance(item.get("clause_no"), str)
        and bool(item.get("clause_no", "").strip())
        for item in original_citations
    )
    citation_repair_applied = bool(normalized.get("citations")) and not had_structured_citation
    _atomic_write_json(work / "final_result.json", normalized)

    if evidence_input is None:
        evidence_input = _load_json_object(work / "evidence_input.json")
    semantic_evidence = _normalized_evidence_input(evidence_input)
    _atomic_write_json(work / "evidence_input.json", semantic_evidence)

    anomalies = normalized.get("anomaly_ids", [])
    records = normalized.get("record_ids", [])
    citations = normalized.get("citations", [])
    answer = normalized.get("answer", "")
    missing_evidence: list[str] = []
    if anomalies and not records:
        missing_evidence.append("positive result has no supporting record_ids")
    if anomalies and not citations:
        missing_evidence.append("positive result has no supporting policy citations")
    if anomalies and not answer:
        missing_evidence.append("positive result has no fact narrative")
    evidence_rows: list[dict[str, Any]] = []
    row_anomalies: list[str] = []
    row_records: set[str] = set()
    row_citations: set[tuple[str, str]] = set()
    final_records = set(records)
    final_citations = {_citation_key(item) for item in citations}
    for index, row in enumerate(semantic_evidence["evidence_rows"]):
        anomaly_id = row["anomaly_id"]
        if not anomaly_id:
            missing_evidence.append(f"evidence row {index} has no anomaly_id")
            continue
        row_anomalies.append(anomaly_id)
        if not row["record_ids"]:
            missing_evidence.append(f"evidence row {anomaly_id} has no record_ids")
        if not row["citations"]:
            missing_evidence.append(f"evidence row {anomaly_id} has no citations")
        if not row["facts"]:
            missing_evidence.append(f"evidence row {anomaly_id} has no verified facts")
        unknown_records = set(row["record_ids"]) - final_records
        if unknown_records:
            missing_evidence.append(
                f"evidence row {anomaly_id} contains records absent from final result: {sorted(unknown_records)}"
            )
        unknown_citations = {_citation_key(item) for item in row["citations"]} - final_citations
        if unknown_citations:
            missing_evidence.append(
                f"evidence row {anomaly_id} contains citations absent from final result"
            )
        if row["record_ids"] and row["citations"] and row["facts"] and not unknown_records and not unknown_citations:
            evidence_rows.append(
                {
                    **deepcopy(row),
                    "fact_supported": True,
                    "rule_supported": True,
                    "coverage_status": "pass",
                }
            )
            row_records.update(row["record_ids"])
            row_citations.update(_citation_key(item) for item in row["citations"])

    if anomalies:
        if sorted(row_anomalies) != sorted(anomalies):
            missing_evidence.append("evidence rows do not map exactly one row to each final anomaly_id")
        if len(row_anomalies) != len(set(row_anomalies)):
            missing_evidence.append("evidence rows contain duplicate anomaly_id values")
        if row_records != final_records:
            missing_evidence.append("evidence row record_ids do not exactly cover final record_ids")
        if row_citations != final_citations:
            missing_evidence.append("evidence row citations do not exactly cover final citations")
    elif semantic_evidence["evidence_rows"]:
        missing_evidence.append("no-anomaly result must not contain anomaly evidence rows")

    no_anomaly = semantic_evidence["no_anomaly_coverage"]
    if not anomalies:
        if not answer:
            missing_evidence.append("no-anomaly result has no conclusion narrative")
        for field in ("searched_population", "query_conditions", "conclusion"):
            if not no_anomaly[field]:
                missing_evidence.append(f"no-anomaly evidence has no {field}")
        if no_anomaly["complete"] is not True:
            missing_evidence.append("no-anomaly evidence is not marked complete")

    missing_evidence = _dedupe(missing_evidence)

    evidence = {
        "status": "pass" if not missing_evidence else "blocked",
        "coverage_percent": 100 if not missing_evidence else 0,
        "evidence_rows": evidence_rows,
        "candidate_record_ids": list(records),
        "submitted_record_ids": list(records),
        "unowned_record_ids": sorted(final_records - row_records) if anomalies else [],
        "unused_candidate_record_ids": [],
        "unused_citations": [
            {"doc_id": doc_id, "clause_no": clause_no}
            for doc_id, clause_no in sorted(final_citations - row_citations)
        ] if anomalies else [],
        "missing_evidence": missing_evidence,
        "no_anomaly_coverage": no_anomaly if not anomalies else {
            "complete": False,
            "searched_population": "not_applicable",
            "query_conditions": "not_applicable",
            "checked_rules": [],
            "population_count": 0,
            "conclusion": "not_applicable",
        },
        "reconciled_figures": {},
        "unresolved_items": [],
    }
    _atomic_write_json(work / "evidence_matrix.json", evidence)

    validation = {
        "status": "pass" if not missing_evidence else "fail",
        "errors": missing_evidence,
        "warnings": (
            ["citations normalized from explicit document and clause text"]
            if citation_repair_applied
            else []
        ),
        "field_checks": {"four_field_result": set(normalized) == {"anomaly_ids", "record_ids", "answer", "citations"}},
        "id_checks": {"duplicates_removed": True},
        "evidence_checks": {
            "generated_by": SCRIPTED_WORKFLOW_VERSION,
            "semantic_input_authored_by_model": True,
            "exact_set_coverage_checked": True,
        },
        "answer_consistency_checks": {},
        "repair_count": 1 if citation_repair_applied else 0,
        "repairable_fields": [],
        "submission_allowed": not missing_evidence,
    }
    _atomic_write_json(work / "validation_report.json", validation)

    workflow = _load_json_object(work / "scripted_workflow.json")
    memory = _load_json_object(work / "task_memory.json")
    memory.update(
        {
            "task_id": task_id,
            "question": workflow.get("question", memory.get("question", task_id)),
            "route": workflow.get("route", memory.get("route", {})),
            "applicable_policies": sorted(
                {citation["doc_id"] for citation in citations if citation.get("doc_id")}
            ),
            "record_ids": list(records),
            "findings": list(anomalies),
            "unresolved_items": list(missing_evidence),
            "artifact_paths": [
                "work/scripted_workflow.json",
                "work/task_memory.json",
                "work/final_result.json",
                "work/evidence_input.json",
                "work/evidence_matrix.json",
                "work/validation_report.json",
            ],
            "submission_status": "ready" if not missing_evidence else "repair_required",
            "updated_at": time.time(),
        }
    )
    _atomic_write_json(work / "task_memory.json", memory)

    task_state_path = work / "task_state.json"
    task_state = _load_json_object(task_state_path)
    task_state.update(
        {
            "task_id": task_id,
            "phase": "validation_ready" if not missing_evidence else "repair_required",
            "completed_steps": [
                "workspace_initialized",
                "workflow_routed",
                "investigation",
                "decision",
                "evidence_generated",
            ],
            "pending_steps": ["submission"] if not missing_evidence else ["repair", "submission"],
            "unresolved_items": list(missing_evidence),
            "submission_status": "not_submitted" if not missing_evidence else "repair_required",
        }
    )
    _atomic_write_json(task_state_path, task_state)
    return {
        "result": normalized,
        "evidence_matrix": evidence,
        "validation_report": validation,
        "task_memory": memory,
        "ready": not missing_evidence,
    }


def retained_state(work_dir: Path, task_id: str, submission_status: str) -> dict[str, Any]:
    work_dir = work_dir.resolve()
    work = work_dir / "work"
    workflow = _load_json_object(work / "scripted_workflow.json")
    memory = _load_json_object(work / "task_memory.json")
    evidence = _load_json_object(work / "evidence_matrix.json")
    return {
        "task": workflow.get("question", task_id),
        "constraints": memory.get("constraints", []),
        "audit_plan": workflow.get("route", {}),
        "applicable_policies": memory.get("applicable_policies", []),
        "record_ids": memory.get("record_ids", []),
        "evidence_status": evidence.get("status", "not_recorded"),
        "unresolved_items": memory.get("unresolved_items", []),
        "artifact_index": memory.get("artifact_paths", []),
        "remaining_budget": {"managed_by": "outer_runner"},
        "submission_status": submission_status,
    }
