from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "runner" / "report_gate5_results.py"
SPEC = importlib.util.spec_from_file_location("report_gate5_results", MODULE_PATH)
assert SPEC and SPEC.loader
report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(report)


def test_linear_lower_score() -> None:
    assert report.linear_lower_score(100, 180, 900) == 100
    assert report.linear_lower_score(900, 180, 900) == 0
    assert report.linear_lower_score(540, 180, 900) == 50


def test_display_group() -> None:
    assert report.display_group("ccb-enhanced") == "Claude Code Best 增强组"
    assert report.display_group("oh-my-pi-baseline") == "Oh My Pi 基线组"


def test_math_index() -> None:
    assert report.math_index(15, 0.95) == 14
