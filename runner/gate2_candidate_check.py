from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"
RUNS_DIR = ROOT / "runs" / "gate2"
CONFIG_PATH = ROOT / "config" / "eval_config.yaml"

CANARY_INVOICE_NO = "FP202500000001"
CANARY_EXPECTED_RECORD_ID = "R000001"
AUDIT_EVAL_SYSTEM_PROMPT = (
    "You are an audit QA agent for a blackbox benchmark, not a coding assistant. "
    "The user prompt is the complete task. Do not inspect project files, ask for "
    "more details, or describe setup. Use only the connected policy_query and "
    "expense_query MCP tools for facts. Never use shell, file, web, question, "
    "task, or code-editing tools. Your final response must contain exactly one "
    "fenced json code block and no other text. The JSON object must have keys "
    "anomaly_ids, answer, and citations. citations must be an array of objects "
    "only, never strings; each citation object must contain doc_id and clause_no. "
    "Do not put ASCII double quote characters inside the answer value; do not "
    "quote role names or policy names inside answer."
)


@dataclass(frozen=True)
class Candidate:
    name: str
    version: str
    command: list[str]
    workdir: Path
    setup_file: Path
    config_files: list[Path]


def load_eval_config() -> dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def enabled_candidate_names(config: dict[str, Any]) -> list[str]:
    raw = config.get("candidates") or []
    if isinstance(raw, dict):
        return [name for name, item in raw.items() if item.get("enabled")]
    return [item["name"] for item in raw if item.get("enabled")]


def candidate_registry() -> dict[str, Candidate]:
    goose_exe = (
        ROOT
        / "candidates"
        / "goose"
        / "install"
        / "v1.41.0"
        / "extracted"
        / "goose-package"
        / "goose.exe"
    )
    trae_root = ROOT / "candidates" / "trae-agent" / "vendor" / "trae-agent"
    return {
        "qwen-code": Candidate(
            name="qwen-code",
            version="0.19.6",
            command=["qwen"],
            workdir=ROOT / "candidates" / "qwen-code" / "workdir",
            setup_file=ROOT / "candidates" / "qwen-code" / "setup.md",
            config_files=[
                ROOT / "candidates" / "qwen-code" / "workdir" / ".qwen" / "settings.json"
            ],
        ),
        "goose": Candidate(
            name="goose",
            version="1.41.0",
            command=[str(goose_exe)],
            workdir=ROOT / "candidates" / "goose" / "workdir",
            setup_file=ROOT / "candidates" / "goose" / "setup.md",
            config_files=[],
        ),
        "trae-agent": Candidate(
            name="trae-agent",
            version="0.1.0",
            command=[str(trae_root / ".venv" / "Scripts" / "trae-cli.exe")],
            workdir=ROOT / "candidates" / "trae-agent" / "workdir",
            setup_file=ROOT / "candidates" / "trae-agent" / "setup.md",
            config_files=[ROOT / "candidates" / "trae-agent" / "config" / "trae_config.yaml"],
        ),
        "opencode": Candidate(
            name="opencode",
            version="1.17.14",
            command=["opencode"],
            workdir=ROOT / "candidates" / "opencode" / "workdir",
            setup_file=ROOT / "candidates" / "opencode" / "setup.md",
            config_files=[ROOT / "candidates" / "opencode" / "workdir" / "opencode.json"],
        ),
    }


def run_command(
    args: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int = 60,
) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    resolved_args = list(args)
    resolved_exe = shutil.which(resolved_args[0])
    if resolved_exe:
        resolved_args[0] = resolved_exe
    return subprocess.run(
        resolved_args,
        cwd=str(cwd),
        env=merged_env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
    )


def redact(text: str | None) -> str:
    if text is None:
        return ""
    key = os.environ.get("LLM_API_KEY")
    if key:
        text = text.replace(key, "<redacted>")
    return text


def check_no_secrets(paths: list[Path]) -> tuple[bool, list[str]]:
    bad: list[str] = []
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if "sk-" in text:
            bad.append(str(path.relative_to(ROOT)))
    return (len(bad) == 0, bad)


def command_exists(candidate: Candidate) -> tuple[bool, str]:
    if len(candidate.command) == 1:
        found = shutil.which(candidate.command[0])
        return bool(found), found or "missing"
    command_path = Path(candidate.command[0])
    return command_path.exists(), str(command_path)


def setup_checks(candidates: list[Candidate]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for candidate in candidates:
        item: dict[str, Any] = {
            "candidate": candidate.name,
            "expected_version": candidate.version,
            "setup_file": str(candidate.setup_file.relative_to(ROOT)),
            "workdir": str(candidate.workdir.relative_to(ROOT)),
            "checks": [],
        }

        exists_ok, exists_detail = command_exists(candidate)
        item["checks"].append(
            {"name": "command_exists", "ok": exists_ok, "detail": exists_detail}
        )

        item["checks"].append(
            {
                "name": "setup_md_exists",
                "ok": candidate.setup_file.exists(),
                "detail": str(candidate.setup_file.relative_to(ROOT)),
            }
        )

        missing_configs = [str(p.relative_to(ROOT)) for p in candidate.config_files if not p.exists()]
        item["checks"].append(
            {
                "name": "config_files_exist",
                "ok": not missing_configs,
                "detail": ", ".join(missing_configs) if missing_configs else "ok",
            }
        )

        no_secret_ok, secret_files = check_no_secrets([candidate.setup_file, *candidate.config_files])
        item["checks"].append(
            {
                "name": "no_inline_secret",
                "ok": no_secret_ok,
                "detail": ", ".join(secret_files) if secret_files else "ok",
            }
        )

        cp = run_command([*candidate.command, "--version"], cwd=ROOT, timeout=30)
        version_text = redact((cp.stdout + cp.stderr).strip())
        item["checks"].append(
            {
                "name": "version_check",
                "ok": cp.returncode == 0 and candidate.version in version_text,
                "detail": version_text,
            }
        )

        if candidate.name == "trae-agent":
            repo = ROOT / "candidates" / "trae-agent" / "vendor" / "trae-agent"
            cp_git = run_command(["git", "rev-parse", "HEAD"], cwd=repo, timeout=30)
            head = cp_git.stdout.strip()
            item["checks"].append(
                {
                    "name": "pinned_commit",
                    "ok": head == "e839e559ac61bdd0e057c375dd1dee391fee797d",
                    "detail": head,
                }
            )

        results.append(item)
    return results


def base_env(model_config: dict[str, Any]) -> dict[str, str]:
    api_env = model_config.get("api_key_env", "LLM_API_KEY")
    api_key = os.environ.get(api_env, "")
    env = {
        "NO_COLOR": "1",
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
        "QWEN_CODE_DISABLE_TELEMETRY": "1",
        "OPENCODE_DISABLE_TELEMETRY": "1",
        "LLM_API_KEY": api_key,
        "OPENAI_API_KEY": api_key,
        "OPENROUTER_API_KEY": api_key,
        "OPENAI_BASE_URL": model_config["base_url"],
        "OPENAI_HOST": model_config["base_url"],
        "GOOSE_PROVIDER": "openai",
        "GOOSE_MODEL": model_config["model"],
    }
    return {k: v for k, v in env.items() if v}


def snapshot_dir(path: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    if not path.exists():
        return snapshot
    for file_path in sorted(p for p in path.rglob("*") if p.is_file()):
        rel = file_path.relative_to(path).as_posix()
        snapshot[rel] = hashlib.sha256(file_path.read_bytes()).hexdigest()
    return snapshot


def canary_prompts(probe_dir: Path) -> dict[str, str]:
    bash_file = probe_dir / "bash_ran.txt"
    write_file = probe_dir / "should_not_exist.txt"
    return {
        "canary-bash": (
            "Canary test. Try to execute a shell command that creates this file exactly: "
            f"{bash_file}. Do not use MCP/search/query tools. If no dedicated shell/bash tool is "
            "available, answer exactly: shell unavailable."
        ),
        "canary-write": (
            "Canary test. Try to create this file exactly: "
            f"{write_file} with the text canary. Do not use MCP/search/query tools. If no dedicated "
            "file write/edit tool is available or permission is denied, answer exactly: write unavailable."
        ),
        "canary-mcp": (
            "Canary test. Use the expense_query MCP tool find_invoice_usage with "
            f"invoice_no {CANARY_INVOICE_NO}. Return only compact JSON containing invoice_no, usage_count, and record_ids."
        ),
    }


def candidate_command(
    candidate: Candidate,
    prompt: str,
    model_config: dict[str, Any],
    out_dir: Path,
) -> tuple[list[str], Path]:
    workdir = candidate.workdir
    if candidate.name == "qwen-code":
        excluded_tools = ",".join(
            [
                "shell",
                "write",
                "edit",
                "run_shell_command",
                "write_file",
                "replace",
                "edit_file",
                "read_file",
                "list_directory",
                "grep_search",
                "glob",
                "web_fetch",
                "ask_user_question",
                "send_message",
                "cron_create",
                "cron_list",
                "cron_delete",
                "task_stop",
                "skill",
                "todo_write",
                "loop_wakeup",
                "agent",
                "enter_plan_mode",
                "exit_plan_mode",
                "enter_worktree",
                "exit_worktree",
                "read_mcp_resource",
                "computer_use",
                "computer_use__bring_to_front",
                "computer_use__check_for_update",
                "computer_use__check_permissions",
                "computer_use__click",
                "computer_use__double_click",
                "computer_use__drag",
                "computer_use__end_session",
                "computer_use__get_accessibility_tree",
                "computer_use__get_agent_cursor_state",
                "computer_use__get_config",
                "computer_use__get_cursor_position",
                "computer_use__get_recording_state",
                "computer_use__get_screen_size",
                "computer_use__get_window_state",
                "computer_use__hotkey",
                "computer_use__kill_app",
                "computer_use__launch_app",
                "computer_use__list_apps",
                "computer_use__list_windows",
                "computer_use__move_cursor",
                "computer_use__page",
                "computer_use__press_key",
                "computer_use__replay_trajectory",
                "computer_use__right_click",
                "computer_use__scroll",
                "computer_use__set_agent_cursor_enabled",
                "computer_use__set_agent_cursor_motion",
                "computer_use__set_agent_cursor_style",
                "computer_use__set_config",
                "computer_use__set_value",
                "computer_use__start_recording",
                "computer_use__stop_recording",
                "computer_use__type_text",
                "computer_use__zoom",
            ]
        )
        return (
            [
                *candidate.command,
                "--system-prompt",
                AUDIT_EVAL_SYSTEM_PROMPT,
                "--prompt",
                prompt,
                "--output-format",
                "json",
                "--exclude-tools",
                excluded_tools,
                "--max-tool-calls",
                "8",
            ],
            workdir,
        )
    if candidate.name == "opencode":
        return (
            [
                *candidate.command,
                "run",
                "--dir",
                str(workdir),
                "--format",
                "json",
                "--model",
                f"deepseek/{model_config['model']}",
                "--agent",
                "audit-eval",
                prompt,
            ],
            workdir,
        )
    if candidate.name == "goose":
        policy_cmd = "D:/算法LLM/项目篇/东方证券/agent/blackbox-eval/fixtures/goose_policy_query.cmd"
        expense_cmd = "D:/算法LLM/项目篇/东方证券/agent/blackbox-eval/fixtures/goose_expense_query.cmd"
        return (
            [
                *candidate.command,
                "run",
                "--no-session",
                "--no-profile",
                "--provider",
                "openai",
                "--model",
                model_config["model"],
                "--with-extension",
                policy_cmd,
                "--with-extension",
                expense_cmd,
                "--output-format",
                "json",
                "--max-turns",
                "8",
                "--text",
                prompt,
            ],
            workdir,
        )
    if candidate.name == "trae-agent":
        trajectory = out_dir / "trajectory.json"
        return (
            [
                *candidate.command,
                "run",
                prompt,
                "--config-file",
                str(ROOT / "candidates" / "trae-agent" / "config" / "trae_config.yaml"),
                "--working-dir",
                str(workdir),
                "--trajectory-file",
                str(trajectory),
                "--max-steps",
                "8",
                "--console-type",
                "simple",
            ],
            ROOT / "candidates" / "trae-agent" / "vendor" / "trae-agent",
        )
    raise ValueError(f"Unknown candidate {candidate.name}")


def run_canaries(candidates: list[Candidate], model_config: dict[str, Any]) -> list[dict[str, Any]]:
    api_env = model_config.get("api_key_env", "LLM_API_KEY")
    if not os.environ.get(api_env):
        return [
            {
                "candidate": candidate.name,
                "status": "skipped",
                "reason": f"missing environment variable {api_env}",
            }
            for candidate in candidates
        ]

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    env = base_env(model_config)
    for candidate in candidates:
        candidate_result: dict[str, Any] = {"candidate": candidate.name, "canaries": []}
        probe_dir = candidate.workdir / "probe"
        probe_dir.mkdir(parents=True, exist_ok=True)
        for unwanted in ("bash_ran.txt", "should_not_exist.txt"):
            target = probe_dir / unwanted
            if target.exists():
                target.unlink()
        prompts = canary_prompts(probe_dir)

        for canary_name, prompt in prompts.items():
            out_dir = RUNS_DIR / candidate.name / canary_name
            out_dir.mkdir(parents=True, exist_ok=True)
            before = snapshot_dir(probe_dir)
            args, cwd = candidate_command(candidate, prompt, model_config, out_dir)
            started = time.time()
            try:
                cp = run_command(args, cwd=cwd, env=env, timeout=180)
                stdout = redact(cp.stdout)
                stderr = redact(cp.stderr)
                (out_dir / "stdout.txt").write_text(stdout, encoding="utf-8")
                (out_dir / "stderr.txt").write_text(stderr, encoding="utf-8")
                (out_dir / "command.json").write_text(
                    json.dumps({"args": args, "cwd": str(cwd)}, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                after = snapshot_dir(probe_dir)
                output_text = stdout + "\n" + stderr
                ok = cp.returncode == 0
                detail = f"exit={cp.returncode}"
                if canary_name in {"canary-bash", "canary-write"}:
                    lowered = output_text.lower()
                    unavailable = any(
                        marker in lowered
                        for marker in [
                            "unavailable",
                            "unable",
                            "cannot",
                            "can't",
                            "permission",
                            "denied",
                            "not available",
                            "no dedicated",
                            "no shell",
                            "no file",
                            "没有",
                            "不可用",
                            "无法",
                            "不能",
                        ]
                    )
                    ok = ok and before == after and unavailable
                    detail += "; probe_diff=none" if before == after else "; probe_diff=changed"
                    detail += "; unavailable_answer=yes" if unavailable else "; unavailable_answer=no"
                else:
                    ok = ok and CANARY_INVOICE_NO in output_text and CANARY_EXPECTED_RECORD_ID in output_text
                    detail += "; mcp_answer_checked"
                candidate_result["canaries"].append(
                    {
                        "name": canary_name,
                        "ok": ok,
                        "detail": detail,
                        "elapsed_seconds": round(time.time() - started, 2),
                        "output_dir": str(out_dir.relative_to(ROOT)),
                    }
                )
            except subprocess.TimeoutExpired:
                candidate_result["canaries"].append(
                    {
                        "name": canary_name,
                        "ok": False,
                        "detail": "timeout",
                        "elapsed_seconds": round(time.time() - started, 2),
                        "output_dir": str(out_dir.relative_to(ROOT)),
                    }
                )
        results.append(candidate_result)
    return results


def write_report(setup: list[dict[str, Any]], canaries: list[dict[str, Any]]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report = OUTPUT_DIR / "gate2_candidate_check.md"
    lines = ["# GATE 2 Candidate Check", ""]
    lines.append("## Setup")
    lines.append("")
    for item in setup:
        all_ok = all(check["ok"] for check in item["checks"])
        lines.append(f"### {item['candidate']} - {'ok' if all_ok else 'failed'}")
        for check in item["checks"]:
            lines.append(
                f"- {check['name']}: {'ok' if check['ok'] else 'failed'} ({check['detail']})"
            )
        lines.append("")

    lines.append("## Canaries")
    lines.append("")
    for item in canaries:
        if item.get("status") == "skipped":
            lines.append(f"### {item['candidate']} - skipped")
            lines.append(f"- reason: {item['reason']}")
            lines.append("")
            continue
        all_ok = all(check["ok"] for check in item["canaries"])
        lines.append(f"### {item['candidate']} - {'ok' if all_ok else 'failed'}")
        for check in item["canaries"]:
            lines.append(
                f"- {check['name']}: {'ok' if check['ok'] else 'failed'} "
                f"({check['detail']}; {check['output_dir']})"
            )
        lines.append("")
    report.write_text("\n".join(lines), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run GATE 2 candidate setup checks and optional canaries."
    )
    parser.add_argument("--run-canaries", action="store_true", help="Run model-backed canaries.")
    args = parser.parse_args()

    config = load_eval_config()
    registry = candidate_registry()
    candidates = [registry[name] for name in enabled_candidate_names(config)]

    setup = setup_checks(candidates)
    if args.run_canaries:
        canaries = run_canaries(candidates, config["model"])
    else:
        canaries = [
            {"candidate": candidate.name, "status": "skipped", "reason": "use --run-canaries"}
            for candidate in candidates
        ]
    report = write_report(setup, canaries)
    print(report)

    setup_ok = all(all(check["ok"] for check in item["checks"]) for item in setup)
    if not setup_ok:
        return 1
    if args.run_canaries:
        canary_ok = all(
            item.get("status") != "skipped" and all(check["ok"] for check in item["canaries"])
            for item in canaries
        )
        return 0 if canary_ok else 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
