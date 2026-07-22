from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "domain-enhancement" / "scripted-audit-core" / "scripts"))

import run_gate3_development as runtime  # noqa: E402
from audit_trace import (  # noqa: E402
    finish_run,
    record_event,
    redact_secret_in_tree,
    start_run,
)
from formal_eval_plan import MODEL_NAME, TASK_TIMEOUT_SECONDS  # noqa: E402
from scripted_workflow_core import (  # noqa: E402
    SCRIPTED_WORKFLOW_VERSION,
    initialize_scripted_task,
    retained_state,
)
from audit_control_core import checkpoint_context  # noqa: E402


FORMAL = ROOT / "data" / "formal_case_rubric"
DATA_DB = FORMAL / "expense_formal.db"
DOMAIN = ROOT / "domain-enhancement"
SCRIPTED_ADAPTERS = DOMAIN / "scripted-adapters"
RUN_ROOT = ROOT / "runs" / "gate4_scripted"
RUN_ROOT_BASENAME = "gate4_scripted"
GATE_LABEL = "GATE4脚本化领域增强对比组"
SUMMARY_GATE = "GATE4_SCRIPTED_COMPARISON"
COMPARISON_SOURCE = "runs/gate4_formal"
VALIDATE_FORMAL_RUBRICS = True
REQUIRE_SCRIPTED_FREEZE = True
SCRIPTED_FREEZE = ROOT / "config" / "scripted_gate3_frozen_lock.json"
PROXY_PORT = 18791
GROUPS = (
    "ccb-scripted-enhanced",
    "codex-scripted-enhanced",
    "openclaude-scripted-enhanced",
    "opencode-scripted-enhanced",
    "oh-my-pi-scripted-enhanced",
    "pi-agent-scripted-enhanced",
)
FRAMEWORKS = {
    "ccb": "claude-code-best",
    "codex": "codex",
    "openclaude": "openclaude",
    "opencode": "opencode",
    "oh-my-pi": "oh-my-pi",
    "pi-agent": "pi-agent",
}
BUILDERS = {
    "ccb": runtime.ccb_command,
    "codex": runtime.codex_command,
    "openclaude": runtime.openclaude_command,
    "opencode": runtime.opencode_command,
    "oh-my-pi": runtime.oh_my_pi_command,
    "pi-agent": runtime.pi_agent_command,
}


def _fingerprint(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(
                item for item in path.rglob("*")
                if item.is_file() and "__pycache__" not in item.parts and item.suffix != ".pyc"
            )
        elif path.is_file():
            files.append(path)
    for path in sorted(set(files), key=lambda item: item.as_posix()):
        try:
            label = path.relative_to(ROOT).as_posix()
        except ValueError:
            label = path.name
        digest.update(label.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def scripted_config_fingerprint() -> str:
    return _fingerprint(
        [
            ROOT / "config" / "scripted_enhancement_plan.yaml",
            DOMAIN / "scripted-audit-core",
            DOMAIN / "scripted-control-mcp",
            DOMAIN / "shared-audit-core" / "schemas",
            DOMAIN / "shared-audit-core" / "scripts",
            DOMAIN / "build_scripted_adapters.py",
            ROOT / "runner" / "run_gate4_scripted.py",
            ROOT / "runner" / "run_gate3_scripted.py",
        ]
    )


def scripted_dataset_fingerprint() -> str:
    paths = [FORMAL / "evals.json", DATA_DB, ROOT / "config" / "source_eval_lock.yaml"]
    cases = FORMAL / "cases.json"
    if cases.exists():
        paths.append(cases)
    return _fingerprint(paths)


def write_scripted_freeze() -> dict[str, Any]:
    lock = {
        "workflow_version": SCRIPTED_WORKFLOW_VERSION,
        "config_fingerprint": scripted_config_fingerprint(),
        "gate3_run_summary": RUN_ROOT.relative_to(ROOT).as_posix() + "/run_summary.json",
        "frozen_at": time.time(),
    }
    runtime.write_text(SCRIPTED_FREEZE, json.dumps(lock, ensure_ascii=False, indent=2) + "\n")
    return lock


def verify_scripted_freeze() -> None:
    if not SCRIPTED_FREEZE.exists():
        raise SystemExit("missing scripted GATE3 freeze lock; run runner/run_gate3_scripted.py first")
    lock = json.loads(SCRIPTED_FREEZE.read_text(encoding="utf-8"))
    expected = {
        "workflow_version": SCRIPTED_WORKFLOW_VERSION,
        "config_fingerprint": scripted_config_fingerprint(),
    }
    mismatches = {
        key: {"expected": value, "actual": lock.get(key)}
        for key, value in expected.items()
        if lock.get(key) != value
    }
    if mismatches:
        raise SystemExit(f"scripted GATE3 freeze mismatch: {json.dumps(mismatches, ensure_ascii=False)}")


def _group_prefix(group: str) -> str:
    suffix = "-scripted-enhanced"
    if not group.endswith(suffix):
        raise ValueError(f"invalid scripted group: {group}")
    return group[: -len(suffix)]


def _task_question(task: dict[str, Any]) -> str:
    variants = task.get("prompt_variants")
    if isinstance(variants, dict) and isinstance(variants.get("precise"), str):
        return variants["precise"]
    return str(task.get("prompt", ""))


def load_tasks(task_ids: list[str]) -> list[dict[str, Any]]:
    raw = json.loads((FORMAL / "evals.json").read_text(encoding="utf-8"))
    tasks = [{**task, "prompt": _task_question(task)} for task in raw]
    if not task_ids:
        return tasks
    selected = [task for task in tasks if task["id"] in set(task_ids)]
    missing = sorted(set(task_ids) - {task["id"] for task in selected})
    if missing:
        raise ValueError(f"unknown formal task IDs: {missing}")
    return selected


def safe_reset() -> None:
    target = RUN_ROOT.resolve()
    expected = (ROOT / "runs").resolve()
    if target.parent != expected or target.name != RUN_ROOT_BASENAME:
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

        last_error: OSError | None = None
        for attempt in range(5):
            try:
                shutil.rmtree(target, onexc=remove_readonly)
                last_error = None
                break
            except OSError as exc:
                last_error = exc
                if attempt == 4:
                    break
                time.sleep(0.25 * (attempt + 1))
        if last_error is not None:
            stale = target.with_name(f"{target.name}-stale-{int(time.time())}")
            if stale.parent != expected or not stale.name.startswith(f"{target.name}-stale-"):
                raise ValueError(f"refusing to isolate unexpected stale path: {stale}")
            try:
                target.rename(stale)
            except OSError:
                raise last_error
    target.mkdir(parents=True)


def archive_retry_task(group: str, task_id: str, reason: str) -> Path | None:
    source = (RUN_ROOT / group / task_id).resolve()
    root = RUN_ROOT.resolve()
    if source.parent.parent != root or not source.exists():
        return None
    history = root / "retry-history" / group / task_id
    history.mkdir(parents=True, exist_ok=True)
    attempts = [path for path in history.iterdir() if path.is_dir() and path.name.startswith("attempt-")]
    destination = history / f"attempt-{len(attempts) + 1:02d}"
    shutil.move(str(source), str(destination))
    registry = root / "retry_registry.jsonl"
    with registry.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "group": group,
                    "task_id": task_id,
                    "reason": reason,
                    "archived_to": destination.relative_to(ROOT).as_posix(),
                    "archived_at": time.time(),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n"
        )
    return destination


def scripted_task_prompt(task: dict[str, Any], enhanced: bool, framework: str | None = None) -> str:
    _ = enhanced
    framework_key = framework or ""
    framework_hint = (
        "OpenClaude只保证Bash、Edit、Read可用；需要落盘时使用Edit或Bash安全脚本。"
        if framework_key.startswith("openclaude")
        else ""
    )
    return f"""你正在执行{GATE_LABEL}。

任务ID：{task['id']}
题型：{task['category']}
问题：{task['prompt']}

先读取work/scripted_workflow.json，只使用其中列出的必要Skills。不要自行维护audit_plan、Task Memory、Checkpoint、生成后的evidence_matrix或validation_report，这些由外部脚本处理。子智能体角色只是可选授权，不是必调步骤；简单任务留在主智能体完成。
{framework_hint}

要求：
1. 必须查询制度和只读业务库后判断，可以使用Shell、Python、SQLite和当前工作区临时文件。
2. 禁止读取ground_truth、cases.json、Rubric、判卷代码、历史答案、其他任务或候选轨迹，也不得访问无关互联网。
3. 只回答题目要求的规则和范围。异常record_ids只包含参与违规的记录；无异常时保留直接核查或结论覆盖的记录并明确写“无异常”。
4. 把anomaly_ids、record_ids、answer、citations四个语义字段写入预置的work/final_result.json。存在异常时，citations必须写明制度文件名和具体条款；推荐使用doc_id、clause_no对象，脚本也可将答案中已明确写出的“制度文件名+条款”归一化为对象，但不会推断未写出的依据。
5. 同时填写预置的work/evidence_input.json。存在异常时，每个anomaly_id只写其实际对应的record_ids、citations和已核实facts；无异常时写明searched_population、query_conditions、checked_rules、population_count、conclusion并将complete设为true。脚本只检查和转换，不会替你生成业务证据。随后以空参数调用audit_control.validate_audit_result；valid=true后，再以空参数调用audit_control.submit_audit_result。不要把长中文答案嵌入MCP参数。
6. 生成后的证据矩阵、验证报告、任务状态快照和阶段Checkpoint由脚本自动生成；不要调用checkpoint_audit_context，也不要执行已下沉的evidence-coverage-check或result-validator流程。
7. 提交成功后只输出GATE4_TASK_PASS；无法提交时只输出GATE4_TASK_FAIL。
"""


def configure_runtime() -> None:
    runtime.DEV = FORMAL
    runtime.DEV_DB = DATA_DB
    runtime.RUN_ROOT = RUN_ROOT
    runtime.PROXY_PORT = PROXY_PORT
    runtime.load_tasks = load_tasks
    runtime.safe_reset = safe_reset
    runtime.task_prompt = scripted_task_prompt
    runtime.CCB_PLUGIN = SCRIPTED_ADAPTERS / "claude-code-best" / "securities-expense-audit"
    runtime.CODEX_PLUGIN = SCRIPTED_ADAPTERS / "codex" / "securities-expense-audit"
    runtime.OPENCLAUDE_PLUGIN = SCRIPTED_ADAPTERS / "openclaude" / "securities-expense-audit"
    runtime.OPENCODE_PLUGIN = SCRIPTED_ADAPTERS / "opencode" / "securities-expense-audit"
    runtime.OH_MY_PI_PLUGIN = SCRIPTED_ADAPTERS / "oh-my-pi" / "securities-expense-audit"
    runtime.PI_AGENT_PLUGIN = SCRIPTED_ADAPTERS / "pi-agent" / "securities-expense-audit"


def _write_scripted_instructions(workspace: Path) -> None:
    instructions = (DOMAIN / "scripted-audit-core" / "references" / "main_workflow.md").read_text(
        encoding="utf-8"
    )
    runtime.write_text(workspace / "AGENTS.md", instructions)
    runtime.write_text(workspace / "CLAUDE.md", instructions)


def run_one(group: str, task: dict[str, Any], timeout: int) -> dict[str, Any]:
    prefix = _group_prefix(group)
    framework = FRAMEWORKS[prefix]
    builder = BUILDERS[prefix]
    unused_baseline = RUN_ROOT / ".unused-baseline"
    command, child_env = builder(group, task, unused_baseline, os.environ.copy())
    base = RUN_ROOT / group / task["id"]
    workspace = base / "workspace"
    artifacts = base / "artifacts"
    _write_scripted_instructions(workspace)
    start_run(
        workspace=workspace,
        task_id=task["id"],
        framework=framework,
        experiment_group=group,
        model=MODEL_NAME,
        timeout_seconds=timeout,
    )
    workflow = initialize_scripted_task(
        work_dir=workspace,
        task_id=task["id"],
        category=task["category"],
        question=task["prompt"],
        framework=framework,
        experiment_group=group,
        timeout_seconds=timeout,
    )
    route = workflow["route"]
    for skill in route["skills"]:
        record_event(
            work_dir=workspace,
            task_id=task["id"],
            event_type="skill_selected",
            source="external_scripted_router",
            framework=framework,
            experiment_group=group,
            reason_code=route["route"],
            summary={
                "skill": skill,
                "category": task["category"],
                "selection_source": "public_category_route",
            },
            artifact_paths=["work/scripted_workflow.json"],
        )
    for artifact_path in (
        "work/scripted_workflow.json",
        "work/task_memory.json",
        "work/evidence_input.json",
    ):
        record_event(
            work_dir=workspace,
            task_id=task["id"],
            event_type="artifact_written",
            source="external_scripted_router",
            framework=framework,
            experiment_group=group,
            summary={"artifact_type": Path(artifact_path).stem},
            artifact_paths=[artifact_path],
        )
    checkpoint_context(
        work_dir=workspace,
        task_id=task["id"],
        stage="planning_completed",
        context_usage_percent=0.0,
        retained_state=retained_state(workspace, task["id"], "not_submitted"),
        artifact_paths=[
            "work/scripted_workflow.json",
            "work/task_memory.json",
            "work/evidence_input.json",
        ],
        compacted=False,
        estimation_method="external_scripted_stage",
    )

    started = time.time()
    container_name = f"g3-{group}-{task['id'].lower()}"
    returncode, timed_out, stdout, stderr = runtime._run_captured_command(
        command,
        child_env,
        timeout,
        container_name,
    )
    runtime.write_text(artifacts / "trajectory.jsonl", stdout)
    runtime.write_text(artifacts / "stderr.log", stderr)
    elapsed_seconds = time.time() - started
    redact_secret_in_tree(base, child_env.get("LLM_API_KEY", ""))
    finish_run(
        workspace=workspace,
        artifacts_dir=artifacts,
        task_id=task["id"],
        framework=framework,
        experiment_group=group,
        returncode=returncode,
        timed_out=timed_out,
        elapsed_seconds=elapsed_seconds,
    )
    receipt_path = workspace / "submission_receipt.json"
    receipt: dict[str, Any] = {}
    if receipt_path.exists():
        try:
            value = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt = value if isinstance(value, dict) else {}
        except json.JSONDecodeError:
            receipt = {"status": "invalid_json"}
    result = {
        "group": group,
        "task_id": task["id"],
        "returncode": returncode,
        "timed_out": timed_out,
        "elapsed_seconds": round(elapsed_seconds, 3),
        "submission_status": receipt.get("status", "missing"),
        "submission_attempt": receipt.get("attempt"),
        "workflow_version": SCRIPTED_WORKFLOW_VERSION,
        "config_fingerprint": scripted_config_fingerprint(),
        "dataset_fingerprint": scripted_dataset_fingerprint(),
    }
    runtime.write_text(base / "run_result.json", json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


def _run_result_accepted(value: dict[str, Any], timeout: int) -> bool:
    return (
        value.get("submission_status") == "accepted"
        and value.get("returncode") == 0
        and not value.get("timed_out")
        and isinstance(value.get("elapsed_seconds"), (int, float))
        and value["elapsed_seconds"] <= timeout
    )


def _load_run_result(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _is_reusable(group: str, task_id: str, timeout: int) -> bool:
    path = RUN_ROOT / group / task_id / "run_result.json"
    if not path.exists():
        return False
    value = _load_run_result(path)
    return (
        _run_result_accepted(value, timeout)
        and value.get("workflow_version") == SCRIPTED_WORKFLOW_VERSION
        and value.get("config_fingerprint") == scripted_config_fingerprint()
        and value.get("dataset_fingerprint") == scripted_dataset_fingerprint()
    )


def _write_summary(tasks: list[dict[str, Any]]) -> None:
    runs: list[dict[str, Any]] = []
    for group in GROUPS:
        for task in tasks:
            path = RUN_ROOT / group / task["id"] / "run_result.json"
            if path.exists():
                runs.append(json.loads(path.read_text(encoding="utf-8")))
    runs.sort(key=lambda item: (item["group"], item["task_id"]))
    summary = {
        "gate": SUMMARY_GATE,
        "workflow_version": SCRIPTED_WORKFLOW_VERSION,
        "config_fingerprint": scripted_config_fingerprint(),
        "dataset_fingerprint": scripted_dataset_fingerprint(),
        "groups": list(GROUPS),
        "comparison_sources": {
            "baseline_and_original_enhanced": COMPARISON_SOURCE,
            "scripted_enhanced": RUN_ROOT.relative_to(ROOT).as_posix(),
        },
        "tasks": [task["id"] for task in tasks],
        "runs": runs,
    }
    runtime.write_text(RUN_ROOT / "run_summary.json", json.dumps(summary, ensure_ascii=False, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the isolated scripted-enhancement comparison group")
    parser.add_argument("--groups", nargs="+", choices=GROUPS, default=list(GROUPS))
    parser.add_argument("--task-id", action="append", default=[])
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--timeout", type=int, default=TASK_TIMEOUT_SECONDS)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--retry-reason", default="scripted_resume")
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()

    configure_runtime()
    subprocess.run(
        [sys.executable, str(DOMAIN / "build_scripted_adapters.py")],
        cwd=ROOT,
        check=True,
    )
    if REQUIRE_SCRIPTED_FREEZE:
        verify_scripted_freeze()
    if VALIDATE_FORMAL_RUBRICS:
        subprocess.run(
            [sys.executable, str(ROOT / "runner" / "validate_case_rubrics.py")],
            cwd=ROOT,
            check=True,
        )
    tasks = load_tasks(args.task_id)
    if args.prepare_only:
        print(json.dumps({"status": "ready", "groups": list(args.groups), "tasks": len(tasks)}, ensure_ascii=False))
        return 0
    if not os.environ.get("LLM_API_KEY"):
        raise SystemExit("LLM_API_KEY is not present in this process")
    if args.timeout != TASK_TIMEOUT_SECONDS:
        raise SystemExit(f"scripted comparison timeout must remain {TASK_TIMEOUT_SECONDS} seconds")
    if args.resume:
        RUN_ROOT.mkdir(parents=True, exist_ok=True)
    else:
        safe_reset()

    proxy: subprocess.Popen[str] | None = None
    proxy_out = None
    proxy_err = None
    try:
        if any(group.startswith("codex") for group in args.groups):
            proxy_dir = RUN_ROOT / "proxy"
            proxy_dir.mkdir(exist_ok=True)
            proxy_env = os.environ.copy()
            proxy_env.update(
                {
                    "CODEX_DEEPSEEK_PROXY_HOST": "0.0.0.0",
                    "CODEX_DEEPSEEK_PROXY_PORT": str(PROXY_PORT),
                    "CODEX_PROXY_TRACE": str(proxy_dir / "trace.jsonl"),
                    "LLM_MODEL_NAME": MODEL_NAME,
                }
            )
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
            runtime.wait_for_proxy(PROXY_PORT)

        jobs = [(group, task) for task in tasks for group in args.groups]
        if args.resume:
            jobs = [
                (group, task)
                for group, task in jobs
                if not _is_reusable(group, task["id"], args.timeout)
            ]
            for group, task in jobs:
                archive_retry_task(group, task["id"], args.retry_reason)
        with ThreadPoolExecutor(max_workers=max(1, min(args.workers, len(jobs) or 1))) as executor:
            futures = {
                executor.submit(run_one, group, task, args.timeout): (group, task["id"])
                for group, task in jobs
            }
            for future in as_completed(futures):
                print(json.dumps(future.result(), ensure_ascii=False), flush=True)
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

    _write_summary(tasks)
    failures: list[dict[str, Any]] = []
    for group in args.groups:
        for task in tasks:
            path = RUN_ROOT / group / task["id"] / "run_result.json"
            value = _load_run_result(path)
            if not _run_result_accepted(value, args.timeout):
                failures.append({"group": group, "task_id": task["id"], "result": value})
    if failures:
        print(json.dumps({"status": "failed", "failures": failures}, ensure_ascii=False), flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
