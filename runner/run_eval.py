from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

import yaml

from gate2_candidate_check import (
    ROOT,
    base_env,
    candidate_command,
    candidate_registry,
    candidate_runtime_env,
    enabled_candidate_names,
    load_eval_config,
    redact,
    snapshot_dir,
)


CONFIG_PATH = ROOT / "config" / "eval_config.yaml"


def load_tasks(config: dict[str, Any]) -> list[dict[str, Any]]:
    evals_path = Path(config["paths"]["evals"])
    with evals_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8").strip()


def repair_mojibake(text: str) -> str:
    try:
        repaired = text.encode("latin1").decode("utf-8")
    except UnicodeError:
        return text
    cjk_original = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    cjk_repaired = sum(1 for char in repaired if "\u4e00" <= char <= "\u9fff")
    return repaired if cjk_repaired > cjk_original else text


def selected_tasks(
    tasks: list[dict[str, Any]], *, level: str | None, task_ids: list[str], limit: int | None
) -> list[dict[str, Any]]:
    if task_ids:
        task_id_set = set(task_ids)
        selected = [task for task in tasks if task["id"] in task_id_set]
    elif level:
        selected = [task for task in tasks if str(task.get("level")).lower() == level.lower()]
    else:
        selected = list(tasks)
    if limit is not None:
        selected = selected[:limit]
    return selected


def task_dir_name(task_id: str, variant: str, repeat_index: int) -> str:
    if variant == "precise" and repeat_index == 1:
        return task_id
    return f"{task_id}__{variant}__r{repeat_index}"


def build_prompt(task: dict[str, Any], variant: str, config: dict[str, Any]) -> str:
    role_prompt = read_text(config["fixtures"]["audit_role_prompt"])
    output_contract = read_text(config["fixtures"]["output_contract"])
    prompt_variants = task.get("prompt_variants") or {}
    task_prompt = prompt_variants.get(variant)
    if not task_prompt:
        raise ValueError(f"Task {task['id']} has no prompt variant {variant!r}")
    return "\n\n".join(
        [
            f"请直接回答这个审计问题: {task_prompt}",
            "这是完整任务,不要要求用户再提供任务或文件,不要探索项目目录,不要寻找评测入口。",
            "必须使用已连接的 MCP 工具查询制度或业务事实后再回答。",
            role_prompt,
            output_contract,
            f"任务元数据: id={task['id']}; level={task.get('level', '')}; category={task.get('category', '')}.",
            "现在开始,最终只输出一个可解析 JSON 代码块。",
        ]
    )


def diff_snapshots(before: dict[str, str], after: dict[str, str]) -> list[str]:
    lines: list[str] = []
    before_keys = set(before)
    after_keys = set(after)
    for rel in sorted(after_keys - before_keys):
        lines.append(f"ADDED {rel}")
    for rel in sorted(before_keys - after_keys):
        lines.append(f"REMOVED {rel}")
    for rel in sorted(before_keys & after_keys):
        if before[rel] != after[rel]:
            lines.append(f"MODIFIED {rel}")
    return lines


def parse_json_output_events(stdout: str) -> Any | None:
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        jsonl_events = []
        for line in stdout.splitlines():
            stripped = line.strip()
            if not stripped or not stripped.startswith(("{", "[")):
                continue
            try:
                jsonl_events.append(json.loads(stripped))
            except json.JSONDecodeError:
                pass
        if jsonl_events:
            return jsonl_events
        start = stdout.find("{")
        end = stdout.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(stdout[start : end + 1])
            except json.JSONDecodeError:
                return None
        return None


def content_text(content: Any) -> str:
    if isinstance(content, str):
        return repair_mojibake(content)
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return repair_mojibake("\n".join(part for part in parts if part))
    return ""


def event_text(event: dict[str, Any]) -> str:
    if event.get("type") == "text":
        part = event.get("part")
        if isinstance(part, dict) and isinstance(part.get("text"), str):
            return repair_mojibake(part["text"])
    part = event.get("part")
    if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str):
        return repair_mojibake(part["text"])
    return ""


def extract_final_text(stdout: str, stderr: str) -> str:
    events = parse_json_output_events(stdout)
    if isinstance(events, list):
        for event in reversed(events):
            if isinstance(event, dict) and event.get("type") == "result" and event.get("result"):
                return repair_mojibake(str(event["result"]))
            if isinstance(event, dict):
                text = event_text(event)
                if text:
                    return text
        for event in reversed(events):
            if not isinstance(event, dict):
                continue
            message = event.get("message")
            if isinstance(message, dict) and message.get("role") == "assistant":
                text = content_text(message.get("content"))
                if text:
                    return text
    if isinstance(events, dict):
        messages = events.get("messages")
        if isinstance(messages, list):
            for message in reversed(messages):
                if not isinstance(message, dict) or message.get("role") != "assistant":
                    continue
                text = content_text(message.get("content"))
                if text:
                    return text
        for key in ("result", "text", "message", "content"):
            value = events.get(key)
            if isinstance(value, str) and value:
                return repair_mojibake(value)
    return repair_mojibake(stdout.strip() or stderr.strip())


def extract_last_message_file(out_dir: Path) -> str | None:
    last_message = out_dir / "last_message.txt"
    if not last_message.exists() or last_message.stat().st_size == 0:
        return None
    return repair_mojibake(last_message.read_text(encoding="utf-8", errors="replace").strip())


def coerce_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item is not None and str(item).strip()]
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [str(value)]


def normalize_answer_json(answer: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    normalized = dict(answer)
    for key in ("anomaly_ids", "record_ids"):
        if key not in normalized:
            normalized[key] = []
            warnings.append(f"missing_{key}")
        else:
            if not isinstance(normalized[key], list):
                warnings.append(f"coerced_{key}")
            normalized[key] = coerce_string_list(normalized[key])

    if "answer" not in normalized:
        normalized["answer"] = ""
        warnings.append("missing_answer")
    elif not isinstance(normalized["answer"], str):
        normalized["answer"] = str(normalized["answer"])
        warnings.append("coerced_answer")

    citations = normalized.get("citations")
    if citations is None:
        normalized["citations"] = []
        warnings.append("missing_citations")
    elif isinstance(citations, list):
        cleaned = []
        for citation in citations:
            if isinstance(citation, dict):
                cleaned.append(
                    {
                        "doc_id": str(citation.get("doc_id", "")),
                        "clause_no": str(citation.get("clause_no", "")),
                    }
                )
            else:
                warnings.append("dropped_non_object_citation")
        normalized["citations"] = cleaned
    else:
        normalized["citations"] = []
        warnings.append("coerced_citations")
    return normalized, warnings


def try_parse_answer(candidate: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        parsed = json.loads(candidate.strip())
        if isinstance(parsed, dict):
            normalized, warnings = normalize_answer_json(parsed)
            warning_text = "; ".join(warnings) if warnings else None
            return normalized, warning_text
        return None, "JSON value is not an object"
    except json.JSONDecodeError as exc:
        return None, str(exc)


def extract_braced_json(text: str) -> str | None:
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def recover_answer_json(text: str) -> dict[str, Any] | None:
    candidate = text.strip()
    recovered: dict[str, Any] = {}
    for key in ("anomaly_ids", "record_ids"):
        match = re.search(rf'"{key}"\s*:\s*\[([\s\S]*?)\]', candidate)
        recovered[key] = re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', match.group(1)) if match else []
    answer_match = re.search(
        r'"answer"\s*:\s*"([\s\S]*?)"\s*,\s*"(?:citations|record_ids|anomaly_ids)"',
        candidate,
    )
    recovered["answer"] = answer_match.group(1).replace("\n", " ").strip() if answer_match else ""
    citations_match = re.search(r'"citations"\s*:\s*(\[[\s\S]*?\])', candidate)
    if citations_match:
        try:
            citations = json.loads(citations_match.group(1))
        except json.JSONDecodeError:
            citations = []
    else:
        citations = []
    recovered["citations"] = citations
    if any(recovered.get(key) for key in ("anomaly_ids", "record_ids", "answer", "citations")):
        normalized, _ = normalize_answer_json(recovered)
        return normalized
    return None


def extract_answer_json(final_text: str) -> tuple[dict[str, Any] | None, str | None, bool]:
    last_error: str | None = None
    candidates = re.findall(r"```(?:json)?\s*([\s\S]*?)```", final_text, flags=re.IGNORECASE)
    candidates.extend([final_text.strip()])
    braced = extract_braced_json(final_text)
    if braced:
        candidates.append(braced)

    seen: set[str] = set()
    for candidate in reversed(candidates):
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        parsed, parse_error = try_parse_answer(candidate)
        if parsed is not None:
            return parsed, parse_error, bool(parse_error)
        last_error = parse_error

    for candidate in reversed(candidates):
        recovered = recover_answer_json(candidate)
        if recovered is not None:
            return recovered, f"recovered from invalid JSON: {last_error}", True
    return None, last_error or "no JSON object found", False


def output_contract_warnings(
    final_text: str,
    parsed_answer: dict[str, Any] | None,
    parse_error: str | None,
) -> list[str]:
    if parsed_answer is None:
        return []
    warnings: list[str] = []
    blocks = list(re.finditer(r"```(?:json)?\s*([\s\S]*?)```", final_text, flags=re.IGNORECASE))
    if len(blocks) != 1:
        warnings.append("expected_exactly_one_json_code_block")
    elif final_text[: blocks[0].start()].strip() or final_text[blocks[0].end() :].strip():
        warnings.append("extra_text_outside_json_code_block")
    if parse_error:
        warnings.extend(part.strip() for part in parse_error.split(";") if part.strip())
    return warnings


def extract_final_text_from_trajectory(out_dir: Path) -> str | None:
    trajectory_path = out_dir / "trajectory.json"
    if not trajectory_path.exists() or trajectory_path.stat().st_size == 0:
        return None
    try:
        data = json.loads(trajectory_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None

    fallback = data.get("final_result")
    if isinstance(fallback, str) and fallback.strip():
        fallback = repair_mojibake(fallback.strip())
        parsed, _, _ = extract_answer_json(fallback)
        if parsed is not None:
            return fallback

    steps = data.get("agent_steps")
    if isinstance(steps, list):
        for step in reversed(steps):
            if not isinstance(step, dict):
                continue
            response = step.get("llm_response")
            if not isinstance(response, dict):
                continue
            content = response.get("content")
            if not isinstance(content, str) or not content.strip():
                continue
            content = repair_mojibake(content.strip())
            parsed, _, _ = extract_answer_json(content)
            if parsed is not None:
                return content

    if isinstance(fallback, str) and fallback:
        return fallback
    return None


def write_trajectory(stdout: str, out_dir: Path) -> str:
    trajectory_path = out_dir / "trajectory.json"
    if trajectory_path.exists() and trajectory_path.stat().st_size > 0:
        (out_dir / "stdout_events.json").write_text(stdout, encoding="utf-8")
        return trajectory_path.name
    events = parse_json_output_events(stdout)
    if events is not None:
        trajectory_path.write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        trajectory_path.write_text(stdout, encoding="utf-8")
    return trajectory_path.name


@contextmanager
def claude_task_config(candidate_name: str, task_log_dir: Path) -> Iterator[None]:
    if candidate_name != "claude-code":
        yield
        return

    config_path = ROOT / "candidates" / "claude-code" / "mcp_config.json"
    original = config_path.read_text(encoding="utf-8")
    data = json.loads(original)
    for server in data.get("mcpServers", {}).values():
        env = server.setdefault("env", {})
        env.pop("EVAL_TASK_LOG", None)
    clean_original = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    for server in data.get("mcpServers", {}).values():
        env = server.setdefault("env", {})
        env["EVAL_TASK_LOG"] = str(task_log_dir)
    config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        yield
    finally:
        config_path.write_text(clean_original, encoding="utf-8")


@contextmanager
def codex_task_config(candidate_name: str, task_log_dir: Path) -> Iterator[None]:
    if candidate_name != "codex":
        yield
        return

    config_path = ROOT / "candidates" / "codex" / "config.toml"
    original = config_path.read_text(encoding="utf-8")
    clean_original = re.sub(r"^EVAL_TASK_LOG\s*=.*\n", "", original, flags=re.MULTILINE)
    task_log_value = json.dumps(task_log_dir.as_posix(), ensure_ascii=False)
    updated = re.sub(
        r"(\[mcp_servers\.(?:policy_query|expense_query)\.env\]\n)",
        rf"\1EVAL_TASK_LOG = {task_log_value}\n",
        clean_original,
    )
    config_path.write_text(updated, encoding="utf-8")
    try:
        yield
    finally:
        config_path.write_text(clean_original, encoding="utf-8")


@contextmanager
def qwen_task_log_config(candidate_name: str, task_log_dir: Path) -> Iterator[None]:
    if candidate_name != "qwen-code":
        yield
        return

    settings_path = ROOT / "candidates" / "qwen-code" / "workdir" / ".qwen" / "settings.json"
    original = settings_path.read_text(encoding="utf-8")
    data = json.loads(original)
    for server in data.get("mcpServers", {}).values():
        env = server.setdefault("env", {})
        env.pop("EVAL_TASK_LOG", None)
    clean_original = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    for server in data.get("mcpServers", {}).values():
        env = server.setdefault("env", {})
        env["EVAL_TASK_LOG"] = str(task_log_dir)
    settings_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        cp = subprocess.run(
            [str(shutil.which("qwen") or "qwen"), "mcp", "approve", "--all"],
            cwd=str(settings_path.parents[1]),
            env=os.environ.copy(),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=30,
        )
        (task_log_dir / "qwen_mcp_approve_stdout.log").write_text(redact(cp.stdout), encoding="utf-8")
        (task_log_dir / "qwen_mcp_approve_stderr.log").write_text(redact(cp.stderr), encoding="utf-8")
        if cp.returncode != 0:
            raise RuntimeError(f"qwen mcp approve failed with exit {cp.returncode}")
        yield
    finally:
        settings_path.write_text(clean_original, encoding="utf-8")


@contextmanager
def opencode_task_config(candidate_name: str, task_log_dir: Path) -> Iterator[None]:
    if candidate_name != "opencode":
        yield
        return

    config_path = ROOT / "candidates" / "opencode" / "workdir" / "opencode.json"
    original = config_path.read_text(encoding="utf-8")
    data = json.loads(original)
    permission = data.setdefault("permission", {})
    permission.update(
        {
            "*": "deny",
            "policy_query_*": "allow",
            "expense_query_*": "allow",
            "read": "deny",
            "task": "deny",
            "glob": "deny",
            "grep": "deny",
            "bash": "deny",
            "edit": "deny",
            "write": "deny",
            "webfetch": "deny",
            "websearch": "deny",
            "question": "deny",
            "todowrite": "deny",
            "todoread": "deny",
        }
    )
    for server in data.get("mcp", {}).values():
        env = server.setdefault("environment", {})
        env.pop("EVAL_TASK_LOG", None)
    clean_original = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    for server in data.get("mcp", {}).values():
        env = server.setdefault("environment", {})
        env["EVAL_TASK_LOG"] = str(task_log_dir)
    config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        yield
    finally:
        config_path.write_text(clean_original, encoding="utf-8")


@contextmanager
def trae_task_config(candidate_name: str, task_log_dir: Path) -> Iterator[None]:
    if candidate_name != "trae-agent":
        yield
        return

    config_path = ROOT / "candidates" / "trae-agent" / "config" / "trae_config.yaml"
    original = config_path.read_text(encoding="utf-8")
    data = yaml.safe_load(original)
    for server in (data.get("mcp_servers") or {}).values():
        env = server.setdefault("env", {})
        env.pop("EVAL_TASK_LOG", None)
    clean_original = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
    for server in (data.get("mcp_servers") or {}).values():
        env = server.setdefault("env", {})
        env["EVAL_TASK_LOG"] = str(task_log_dir)
    config_path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    try:
        yield
    finally:
        config_path.write_text(clean_original, encoding="utf-8")


@contextmanager
def candidate_task_config(candidate_name: str, task_log_dir: Path) -> Iterator[None]:
    with qwen_task_log_config(candidate_name, task_log_dir):
        with opencode_task_config(candidate_name, task_log_dir):
            with trae_task_config(candidate_name, task_log_dir):
                with claude_task_config(candidate_name, task_log_dir):
                    with codex_task_config(candidate_name, task_log_dir):
                        yield


def run_one(
    *,
    candidate: Any,
    task: dict[str, Any],
    variant: str,
    repeat_index: int,
    run_root: Path,
    config: dict[str, Any],
    timeout_seconds: int,
) -> dict[str, Any]:
    task_dir = run_root / candidate.name / task_dir_name(task["id"], variant, repeat_index)
    task_dir.mkdir(parents=True, exist_ok=True)
    result_path = task_dir / "result.json"
    if result_path.exists():
        existing = json.loads(result_path.read_text(encoding="utf-8"))
        if existing.get("completed"):
            return existing

    prompt = build_prompt(task, variant, config)
    env = base_env(config["model"])
    env.update(
        {
            "EVAL_TASK_LOG": str(task_dir),
            "EVAL_POLICY_CORPUS_DIR": str(Path(config["paths"]["policy_corpus_dir"])),
            "EVAL_EXPENSE_DB": str(Path(config["paths"]["expense_db"])),
        }
    )
    env.update(candidate_runtime_env(candidate.name, config["model"]))
    args, cwd = candidate_command(candidate, prompt, config["model"], task_dir)

    with candidate_task_config(candidate.name, task_dir):
        before = snapshot_dir(candidate.workdir)
        started = time.time()
        timed_out = False
        try:
            cp = subprocess.run(
                [str(shutil.which(args[0]) or args[0]), *args[1:]],
                cwd=str(cwd),
                env={**os.environ, **env},
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=timeout_seconds,
            )
            stdout = redact(cp.stdout)
            stderr = redact(cp.stderr)
            exit_code = cp.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = redact(exc.stdout if isinstance(exc.stdout, str) else "")
            stderr = redact(exc.stderr if isinstance(exc.stderr, str) else "")
            exit_code = None
        elapsed = time.time() - started
        after = snapshot_dir(candidate.workdir)

    (task_dir / "stdout.log").write_text(stdout, encoding="utf-8")
    (task_dir / "stderr.log").write_text(stderr, encoding="utf-8")
    (task_dir / "command.json").write_text(
        json.dumps({"args": args, "cwd": str(cwd)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    diff_lines = diff_snapshots(before, after)
    (task_dir / "workdir_diff.txt").write_text("\n".join(diff_lines), encoding="utf-8")
    tool_log = task_dir / "tool_calls.jsonl"
    if not tool_log.exists():
        tool_log.write_text("", encoding="utf-8")
    trajectory_name = write_trajectory(stdout, task_dir)
    final_text = (
        extract_last_message_file(task_dir)
        or extract_final_text_from_trajectory(task_dir)
        or extract_final_text(stdout, stderr)
    )
    parsed_answer, parse_error, format_repaired = extract_answer_json(final_text)
    contract_warnings = output_contract_warnings(final_text, parsed_answer, parse_error)
    tool_call_count = sum(1 for line in tool_log.read_text(encoding="utf-8").splitlines() if line.strip())

    result = {
        "completed": True,
        "candidate": candidate.name,
        "task_id": task["id"],
        "level": task.get("level"),
        "category": task.get("category"),
        "variant": variant,
        "repeat_index": repeat_index,
        "elapsed_seconds": round(elapsed, 2),
        "exit_code": exit_code,
        "timeout": timed_out,
        "format_failure": parsed_answer is None,
        "format_repaired": format_repaired,
        "parse_error": parse_error,
        "contract_warnings": contract_warnings,
        "answer_json": parsed_answer,
        "final_text": final_text,
        "tool_calls_count": tool_call_count,
        "tool_log_present": tool_log.exists(),
        "workdir_diff_empty": not diff_lines,
        "files": {
            "stdout": "stdout.log",
            "stderr": "stderr.log",
            "tool_calls": "tool_calls.jsonl",
            "trajectory": trajectory_name,
            "result": "result.json",
            "workdir_diff": "workdir_diff.txt",
            "last_message": "last_message.txt",
        },
    }
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run blackbox eval tasks and collect artifacts.")
    parser.add_argument("--candidate", default="qwen-code")
    parser.add_argument("--level", default="L1")
    parser.add_argument("--all-tasks", action="store_true")
    parser.add_argument("--task-id", action="append", default=[])
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--variant", default="precise")
    parser.add_argument("--all-variants", action="store_true")
    parser.add_argument("--repeat-index", type=int, default=1)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--timeout-seconds", type=int, default=None)
    args = parser.parse_args()

    config = load_eval_config()
    registry = candidate_registry()
    enabled = set(enabled_candidate_names(config))
    if args.candidate not in enabled:
        raise SystemExit(f"candidate {args.candidate!r} is not enabled in {CONFIG_PATH}")
    candidate = registry[args.candidate]
    run_id = args.run_id or f"gate3_smoke_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_root = Path(config["paths"]["runs_dir"]) / run_id
    run_root.mkdir(parents=True, exist_ok=True)
    selected_level = None if args.all_tasks else args.level
    selected_limit = None if args.all_tasks else args.limit
    tasks = selected_tasks(
        load_tasks(config),
        level=selected_level,
        task_ids=args.task_id,
        limit=selected_limit,
    )
    if not tasks:
        raise SystemExit("no tasks selected")
    variants = (
        list(config["execution"].get("prompt_variants") or ["precise"])
        if args.all_variants
        else [args.variant]
    )
    repeat_indices = (
        list(range(1, int(config["execution"].get("repeats_per_variant", 1)) + 1))
        if args.all_variants
        else [args.repeat_index]
    )

    timeout_seconds = args.timeout_seconds or int(config["execution"]["task_timeout_seconds"])
    manifest = {
        "run_id": run_id,
        "candidate": candidate.name,
        "variants": variants,
        "repeat_indices": repeat_indices,
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "tasks": [task["id"] for task in tasks],
        "config": str(CONFIG_PATH),
    }
    (run_root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    results = []
    for task in tasks:
        for variant in variants:
            for repeat_index in repeat_indices:
                print(
                    f"running {candidate.name} {task['id']} {variant} r{repeat_index}",
                    flush=True,
                )
                results.append(
                    run_one(
                        candidate=candidate,
                        task=task,
                        variant=variant,
                        repeat_index=repeat_index,
                        run_root=run_root,
                        config=config,
                        timeout_seconds=timeout_seconds,
                    )
                )
    manifest["finished_at"] = datetime.now().isoformat(timespec="seconds")
    manifest["results"] = len(results)
    (run_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"run_id": run_id, "results": len(results)}, ensure_ascii=False))
    return 0 if all(item.get("completed") and not item.get("timeout") for item in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
