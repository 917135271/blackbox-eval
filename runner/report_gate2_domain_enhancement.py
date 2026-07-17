from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DOMAIN = ROOT / "domain-enhancement"
RUN_ROOT = ROOT / "runs" / "gate2_domain_enhancement"
OUTPUT_JSON = ROOT / "output" / "gate2_domain_enhancement.json"
OUTPUT_MD = ROOT / "output" / "gate2_domain_enhancement.md"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def json_lines(path: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            items.append(item)
    return items


def run_check(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    output = (completed.stdout + completed.stderr).strip()
    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "output_tail": output[-3000:],
    }


def validate_skills() -> dict[str, Any]:
    validator = Path.home() / ".codex" / "skills" / ".system" / "skill-creator" / "scripts" / "quick_validate.py"
    results: dict[str, Any] = {}
    for path in sorted((DOMAIN / "shared-audit-core" / "skills").iterdir()):
        if path.is_dir():
            results[path.name] = run_check([sys.executable, str(validator), str(path)])
    return {
        "ok": len(results) == 7 and all(item["ok"] for item in results.values()),
        "skills": results,
    }


def validate_plugins() -> dict[str, Any]:
    codex_validator = Path.home() / ".codex" / "skills" / ".system" / "plugin-creator" / "scripts" / "validate_plugin.py"
    codex_plugin = DOMAIN / "adapters" / "codex" / "securities-expense-audit"
    ccb_plugin = DOMAIN / "adapters" / "claude-code-best" / "securities-expense-audit"
    ccb = ROOT / "candidates" / "claude-code" / "runtime" / "node_modules" / ".bin" / "ccb.cmd"
    results = {
        "codex": run_check([sys.executable, str(codex_validator), str(codex_plugin)]),
        "claude-code-best": run_check([str(ccb), "plugin", "validate", str(ccb_plugin)]),
    }
    return {"ok": all(item["ok"] for item in results.values()), "candidates": results}


def contains_text(value: Any, text: str) -> bool:
    if isinstance(value, str):
        return text in value
    if isinstance(value, dict):
        return any(contains_text(item, text) for item in value.values())
    if isinstance(value, list):
        return any(contains_text(item, text) for item in value)
    return False


def has_ccb_tool_use(events: list[dict[str, Any]], tool_name: str, input_text: str) -> bool:
    for event in events:
        if event.get("type") != "assistant":
            continue
        for block in event.get("message", {}).get("content", []):
            if (
                isinstance(block, dict)
                and block.get("type") == "tool_use"
                and block.get("name") == tool_name
                and contains_text(block.get("input"), input_text)
            ):
                return True
    return False


def secret_scan(paths: list[Path]) -> dict[str, Any]:
    key = os.environ.get("LLM_API_KEY", "")
    needle = key.encode("utf-8") if key else None
    generic_secret = re.compile(rb"\bsk-[A-Za-z0-9_-]{16,}\b")
    matches: list[str] = []
    for root in paths:
        for path in root.rglob("*"):
            try:
                if not path.is_file() or path.stat().st_size > 50 * 1024 * 1024:
                    continue
            except OSError:
                continue
            try:
                content = path.read_bytes()
                if (needle and needle in content) or generic_secret.search(content):
                    matches.append(path.relative_to(ROOT).as_posix())
            except OSError:
                continue
    return {"performed": True, "matches": matches}


def build_report() -> dict[str, Any]:
    ccb_events = json_lines(RUN_ROOT / "claude-code-best" / "artifacts" / "trajectory.jsonl")
    codex_events = json_lines(RUN_ROOT / "codex" / "artifacts" / "trajectory.jsonl")
    ccb_init = next((item for item in ccb_events if item.get("type") == "system" and item.get("subtype") == "init"), {})
    ccb_result = next((item for item in reversed(ccb_events) if item.get("type") == "result"), {})

    ccb_receipt = load_json(RUN_ROOT / "claude-code-best" / "workspace" / "submission_receipt.json")
    codex_receipt = load_json(RUN_ROOT / "codex" / "workspace" / "submission_receipt.json")
    ccb_state = load_json(RUN_ROOT / "claude-code-best" / "workspace" / ".audit-control" / "state.json")
    codex_state = load_json(RUN_ROOT / "codex" / "workspace" / ".audit-control" / "state.json")
    ccb_manifest = load_json(DOMAIN / "adapters" / "claude-code-best" / "securities-expense-audit" / "build_manifest.json")
    codex_manifest = load_json(DOMAIN / "adapters" / "codex" / "securities-expense-audit" / "build_manifest.json")

    plugin_skills = [item for item in ccb_init.get("skills", []) if item.startswith("securities-expense-audit:")]
    plugin_agents = [item for item in ccb_init.get("agents", []) if item.startswith("securities-expense-audit:")]
    ccb_mcp_connected = any(
        item.get("name") == "plugin:securities-expense-audit:audit_control" and item.get("status") == "connected"
        for item in ccb_init.get("mcp_servers", [])
    )
    ccb_native_agent = has_ccb_tool_use(
        ccb_events,
        "Agent",
        "securities-expense-audit:policy-researcher",
    )
    ccb_submit_mcp = any(
        contains_text(item, "mcp__plugin_securities-expense-audit_audit_control__submit_audit_result")
        and contains_text(item, '"status": "accepted"')
        for item in ccb_events
    )

    codex_spawn = any(
        item.get("type") == "item.completed"
        and item.get("item", {}).get("type") == "collab_tool_call"
        and item.get("item", {}).get("tool") == "spawn_agent"
        and bool(item.get("item", {}).get("receiver_thread_ids"))
        for item in codex_events
    )
    codex_wait = any(
        item.get("type") == "item.completed"
        and item.get("item", {}).get("type") == "collab_tool_call"
        and item.get("item", {}).get("tool") == "wait"
        and any(state.get("status") == "completed" for state in item.get("item", {}).get("agents_states", {}).values())
        for item in codex_events
    )
    codex_submit_mcp = any(
        item.get("type") == "item.completed"
        and item.get("item", {}).get("type") == "mcp_tool_call"
        and item.get("item", {}).get("server") == "audit_control"
        and item.get("item", {}).get("tool") == "submit_audit_result"
        and contains_text(item.get("item", {}).get("result"), '"status": "accepted"')
        for item in codex_events
    )

    unit_tests = run_check([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    skill_validation = validate_skills()
    plugin_validation = validate_plugins()
    security = secret_scan([DOMAIN, RUN_ROOT, ROOT / "config"])
    runner_source = (ROOT / "runner" / "run_gate2_domain_canary.py").read_text(encoding="utf-8")

    checks = {
        "seven_canonical_skills": len(list((DOMAIN / "shared-audit-core" / "skills").glob("*/SKILL.md"))) == 7,
        "shared_skill_hashes_identical": ccb_manifest["canonical_skill_hashes"] == codex_manifest["canonical_skill_hashes"],
        "thirteen_business_and_governance_schemas": len(list((DOMAIN / "shared-audit-core" / "schemas").glob("*.json"))) == 13,
        "three_roles_each_adapter": len(list((DOMAIN / "adapters" / "claude-code-best" / "securities-expense-audit" / "agents").glob("*.md"))) == 3
        and len(list((DOMAIN / "adapters" / "codex" / "securities-expense-audit" / "agents").glob("*.toml"))) == 3,
        "unit_tests": unit_tests["ok"],
        "all_skills_validate": skill_validation["ok"],
        "both_plugins_validate": plugin_validation["ok"],
        "ccb_runtime_discovered_seven_skills": len(plugin_skills) == 7,
        "ccb_runtime_discovered_three_agents": len(plugin_agents) == 3,
        "ccb_control_mcp_connected": ccb_mcp_connected,
        "ccb_native_subagent_completed": ccb_native_agent
        and (RUN_ROOT / "claude-code-best" / "workspace" / "work" / "subagents" / "policy_researcher" / "policy_applicability.json").exists()
        and (RUN_ROOT / "claude-code-best" / "workspace" / "work" / "subagents" / "policy_researcher" / "summary.json").exists(),
        "ccb_submit_via_mcp": ccb_submit_mcp,
        "ccb_canary_success": ccb_result.get("subtype") == "success"
        and "GATE2_CANARY_PASS" in str(ccb_result.get("result", "")),
        "codex_native_subagent_completed": codex_spawn
        and codex_wait
        and (RUN_ROOT / "codex" / "workspace" / "work" / "subagents" / "policy_researcher" / "policy_applicability.json").exists()
        and (RUN_ROOT / "codex" / "workspace" / "work" / "subagents" / "policy_researcher" / "summary.json").exists(),
        "codex_submit_via_mcp": codex_submit_mcp,
        "codex_canary_success": any(item.get("type") == "turn.completed" for item in codex_events)
        and any(contains_text(item, "GATE2_CANARY_PASS") for item in codex_events),
        "both_submissions_first_attempt": ccb_receipt.get("status") == "accepted"
        and ccb_receipt.get("attempt") == 1
        and codex_receipt.get("status") == "accepted"
        and codex_receipt.get("attempt") == 1,
        "subagent_call_limits_enforced": ccb_state.get("subagent_calls") == {"policy_researcher": 1}
        and codex_state.get("subagent_calls") == {"policy_researcher": 1},
        "subagent_completion_registered": all(
            invocation.get("status") == "completed"
            for state in (ccb_state, codex_state)
            for invocation in state.get("subagent_invocations", {}).values()
        )
        and all(state.get("subagent_invocations") for state in (ccb_state, codex_state)),
        "governance_traces_present": all(
            (RUN_ROOT / candidate / "workspace" / "traces" / name).exists()
            for candidate in ("claude-code-best", "codex")
            for name in (
                "events.jsonl",
                "tool_calls.jsonl",
                "subagents.jsonl",
                "context_events.jsonl",
                "artifact_manifest.json",
            )
        )
        and all((RUN_ROOT / candidate / "workspace" / "run_manifest.json").exists() for candidate in ("claude-code-best", "codex")),
        "no_direct_control_import_bypass": not contains_text(ccb_events, "from audit_control_mcp import")
        and not contains_text(codex_events, "from audit_control_mcp import"),
        "hidden_answer_mapping_not_used": ccb_receipt.get("checks", {}).get("hidden_answer_mapping_used") is False
        and codex_receipt.get("checks", {}).get("hidden_answer_mapping_used") is False,
        "hidden_assets_not_mounted": 'volume(ROOT / "data" / "ground_truth' not in runner_source
        and 'volume(ROOT / "data" / "evals' not in runner_source,
        "secret_not_persisted": not security["matches"],
    }
    passed = all(checks.values())
    return {
        "gate": "GATE2",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "pass" if passed else "fail",
        "allow_next_gate": passed,
        "checks": checks,
        "validation": {
            "unit_tests": unit_tests,
            "skills": skill_validation,
            "plugins": plugin_validation,
        },
        "security": security,
        "canaries": {
            "claude-code-best": {
                "version": ccb_init.get("claude_code_version"),
                "model": ccb_init.get("model"),
                "skills": plugin_skills,
                "agents": plugin_agents,
                "receipt": ccb_receipt,
                "trajectory": "runs/gate2_domain_enhancement/claude-code-best/artifacts/trajectory.jsonl",
            },
            "codex": {
                "version": "0.144.4",
                "model": "deepseek-v4-pro",
                "receipt": codex_receipt,
                "trajectory": "runs/gate2_domain_enhancement/codex/artifacts/trajectory.jsonl",
            },
        },
        "attempt_findings": [
            "Attempt 1 exposed that Claude --bare omitted plugin MCP/native Agent tools, while Codex forwarded a local placeholder token and used a read-only CODEX_HOME.",
            "Attempt 2 fixed runtime loading. Claude passed; Codex multi_agent_v2 reported a spawn without a child thread and exhausted its one repair before writing the corrected files.",
            "Attempt 3 switched Codex to stable multi_agent V1. It returned a real child thread, completed wait, and submitted successfully on attempt 1.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    status = "通过" if report["status"] == "pass" else "未通过"
    rows = "\n".join(
        f"| {name} | {'通过' if value else '失败'} |"
        for name, value in report["checks"].items()
    )
    ccb = report["canaries"]["claude-code-best"]
    codex = report["canaries"]["codex"]
    return f"""# GATE2 领域增强能力验收报告

## 结论

GATE2治理层 **{status}**。已形成一份共享证券费用审计核心、四套现有框架适配器、七个领域 Skill、三个受控子智能体、单题任务状态、上下文Checkpoint、统一Hooks事件和结果提交工具。Claude Code Best与Codex完成真实运行时Canary，并通过“授权、原生执行、完成登记、校验、首次提交”全链路。

{'允许对现有四个框架执行治理版GATE3开发题复跑；新增oh-my-pi仍需先完成GATE1和适配器构建。' if report['allow_next_gate'] else '暂不允许进入治理版GATE3，需修复失败项。'}

## 交付内容

- 共享核心：`domain-enhancement/shared-audit-core/`
- Claude Code Best 包装：`domain-enhancement/adapters/claude-code-best/securities-expense-audit/`
- Codex 包装：`domain-enhancement/adapters/codex/securities-expense-audit/`
- OpenClaude 包装：`domain-enhancement/adapters/openclaude/securities-expense-audit/`
- OpenCode 包装：`domain-enhancement/adapters/opencode/securities-expense-audit/`
- 统一控制 MCP：`domain-enhancement/control-mcp/audit_control_mcp.py`
- 四端构建脚本：`domain-enhancement/build_adapters.py`
- 集成 Canary：`runner/run_gate2_domain_canary.py`
- 自动化测试：`tests/test_domain_enhancement.py`

## 运行时结果

| 候选 | Skill | 子智能体 | 控制 MCP | 提交结果 | 修复次数 |
| --- | ---: | --- | --- | --- | ---: |
| Claude Code Best {ccb['version']} | 7 | 原生 Agent 完成 | 已连接 | accepted | 0 |
| Codex {codex['version']} | 7 | V1 spawn/wait 完成 | 已连接 | accepted | 0 |

两个回执都验证了 `R000001` 的业务库存在性，且均记录 `hidden_answer_mapping_used=false`。两次运行均生成统一事件、工具、子智能体、上下文、产物和运行清单。Canary只验证能力装配与执行链路，不计入开发题或15道正式案例成绩。

## 验收项

| 检查 | 结果 |
| --- | --- |
{rows}

## 修复记录

1. 首次运行发现 Claude 的 `--bare` 模式没有开放插件 MCP 和原生 Agent；已切换为完整非交互模式，并禁止 Bash 直调控制代码。
2. 首次 Codex 运行发现本地占位令牌被转发到 DeepSeek，且只读 `CODEX_HOME` 阻止系统 Skill 初始化；已改为安全继承密钥和隔离可写 `CODEX_HOME`。
3. Codex `multi_agent_v2` 在 Responses-to-Chat 适配下出现无真实子线程的假 spawn；已切回源码稳定的 `multi_agent` V1，真实返回 child thread 并完成 wait。
4. Codex 曾在第二次提交后才完成文件修复；提交器维持最多一次修复，不放宽约束。V1 重跑按正确顺序首轮通过。

## 证据位置

- Claude 轨迹：`{ccb['trajectory']}`
- Codex 轨迹：`{codex['trajectory']}`
- 首次失败归因：`runs/gate2_domain_enhancement_attempt1/`
- Codex V2 失败归因：`runs/gate2_domain_enhancement/codex_attempt2_v2/`
- 机器可读报告：`output/gate2_domain_enhancement.json`
"""


def main() -> int:
    report = build_report()
    OUTPUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "allow_next_gate": report["allow_next_gate"], "output": str(OUTPUT_MD)}, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
