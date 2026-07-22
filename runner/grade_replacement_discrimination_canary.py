from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import grade_gate5_rubrics as grader  # noqa: E402
from formal_eval_plan import GROUPS  # noqa: E402
from run_replacement_discrimination_canary import CASE_IDS, RUN_ROOT  # noqa: E402


def main() -> int:
    grader.RUN_ROOT = RUN_ROOT
    grader.GRADE_ROOT = RUN_ROOT / "judge_v7"
    grader.GRADES_PATH = RUN_ROOT / "grades_v7.jsonl"
    grader.GROUPS = GROUPS
    if "--task-id" not in sys.argv:
        for task_id in CASE_IDS:
            sys.argv.extend(["--task-id", task_id])
    return grader.main()


if __name__ == "__main__":
    raise SystemExit(main())
