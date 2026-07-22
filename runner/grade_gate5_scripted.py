from __future__ import annotations

from pathlib import Path

import grade_gate5_rubrics as grader


ROOT = Path(__file__).resolve().parents[1]
SCRIPTED_GROUPS = (
    "ccb-scripted-enhanced",
    "codex-scripted-enhanced",
    "openclaude-scripted-enhanced",
    "opencode-scripted-enhanced",
    "oh-my-pi-scripted-enhanced",
    "pi-agent-scripted-enhanced",
)
RUN_ROOT = ROOT / "runs" / "gate4_scripted"


def configure() -> None:
    grader.RUN_ROOT = RUN_ROOT
    grader.GRADE_ROOT = RUN_ROOT / "gate5_judge_v7"
    grader.GRADES_PATH = RUN_ROOT / "gate5_grades_v7.jsonl"
    grader.GROUPS = SCRIPTED_GROUPS


if __name__ == "__main__":
    configure()
    raise SystemExit(grader.main())
