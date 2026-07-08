from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from gate2_candidate_check import ROOT, load_eval_config


REQUIRED_FILES = [
    "stdout.log",
    "stderr.log",
    "tool_calls.jsonl",
    "trajectory.json",
    "result.json",
    "workdir_diff.txt",
]


def load_grades(run_root: Path) -> list[dict[str, Any]]:
    grades_path = run_root / "grades.jsonl"
    if not grades_path.exists():
        return []
    return [json.loads(line) for line in grades_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def pct(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "n/a"
    return f"{numerator / denominator:.0%}"


def artifact_status(grade: dict[str, Any]) -> tuple[bool, list[str]]:
    task_dir = ROOT / grade["run_path"]
    missing = [name for name in REQUIRED_FILES if not (task_dir / name).exists()]
    return not missing, missing


def summarize_candidate(candidate: str, run_id: str, grades: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(grades)
    passed = sum(1 for row in grades if row.get("score") == 1.0)
    format_ok = sum(1 for row in grades if not row.get("format_failure"))
    clean_workdir = sum(1 for row in grades if row.get("workdir_diff_empty"))
    tool_calls = sum(int(row.get("tool_calls_count") or 0) for row in grades)
    complete = sum(1 for row in grades if artifact_status(row)[0])
    failures = Counter(row.get("failure_layer") or "ok" for row in grades)
    return {
        "candidate": candidate,
        "run_id": run_id,
        "total": total,
        "passed": passed,
        "format_ok": format_ok,
        "clean_workdir": clean_workdir,
        "tool_calls": tool_calls,
        "complete": complete,
        "failures": dict(failures),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate aggregate GATE 3 smoke report.")
    parser.add_argument(
        "--run",
        action="append",
        required=True,
        help="Candidate/run pair, for example goose=gate3_smoke_goose_v2",
    )
    parser.add_argument("--output-name", default="gate3_all_candidates_smoke_report.md")
    args = parser.parse_args()

    config = load_eval_config()
    runs_dir = Path(config["paths"]["runs_dir"])
    output_dir = Path(config["paths"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    all_grades: list[dict[str, Any]] = []
    summaries = []
    run_pairs: list[tuple[str, str]] = []
    for raw in args.run:
        if "=" not in raw:
            raise SystemExit(f"invalid --run value {raw!r}; use candidate=run_id")
        candidate, run_id = raw.split("=", 1)
        run_pairs.append((candidate, run_id))
        grades = load_grades(runs_dir / run_id)
        all_grades.extend(grades)
        summaries.append(summarize_candidate(candidate, run_id, grades))

    lines = [
        "# GATE 3 All Candidates Smoke Report",
        "",
        f"- generated_at: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- model_endpoint: `{config['model']['base_url']}`",
        f"- model: `{config['model']['model']}`",
        "- scope: each candidate ran `L1-001`, `L1-002`, `L1-003` with the same prompt variant `precise`.",
        "- baseline_note: current endpoint is the user-approved DeepSeek cloud API, not the original local-only target.",
        "",
        "## Candidate Summary",
        "",
        "| candidate | run_id | score | format | tool_calls | clean_workdir | artifacts | failures |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for item in summaries:
        lines.append(
            "| {candidate} | `{run_id}` | {passed}/{total} | {format_ok} | {tool_calls} | {clean} | {complete}/{total} | `{failures}` |".format(
                candidate=item["candidate"],
                run_id=item["run_id"],
                passed=item["passed"],
                total=item["total"],
                format_ok=pct(item["format_ok"], item["total"]),
                tool_calls=item["tool_calls"],
                clean=pct(item["clean_workdir"], item["total"]),
                complete=item["complete"],
                failures=item["failures"],
            )
        )

    lines.extend(
        [
            "",
            "## Task Detail",
            "",
            "| candidate | task | score | format | tool_calls | elapsed_s | workdir | failure |",
            "| --- | --- | ---: | --- | ---: | ---: | --- | --- |",
        ]
    )
    for row in sorted(all_grades, key=lambda item: (item.get("candidate", ""), item.get("task_id", ""))):
        lines.append(
            "| {candidate} | {task_id} | {score:.1f} | {fmt} | {tool_calls} | {elapsed} | {workdir} | {failure} |".format(
                candidate=row.get("candidate"),
                task_id=row.get("task_id"),
                score=float(row.get("score", 0.0)),
                fmt="ok" if not row.get("format_failure") else "fail",
                tool_calls=row.get("tool_calls_count"),
                elapsed=row.get("elapsed_seconds"),
                workdir="clean" if row.get("workdir_diff_empty") else "changed",
                failure=row.get("failure_layer") or "ok",
            )
        )

    lines.extend(["", "## Notes", ""])
    lines.append(
        "- `qwen-code`: uses the official headless `--system-prompt` path plus MCP task-log injection. It may still emit explanatory text before a JSON block; the deterministic format metric is based on parseable JSON extraction."
    )
    lines.append(
        "- `opencode`: uses an official custom primary agent plus permission denies for native file/project/shell tools and explicit allows for benchmark MCP namespaces."
    )
    lines.append(
        "- `trae-agent`: requires local engineering patches for YAML `system_prompt`, async cleanup, and `task_done.result` promotion. It is therefore an engineering-usable baseline, not a strict unmodified vendor baseline."
    )
    lines.append(
        "- `goose`: uses extension-based MCP wiring and no candidate source patch."
    )

    lines.extend(["", "## Artifact Notes", ""])
    for row in sorted(all_grades, key=lambda item: (item.get("candidate", ""), item.get("task_id", ""))):
        ok, missing = artifact_status(row)
        lines.append(
            f"- `{row.get('candidate')}/{row.get('task_id')}`: {'ok' if ok else 'missing ' + ', '.join(missing)}"
        )

    output_path = output_dir / args.output_name
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
