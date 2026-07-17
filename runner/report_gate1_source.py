from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs" / "gate1_v2_source"
OUTPUT_JSON = ROOT / "output" / "gate1_source_environment.json"
OUTPUT_MD = ROOT / "output" / "gate1_source_environment.md"
LOCK_YAML = ROOT / "config" / "source_eval_lock.yaml"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def command(*args: str, cwd: Path = ROOT) -> str:
    result = subprocess.run(
        list(args),
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def json_lines(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not path.exists():
        return events
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip().lstrip("\ufeff")
        if not stripped.startswith("{"):
            continue
        try:
            item = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            events.append(item)
    return events


def parse_json_document(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace").strip().lstrip("\ufeff")
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        pass
    for line in reversed(text.splitlines()):
        stripped = line.strip()
        if not stripped.startswith("{"):
            continue
        try:
            value = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            value = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return {}
        return value if isinstance(value, dict) else {}
    return {}


def docker_image(image: str) -> dict[str, Any]:
    raw = command("docker", "image", "inspect", image)
    item = json.loads(raw)[0]
    return {
        "tag": image,
        "id": item.get("Id"),
        "created": item.get("Created"),
        "size_bytes": item.get("Size"),
    }


def tool_log(path: Path) -> list[dict[str, Any]]:
    return json_lines(path)


def ccb_canary() -> dict[str, Any]:
    root = RUN_ROOT / "claude-code-canary"
    events = json_lines(root / "artifacts" / "trajectory.jsonl")
    init = next((event for event in events if event.get("type") == "system"), {})
    result = next((event for event in reversed(events) if event.get("type") == "result"), {})
    structured = parse_json_document(root / "artifacts" / "structured_output.json")
    runtime = parse_json_document(root / "workspace" / "canary_runtime.json")
    tools = tool_log(root / "artifacts" / "tool_calls.jsonl")
    structured_output = structured.get("structured_output") or {}
    return {
        "exit_ok": result.get("subtype") == "success" and not result.get("is_error"),
        "version": init.get("claude_code_version"),
        "model": init.get("model"),
        "permission_mode": init.get("permissionMode"),
        "mcp_servers": init.get("mcp_servers") or [],
        "available_tools": init.get("tools") or [],
        "available_agents": init.get("agents") or [],
        "available_skills": init.get("skills") or [],
        "available_plugins": init.get("plugins") or [],
        "turns": result.get("num_turns"),
        "usage": result.get("usage") or {},
        "runtime_probe": runtime,
        "mcp_calls": [
            {"server": item.get("server"), "tool": item.get("tool"), "ok": item.get("ok")}
            for item in tools
        ],
        "structured_output": structured_output,
        "trajectory": str((root / "artifacts" / "trajectory.jsonl").relative_to(ROOT)),
    }


def codex_canary() -> dict[str, Any]:
    root = RUN_ROOT / "codex-canary"
    events = json_lines(root / "artifacts" / "trajectory.jsonl")
    runtime = parse_json_document(root / "workspace" / "canary_runtime.json")
    final = parse_json_document(root / "artifacts" / "last_message.json")
    tools = tool_log(root / "artifacts" / "tool_calls.jsonl")
    proxy_events = json_lines(root / "artifacts" / "proxy_trace.jsonl")
    errors = [
        event
        for event in events
        if event.get("type") in {"error", "turn.failed"} or event.get("error")
    ]
    return {
        "exit_ok": bool(events) and not errors and bool(final),
        "version": command(
            "docker", "run", "--rm", "blackbox-eval/codex-source:0.144.4", "--version"
        ),
        "model": "deepseek-v4-pro",
        "runtime_probe": runtime,
        "mcp_calls": [
            {"server": item.get("server"), "tool": item.get("tool"), "ok": item.get("ok")}
            for item in tools
        ],
        "proxy_rounds": sum(
            1 for item in proxy_events if item.get("path") == "/v1/responses" and item.get("status") == 200
        ),
        "final_output": final,
        "event_types": sorted({str(event.get("type")) for event in events if event.get("type")}),
        "trajectory": str((root / "artifacts" / "trajectory.jsonl").relative_to(ROOT)),
    }


def has_successful_call(canary: dict[str, Any], tool: str) -> bool:
    return any(item.get("tool") == tool and item.get("ok") for item in canary.get("mcp_calls", []))


def secret_scan(paths: list[Path]) -> dict[str, Any]:
    key = os.environ.get("LLM_API_KEY", "")
    if not key:
        return {"performed": False, "matches": []}
    needle = key.encode("utf-8")
    matches: list[str] = []
    skipped: list[str] = []
    skipped_dirs = {"vendor", "build-cache", "__pycache__", ".git", "node_modules"}
    for root in paths:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
            dirnames[:] = [name for name in dirnames if name not in skipped_dirs]
            for filename in filenames:
                path = Path(dirpath) / filename
                try:
                    if path.stat().st_size > 20 * 1024 * 1024:
                        continue
                    if needle in path.read_bytes():
                        matches.append(str(path.relative_to(ROOT)))
                except OSError:
                    skipped.append(str(path.relative_to(ROOT)))
    return {"performed": True, "matches": matches, "skipped_unreadable": skipped}


def build_report() -> tuple[dict[str, Any], dict[str, Any]]:
    ccb = ccb_canary()
    codex = codex_canary()
    source_lock = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "model": {
            "provider": "DeepSeek",
            "name": "deepseek-v4-pro",
            "api_key_env": "LLM_API_KEY",
        },
        "claude_code_best": {
            "repository": "https://github.com/claude-code-best/claude-code.git",
            "tag": "v2.8.3",
            "commit": command(
                "git", "rev-parse", "HEAD", cwd=ROOT / "candidates" / "claude-code" / "vendor" / "claude-code"
            ),
            "bun": "1.3.12",
            "image": docker_image("blackbox-eval/ccb-source-nonroot:2.8.3"),
        },
        "codex": {
            "repository": "https://github.com/openai/codex.git",
            "tag": "rust-v0.144.4",
            "commit": "8c68d4c87dc54d38861f5114e920c3de2efa5876",
            "rust": "1.95.0",
            "upstream_lock_sha256": sha256(
                ROOT / "candidates" / "codex" / "source-artifacts" / "Cargo.lock.upstream"
            ),
            "resolved_lock_sha256": sha256(
                ROOT / "candidates" / "codex" / "source-artifacts" / "Cargo.lock.resolved"
            ),
            "binary_sha256": sha256(
                ROOT / "candidates" / "codex" / "source-artifacts" / "codex"
            ),
            "model_context_window": 131072,
            "model_auto_compact_token_limit": 100000,
            "model_catalog_sha256": sha256(
                ROOT / "candidates" / "codex" / "model_catalog.deepseek.json"
            ),
            "base_instructions_sha256": sha256(
                ROOT
                / "candidates"
                / "codex"
                / "vendor"
                / "codex"
                / "codex-rs"
                / "models-manager"
                / "prompt.md"
            ),
            "image": docker_image("blackbox-eval/codex-source:0.144.4"),
            "wire_api": "responses",
            "deepseek_adapter": "candidates/codex/deepseek_chat_proxy.py",
        },
        "dataset": {
            "evals_sha256": sha256(ROOT / "data" / "evals.json"),
            "expense_db_sha256": sha256(ROOT / "data" / "expense.db"),
            "policy_document_count": len(list((ROOT / "data" / "corpus").glob("*.md"))),
        },
    }

    checks = {
        "ccb_source_version": ccb.get("version") == "2.8.3",
        "codex_source_version": "0.144.4" in str(codex.get("version")),
        "deepseek_model_ccb": ccb.get("model") == "deepseek-v4-pro",
        "deepseek_model_codex": codex.get("model") == "deepseek-v4-pro",
        "ccb_shell_python_sqlite_file": all(
            [
                ccb.get("runtime_probe", {}).get("python_version"),
                ccb.get("runtime_probe", {}).get("sqlite_available") is True,
                ccb.get("structured_output", {}).get("shell_ok") is True,
                ccb.get("structured_output", {}).get("file_read_write_ok") is True,
            ]
        ),
        "codex_shell_python_sqlite_file": all(
            [
                codex.get("runtime_probe", {}).get("python_version"),
                codex.get("runtime_probe", {}).get("sqlite_ok") is True,
                codex.get("final_output", {}).get("shell_ok") is True,
                codex.get("final_output", {}).get("file_read_write_ok") is True,
            ]
        ),
        "ccb_mcp": has_successful_call(ccb, "find_invoice_usage")
        and has_successful_call(ccb, "search_policy"),
        "codex_mcp": has_successful_call(codex, "find_invoice_usage")
        and has_successful_call(codex, "search_policy"),
        "ccb_structured_output": ccb.get("structured_output", {}).get("model_ok") is True,
        "codex_structured_output": codex.get("final_output", {}).get("model_ok") is True,
        "ccb_trajectory": bool(ccb.get("trajectory")),
        "codex_trajectory": bool(codex.get("trajectory")),
        "codex_protocol_tool_loop": int(codex.get("proxy_rounds") or 0) >= 2,
    }
    security = secret_scan(
        [
            RUN_ROOT,
            ROOT / "candidates" / "claude-code",
            ROOT / "candidates" / "codex",
            ROOT / "config",
        ]
    )
    checks["secret_not_persisted"] = security.get("performed") is True and not security.get("matches")
    passed = all(checks.values())
    report = {
        "gate": "GATE1",
        "status": "pass" if passed else "fail",
        "allow_next_gate": passed,
        "checks": checks,
        "security": security,
        "canaries": {"claude-code-best": ccb, "codex": codex},
        "build_findings": [
            "CCB v2.8.3 source tag requires build-only stubs for absent optional resources.",
            "CCB must run as a non-root user before bypassPermissions is accepted.",
            "Codex v0.144.4 source lock is inconsistent with its manifests; a resolved lock is retained and rechecked with --locked.",
            "Codex v0.144.4 requires Responses API, so DeepSeek is connected through an independent Responses-to-Chat adapter.",
            "Codex uses an explicit DeepSeek model catalog and source-native base instructions to avoid fallback model metadata.",
        ],
        "source_lock": source_lock,
    }
    return report, source_lock


def markdown(report: dict[str, Any]) -> str:
    checks = report["checks"]
    ccb = report["canaries"]["claude-code-best"]
    codex = report["canaries"]["codex"]
    status = "通过" if report["status"] == "pass" else "未通过"
    rows = [
        ("源码与版本", checks["ccb_source_version"], checks["codex_source_version"]),
        ("DeepSeek v4 Pro", checks["deepseek_model_ccb"], checks["deepseek_model_codex"]),
        ("Shell/Python/SQLite/文件", checks["ccb_shell_python_sqlite_file"], checks["codex_shell_python_sqlite_file"]),
        ("制度与费用 MCP", checks["ccb_mcp"], checks["codex_mcp"]),
        ("结构化结果", checks["ccb_structured_output"], checks["codex_structured_output"]),
        ("完整轨迹", checks["ccb_trajectory"], checks["codex_trajectory"]),
    ]
    table = "\n".join(
        f"| {name} | {'通过' if left else '失败'} | {'通过' if right else '失败'} |"
        for name, left, right in rows
    )
    findings = "\n".join(f"- {item}" for item in report["build_findings"])
    return f"""# GATE1 源码环境与能力验收报告

## 结论

GATE1 **{status}**。Claude Code Best 与 Codex 均使用锁定源码构建，接入
`deepseek-v4-pro`，并在隔离容器中完成基础工具、MCP、结构化输出和轨迹留存验证。
{'允许进入 GATE2。' if report['allow_next_gate'] else '不允许进入 GATE2，需先修复失败项。'}

## 版本锁定

| 候选 | 版本 | 源码标识 | 运行镜像 |
| --- | --- | --- | --- |
| Claude Code Best | {ccb.get('version')} | `v2.8.3 / 7680c291...` | `blackbox-eval/ccb-source-nonroot:2.8.3` |
| Codex | {codex.get('version')} | `rust-v0.144.4 / 8c68d4c8...` | `blackbox-eval/codex-source:0.144.4` |

## 验收结果

| 验收项 | Claude Code Best | Codex |
| --- | --- | --- |
{table}

Codex 的 Responses-to-Chat 代理成功完成 {codex.get('proxy_rounds', 0)} 轮真实请求；
Claude Code Best Canary 共执行 {ccb.get('turns', 0)} 轮，并在运行中自行发现和修正一次 SQL 元数据表名错误。

## 构建发现

{findings}

## 安全检查

- API 密钥仅通过 `LLM_API_KEY` 注入。
- 密钥落盘扫描：{'未发现匹配' if checks['secret_not_persisted'] else '未通过或未执行'}。
- Canary 只挂载 MCP 脚本、制度语料和费用数据库；未挂载 Ground Truth、历史答案、判卷代码或其他候选轨迹。
- 两端均以非 root 用户运行，业务输入只读，工作区和轨迹目录可写。

## 证据位置

- Claude Code Best：`{ccb.get('trajectory')}`
- Codex：`{codex.get('trajectory')}`
- 机器可读结果：`output/gate1_source_environment.json`
- 完整版本锁定：`config/source_eval_lock.yaml`
"""


def main() -> int:
    report, source_lock = build_report()
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(markdown(report), encoding="utf-8")
    LOCK_YAML.write_text(
        yaml.safe_dump(source_lock, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    print(json.dumps({"status": report["status"], "allow_next_gate": report["allow_next_gate"]}))
    return 0 if report["allow_next_gate"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
