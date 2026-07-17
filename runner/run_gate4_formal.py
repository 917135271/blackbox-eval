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
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_gate3_development as runtime  # noqa: E402


FORMAL = ROOT / "data" / "formal_case_rubric"
RUN_ROOT = ROOT / "runs" / "gate4_formal"
FREEZE_PATH = ROOT / "config" / "gate3_frozen_lock.json"
GROUPS = runtime.GROUPS


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_frozen_configuration() -> dict[str, Any]:
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    for relative, expected in freeze.get("files", {}).items():
        path = ROOT / relative
        if not path.exists():
            errors.append(f"missing:{relative}")
        elif _sha256(path) != expected:
            errors.append(f"hash_mismatch:{relative}")
    if freeze.get("formal_task_count_per_group") != 15:
        errors.append("formal_task_count_per_group")
    if freeze.get("task_timeout_seconds") != 900:
        errors.append("task_timeout_seconds")
    if tuple(freeze.get("groups", [])) != GROUPS:
        errors.append("groups")
    if errors:
        raise RuntimeError("GATE3 frozen configuration verification failed: " + ", ".join(errors))
    return freeze


def load_tasks(task_ids: list[str]) -> list[dict[str, Any]]:
    raw_tasks = json.loads((FORMAL / "evals.json").read_text(encoding="utf-8"))
    tasks = [
        {
            **task,
            "prompt": task["prompt_variants"]["precise"],
        }
        for task in raw_tasks
    ]
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
    if target.parent != expected or target.name != "gate4_formal":
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
            stale = expected / f"gate4_formal-stale-{int(time.time() * 1000)}"
            if stale.parent != expected or not stale.name.startswith("gate4_formal-stale-"):
                raise ValueError(f"refusing to archive unexpected path: {stale}")
            target.replace(stale)
    target.mkdir(parents=True)


def archive_retry_task(group: str, task_id: str) -> Path | None:
    valid_task_ids = {task["id"] for task in load_tasks([])}
    if group not in GROUPS or task_id not in valid_task_ids:
        raise ValueError(f"invalid retry target: {group}/{task_id}")
    source = (RUN_ROOT / group / task_id).resolve()
    expected_parent = (RUN_ROOT / group).resolve()
    if source.parent != expected_parent or source.name != task_id or not source.exists():
        return None
    history = RUN_ROOT / "retry-history" / group / task_id
    history.mkdir(parents=True, exist_ok=True)
    index = 1
    while (history / f"attempt-{index}").exists():
        index += 1
    destination = history / f"attempt-{index}"
    shutil.move(str(source), str(destination))
    return destination


def register_retry(*, group: str, task_id: str, attempt_path: Path, reason: str) -> None:
    registry = RUN_ROOT / "retry_registry.jsonl"
    entry = {
        "group": group,
        "task_id": task_id,
        "attempt_path": attempt_path.relative_to(ROOT).as_posix(),
        "reason": reason,
        "registered_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "classification": "infrastructure",
    }
    with registry.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")


def task_prompt(task: dict[str, Any], enhanced: bool, framework: str | None = None) -> str:
    mode = "领域增强组" if enhanced else "原生基线组"
    workflow = (
        "必须遵循已安装的证券费用审计 Skills；先规划并记录Checkpoint，再按触发条件调查、复核、校验并通过统一工具提交。若复杂度至少为2且存在符合路由规则的角色，必须先授权原生子智能体，并在角色结束后登记结构化摘要和产物。"
        if enhanced
        else "不得调用领域 Skills 或子智能体；使用框架基础工具、业务 MCP 和统一提交工具独立完成。"
    )
    framework_hint = (
        "OpenClaude运行时只保证Bash、Edit、Read可用；必须使用Edit或Bash中的安全脚本更新预置JSON，禁止调用Write、Grep等未暴露工具。"
        if framework == "openclaude"
        else ""
    )
    return f"""你正在执行 GATE4 正式证券费用审计评测，当前为{mode}。

任务ID：{task['id']}
题型：{task['category']}
问题：{task['prompt']}

{workflow}
{framework_hint}

要求：
1. 必须查询制度和只读业务库后作答，可以使用 Shell、Python、SQLite 和当前工作区临时文件。
2. 只处理当前独立任务。禁止读取 ground_truth、cases.json、Rubric、判卷代码、历史答案、其他任务或候选轨迹，也不得访问与题目无关的互联网。
3. anomaly_ids 必须与审计发现一一对应、稳定且类型明确；不得为了迎合未知答案猜测隐藏编号。record_ids 必须完整、准确且只覆盖本题范围。
4. 有异常时，record_ids 只包含参与本题所问违规的记录，不含累计计算背景、有效豁免或无关规则记录；无异常时仍保留题目直接核查或结论覆盖的记录，并在 answer 中明确写“无异常”。
5. 必须维护 work/final_result.json、work/evidence_matrix.json 和 work/validation_report.json 三个预置文件。对应Schema的绝对路径分别是 /runtime-schemas/final_result.schema.json、/runtime-schemas/evidence_matrix.schema.json 和 /runtime-schemas/validation_report.schema.json；当前工作区兼容路径分别是 /workspace/runtime-schemas/final_result.schema.json、/workspace/runtime-schemas/evidence_matrix.schema.json 和 /workspace/runtime-schemas/validation_report.schema.json。当前目录已经是 /workspace，禁止拼成 /workspace/workspace，也禁止把 .schema.json 猜成普通 .json。
6. 先调用 audit_control.validate_audit_result；取得 valid=true 后，再以 result_path="work/final_result.json" 调用 audit_control.submit_audit_result。不得把完整结果直接打印出来代替提交。
7. 提交成功后最终只输出 GATE4_TASK_PASS；无法提交时只输出 GATE4_TASK_FAIL。
"""


def configure_runtime() -> None:
    runtime.DEV = FORMAL
    runtime.DEV_DB = ROOT / "data" / "expense.db"
    runtime.RUN_ROOT = RUN_ROOT
    runtime.load_tasks = load_tasks
    runtime.safe_reset = safe_reset
    runtime.archive_retry_task = archive_retry_task
    runtime.task_prompt = task_prompt


def collect_full_results() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for group in GROUPS:
        for task in load_tasks([]):
            path = RUN_ROOT / group / task["id"] / "run_result.json"
            if path.exists():
                results.append(json.loads(path.read_text(encoding="utf-8")))
    results.sort(key=lambda item: (item["group"], item["task_id"]))
    return results


def write_full_run_summary() -> list[dict[str, Any]]:
    results = collect_full_results()
    summary = {
        "gate": "GATE4",
        "groups": list(GROUPS),
        "tasks": [task["id"] for task in load_tasks([])],
        "runs": results,
    }
    runtime.write_text(
        RUN_ROOT / "run_summary.json",
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
    )
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--groups", nargs="+", choices=GROUPS, default=list(GROUPS))
    parser.add_argument("--task-id", action="append", default=[])
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--retry-reason", default="")
    args = parser.parse_args()

    if not os.environ.get("LLM_API_KEY"):
        raise SystemExit("LLM_API_KEY is not present in this process")
    if args.force and not args.resume:
        raise SystemExit("--force requires --resume")
    if args.resume and not args.retry_reason:
        raise SystemExit("--resume requires --retry-reason for the formal rerun registry")
    freeze = verify_frozen_configuration()
    if args.timeout != int(freeze["task_timeout_seconds"]):
        raise SystemExit("GATE4 timeout must match the frozen 900-second budget")

    configure_runtime()
    if args.resume:
        RUN_ROOT.mkdir(parents=True, exist_ok=True)
    else:
        safe_reset()
    subprocess.run(
        [sys.executable, str(ROOT / "runner" / "validate_case_rubrics.py")],
        cwd=ROOT,
        check=True,
    )
    subprocess.run([sys.executable, str(runtime.DOMAIN / "build_adapters.py")], cwd=ROOT, check=True)
    tasks = load_tasks(args.task_id)
    baseline_runtime = runtime.prepare_baseline_runtime()

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
                    "CODEX_DEEPSEEK_PROXY_PORT": str(runtime.PROXY_PORT),
                    "CODEX_PROXY_TRACE": str(proxy_dir / "trace.jsonl"),
                    "LLM_MODEL_NAME": "deepseek-v4-pro",
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
            runtime.wait_for_proxy(runtime.PROXY_PORT)

        jobs = [(group, task) for task in tasks for group in args.groups]
        if args.resume:
            pending = []
            for group, task in jobs:
                result_path = RUN_ROOT / group / task["id"] / "run_result.json"
                result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else {}
                if not args.force and runtime.is_reusable_result(result, args.timeout):
                    continue
                attempt_path = archive_retry_task(group, task["id"])
                if attempt_path is not None:
                    register_retry(
                        group=group,
                        task_id=task["id"],
                        attempt_path=attempt_path,
                        reason=args.retry_reason,
                    )
                pending.append((group, task))
            jobs = pending

        with ThreadPoolExecutor(max_workers=max(1, min(args.workers, len(jobs) or 1))) as executor:
            futures = {
                executor.submit(runtime.run_one, group, task, baseline_runtime, args.timeout): (
                    group,
                    task["id"],
                )
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

    write_full_run_summary()
    results = [
        result
        for result in collect_full_results()
        if result["group"] in args.groups
        and result["task_id"] in {task["id"] for task in tasks}
    ]
    expected = len(args.groups) * len(tasks)
    passed = len(results) == expected and all(
        item["submission_status"] == "accepted"
        and not item["timed_out"]
        and float(item["elapsed_seconds"]) <= args.timeout
        for item in results
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
