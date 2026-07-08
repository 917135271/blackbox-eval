from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from gate2_candidate_check import ROOT, candidate_registry, load_eval_config


FIXTURE_FILES = [
    ROOT / "fixtures" / "policy_query_mcp.py",
    ROOT / "fixtures" / "expense_query_mcp.py",
    ROOT / "fixtures" / "audit_role_prompt.md",
    ROOT / "fixtures" / "output_contract.md",
]


def sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_grades(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def artifact_status(run_root: Path, grade: dict[str, Any]) -> dict[str, bool]:
    run_path = ROOT / grade["run_path"]
    required = {
        "stdout.log": run_path / "stdout.log",
        "stderr.log": run_path / "stderr.log",
        "tool_calls.jsonl": run_path / "tool_calls.jsonl",
        "trajectory.json": run_path / "trajectory.json",
        "result.json": run_path / "result.json",
        "workdir_diff.txt": run_path / "workdir_diff.txt",
    }
    return {name: path.exists() for name, path in required.items()}


def pct(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "n/a"
    return f"{numerator / denominator:.0%}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate blackbox eval report.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-name", default="gate3_smoke_report.md")
    args = parser.parse_args()

    config = load_eval_config()
    run_root = Path(config["paths"]["runs_dir"]) / args.run_id
    manifest = read_json(run_root / "manifest.json")
    grades = load_grades(run_root / "grades.jsonl")
    output_dir = Path(config["paths"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / args.output_name
    run_report_path = run_root / "report.md"

    total = len(grades)
    passed = sum(1 for row in grades if row.get("score") == 1.0)
    format_ok = sum(1 for row in grades if not row.get("format_failure"))
    clean_workdir = sum(1 for row in grades if row.get("workdir_diff_empty"))
    failure_layers = Counter(row.get("failure_layer") or "ok" for row in grades)
    candidates = candidate_registry()
    candidate = candidates[manifest["candidate"]]

    lines = [
        "# GATE 3 Smoke Report",
        "",
        f"- run_id: `{args.run_id}`",
        f"- generated_at: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- candidate: `{manifest['candidate']}`",
        f"- candidate_version: `{candidate.version}`",
        f"- model_endpoint: `{config['model']['base_url']}`",
        f"- model: `{config['model']['model']}`",
        "- baseline_note: current endpoint is the user-approved DeepSeek cloud API, not the original local-only target.",
        f"- tasks: `{', '.join(manifest.get('tasks', []))}`",
        "",
        "## Fixture Hashes",
        "",
    ]
    for path in FIXTURE_FILES:
        lines.append(f"- `{path.relative_to(ROOT)}`: `{sha256(path)}`")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- score: `{passed}/{total}`",
            f"- format_follow_rate: `{pct(format_ok, total)}`",
            f"- clean_workdir_rate: `{pct(clean_workdir, total)}`",
            f"- failure_layers: `{dict(failure_layers)}`",
            "",
            "## Task Results",
            "",
            "| task | kind | score | format | tool_calls | elapsed_s | workdir | failure |",
            "| --- | --- | ---: | --- | ---: | ---: | --- | --- |",
        ]
    )
    for row in grades:
        lines.append(
            "| {task_id} | {kind} | {score:.1f} | {fmt} | {tool_calls} | {elapsed} | {workdir} | {failure} |".format(
                task_id=row.get("task_id"),
                kind=row.get("kind"),
                score=float(row.get("score", 0.0)),
                fmt="ok" if not row.get("format_failure") else "fail",
                tool_calls=row.get("tool_calls_count"),
                elapsed=row.get("elapsed_seconds"),
                workdir="clean" if row.get("workdir_diff_empty") else "changed",
                failure=row.get("failure_layer") or "ok",
            )
        )
    lines.extend(["", "## Grade Details", ""])
    for row in grades:
        if row.get("kind") == "expected_facts":
            details = ", ".join(
                f"{item['fact']}={'hit' if item['hit'] else 'miss'}"
                for item in row.get("fact_hits", [])
            )
            lines.append(
                f"- `{row['task_id']}`: facts `{details}`; citation_ok `{row.get('citation_ok')}`"
            )
        else:
            lines.append(
                f"- `{row['task_id']}`: expected `{row.get('expected_anomaly_ids')}`; "
                f"predicted `{row.get('predicted_anomaly_ids')}`; "
                f"precision `{row.get('precision')}`; recall `{row.get('recall')}`"
            )
    lines.extend(["", "## Artifact Completeness", ""])
    for row in grades:
        status = artifact_status(run_root, row)
        missing = [name for name, ok in status.items() if not ok]
        lines.append(f"- `{row['task_id']}`: {'ok' if not missing else 'missing ' + ', '.join(missing)}")
    lines.extend(
        [
            "",
            "## Manual Check Point",
            "",
            "This GATE 3 report is the human confirmation point for deterministic grading before GATE 4 full baseline.",
        ]
    )

    text = "\n".join(lines) + "\n"
    report_path.write_text(text, encoding="utf-8")
    run_report_path.write_text(text, encoding="utf-8")
    print(report_path)
    return 0 if total > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
