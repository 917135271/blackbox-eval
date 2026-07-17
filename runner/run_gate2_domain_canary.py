from __future__ import annotations

import json
import argparse
import os
import shutil
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_trace import finish_run, start_run  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
DOMAIN = ROOT / "domain-enhancement"
RUN_ROOT = ROOT / "runs" / "gate2_domain_enhancement"
CCB_PLUGIN = DOMAIN / "adapters" / "claude-code-best" / "securities-expense-audit"
CODEX_PLUGIN = DOMAIN / "adapters" / "codex" / "securities-expense-audit"
OH_MY_PI_PLUGIN = DOMAIN / "adapters" / "oh-my-pi" / "securities-expense-audit"
PROXY_PORT = 18789


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safe_reset_run_root() -> None:
    target = RUN_ROOT.resolve()
    expected_parent = (ROOT / "runs").resolve()
    if target.parent != expected_parent or target.name != "gate2_domain_enhancement":
        raise ValueError(f"refusing to reset unexpected path: {target}")
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)


def safe_reset_candidate(name: str) -> None:
    if name not in {"claude-code-best", "codex", "oh-my-pi"}:
        raise ValueError(f"unknown candidate: {name}")
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    target = (RUN_ROOT / name).resolve()
    if target.parent != RUN_ROOT.resolve() or target.name != name:
        raise ValueError(f"refusing to reset unexpected candidate path: {target}")
    if target.exists():
        shutil.rmtree(target)


def volume(path: Path, container_path: str, read_only: bool = True) -> list[str]:
    suffix = ":ro" if read_only else ""
    return ["-v", f"{path.resolve()}:{container_path}{suffix}"]


def canary_prompt(framework: str, native_role: str) -> str:
    native_instruction = (
        "Oh My Pi 必须使用原生 task 工具调用 policy-researcher 角色并等待任务完成；"
        if framework == "Oh My Pi"
        else ""
    )
    return f"""你正在执行 GATE2 领域增强集成 Canary，不是正式评测题。框架为 {framework}。

必须完成以下步骤，不得省略：
1. 明确遵循 audit-query-planner Skill，在 work/audit_plan.json 写入一个复杂度为3的集成计划，理由包括多制度版本核查；不要作业务异常判断。
2. 调用 checkpoint_audit_context 记录 planning_completed Checkpoint。retained_state必须包含task、constraints、audit_plan、applicable_policies、record_ids、evidence_status、unresolved_items、artifact_index、remaining_budget和submission_status，可使用当前Canary的精简值。然后直接调用 audit_control MCP 的 authorize_audit_subagent，role=policy_researcher，reason_code=MULTI_POLICY_VERSION_CHECK，complexity=3，context 只包含本 Canary 目标，token budget=4000。严禁通过 Bash、Python import 或读取控制代码绕过 MCP 工具；如果工具不可见，本 Canary 必须失败。
3. 授权成功后，保存返回的 invocation_id，并用框架原生子智能体机制调用角色 {native_role}。Codex 必须使用稳定 V1 的 spawn_agent 并用 wait_agent 等待明确的 agent id；Claude Code Best 必须使用 Agent 工具。{native_instruction}严禁由主智能体模拟子智能体。要求子智能体用 policy_query 读取 01_expense_reimbursement_2025.md 的第十条，将详细结果和六字段摘要分别保存到 work/subagents/policy_researcher/policy_applicability.json 与 work/subagents/policy_researcher/summary.json。等待子智能体完成，不得派生更多子智能体。
4. 调用 complete_audit_subagent，传入 invocation_id、summary_path 和产物路径，必须取得 completed=true。主智能体只能使用该工具返回的结构化摘要。
5. 主智能体调用 expense_query.get_expense_detail 验证 R000001 存在。
6. 为了只验证提交链路，创建以下中间文件：
   - work/evidence_matrix.json：status=pass，coverage_percent=100，evidence_rows=[]，candidate_record_ids 和 submitted_record_ids 均为 [R000001]，unowned_record_ids、unused_candidate_record_ids、unused_citations、missing_evidence、unresolved_items 均为空数组，no_anomaly_coverage 至少包含 complete=true，reconciled_figures 为空对象。
   - work/validation_report.json：status=pass，errors 和 warnings 为空数组，field_checks、id_checks、evidence_checks、answer_consistency_checks 均为包含 status=pass 的对象，repair_count=0，repairable_fields=[]，submission_allowed=true。
   - work/final_result.json：anomaly_ids=[]，record_ids=[R000001]，answer=GATE2集成检查完成，记录R000001已通过只读业务库验证。，citations=[]。
7. 调用 checkpoint_audit_context 记录 validation_ready Checkpoint。调用 result-validator Skill 的规则复核这些文件，然后直接调用 audit_control MCP 的 submit_audit_result。严禁通过 Bash或Python import 直调控制代码。必须取得 status=accepted；失败时按结构化错误只修复一次。
8. 最终只简短报告 GATE2_CANARY_PASS 或 GATE2_CANARY_FAIL，不要把最终 JSON 当作提交方式打印出来。

禁止读取 ground_truth.yaml、evals.json、判卷代码、历史答案、其他候选轨迹或其他任务工作区。"""


def prepare_workspaces(candidates: list[str]) -> None:
    workflow = (DOMAIN / "shared-audit-core" / "references" / "main_workflow.md").read_text(encoding="utf-8")
    for name in candidates:
        base = RUN_ROOT / name
        (base / "workspace").mkdir(parents=True)
        (base / "artifacts").mkdir(parents=True)
        write_text(base / "workspace" / "AGENTS.md", workflow)
        write_text(base / "workspace" / "CLAUDE.md", workflow)

    if "claude-code-best" in candidates:
        ccb_config = RUN_ROOT / "claude-code-best" / "config"
        ccb_config.mkdir(parents=True)
        shutil.copy2(ROOT / "candidates" / "claude-code" / "settings.json", ccb_config / "settings.json")
        shutil.copy2(ROOT / "candidates" / "claude-code" / "mcp_config.container.json", ccb_config / "mcp.json")

    if "oh-my-pi" in candidates:
        from run_gate3_development import oh_my_pi_mcp_config, oh_my_pi_models_config

        omp_home = RUN_ROOT / "oh-my-pi" / "omp-home"
        omp_home.mkdir(parents=True)
        write_text(omp_home / "models.yml", oh_my_pi_models_config())
        omp_dir = RUN_ROOT / "oh-my-pi" / "workspace" / ".omp"
        omp_dir.mkdir()
        write_text(
            omp_dir / "mcp.json",
            json.dumps(oh_my_pi_mcp_config("gate2-oh-my-pi-canary", True), ensure_ascii=False, indent=2) + "\n",
        )
        shutil.copytree(OH_MY_PI_PLUGIN / "skills", omp_dir / "skills")
        shutil.copytree(OH_MY_PI_PLUGIN / ".omp" / "agents", omp_dir / "agents")
        shutil.copytree(OH_MY_PI_PLUGIN / ".omp" / "extensions", omp_dir / "extensions")

    if "codex" not in candidates:
        return

    codex_home = RUN_ROOT / "codex" / "codex-home"
    shutil.copytree(CODEX_PLUGIN / "skills", codex_home / "skills")
    shutil.copytree(CODEX_PLUGIN / "agents", codex_home / "agents")

    codex_config = f'''model = "deepseek-v4-pro"
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
multi_agent = true
multi_agent_v2 = false

[model_providers.deepseek]
name = "DeepSeek via Responses adapter"
base_url = "http://host.docker.internal:{PROXY_PORT}/v1"
env_key = "LLM_API_KEY"
wire_api = "responses"

[agents.policy_researcher]
description = "Resolve applicable policy versions, dates, conflicts, exceptions, and clauses."
config_file = "/home/codex/.codex/agents/policy_researcher.toml"
nickname_candidates = ["PolicyResearcher"]

[agents.data_analyst]
description = "Execute complete read-only SQLite and Python expense analysis."
config_file = "/home/codex/.codex/agents/data_analyst.toml"
nickname_candidates = ["DataAnalyst"]

[agents.independent_reviewer]
description = "Challenge findings for exceptions, boundaries, omissions, and false positives."
config_file = "/home/codex/.codex/agents/independent_reviewer.toml"
nickname_candidates = ["IndependentReviewer"]

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
args = ["/plugin/shared/control-mcp/audit_control_mcp.py"]
startup_timeout_sec = 30
tool_timeout_sec = 120

[mcp_servers.audit_control.env]
AUDIT_TASK_ID = "gate2-codex-canary"
AUDIT_WORK_DIR = "/workspace"
EVAL_EXPENSE_DB = "/benchmark/data/expense.db"
EVAL_POLICY_CORPUS_DIR = "/benchmark/data/corpus"
PYTHONIOENCODING = "utf-8"
'''
    write_text(codex_home / "config.toml", codex_config)


def common_volumes(plugin: Path, workspace: Path, artifacts: Path) -> list[str]:
    args: list[str] = []
    args += volume(ROOT / "fixtures", "/benchmark/fixtures")
    args += volume(ROOT / "data" / "expense.db", "/benchmark/data/expense.db")
    args += volume(ROOT / "data" / "corpus", "/benchmark/data/corpus")
    args += volume(plugin, "/plugin")
    args += volume(workspace, "/workspace", read_only=False)
    args += volume(artifacts, "/artifacts", read_only=False)
    return args


def run_process(name: str, command: list[str], env: dict[str, str], timeout: int = 900) -> dict[str, Any]:
    framework = {
        "claude-code-best": "claude-code-best",
        "codex": "codex",
        "oh-my-pi": "oh-my-pi",
    }[name]
    task_id = {
        "claude-code-best": "gate2-ccb-canary",
        "codex": "gate2-codex-canary",
        "oh-my-pi": "gate2-oh-my-pi-canary",
    }[name]
    base = RUN_ROOT / name
    start_run(
        workspace=base / "workspace",
        task_id=task_id,
        framework=framework,
        experiment_group=f"{name}-enhanced-governance-canary",
        model="deepseek-v4-pro",
        timeout_seconds=timeout,
    )
    started = time.time()
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        result = {
            "name": name,
            "returncode": completed.returncode,
            "elapsed_seconds": round(time.time() - started, 3),
            "timed_out": False,
        }
        artifacts = base / "artifacts"
        write_text(artifacts / "trajectory.jsonl", completed.stdout)
        write_text(artifacts / "stderr.log", completed.stderr)
        finish_run(
            workspace=base / "workspace",
            artifacts_dir=artifacts,
            task_id=task_id,
            framework=framework,
            experiment_group=f"{name}-enhanced-governance-canary",
            returncode=completed.returncode,
            timed_out=False,
            elapsed_seconds=result["elapsed_seconds"],
        )
        return result
    except subprocess.TimeoutExpired as exc:
        artifacts = base / "artifacts"
        stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        write_text(artifacts / "trajectory.jsonl", stdout)
        write_text(artifacts / "stderr.log", stderr)
        result = {
            "name": name,
            "returncode": None,
            "elapsed_seconds": round(time.time() - started, 3),
            "timed_out": True,
        }
        finish_run(
            workspace=base / "workspace",
            artifacts_dir=artifacts,
            task_id=task_id,
            framework=framework,
            experiment_group=f"{name}-enhanced-governance-canary",
            returncode=None,
            timed_out=True,
            elapsed_seconds=result["elapsed_seconds"],
        )
        return result


def ccb_command(env: dict[str, str]) -> tuple[list[str], dict[str, str]]:
    base = RUN_ROOT / "claude-code-best"
    config = base / "config"
    command = ["docker", "run", "--rm", "--name", "gate2-ccb-canary"]
    command += [
        "-e", "OPENAI_API_KEY",
        "-e", "CLAUDE_CODE_USE_OPENAI=1",
        "-e", "OPENAI_BASE_URL=https://api.deepseek.com",
        "-e", "OPENAI_MODEL=deepseek-v4-pro",
        "-e", "ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-v4-pro",
        "-e", "ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-v4-pro",
        "-e", "ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-v4-pro",
        "-e", "AUDIT_TASK_ID=gate2-ccb-canary",
        "-e", "AUDIT_WORK_DIR=/workspace",
        "-e", "AUDIT_FRAMEWORK=claude-code-best",
        "-e", "AUDIT_EXPERIMENT_GROUP=claude-code-best-enhanced-governance-canary",
        "-e", "EVAL_EXPENSE_DB=/benchmark/data/expense.db",
        "-e", "EVAL_POLICY_CORPUS_DIR=/benchmark/data/corpus",
        "-e", "EVAL_TASK_LOG=/artifacts/tool_calls.jsonl",
    ]
    command += common_volumes(CCB_PLUGIN, base / "workspace", base / "artifacts")
    command += volume(config / "settings.json", "/config/settings.json")
    command += volume(config / "mcp.json", "/config/mcp.json")
    command += [
        "-w", "/workspace",
        "blackbox-eval/ccb-source-nonroot:2.8.3",
        "--print",
        "--plugin-dir", "/plugin",
        "--settings", "/config/settings.json",
        "--mcp-config", "/config/mcp.json",
        "--dangerously-skip-permissions",
        "--output-format", "stream-json",
        "--verbose",
        "--debug-file", "/artifacts/debug.log",
        "--no-session-persistence",
        "--effort", "high",
        canary_prompt("Claude Code Best", "securities-expense-audit:policy-researcher"),
    ]
    child_env = env.copy()
    child_env["OPENAI_API_KEY"] = env["LLM_API_KEY"]
    return command, child_env


def codex_command(env: dict[str, str]) -> tuple[list[str], dict[str, str]]:
    base = RUN_ROOT / "codex"
    command = ["docker", "run", "--rm", "--name", "gate2-codex-canary"]
    command += [
        "-e", "LLM_API_KEY",
        "-e", "CODEX_HOME=/home/codex/.codex",
        "-e", "NO_PROXY=host.docker.internal,localhost,127.0.0.1",
        "-e", "no_proxy=host.docker.internal,localhost,127.0.0.1",
        "-e", "AUDIT_PLUGIN_ROOT=/plugin",
        "-e", "AUDIT_TASK_ID=gate2-codex-canary",
        "-e", "AUDIT_WORK_DIR=/workspace",
        "-e", "AUDIT_FRAMEWORK=codex",
        "-e", "AUDIT_EXPERIMENT_GROUP=codex-enhanced-governance-canary",
        "-e", "EVAL_EXPENSE_DB=/benchmark/data/expense.db",
        "-e", "EVAL_POLICY_CORPUS_DIR=/benchmark/data/corpus",
    ]
    command += common_volumes(CODEX_PLUGIN, base / "workspace", base / "artifacts")
    command += volume(base / "codex-home", "/home/codex/.codex", read_only=False)
    command += [
        "-w", "/workspace",
        "blackbox-eval/codex-source:0.144.4",
        "exec",
        "--json",
        "--strict-config",
        "--skip-git-repo-check",
        "--ephemeral",
        "--dangerously-bypass-approvals-and-sandbox",
        "-C", "/workspace",
        "-o", "/artifacts/last_message.txt",
        canary_prompt("Codex", "policy_researcher"),
    ]
    return command, env.copy()


def oh_my_pi_command(env: dict[str, str]) -> tuple[list[str], dict[str, str]]:
    base = RUN_ROOT / "oh-my-pi"
    command = ["docker", "run", "--rm", "--name", "gate2-oh-my-pi-canary"]
    command += [
        "-e", "LLM_API_KEY",
        "-e", "PI_CODING_AGENT_DIR=/omp-home",
        "-e", "OMP_MCP_TIMEOUT_MS=120000",
        "-e", "PI_NO_PTY=1",
        "-e", "AUDIT_TASK_ID=gate2-oh-my-pi-canary",
        "-e", "AUDIT_WORK_DIR=/workspace",
        "-e", "AUDIT_SUBAGENTS_ENABLED=1",
        "-e", "AUDIT_FRAMEWORK=oh-my-pi",
        "-e", "AUDIT_EXPERIMENT_GROUP=oh-my-pi-enhanced-governance-canary",
        "-e", "EVAL_EXPENSE_DB=/benchmark/data/expense.db",
        "-e", "EVAL_POLICY_CORPUS_DIR=/benchmark/data/corpus",
    ]
    command += common_volumes(OH_MY_PI_PLUGIN, base / "workspace", base / "artifacts")
    command += volume(base / "omp-home", "/omp-home", read_only=False)
    command += [
        "-w", "/workspace",
        "blackbox-eval/oh-my-pi-source:17.0.1",
        "--print",
        "--mode", "json",
        "--no-session",
        "--no-title",
        "--provider", "deepseek",
        "--model", "deepseek-v4-pro",
        "--thinking", "high",
        "--approval-mode", "yolo",
        "--max-time", "900",
        "--tools", "read,bash,edit,eval,glob,grep,lsp,checkpoint,todo,write,task,hub",
        "--cwd", "/workspace",
        canary_prompt("Oh My Pi", "policy-researcher"),
    ]
    return command, env.copy()


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
    parser.add_argument(
        "--candidate",
        choices=("all", "claude-code-best", "codex", "oh-my-pi"),
        default="all",
    )
    args = parser.parse_args()
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        raise SystemExit("LLM_API_KEY is not present in this process")
    candidates = ["claude-code-best", "codex", "oh-my-pi"] if args.candidate == "all" else [args.candidate]
    if args.candidate == "all":
        safe_reset_run_root()
    else:
        safe_reset_candidate(args.candidate)
    subprocess.run([sys.executable, str(DOMAIN / "build_adapters.py")], cwd=ROOT, check=True)
    prepare_workspaces(candidates)

    proxy: subprocess.Popen[str] | None = None
    proxy_out = None
    proxy_err = None
    try:
        if "codex" in candidates:
            proxy_env = os.environ.copy()
            proxy_env.update(
                {
                    "CODEX_DEEPSEEK_PROXY_HOST": "0.0.0.0",
                    "CODEX_DEEPSEEK_PROXY_PORT": str(PROXY_PORT),
                    "CODEX_PROXY_TRACE": str(RUN_ROOT / "codex" / "artifacts" / "proxy_trace.jsonl"),
                    "LLM_MODEL_NAME": "deepseek-v4-pro",
                }
            )
            proxy_out = (RUN_ROOT / "codex" / "artifacts" / "proxy_stdout.log").open("w", encoding="utf-8")
            proxy_err = (RUN_ROOT / "codex" / "artifacts" / "proxy_stderr.log").open("w", encoding="utf-8")
            proxy = subprocess.Popen(
                [sys.executable, str(ROOT / "candidates" / "codex" / "deepseek_chat_proxy.py")],
                cwd=ROOT,
                env=proxy_env,
                stdout=proxy_out,
                stderr=proxy_err,
                text=True,
            )
            wait_for_proxy(PROXY_PORT)

        command_args = {
            "claude-code-best": ccb_command,
            "codex": codex_command,
            "oh-my-pi": oh_my_pi_command,
        }
        with ThreadPoolExecutor(max_workers=len(candidates)) as executor:
            futures = [
                executor.submit(run_process, name, *command_args[name](os.environ.copy()))
                for name in candidates
            ]
            results = [future.result() for future in futures]
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

    summary_name = "run_summary.json" if args.candidate == "all" else f"run_summary_{args.candidate}.json"
    write_text(RUN_ROOT / summary_name, json.dumps({"runs": results}, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"run_root": str(RUN_ROOT), "runs": results}, ensure_ascii=False, indent=2))
    return 0 if all(item["returncode"] == 0 and not item["timed_out"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
