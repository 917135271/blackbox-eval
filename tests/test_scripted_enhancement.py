from __future__ import annotations

import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
SCRIPTED_SCRIPTS = ROOT / "domain-enhancement" / "scripted-audit-core" / "scripts"
SHARED_SCRIPTS = ROOT / "domain-enhancement" / "shared-audit-core" / "scripts"
sys.path.insert(0, str(SCRIPTED_SCRIPTS))
sys.path.insert(0, str(SHARED_SCRIPTS))

from audit_control_core import validate_submission  # noqa: E402
from scripted_workflow_core import (  # noqa: E402
    initialize_scripted_task,
    prepare_submission_artifacts,
    route_for,
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _expense_db(path: Path, *record_ids: str) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE expense_records (record_id TEXT PRIMARY KEY)")
        connection.executemany(
            "INSERT INTO expense_records(record_id) VALUES (?)",
            [(record_id,) for record_id in record_ids],
        )


def test_route_keeps_simple_policy_question_compact() -> None:
    route = route_for("policy_qa")
    assert route["route"] == "direct_policy_retrieval"
    assert route["skills"] == []
    assert route["subagent_role"] is None
    assert route["subagent_is_mandatory"] is False


def test_route_selects_batch_skill_for_full_year_audit() -> None:
    route = route_for("full_year_rule_audit")
    assert route["route"] == "batch_rule_audit"
    assert route["skills"] == ["audit-query-planner", "batch-expense-analysis"]
    assert route["subagent_role"] == "data_analyst"
    assert route["subagent_is_mandatory"] is False


def test_development_categories_do_not_fall_back_to_default_route() -> None:
    expected = {
        "policy_exception": "policy_exception_analysis",
        "single_anomaly": "focused_record_audit",
        "batch_analysis": "batch_rule_audit",
        "clean_trap": "reverse_check",
        "aggregate_budget": "cumulative_budget_audit",
    }
    for category, route_name in expected.items():
        route = route_for(category)
        assert route["route"] == route_name
        assert "Unknown public category" not in route["reason"]


def test_initialize_scripted_task_writes_file_memory(tmp_path: Path) -> None:
    workflow = initialize_scripted_task(
        work_dir=tmp_path,
        task_id="CASE-001",
        category="clean_but_suspicious",
        question="核查两条记录是否异常",
        framework="codex",
        experiment_group="codex-scripted-enhanced",
        timeout_seconds=900,
    )
    assert workflow["route"]["route"] == "reverse_check"
    memory = _load_json(tmp_path / "work" / "task_memory.json")
    state = _load_json(tmp_path / "work" / "task_state.json")
    assert memory["task_id"] == "CASE-001"
    assert memory["submission_status"] == "not_submitted"
    assert state["phase"] == "workflow_ready"
    assert "workflow_routed" in state["completed_steps"]


def test_scripted_no_anomaly_artifacts_pass_common_validator(tmp_path: Path) -> None:
    db = tmp_path / "expense.db"
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    _expense_db(db, "R000001")
    initialize_scripted_task(
        work_dir=tmp_path,
        task_id="CASE-002",
        category="clean_but_suspicious",
        question="核查R000001",
        framework="codex",
        experiment_group="codex-scripted-enhanced",
        timeout_seconds=900,
    )
    prepared = prepare_submission_artifacts(
        work_dir=tmp_path,
        task_id="CASE-002",
        result={
            "anomaly_ids": [],
            "record_ids": ["R000001", "R000001"],
            "answer": "经核查无异常。",
            "citations": [],
        },
        evidence_input={
            "evidence_rows": [],
            "no_anomaly_coverage": {
                "complete": True,
                "searched_population": "R000001",
                "query_conditions": "按record_id查询并核对适用规则",
                "checked_rules": [],
                "population_count": 1,
                "conclusion": "未发现异常",
            },
        },
    )
    report = validate_submission(
        result=prepared["result"],
        expense_db=db,
        policy_corpus_dir=corpus,
        evidence_matrix=prepared["evidence_matrix"],
        validation_report=prepared["validation_report"],
    )
    assert report["valid"] is True
    assert prepared["result"]["record_ids"] == ["R000001"]
    assert prepared["evidence_matrix"]["no_anomaly_coverage"]["complete"] is True


def test_scripted_positive_artifacts_use_only_semantic_result(tmp_path: Path) -> None:
    db = tmp_path / "expense.db"
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    _expense_db(db, "R000002", "R000003")
    (corpus / "POLICY.md").write_text("第五条 单笔费用上限。", encoding="utf-8")
    initialize_scripted_task(
        work_dir=tmp_path,
        task_id="CASE-003",
        category="policy_data_comparison",
        question="核查两条记录",
        framework="opencode",
        experiment_group="opencode-scripted-enhanced",
        timeout_seconds=900,
    )
    prepared = prepare_submission_artifacts(
        work_dir=tmp_path,
        task_id="CASE-003",
        result={
            "anomaly_ids": ["OVER_LIMIT"],
            "record_ids": ["R000002", "R000003"],
            "answer": "两条记录合计金额超过适用上限，确认存在异常。",
            "citations": [{"doc_id": "POLICY.md", "clause_no": "第五条"}],
        },
        evidence_input={
            "evidence_rows": [{
                "anomaly_id": "OVER_LIMIT",
                "record_ids": ["R000002", "R000003"],
                "citations": [{"doc_id": "POLICY.md", "clause_no": "第五条"}],
                "facts": ["两条记录合计金额超过上限"],
            }],
            "no_anomaly_coverage": {},
        },
    )
    report = validate_submission(
        result=prepared["result"],
        expense_db=db,
        policy_corpus_dir=corpus,
        evidence_matrix=prepared["evidence_matrix"],
        validation_report=prepared["validation_report"],
    )
    assert report["valid"] is True
    assert prepared["evidence_matrix"]["evidence_rows"][0]["record_ids"] == [
        "R000002",
        "R000003",
    ]
    assert prepared["task_memory"]["findings"] == ["OVER_LIMIT"]


def test_scripted_normalizes_explicit_text_citations(tmp_path: Path) -> None:
    initialize_scripted_task(
        work_dir=tmp_path,
        task_id="CASE-003B",
        category="single_anomaly",
        question="核查重复报销",
        framework="claude-code-best",
        experiment_group="ccb-scripted-enhanced",
        timeout_seconds=900,
    )
    prepared = prepare_submission_artifacts(
        work_dir=tmp_path,
        task_id="CASE-003B",
        result={
            "anomaly_ids": ["DUP-001"],
            "record_ids": ["R000002", "R000003"],
            "answer": "违反01_expense_reimbursement_2025.md第十条，构成重复报销。",
            "citations": ["01_expense_reimbursement_2025.md 第十条：同一发票限报一次"],
        },
        evidence_input={
            "evidence_rows": [{
                "anomaly_id": "DUP-001",
                "record_ids": ["R000002", "R000003"],
                "citations": ["01_expense_reimbursement_2025.md 第十条"],
                "facts": ["两条记录使用同一发票"],
            }],
        },
    )
    assert prepared["result"]["citations"] == [
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"}
    ]
    assert prepared["validation_report"]["repair_count"] == 1
    assert prepared["ready"] is True


def test_scripted_extracts_citation_from_answer_when_array_is_empty(tmp_path: Path) -> None:
    initialize_scripted_task(
        work_dir=tmp_path,
        task_id="CASE-003C",
        category="batch_analysis",
        question="核查月度标准",
        framework="pi-agent",
        experiment_group="pi-agent-scripted-enhanced",
        timeout_seconds=900,
    )
    prepared = prepare_submission_artifacts(
        work_dir=tmp_path,
        task_id="CASE-003C",
        result={
            "anomaly_ids": ["STD-001"],
            "record_ids": ["R000004"],
            "answer": "依据07_office_communication.md第二条，办公用品超过月度标准。",
            "citations": [],
        },
        evidence_input={
            "evidence_rows": [{
                "anomaly_id": "STD-001",
                "record_ids": ["R000004"],
                "citations": ["07_office_communication.md 第二条"],
                "facts": ["办公用品超过月度标准"],
            }],
        },
    )
    assert prepared["result"]["citations"] == [
        {"doc_id": "07_office_communication.md", "clause_no": "第二条"}
    ]
    assert prepared["ready"] is True


def test_generated_artifacts_match_existing_schemas(tmp_path: Path) -> None:
    initialize_scripted_task(
        work_dir=tmp_path,
        task_id="CASE-004",
        category="policy_qa",
        question="制度问答",
        framework="pi-agent",
        experiment_group="pi-agent-scripted-enhanced",
        timeout_seconds=900,
    )
    prepare_submission_artifacts(
        work_dir=tmp_path,
        task_id="CASE-004",
        result={
            "anomaly_ids": [],
            "record_ids": [],
            "answer": "制度问答不构成异常。",
            "citations": [],
        },
        evidence_input={
            "evidence_rows": [],
            "no_anomaly_coverage": {
                "complete": True,
                "searched_population": "制度语料",
                "query_conditions": "检索题目所问制度条款",
                "checked_rules": [],
                "population_count": 0,
                "conclusion": "制度问答不构成异常",
            },
        },
    )
    schemas = ROOT / "domain-enhancement" / "shared-audit-core" / "schemas"
    for filename, artifact in (
        ("task-state.schema.json", "task_state.json"),
        ("evidence-matrix.schema.json", "evidence_matrix.json"),
        ("validation-report.schema.json", "validation_report.json"),
    ):
        jsonschema.validate(
            _load_json(tmp_path / "work" / artifact),
            _load_json(schemas / filename),
        )


def test_all_scripted_adapters_have_thin_skill_set() -> None:
    adapter_root = ROOT / "domain-enhancement" / "scripted-adapters"
    expected = {
        "audit-query-planner",
        "audit-report",
        "batch-expense-analysis",
        "false-positive-review",
        "policy-version-check",
    }
    frameworks = {
        "claude-code-best",
        "codex",
        "openclaude",
        "opencode",
        "oh-my-pi",
        "pi-agent",
    }
    for framework in frameworks:
        plugin = adapter_root / framework / "securities-expense-audit"
        assert {path.name for path in (plugin / "skills").iterdir() if path.is_dir()} == expected
        assert not (plugin / "skills" / "evidence-coverage-check").exists()
        assert not (plugin / "skills" / "result-validator").exists()
        assert (plugin / "shared" / "control-mcp" / "audit_control_mcp.py").exists()


def test_scripted_control_wrapper_generates_and_submits(
    tmp_path: Path,
    monkeypatch,
) -> None:
    db = tmp_path / "expense.db"
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    _expense_db(db, "R000009")
    initialize_scripted_task(
        work_dir=tmp_path,
        task_id="CASE-009",
        category="clean_but_suspicious",
        question="核查R000009",
        framework="codex",
        experiment_group="codex-scripted-enhanced",
        timeout_seconds=900,
    )
    monkeypatch.setenv("AUDIT_WORK_DIR", str(tmp_path))
    monkeypatch.setenv("AUDIT_TASK_ID", "CASE-009")
    monkeypatch.setenv("AUDIT_FRAMEWORK", "codex")
    monkeypatch.setenv("AUDIT_EXPERIMENT_GROUP", "codex-scripted-enhanced")
    monkeypatch.setenv("AUDIT_SUBAGENTS_ENABLED", "1")
    monkeypatch.setenv("EVAL_EXPENSE_DB", str(db))
    monkeypatch.setenv("EVAL_POLICY_CORPUS_DIR", str(corpus))

    wrapper_path = (
        ROOT
        / "domain-enhancement"
        / "scripted-adapters"
        / "codex"
        / "securities-expense-audit"
        / "shared"
        / "control-mcp"
        / "audit_control_mcp.py"
    )
    spec = importlib.util.spec_from_file_location("scripted_control_wrapper_test", wrapper_path)
    assert spec is not None and spec.loader is not None
    wrapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)
    result = {
        "anomaly_ids": [],
        "record_ids": ["R000009"],
        "answer": "经完整核查无异常。",
        "citations": [],
    }
    (tmp_path / "work" / "final_result.json").write_text(
        json.dumps(result, ensure_ascii=False),
        encoding="utf-8",
    )
    (tmp_path / "work" / "evidence_input.json").write_text(
        json.dumps(
            {
                "evidence_rows": [],
                "no_anomaly_coverage": {
                    "complete": True,
                    "searched_population": "R000009",
                    "query_conditions": "按record_id查询并核对全部适用规则",
                    "checked_rules": [],
                    "population_count": 1,
                    "conclusion": "经完整核查无异常",
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    preflight = wrapper.validate_audit_result()
    assert preflight["valid"] is True
    assert preflight["scripted_enhancement"]["artifacts_generated"] is True
    submission = wrapper.submit_audit_result()
    assert submission["status"] == "accepted"
    assert _load_json(tmp_path / "final_submission.json")["record_ids"] == ["R000009"]
    assert _load_json(tmp_path / "work" / "context_checkpoint.json")["stage"] == "submission_ready"


def test_scripted_runner_isolated_from_formal_run_root() -> None:
    path = ROOT / "runner" / "run_gate4_scripted.py"
    spec = importlib.util.spec_from_file_location("run_gate4_scripted_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.RUN_ROOT.name == "gate4_scripted"
    assert module.PROXY_PORT != 18790
    assert len(module.GROUPS) == 6
    assert all(group.endswith("-scripted-enhanced") for group in module.GROUPS)


def test_scripted_positive_result_without_authored_evidence_is_blocked(tmp_path: Path) -> None:
    initialize_scripted_task(
        work_dir=tmp_path,
        task_id="CASE-010",
        category="single_anomaly",
        question="核查异常",
        framework="codex",
        experiment_group="codex-scripted-enhanced",
        timeout_seconds=900,
    )
    prepared = prepare_submission_artifacts(
        work_dir=tmp_path,
        task_id="CASE-010",
        result={
            "anomaly_ids": ["A-1"],
            "record_ids": ["R1"],
            "answer": "存在异常",
            "citations": [{"doc_id": "POLICY.md", "clause_no": "第一条"}],
        },
    )
    assert prepared["ready"] is False
    assert prepared["validation_report"]["submission_allowed"] is False


def test_scripted_no_anomaly_requires_search_scope(tmp_path: Path) -> None:
    initialize_scripted_task(
        work_dir=tmp_path,
        task_id="CASE-011",
        category="clean_trap",
        question="是否异常",
        framework="opencode",
        experiment_group="opencode-scripted-enhanced",
        timeout_seconds=900,
    )
    prepared = prepare_submission_artifacts(
        work_dir=tmp_path,
        task_id="CASE-011",
        result={"anomaly_ids": [], "record_ids": [], "answer": "无异常", "citations": []},
    )
    assert prepared["ready"] is False
    assert any("searched_population" in item for item in prepared["evidence_matrix"]["missing_evidence"])


def test_scripted_evidence_keeps_per_finding_ownership(tmp_path: Path) -> None:
    initialize_scripted_task(
        work_dir=tmp_path,
        task_id="CASE-012",
        category="batch_analysis",
        question="核查两类异常",
        framework="pi-agent",
        experiment_group="pi-agent-scripted-enhanced",
        timeout_seconds=900,
    )
    citations = [
        {"doc_id": "P.md", "clause_no": "第一条"},
        {"doc_id": "P.md", "clause_no": "第二条"},
    ]
    prepared = prepare_submission_artifacts(
        work_dir=tmp_path,
        task_id="CASE-012",
        result={
            "anomaly_ids": ["A-1", "A-2"],
            "record_ids": ["R1", "R2"],
            "answer": "发现两类异常",
            "citations": citations,
        },
        evidence_input={
            "evidence_rows": [
                {"anomaly_id": "A-1", "record_ids": ["R1"], "citations": [citations[0]], "facts": ["事实1"]},
                {"anomaly_id": "A-2", "record_ids": ["R2"], "citations": [citations[1]], "facts": ["事实2"]},
            ]
        },
    )
    assert prepared["ready"] is True
    assert prepared["evidence_matrix"]["evidence_rows"][0]["record_ids"] == ["R1"]
    assert prepared["evidence_matrix"]["evidence_rows"][1]["record_ids"] == ["R2"]


def test_scripted_runner_rejects_old_version_for_resume(tmp_path: Path) -> None:
    path = ROOT / "runner" / "run_gate4_scripted.py"
    spec = importlib.util.spec_from_file_location("run_gate4_scripted_reuse_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.RUN_ROOT = tmp_path
    result_path = tmp_path / "codex-scripted-enhanced" / "CASE-1" / "run_result.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text(
        json.dumps(
            {
                "submission_status": "accepted",
                "returncode": 0,
                "timed_out": False,
                "elapsed_seconds": 1,
                "workflow_version": "scripted-enhancement-v1.1",
                "config_fingerprint": module.scripted_config_fingerprint(),
                "dataset_fingerprint": module.scripted_dataset_fingerprint(),
            }
        ),
        encoding="utf-8",
    )
    assert module._is_reusable("codex-scripted-enhanced", "CASE-1", 900) is False


def test_scripted_report_quality_excludes_format_item() -> None:
    path = ROOT / "runner" / "report_scripted_comparison.py"
    spec = importlib.util.spec_from_file_location("report_scripted_comparison_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    case = {
        "rubric": {
            "checklist": [
                {"id": "semantic-a", "metric": "conclusion"},
                {"id": "semantic-b", "metric": "policy"},
                {"id": "submission", "metric": "format"},
            ]
        }
    }
    row = {
        "checklist": [
            {"id": "semantic-a", "value": 1},
            {"id": "semantic-b", "value": 0},
            {"id": "submission", "value": 1},
        ]
    }
    assert module._semantic_case_score(row, case) == 50.0
