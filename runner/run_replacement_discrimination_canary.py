from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_gate3_development as runtime  # noqa: E402
from formal_eval_plan import GROUPS  # noqa: E402


FORMAL = ROOT / "data" / "formal_case_rubric"
RUN_ROOT = ROOT / "runs" / "gate3_replacement_canary"
CASE_IDS = ("PV-CASE-001", "RA-CASE-001", "RA-CASE-002", "RR-CASE-001")


def load_tasks(task_ids: list[str]) -> list[dict[str, Any]]:
    tasks = json.loads((FORMAL / "evals.json").read_text(encoding="utf-8"))
    selected_ids = set(task_ids or CASE_IDS)
    selected = [
        {**task, "prompt": task["prompt_variants"]["precise"]}
        for task in tasks
        if task["id"] in selected_ids
    ]
    missing = sorted(selected_ids - {task["id"] for task in selected})
    if missing:
        raise ValueError(f"unknown replacement case IDs: {missing}")
    return selected


def safe_reset() -> None:
    target = RUN_ROOT.resolve()
    expected = (ROOT / "runs").resolve()
    if target.parent != expected or target.name != "gate3_replacement_canary":
        raise ValueError(f"refusing to reset unexpected path: {target}")
    if target.exists():
        try:
            shutil.rmtree(target)
        except OSError:
            stale = expected / f"gate3_replacement_canary-stale-{int(time.time() * 1000)}"
            target.replace(stale)
    target.mkdir(parents=True, exist_ok=True)


def archive_retry_task(group: str, task_id: str) -> None:
    if group not in GROUPS or task_id not in CASE_IDS:
        raise ValueError(f"invalid replacement Canary retry target: {group}/{task_id}")
    source = (RUN_ROOT / group / task_id).resolve()
    if source.parent != (RUN_ROOT / group).resolve() or not source.exists():
        return
    history = RUN_ROOT / "retry-history" / group / task_id
    history.mkdir(parents=True, exist_ok=True)
    index = 1
    while (history / f"attempt-{index}").exists():
        index += 1
    shutil.move(str(source), str(history / f"attempt-{index}"))


def task_prompt(task: dict[str, Any], enhanced: bool, framework: str | None = None) -> str:
    mode = "领域增强组" if enhanced else "原生基线组"
    workflow = (
        "遵循已安装的证券费用审计Skills，按需使用Checkpoint、子智能体、证据复核和结果校验。"
        if enhanced
        else "不得调用领域Skills或子智能体，使用框架基础工具、业务MCP和统一提交工具完成。"
    )
    return f"""你正在执行GATE3新正式题区分度Canary，该运行只用于冻结前验证，不进入正式排名。当前为{mode}。

任务ID：{task['id']}
题型：{task['category']}
问题：{task['prompt']}

{workflow}

要求：
1. 必须查询制度和只读业务库后作答，可以使用Shell、Python、SQLite和当前隔离工作区文件。
2. 禁止读取 ground_truth、cases.json、Rubric、判卷代码、历史答案、其他任务或候选轨迹，也不得访问无关互联网。
3. 有异常时，record_ids只包含参与本题违规的记录；无异常时仍保留直接核查或结论覆盖的记录，并在answer中明确写“无异常”。
4. work目录下三个JSON已按共享Schema预置字段骨架，只更新字段值和必要的evidence_rows，不得删除、改名或另建替代格式。validation_report必须保留status="pass"、空errors、空warnings、field_checks、id_checks、evidence_checks、answer_consistency_checks、repair_count=0、空repairable_fields和submission_allowed=true；字段名不是allow_submission。
5. 使用result_path="work/final_result.json"及两个默认报告路径调用validate_audit_result；取得valid=true后，以相同result_path调用submit_audit_result。提交工具返回repair_required时最多修复一次，返回rejected后不得重试。
6. 不得打印最终JSON代替统一提交。提交成功后只输出GATE3_CANARY_PASS；无法提交时只输出GATE3_CANARY_FAIL。
"""


def configure_runtime() -> None:
    runtime.DEV_DB = FORMAL / "expense_formal.db"
    runtime.RUN_ROOT = RUN_ROOT
    runtime.load_tasks = load_tasks
    runtime.safe_reset = safe_reset
    runtime.archive_retry_task = archive_retry_task
    runtime.task_prompt = task_prompt


def main() -> int:
    configure_runtime()
    return runtime.main()


if __name__ == "__main__":
    raise SystemExit(main())
