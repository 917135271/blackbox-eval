from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "data" / "formal_case_rubric" / "cases.json"
OUTPUT_PATH = ROOT / "output" / "formal_cases_and_rubrics_v7.md"


def compact(value: Any) -> str:
    if isinstance(value, str):
        return value.replace("|", "\\|")
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("|", "\\|")


def render(dataset: dict[str, Any]) -> str:
    lines = [
        f"# 正式题与逐题Rubric：{dataset['dataset_id']}",
        "",
        f"Rubric版本：`{dataset['rubric_version']}`。本文件由`runner/render_formal_cases.py`从冻结JSON生成。",
        "",
    ]
    for case in dataset["cases"]:
        lines.extend(
            [
                f"## {case['id']}：{case['case_family']}",
                "",
                f"**题目：** {case['prompt']}",
                "",
                f"**选题目的：** {case['selection_reason']}",
                "",
                "| ID | 维度 | 判定方式 | 检查内容 | 通过条件 |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for criterion in case["rubric"]["checklist"]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{criterion['id']}`",
                        f"`{criterion['metric']}`",
                        f"`{criterion['evaluation_mode']}`",
                        compact(criterion["check"]),
                        compact(criterion["pass_condition"]),
                    ]
                )
                + " |"
            )
        failures = case["rubric"].get("critical_failures", [])
        if failures:
            lines.extend(
                [
                    "",
                    "**严重错误封顶：**",
                    "",
                    "| ID | 条件 | 分数上限 |",
                    "| --- | --- | ---: |",
                ]
            )
            for failure in failures:
                lines.append(
                    f"| `{failure['id']}` | {compact(failure['check'])} | {failure['score_cap']} |"
                )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the frozen formal cases and Rubrics.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render(json.loads(CASES_PATH.read_text(encoding="utf-8")))
    if args.check:
        if not OUTPUT_PATH.exists() or OUTPUT_PATH.read_text(encoding="utf-8") != expected:
            raise SystemExit(f"stale generated file: {OUTPUT_PATH}")
        print(json.dumps({"status": "pass", "path": str(OUTPUT_PATH)}, ensure_ascii=False))
        return 0
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(expected, encoding="utf-8")
    print(json.dumps({"status": "built", "path": str(OUTPUT_PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
