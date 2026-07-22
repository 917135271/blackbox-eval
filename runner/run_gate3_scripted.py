from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import run_gate4_scripted as scripted


ROOT = Path(__file__).resolve().parents[1]


def configure() -> None:
    scripted.FORMAL = ROOT / "data" / "development"
    scripted.DATA_DB = scripted.FORMAL / "expense_dev.db"
    scripted.RUN_ROOT = ROOT / "runs" / "gate3_scripted"
    scripted.RUN_ROOT_BASENAME = "gate3_scripted"
    scripted.GATE_LABEL = "GATE3脚本化增强开发题Canary"
    scripted.SUMMARY_GATE = "GATE3_SCRIPTED_CANARY"
    scripted.COMPARISON_SOURCE = "runs/gate3_development"
    scripted.VALIDATE_FORMAL_RUBRICS = False
    scripted.REQUIRE_SCRIPTED_FREEZE = False


if __name__ == "__main__":
    configure()
    subprocess.run(
        [sys.executable, str(scripted.FORMAL / "build_dev_dataset.py")],
        cwd=ROOT,
        check=True,
    )
    exit_code = scripted.main()
    if exit_code == 0:
        scripted.write_scripted_freeze()
    raise SystemExit(exit_code)
