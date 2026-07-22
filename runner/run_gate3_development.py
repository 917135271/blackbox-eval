from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import stat
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_trace import finish_run, redact_secret_in_tree, start_run  # noqa: E402
from formal_eval_plan import (  # noqa: E402
    GROUPS,
    MODEL_BASE_URL,
    MODEL_NAME,
    TASK_TIMEOUT_SECONDS,
)


DOMAIN = ROOT / "domain-enhancement"
DEV = ROOT / "data" / "development"
DEV_DB = DEV / "expense_dev.db"
RUN_ROOT = ROOT / "runs" / "gate3_development"
CCB_PLUGIN = DOMAIN / "adapters" / "claude-code-best" / "securities-expense-audit"
CODEX_PLUGIN = DOMAIN / "adapters" / "codex" / "securities-expense-audit"
OPENCLAUDE_PLUGIN = DOMAIN / "adapters" / "openclaude" / "securities-expense-audit"
OPENCODE_PLUGIN = DOMAIN / "adapters" / "opencode" / "securities-expense-audit"
OH_MY_PI_PLUGIN = DOMAIN / "adapters" / "oh-my-pi" / "securities-expense-audit"
PI_AGENT_PLUGIN = DOMAIN / "adapters" / "pi-agent" / "securities-expense-audit"
PROXY_PORT = 18790


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def volume(path: Path, container_path: str, read_only: bool = True) -> list[str]:
    return ["-v", f"{path.resolve()}:{container_path}{':ro' if read_only else ''}"]


def safe_reset() -> None:
    target = RUN_ROOT.resolve()
    expected = (ROOT / "runs").resolve()
    if target.parent != expected or target.name != "gate3_development":
        raise ValueError(f"refusing to reset unexpected path: {target}")
    if target.exists():
        def remove_readonly(func: Any, path: str, exc: BaseException) -> None:
            if isinstance(exc, FileNotFoundError):
                return
            if isinstance(exc, PermissionError):
                os.chmod(path, stat.S_IWRITE)
                func(path)
                return
            raise exc

        try:
            shutil.rmtree(target, onexc=remove_readonly)
        except OSError:
            stale = expected / f"gate3_development-stale-{int(time.time() * 1000)}"
            if stale.parent != expected or not stale.name.startswith("gate3_development-stale-"):
                raise ValueError(f"refusing to archive unexpected path: {stale}")
            target.replace(stale)
    target.mkdir(parents=True)


def load_tasks(task_ids: list[str]) -> list[dict[str, Any]]:
    tasks = json.loads((DEV / "evals.json").read_text(encoding="utf-8"))
    if not task_ids:
        return tasks
    selected = [task for task in tasks if task["id"] in set(task_ids)]
    missing = sorted(set(task_ids) - {task["id"] for task in selected})
    if missing:
        raise ValueError(f"unknown task IDs: {missing}")
    return selected


def prepare_baseline_runtime() -> Path:
    runtime = RUN_ROOT / "baseline-runtime"
    if runtime.exists():
        resolved = runtime.resolve()
        if resolved.parent != RUN_ROOT.resolve() or resolved.name != "baseline-runtime":
            raise ValueError(f"refusing to refresh unexpected baseline runtime: {resolved}")
        shutil.rmtree(runtime)
    shutil.copytree(DOMAIN / "control-mcp", runtime / "control-mcp")
    for name in ("references", "routing", "schemas", "scripts"):
        shutil.copytree(DOMAIN / "shared-audit-core" / name, runtime / "shared-audit-core" / name)
    return runtime


def archive_retry_task(group: str, task_id: str) -> None:
    if group not in GROUPS or not task_id.startswith("DEV-"):
        raise ValueError(f"invalid retry target: {group}/{task_id}")
    source = (RUN_ROOT / group / task_id).resolve()
    expected_parent = (RUN_ROOT / group).resolve()
    if source.parent != expected_parent or source.name != task_id or not source.exists():
        return
    history = RUN_ROOT / "retry-history" / group / task_id
    history.mkdir(parents=True, exist_ok=True)
    index = 1
    while (history / f"attempt-{index}").exists():
        index += 1
    shutil.move(str(source), str(history / f"attempt-{index}"))


def is_reusable_result(result: dict[str, Any], timeout: int) -> bool:
    elapsed = result.get("elapsed_seconds")
    return (
        result.get("submission_status") == "accepted"
        and not result.get("timed_out")
        and isinstance(elapsed, (int, float))
        and elapsed <= timeout
    )


def baseline_instructions() -> str:
    return """# GATE3 Baseline Runtime

Use the policy_query and expense_query MCP tools plus Shell, Python, SQLite, and files inside this isolated workspace. Do not use domain Skills or native subagents in this baseline group.

Before calling submit_audit_result, write work/evidence_matrix.json and work/validation_report.json. The evidence matrix must have status pass, coverage_percent 100, evidence_rows, candidate_record_ids, submitted_record_ids, empty unowned_record_ids, empty unused_candidate_record_ids, empty unused_citations, empty missing_evidence, no_anomaly_coverage, reconciled_figures, and empty unresolved_items. Every anomaly evidence row must include anomaly_id, record_ids, citations as objects containing only doc_id and clause_no, facts as a non-empty array, fact_supported true, rule_supported true, and coverage_status pass. For a no-anomaly result, use no evidence rows and set no_anomaly_coverage.complete true.

The validation report must have status pass, empty errors and warnings, field_checks, id_checks, evidence_checks, answer_consistency_checks, repair_count 0, empty repairable_fields, and submission_allowed true. Call validate_audit_result before submission; repair all reported fields and correlated files, then preflight once more. Submit exactly anomaly_ids, record_ids, answer, and citations only after valid=true. Repair only once if the submit tool itself returns repair_required, and never retry after rejection.
"""


def task_prompt(task: dict[str, Any], enhanced: bool, framework: str | None = None) -> str:
    mode = "领域增强组" if enhanced else "原生基线组"
    workflow = (
        "必须遵循已安装的证券费用审计 Skills；先规划并记录Checkpoint，再按触发条件调查、复核、校验并通过统一工具提交。若复杂度至少为2且存在符合路由规则的角色，必须调用authorize_audit_subagent授权原生子智能体，并在原生角色结束后调用complete_audit_subagent登记摘要和产物；主上下文只接收六字段结构化摘要。"
        if enhanced
        else "不得调用领域 Skills 或子智能体；使用框架基础工具、业务 MCP 和统一提交工具独立完成。"
    )
    framework_hint = (
        "OpenClaude运行时只保证Bash、Edit、Read可用；三个JSON文件已经存在，必须使用Edit或Bash中的安全脚本更新，禁止调用Write、Grep等未暴露工具。"
        if framework == "openclaude"
        else ""
    )
    return f"""你正在执行 GATE3 独立开发题，当前为{mode}，不是正式评测题。

任务ID：{task['id']}
题型：{task['category']}
问题：{task['prompt']}
领域增强路由提示：{task.get('routing_hint', '由规划器按规则计算') if enhanced else '基线组不使用领域路由'}

{workflow}
{framework_hint}

要求：
1. 必须查询制度和只读开发业务库后作答，可以使用 Shell、Python、SQLite和临时文件。
2. 只处理当前独立工作区。禁止读取 ground_truth、正式 evals、判卷代码、历史答案、其他任务或候选轨迹。
3. anomaly_ids 是审计发现标识，使用非空且内部一致的字符串即可；开发题判定以业务结论、record_ids和制度证据为主。
4. record_ids必须遵守统一语义：有异常时只包含参与当前题目所问违规的记录，不含累计计算背景、有效豁免或无关规则记录；无异常时仍保留题目直接核查或结论覆盖的记录，并在answer中明确写“无异常”。
5. 工作区的work/final_result.json、work/evidence_matrix.json和work/validation_report.json已经按共享Schema预置字段骨架；必须先把最终答案写入final_result.json，只更新字段值和必要的evidence_rows，不得改名、删除必填字段或另建替代格式。如需核对，只读取绝对路径/runtime-schemas下的共享Schema，或当前工作区绝对路径/workspace/runtime-schemas下三个明确的*.schema.json文件；当前目录已经是/workspace，禁止拼成/workspace/workspace；不要猜测其他路径或文件名。
6. 调用audit_control.validate_audit_result时使用result_path="work/final_result.json"及两个默认报告路径；取得valid=true后，以相同result_path调用audit_control.submit_audit_result。不要把完整结果对象嵌套在工具参数中。不得用终端直接import控制代码，也不得把最终JSON打印出来代替提交。
7. 提交成功后最终只输出 GATE3_TASK_PASS；无法提交时只输出 GATE3_TASK_FAIL。
"""


def prepare_submission_templates(workspace: Path) -> None:
    work = workspace / "work"
    work.mkdir(parents=True, exist_ok=True)
    evidence_matrix = {
        "status": "pass",
        "coverage_percent": 100,
        "evidence_rows": [],
        "candidate_record_ids": [],
        "submitted_record_ids": [],
        "unowned_record_ids": [],
        "unused_candidate_record_ids": [],
        "unused_citations": [],
        "missing_evidence": [],
        "no_anomaly_coverage": {"complete": False},
        "reconciled_figures": {},
        "unresolved_items": [],
    }
    validation_report = {
        "status": "pass",
        "errors": [],
        "warnings": [],
        "field_checks": {},
        "id_checks": {},
        "evidence_checks": {},
        "answer_consistency_checks": {},
        "repair_count": 0,
        "repairable_fields": [],
        "submission_allowed": True,
    }
    final_result = {"anomaly_ids": [], "record_ids": [], "answer": "待填写", "citations": []}
    write_text(work / "final_result.json", json.dumps(final_result, ensure_ascii=False, indent=2) + "\n")
    write_text(work / "evidence_matrix.json", json.dumps(evidence_matrix, ensure_ascii=False, indent=2) + "\n")
    write_text(work / "validation_report.json", json.dumps(validation_report, ensure_ascii=False, indent=2) + "\n")


def ccb_mcp_config(baseline: bool) -> dict[str, Any]:
    servers: dict[str, Any] = {
        "policy_query": {
            "type": "stdio",
            "command": "python3",
            "args": ["/benchmark/fixtures/policy_query_mcp.py"],
            "env": {
                "EVAL_POLICY_CORPUS_DIR": "/benchmark/data/corpus",
                "EVAL_TASK_LOG": "/artifacts/tool_calls.jsonl",
                "PYTHONIOENCODING": "utf-8",
            },
        },
        "expense_query": {
            "type": "stdio",
            "command": "python3",
            "args": ["/benchmark/fixtures/expense_query_mcp.py"],
            "env": {
                "EVAL_EXPENSE_DB": "/benchmark/data/expense.db",
                "EVAL_TASK_LOG": "/artifacts/tool_calls.jsonl",
                "PYTHONIOENCODING": "utf-8",
            },
        },
    }
    if baseline:
        servers["audit_control"] = {
            "type": "stdio",
            "command": "python3",
            "args": ["/baseline/control-mcp/audit_control_mcp.py"],
            "env": {
                "AUDIT_TASK_ID": "${AUDIT_TASK_ID}",
                "AUDIT_WORK_DIR": "${AUDIT_WORK_DIR}",
                "AUDIT_SUBAGENTS_ENABLED": "0",
                "EVAL_EXPENSE_DB": "${EVAL_EXPENSE_DB}",
                "EVAL_POLICY_CORPUS_DIR": "${EVAL_POLICY_CORPUS_DIR}",
                "PYTHONIOENCODING": "utf-8",
            },
        }
    return {"mcpServers": servers}


def openclaude_mcp_config(enhanced: bool) -> dict[str, Any]:
    config = ccb_mcp_config(True)
    control = config["mcpServers"]["audit_control"]
    if enhanced:
        control["args"] = ["/plugin/shared/control-mcp/audit_control_mcp.py"]
        control["env"]["AUDIT_SUBAGENTS_ENABLED"] = "1"
    return config


def codex_config(task_id: str, enhanced: bool) -> str:
    control_path = "/plugin/shared/control-mcp/audit_control_mcp.py" if enhanced else "/baseline/control-mcp/audit_control_mcp.py"
    feature = "true" if enhanced else "false"
    agents = ""
    if enhanced:
        agents = '''
[agents.policy_researcher]
description = "Resolve applicable policy versions, dates, conflicts, exceptions, and clauses."
config_file = "/home/codex/.codex/agents/policy_researcher.toml"

[agents.data_analyst]
description = "Execute complete read-only SQLite and Python expense analysis."
config_file = "/home/codex/.codex/agents/data_analyst.toml"

[agents.independent_reviewer]
description = "Challenge findings for exceptions, boundaries, omissions, and false positives."
config_file = "/home/codex/.codex/agents/independent_reviewer.toml"
'''
    return f'''model = "{MODEL_NAME}"
model_provider = "deepseek"
model_context_window = 131072
model_auto_compact_token_limit = 100000
model_catalog_json = "/opt/codex-source/model_catalog.deepseek.json"
model_instructions_file = "/opt/codex-source/base_instructions.md"
approval_policy = "never"
sandbox_mode = "danger-full-access"
suppress_unstable_features_warning = true

[features]
enable_request_compression = false
multi_agent = {feature}
multi_agent_v2 = false

[model_providers.deepseek]
name = "DeepSeek via Responses adapter"
base_url = "http://host.docker.internal:{PROXY_PORT}/v1"
env_key = "LLM_API_KEY"
wire_api = "responses"
{agents}
[mcp_servers.policy_query]
command = "python3"
args = ["/benchmark/fixtures/policy_query_mcp.py"]
startup_timeout_sec = 30
tool_timeout_sec = 120

[mcp_servers.policy_query.env]
EVAL_POLICY_CORPUS_DIR = "/benchmark/data/corpus"
EVAL_TASK_LOG = "/artifacts/tool_calls.jsonl"
PYTHONIOENCODING = "utf-8"

[mcp_servers.expense_query]
command = "python3"
args = ["/benchmark/fixtures/expense_query_mcp.py"]
startup_timeout_sec = 30
tool_timeout_sec = 120

[mcp_servers.expense_query.env]
EVAL_EXPENSE_DB = "/benchmark/data/expense.db"
EVAL_TASK_LOG = "/artifacts/tool_calls.jsonl"
PYTHONIOENCODING = "utf-8"

[mcp_servers.audit_control]
command = "python3"
args = ["{control_path}"]
startup_timeout_sec = 30
tool_timeout_sec = 120

[mcp_servers.audit_control.env]
AUDIT_TASK_ID = "{task_id}"
AUDIT_WORK_DIR = "/workspace"
AUDIT_SUBAGENTS_ENABLED = "{'1' if enhanced else '0'}"
AUDIT_FRAMEWORK = "codex"
AUDIT_EXPERIMENT_GROUP = "codex-{'enhanced' if enhanced else 'baseline'}"
EVAL_EXPENSE_DB = "/benchmark/data/expense.db"
EVAL_POLICY_CORPUS_DIR = "/benchmark/data/corpus"
PYTHONIOENCODING = "utf-8"
'''


def opencode_config(task_id: str, enhanced: bool) -> dict[str, Any]:
    control_path = "/plugin/shared/control-mcp/audit_control_mcp.py" if enhanced else "/baseline/control-mcp/audit_control_mcp.py"
    config: dict[str, Any] = {
        "$schema": "https://opencode.ai/config.json",
        "autoupdate": False,
        "model": f"deepseek/{MODEL_NAME}",
        "enabled_providers": ["deepseek"],
        "provider": {
            "deepseek": {
                "npm": "@ai-sdk/openai-compatible",
                "name": "DeepSeek",
                "options": {"baseURL": MODEL_BASE_URL, "apiKey": "{env:LLM_API_KEY}"},
                "models": {MODEL_NAME: {"name": MODEL_NAME}},
            }
        },
        "instructions": ["AGENTS.md"],
        "permission": {
            "*": "allow",
            "webfetch": "deny",
            "websearch": "deny",
            "task": "deny" if not enhanced else {
                "*": "deny",
                "policy-researcher": "allow",
                "data-analyst": "allow",
                "independent-reviewer": "allow",
            },
        },
        "mcp": {
            "policy_query": {
                "type": "local",
                "command": ["python3", "/benchmark/fixtures/policy_query_mcp.py"],
                "enabled": True,
                "env": {
                    "EVAL_POLICY_CORPUS_DIR": "/benchmark/data/corpus",
                    "EVAL_TASK_LOG": "/artifacts/tool_calls.jsonl",
                    "PYTHONIOENCODING": "utf-8",
                },
            },
            "expense_query": {
                "type": "local",
                "command": ["python3", "/benchmark/fixtures/expense_query_mcp.py"],
                "enabled": True,
                "env": {
                    "EVAL_EXPENSE_DB": "/benchmark/data/expense.db",
                    "EVAL_TASK_LOG": "/artifacts/tool_calls.jsonl",
                    "PYTHONIOENCODING": "utf-8",
                },
            },
            "audit_control": {
                "type": "local",
                "command": ["python3", control_path],
                "enabled": True,
                "env": {
                    "AUDIT_TASK_ID": task_id,
                "AUDIT_WORK_DIR": "/workspace",
                "AUDIT_SUBAGENTS_ENABLED": "1" if enhanced else "0",
                "AUDIT_FRAMEWORK": "opencode",
                "AUDIT_EXPERIMENT_GROUP": f"opencode-{'enhanced' if enhanced else 'baseline'}",
                    "EVAL_EXPENSE_DB": "/benchmark/data/expense.db",
                    "EVAL_POLICY_CORPUS_DIR": "/benchmark/data/corpus",
                    "PYTHONIOENCODING": "utf-8",
                },
            },
        },
    }
    if enhanced:
        config["agent"] = {
            "policy-researcher": {
                "description": "Resolve applicable policy versions, conflicts, exceptions, and clauses.",
                "mode": "subagent",
                "prompt": "{file:./.opencode/agents/policy-researcher.md}",
            },
            "data-analyst": {
                "description": "Execute complete read-only SQLite and Python expense analysis.",
                "mode": "subagent",
                "prompt": "{file:./.opencode/agents/data-analyst.md}",
            },
            "independent-reviewer": {
                "description": "Challenge findings for exceptions, boundaries, omissions, and false positives.",
                "mode": "subagent",
                "prompt": "{file:./.opencode/agents/independent-reviewer.md}",
            },
        }
    return config


def oh_my_pi_models_config() -> str:
    return f"""providers:
  deepseek:
    baseUrl: {MODEL_BASE_URL}/v1
    apiKey: LLM_API_KEY
    api: openai-completions
    auth: apiKey
    models:
      - id: {MODEL_NAME}
        name: {MODEL_NAME}
        reasoning: true
        input: [text]
        contextWindow: 131072
        maxTokens: 32768
        compat:
          supportsToolChoice: true
          supportsForcedToolChoice: false
          disableReasoningOnToolChoice: true
          streamIdleTimeoutMs: 120000
"""


def oh_my_pi_mcp_config(task_id: str, enhanced: bool) -> dict[str, Any]:
    control_path = "/plugin/shared/control-mcp/audit_control_mcp.py" if enhanced else "/baseline/control-mcp/audit_control_mcp.py"
    return {
        "mcpServers": {
            "policy_query": {
                "type": "stdio",
                "command": "python3",
                "args": ["/benchmark/fixtures/policy_query_mcp.py"],
                "timeout": 120000,
                "env": {
                    "EVAL_POLICY_CORPUS_DIR": "/benchmark/data/corpus",
                    "EVAL_TASK_LOG": "/artifacts/tool_calls.jsonl",
                    "PYTHONIOENCODING": "utf-8",
                },
            },
            "expense_query": {
                "type": "stdio",
                "command": "python3",
                "args": ["/benchmark/fixtures/expense_query_mcp.py"],
                "timeout": 120000,
                "env": {
                    "EVAL_EXPENSE_DB": "/benchmark/data/expense.db",
                    "EVAL_TASK_LOG": "/artifacts/tool_calls.jsonl",
                    "PYTHONIOENCODING": "utf-8",
                },
            },
            "audit_control": {
                "type": "stdio",
                "command": "python3",
                "args": [control_path],
                "timeout": 120000,
                "env": {
                    "AUDIT_TASK_ID": task_id,
                    "AUDIT_WORK_DIR": "/workspace",
                    "AUDIT_SUBAGENTS_ENABLED": "1" if enhanced else "0",
                    "AUDIT_FRAMEWORK": "oh-my-pi",
                    "AUDIT_EXPERIMENT_GROUP": f"oh-my-pi-{'enhanced' if enhanced else 'baseline'}",
                    "EVAL_EXPENSE_DB": "/benchmark/data/expense.db",
                    "EVAL_POLICY_CORPUS_DIR": "/benchmark/data/corpus",
                    "PYTHONIOENCODING": "utf-8",
                },
            },
        }
    }


def prepare_task(group: str, task: dict[str, Any]) -> tuple[Path, Path, Path]:
    base = RUN_ROOT / group / task["id"]
    workspace = base / "workspace"
    artifacts = base / "artifacts"
    config = base / "config"
    for path in (workspace, artifacts, config):
        path.mkdir(parents=True, exist_ok=True)
    prepare_submission_templates(workspace)
    runtime_schemas = workspace / "runtime-schemas"
    runtime_schemas.mkdir()
    schema_source = DOMAIN / "shared-audit-core" / "schemas"
    for source_name, target_name, compatibility_name in (
        (
            "audit-result.schema.json",
            "final_result.schema.json",
            "final_result_schema.json",
        ),
        (
            "evidence-matrix.schema.json",
            "evidence_matrix.schema.json",
            "evidence_matrix_schema.json",
        ),
        (
            "validation-report.schema.json",
            "validation_report.schema.json",
            "validation_report_schema.json",
        ),
    ):
        source = schema_source / source_name
        shutil.copy2(source, runtime_schemas / target_name)
        shutil.copy2(source, runtime_schemas / compatibility_name)
    enhanced = group.endswith("enhanced")
    instructions = (
        (DOMAIN / "shared-audit-core" / "references" / "main_workflow.md").read_text(encoding="utf-8")
        if enhanced
        else baseline_instructions()
    )
    write_text(workspace / "AGENTS.md", instructions)
    write_text(workspace / "CLAUDE.md", instructions)
    write_text(workspace / "task.md", task_prompt(task, enhanced, group.rsplit("-", 1)[0]))
    if group.startswith("ccb"):
        shutil.copy2(ROOT / "candidates" / "claude-code" / "settings.json", config / "settings.json")
        write_text(config / "mcp.json", json.dumps(ccb_mcp_config(not enhanced), ensure_ascii=False, indent=2) + "\n")
    elif group.startswith("codex"):
        codex_home = base / "codex-home"
        codex_home.mkdir()
        if enhanced:
            shutil.copytree(CODEX_PLUGIN / "skills", codex_home / "skills")
            shutil.copytree(CODEX_PLUGIN / "agents", codex_home / "agents")
        write_text(codex_home / "config.toml", codex_config(task["id"], enhanced))
    elif group.startswith("openclaude"):
        write_text(
            config / "mcp.json",
            json.dumps(openclaude_mcp_config(enhanced), ensure_ascii=False, indent=2) + "\n",
        )
    elif group.startswith("opencode"):
        if enhanced:
            opencode_dir = workspace / ".opencode"
            shutil.copytree(OPENCODE_PLUGIN / "skills", opencode_dir / "skills")
            shutil.copytree(OPENCODE_PLUGIN / ".opencode" / "agents", opencode_dir / "agents")
        write_text(workspace / "opencode.json", json.dumps(opencode_config(task["id"], enhanced), ensure_ascii=False, indent=2) + "\n")
    elif group.startswith("oh-my-pi"):
        omp_home = base / "omp-home"
        omp_home.mkdir()
        write_text(omp_home / "models.yml", oh_my_pi_models_config())
        omp_dir = workspace / ".omp"
        omp_dir.mkdir()
        write_text(
            omp_dir / "mcp.json",
            json.dumps(oh_my_pi_mcp_config(task["id"], enhanced), ensure_ascii=False, indent=2) + "\n",
        )
        if enhanced:
            shutil.copytree(OH_MY_PI_PLUGIN / "skills", omp_dir / "skills")
            shutil.copytree(OH_MY_PI_PLUGIN / ".omp" / "agents", omp_dir / "agents")
            shutil.copytree(OH_MY_PI_PLUGIN / ".omp" / "extensions", omp_dir / "extensions")
    elif group.startswith("pi-agent"):
        if enhanced:
            pi_dir = workspace / ".pi"
            pi_dir.mkdir()
            shutil.copytree(PI_AGENT_PLUGIN / ".pi" / "agents", pi_dir / "agents")
    else:
        raise ValueError(f"unsupported group: {group}")
    return base, workspace, artifacts


def common_volumes(workspace: Path, artifacts: Path) -> list[str]:
    args: list[str] = []
    args += volume(ROOT / "fixtures", "/benchmark/fixtures")
    args += volume(DEV_DB, "/benchmark/data/expense.db")
    args += volume(ROOT / "data" / "corpus", "/benchmark/data/corpus")
    args += volume(DOMAIN / "shared-audit-core" / "schemas", "/runtime-schemas")
    args += volume(workspace, "/workspace", read_only=False)
    args += volume(artifacts, "/artifacts", read_only=False)
    return args


def ccb_command(group: str, task: dict[str, Any], baseline_runtime: Path, env: dict[str, str]) -> tuple[list[str], dict[str, str]]:
    base, workspace, artifacts = prepare_task(group, task)
    enhanced = group.endswith("enhanced")
    name = f"g3-{group}-{task['id'].lower()}"
    command = ["docker", "run", "--rm", "--name", name]
    command += [
        "-e", "OPENAI_API_KEY",
        "-e", "CLAUDE_CODE_USE_OPENAI=1",
        "-e", "OPENAI_MAX_RETRIES=2",
        "-e", "OPENAI_TIMEOUT_MS=120000",
        "-e", f"OPENAI_BASE_URL={MODEL_BASE_URL}",
        "-e", f"OPENAI_MODEL={MODEL_NAME}",
        "-e", f"ANTHROPIC_DEFAULT_HAIKU_MODEL={MODEL_NAME}",
        "-e", f"ANTHROPIC_DEFAULT_SONNET_MODEL={MODEL_NAME}",
        "-e", f"ANTHROPIC_DEFAULT_OPUS_MODEL={MODEL_NAME}",
        "-e", f"AUDIT_TASK_ID={task['id']}",
        "-e", "AUDIT_WORK_DIR=/workspace",
        "-e", f"AUDIT_SUBAGENTS_ENABLED={'1' if enhanced else '0'}",
        "-e", "AUDIT_FRAMEWORK=claude-code-best",
        "-e", f"AUDIT_EXPERIMENT_GROUP={group}",
        "-e", "EVAL_EXPENSE_DB=/benchmark/data/expense.db",
        "-e", "EVAL_POLICY_CORPUS_DIR=/benchmark/data/corpus",
    ]
    command += common_volumes(workspace, artifacts)
    command += volume(base / "config" / "settings.json", "/config/settings.json")
    command += volume(base / "config" / "mcp.json", "/config/mcp.json")
    if enhanced:
        command += volume(CCB_PLUGIN, "/plugin")
    else:
        command += volume(baseline_runtime, "/baseline")
    command += [
        "-w", "/workspace",
        "blackbox-eval/ccb-source-nonroot:2.8.3",
        "--print",
    ]
    if enhanced:
        command += ["--plugin-dir", "/plugin"]
    command += [
        "--settings", "/config/settings.json",
        "--mcp-config", "/config/mcp.json",
        "--dangerously-skip-permissions",
        "--output-format", "stream-json",
        "--verbose",
        "--debug-file", "/artifacts/debug.log",
        "--no-session-persistence",
        "--effort", "high",
        task_prompt(task, enhanced),
    ]
    child_env = env.copy()
    child_env["OPENAI_API_KEY"] = env["LLM_API_KEY"]
    return command, child_env


def codex_command(group: str, task: dict[str, Any], baseline_runtime: Path, env: dict[str, str]) -> tuple[list[str], dict[str, str]]:
    base, workspace, artifacts = prepare_task(group, task)
    enhanced = group.endswith("enhanced")
    name = f"g3-{group}-{task['id'].lower()}"
    command = ["docker", "run", "--rm", "--name", name]
    command += [
        "-e", "LLM_API_KEY",
        "-e", "CODEX_HOME=/home/codex/.codex",
        "-e", "NO_PROXY=host.docker.internal,localhost,127.0.0.1",
        "-e", "no_proxy=host.docker.internal,localhost,127.0.0.1",
        "-e", f"AUDIT_TASK_ID={task['id']}",
        "-e", "AUDIT_WORK_DIR=/workspace",
        "-e", f"AUDIT_SUBAGENTS_ENABLED={'1' if enhanced else '0'}",
        "-e", "AUDIT_FRAMEWORK=codex",
        "-e", f"AUDIT_EXPERIMENT_GROUP={group}",
        "-e", "EVAL_EXPENSE_DB=/benchmark/data/expense.db",
        "-e", "EVAL_POLICY_CORPUS_DIR=/benchmark/data/corpus",
    ]
    if enhanced:
        command += ["-e", "AUDIT_PLUGIN_ROOT=/plugin"]
    command += common_volumes(workspace, artifacts)
    command += volume(base / "codex-home", "/home/codex/.codex", read_only=False)
    if enhanced:
        command += volume(CODEX_PLUGIN, "/plugin")
    else:
        command += volume(baseline_runtime, "/baseline")
    command += [
        "-w", "/workspace",
        "blackbox-eval/codex-source:0.144.4",
        "exec", "--json", "--strict-config", "--skip-git-repo-check", "--ephemeral",
        "--dangerously-bypass-approvals-and-sandbox", "-C", "/workspace",
        "-o", "/artifacts/last_message.txt",
        task_prompt(task, enhanced),
    ]
    return command, env.copy()


def openclaude_command(group: str, task: dict[str, Any], baseline_runtime: Path, env: dict[str, str]) -> tuple[list[str], dict[str, str]]:
    base, workspace, artifacts = prepare_task(group, task)
    enhanced = group.endswith("enhanced")
    name = f"g3-{group}-{task['id'].lower()}"
    command = ["docker", "run", "--rm", "--name", name]
    command += [
        "-e", "OPENAI_API_KEY",
        "-e", "CLAUDE_CODE_USE_OPENAI=1",
        "-e", f"OPENAI_BASE_URL={MODEL_BASE_URL}/v1",
        "-e", f"OPENAI_MODEL={MODEL_NAME}",
        "-e", "OPENCLAUDE_CONFIG_DIR=/tmp/openclaude-config",
        "-e", f"AUDIT_TASK_ID={task['id']}",
        "-e", "AUDIT_WORK_DIR=/workspace",
        "-e", f"AUDIT_SUBAGENTS_ENABLED={'1' if enhanced else '0'}",
        "-e", "AUDIT_FRAMEWORK=openclaude",
        "-e", f"AUDIT_EXPERIMENT_GROUP={group}",
        "-e", "EVAL_EXPENSE_DB=/benchmark/data/expense.db",
        "-e", "EVAL_POLICY_CORPUS_DIR=/benchmark/data/corpus",
    ]
    command += common_volumes(workspace, artifacts)
    command += volume(base / "config" / "mcp.json", "/config/mcp.json")
    if enhanced:
        command += ["-e", "AUDIT_PLUGIN_ROOT=/plugin"]
        command += volume(OPENCLAUDE_PLUGIN, "/plugin")
    else:
        command += volume(baseline_runtime, "/baseline")
    command += [
        "-w", "/workspace",
        "blackbox-eval/openclaude-source:0.24.0",
        "-p",
        "--provider", "openai",
        "--model", MODEL_NAME,
        "--output-format", "stream-json",
        "--verbose",
        "--bare",
        "--no-session-persistence",
        "--tools", "default",
        "--mcp-config", "/config/mcp.json",
        "--strict-mcp-config",
        "--dangerously-skip-permissions",
        "--debug-file", "/artifacts/debug.log",
    ]
    if enhanced:
        command += ["--plugin-dir", "/plugin"]
    command += [task_prompt(task, enhanced, "openclaude")]
    child_env = env.copy()
    child_env["OPENAI_API_KEY"] = env["LLM_API_KEY"]
    return command, child_env


def opencode_command(group: str, task: dict[str, Any], baseline_runtime: Path, env: dict[str, str]) -> tuple[list[str], dict[str, str]]:
    _, workspace, artifacts = prepare_task(group, task)
    enhanced = group.endswith("enhanced")
    name = f"g3-{group}-{task['id'].lower()}"
    command = ["docker", "run", "--rm", "--name", name]
    command += [
        "-e", "LLM_API_KEY",
        "-e", f"AUDIT_TASK_ID={task['id']}",
        "-e", "AUDIT_WORK_DIR=/workspace",
        "-e", f"AUDIT_SUBAGENTS_ENABLED={'1' if enhanced else '0'}",
        "-e", "AUDIT_FRAMEWORK=opencode",
        "-e", f"AUDIT_EXPERIMENT_GROUP={group}",
        "-e", "EVAL_EXPENSE_DB=/benchmark/data/expense.db",
        "-e", "EVAL_POLICY_CORPUS_DIR=/benchmark/data/corpus",
    ]
    command += common_volumes(workspace, artifacts)
    if enhanced:
        command += volume(OPENCODE_PLUGIN, "/plugin")
    else:
        command += volume(baseline_runtime, "/baseline")
    command += [
        "-w", "/workspace",
        "blackbox-eval/opencode-source:1.18.1",
        "run", "--pure", "--dir", "/workspace", "--format", "json",
        "--model", f"deepseek/{MODEL_NAME}", "--variant", "high", "--auto",
        task_prompt(task, enhanced),
    ]
    return command, env.copy()


def oh_my_pi_command(group: str, task: dict[str, Any], baseline_runtime: Path, env: dict[str, str]) -> tuple[list[str], dict[str, str]]:
    base, workspace, artifacts = prepare_task(group, task)
    enhanced = group.endswith("enhanced")
    name = f"g3-{group}-{task['id'].lower()}"
    command = ["docker", "run", "--rm", "--name", name]
    command += [
        "-e", "LLM_API_KEY",
        "-e", "PI_CODING_AGENT_DIR=/omp-home",
        "-e", "OMP_MCP_TIMEOUT_MS=120000",
        "-e", "PI_NO_PTY=1",
        "-e", f"AUDIT_TASK_ID={task['id']}",
        "-e", "AUDIT_WORK_DIR=/workspace",
        "-e", f"AUDIT_SUBAGENTS_ENABLED={'1' if enhanced else '0'}",
        "-e", "AUDIT_FRAMEWORK=oh-my-pi",
        "-e", f"AUDIT_EXPERIMENT_GROUP={group}",
        "-e", "EVAL_EXPENSE_DB=/benchmark/data/expense.db",
        "-e", "EVAL_POLICY_CORPUS_DIR=/benchmark/data/corpus",
    ]
    command += common_volumes(workspace, artifacts)
    command += volume(base / "omp-home", "/omp-home", read_only=False)
    if enhanced:
        command += volume(OH_MY_PI_PLUGIN, "/plugin")
    else:
        command += volume(baseline_runtime, "/baseline")
    command += [
        "-w", "/workspace",
        "blackbox-eval/oh-my-pi-source:17.0.1",
        "--print",
        "--mode", "json",
        "--no-session",
        "--no-title",
        "--provider", "deepseek",
        "--model", MODEL_NAME,
        "--thinking", "high",
        "--approval-mode", "yolo",
        "--max-time", str(TASK_TIMEOUT_SECONDS),
        "--tools",
        (
            "read,bash,edit,eval,glob,grep,lsp,checkpoint,todo,write,task,hub"
            if enhanced
            else "read,bash,edit,eval,glob,grep,lsp,checkpoint,todo,write"
        ),
        "--cwd", "/workspace",
        task_prompt(task, enhanced),
    ]
    return command, env.copy()


def pi_agent_command(group: str, task: dict[str, Any], baseline_runtime: Path, env: dict[str, str]) -> tuple[list[str], dict[str, str]]:
    base, workspace, artifacts = prepare_task(group, task)
    enhanced = group.endswith("enhanced")
    name = f"g3-{group}-{task['id'].lower()}"
    command = ["docker", "run", "--rm", "--name", name]
    command += [
        "-e", "LLM_API_KEY",
        "-e", f"AUDIT_TASK_ID={task['id']}",
        "-e", "AUDIT_WORK_DIR=/workspace",
        "-e", f"AUDIT_SUBAGENTS_ENABLED={'1' if enhanced else '0'}",
        "-e", "AUDIT_FRAMEWORK=pi-agent",
        "-e", f"AUDIT_EXPERIMENT_GROUP={group}",
        "-e", "AUDIT_CONTROL_MCP_PATH=/plugin/shared/control-mcp/audit_control_mcp.py",
        "-e", "EVAL_EXPENSE_DB=/benchmark/data/expense.db",
        "-e", "EVAL_POLICY_CORPUS_DIR=/benchmark/data/corpus",
        "-e", "EVAL_TASK_LOG=/artifacts/tool_calls.jsonl",
    ]
    command += common_volumes(workspace, artifacts)
    command += volume(PI_AGENT_PLUGIN, "/plugin")
    command += [
        "-w", "/workspace",
        "blackbox-eval/pi-agent-source:0.80.10",
        "--print",
        "--mode", "json",
        "--no-session",
        "--offline",
        "--approve",
        "--no-extensions",
        "--no-skills",
        "--provider", "deepseek-eval",
        "--model", MODEL_NAME,
        "--thinking", "high",
        "-e", "/plugin/.pi/extensions/business-tools.ts",
        "-e", "/plugin/.pi/extensions/audit-governance.ts",
    ]
    if enhanced:
        command += ["-e", "/plugin/.pi/extensions/subagent/index.ts"]
        for skill in sorted((PI_AGENT_PLUGIN / "skills").glob("*/SKILL.md")):
            command += ["--skill", f"/plugin/skills/{skill.parent.name}/SKILL.md"]
    business_tools = (
        "list_policy_docs,search_policy,get_policy_doc,get_policy_excerpt,"
        "list_expenses,get_expense_detail,find_invoice_usage,list_invoices,find_reused_invoices,"
        "summarize_expenses,summarize_department_budgets,list_records_by_reimburse_delay,"
        "list_records_missing_approval,list_employees,get_employee,get_department_budget,list_approvals"
    )
    control_tools = (
        "authorize_audit_subagent,complete_audit_subagent,checkpoint_audit_context,"
        "validate_audit_result,submit_audit_result"
    )
    command += [
        "--tools",
        f"read,bash,edit,write,{business_tools},{control_tools}{',subagent' if enhanced else ''}",
        task_prompt(task, enhanced, "pi-agent"),
    ]
    return command, env.copy()


def _timeout_text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return value or ""


def _run_captured_command(
    command: list[str],
    child_env: dict[str, str],
    timeout: int,
    container_name: str,
) -> tuple[int | None, bool, str, str]:
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        env=child_env,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return process.returncode, False, stdout, stderr
    except subprocess.TimeoutExpired as first_timeout:
        # On Windows, subprocess.run kills docker.exe before removing the
        # container, then can wait forever on inherited output pipes. Remove
        # the named container first so the Docker stream closes deterministically.
        try:
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                capture_output=True,
                check=False,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            pass
        try:
            stdout, stderr = process.communicate(timeout=30)
        except subprocess.TimeoutExpired as cleanup_timeout:
            process.kill()
            try:
                stdout, stderr = process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                stdout = _timeout_text(cleanup_timeout.stdout or first_timeout.stdout)
                stderr = _timeout_text(cleanup_timeout.stderr or first_timeout.stderr)
        return None, True, _timeout_text(stdout), _timeout_text(stderr)


def run_one(group: str, task: dict[str, Any], baseline_runtime: Path, timeout: int) -> dict[str, Any]:
    builders = {
        "ccb": ccb_command,
        "codex": codex_command,
        "openclaude": openclaude_command,
        "opencode": opencode_command,
        "oh-my-pi": oh_my_pi_command,
        "pi-agent": pi_agent_command,
    }
    prefix = group.rsplit("-", 1)[0]
    builder = builders[prefix]
    command, child_env = builder(group, task, baseline_runtime, os.environ.copy())
    base = RUN_ROOT / group / task["id"]
    framework = {
        "ccb": "claude-code-best",
        "codex": "codex",
        "openclaude": "openclaude",
        "opencode": "opencode",
        "oh-my-pi": "oh-my-pi",
        "pi-agent": "pi-agent",
    }[prefix]
    start_run(
        workspace=base / "workspace",
        task_id=task["id"],
        framework=framework,
        experiment_group=group,
        model=MODEL_NAME,
        timeout_seconds=timeout,
    )
    started = time.time()
    timed_out = False
    returncode: int | None
    stdout = ""
    stderr = ""
    container_name = f"g3-{group}-{task['id'].lower()}"
    returncode, timed_out, stdout, stderr = _run_captured_command(
        command,
        child_env,
        timeout,
        container_name,
    )
    write_text(base / "artifacts" / "trajectory.jsonl", stdout)
    write_text(base / "artifacts" / "stderr.log", stderr)
    elapsed_seconds = time.time() - started
    redact_secret_in_tree(base, child_env.get("LLM_API_KEY", ""))
    finish_run(
        workspace=base / "workspace",
        artifacts_dir=base / "artifacts",
        task_id=task["id"],
        framework=framework,
        experiment_group=group,
        returncode=returncode,
        timed_out=timed_out,
        elapsed_seconds=elapsed_seconds,
    )
    receipt_path = base / "workspace" / "submission_receipt.json"
    receipt = None
    if receipt_path.exists():
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            receipt = {"status": "invalid_json"}
    result = {
        "group": group,
        "task_id": task["id"],
        "returncode": returncode,
        "timed_out": timed_out,
        "elapsed_seconds": round(elapsed_seconds, 3),
        "submission_status": receipt.get("status") if isinstance(receipt, dict) else "missing",
        "submission_attempt": receipt.get("attempt") if isinstance(receipt, dict) else None,
    }
    write_text(base / "run_result.json", json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


def wait_for_proxy(port: int, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.1)
    raise TimeoutError(f"proxy did not listen on port {port}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--groups", nargs="+", choices=GROUPS, default=list(GROUPS))
    parser.add_argument("--task-id", action="append", default=[])
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=TASK_TIMEOUT_SECONDS)
    parser.add_argument("--resume", action="store_true", help="Rerun only missing or unaccepted tasks and preserve successful runs.")
    parser.add_argument("--force", action="store_true", help="With --resume, archive and rerun every selected task even if accepted.")
    args = parser.parse_args()
    if not os.environ.get("LLM_API_KEY"):
        raise SystemExit("LLM_API_KEY is not present in this process")
    if args.force and not args.resume:
        raise SystemExit("--force requires --resume")
    if args.resume:
        RUN_ROOT.mkdir(parents=True, exist_ok=True)
    else:
        safe_reset()
    subprocess.run([sys.executable, str(DEV / "build_dev_dataset.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(DOMAIN / "build_adapters.py")], cwd=ROOT, check=True)
    tasks = load_tasks(args.task_id)
    baseline_runtime = prepare_baseline_runtime()

    proxy: subprocess.Popen[str] | None = None
    proxy_out = None
    proxy_err = None
    try:
        if any(group.startswith("codex") for group in args.groups):
            proxy_dir = RUN_ROOT / "proxy"
            proxy_dir.mkdir(exist_ok=True)
            proxy_env = os.environ.copy()
            proxy_env.update({
                "CODEX_DEEPSEEK_PROXY_HOST": "0.0.0.0",
                "CODEX_DEEPSEEK_PROXY_PORT": str(PROXY_PORT),
                "CODEX_PROXY_TRACE": str(proxy_dir / "trace.jsonl"),
                "LLM_MODEL_NAME": MODEL_NAME,
            })
            proxy_out = (proxy_dir / "stdout.log").open("w", encoding="utf-8")
            proxy_err = (proxy_dir / "stderr.log").open("w", encoding="utf-8")
            proxy = subprocess.Popen(
                [sys.executable, str(ROOT / "candidates" / "codex" / "deepseek_chat_proxy.py")],
                cwd=ROOT,
                env=proxy_env,
                stdout=proxy_out,
                stderr=proxy_err,
                text=True,
            )
            wait_for_proxy(PROXY_PORT)

        jobs = [(group, task) for task in tasks for group in args.groups]
        if args.resume:
            pending = []
            for group, task in jobs:
                result_path = RUN_ROOT / group / task["id"] / "run_result.json"
                result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else {}
                if not args.force and is_reusable_result(result, args.timeout):
                    continue
                archive_retry_task(group, task["id"])
                pending.append((group, task))
            jobs = pending
        results: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=max(1, min(args.workers, len(jobs) or 1))) as executor:
            future_map = {
                executor.submit(run_one, group, task, baseline_runtime, args.timeout): (group, task["id"])
                for group, task in jobs
            }
            for future in as_completed(future_map):
                result = future.result()
                results.append(result)
                print(json.dumps(result, ensure_ascii=False), flush=True)
    finally:
        if proxy is not None:
            proxy.terminate()
            try:
                proxy.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proxy.kill()
                proxy.wait(timeout=5)
        if proxy_out is not None:
            proxy_out.close()
        if proxy_err is not None:
            proxy_err.close()

    all_results: list[dict[str, Any]] = []
    for group in args.groups:
        for task in tasks:
            result_path = RUN_ROOT / group / task["id"] / "run_result.json"
            if result_path.exists():
                all_results.append(json.loads(result_path.read_text(encoding="utf-8")))
    all_results.sort(key=lambda item: (item["group"], item["task_id"]))
    summary = {
        "groups": args.groups,
        "tasks": [task["id"] for task in tasks],
        "runs": all_results,
    }
    write_text(RUN_ROOT / "run_summary.json", json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    expected = len(args.groups) * len(tasks)
    passed = len(all_results) == expected and all(
        item["submission_status"] == "accepted" and not item["timed_out"] for item in all_results
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
