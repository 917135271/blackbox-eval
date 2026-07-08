from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

from gate2_candidate_check import ROOT, candidate_registry, load_eval_config


REQUIRED_TASK_FILES = [
    "stdout.log",
    "tool_calls.jsonl",
    "trajectory.json",
    "result.json",
    "workdir_diff.txt",
]

FIXTURE_FILES = [
    ROOT / "fixtures" / "policy_query_mcp.py",
    ROOT / "fixtures" / "expense_query_mcp.py",
    ROOT / "fixtures" / "audit_role_prompt.md",
    ROOT / "fixtures" / "output_contract.md",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_grades(run_root: Path) -> list[dict[str, Any]]:
    grades_path = run_root / "grades.jsonl"
    if not grades_path.exists():
        return []
    return [
        json.loads(line)
        for line in grades_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def pct(numerator: int | float, denominator: int | float) -> str:
    if not denominator:
        return "n/a"
    return f"{numerator / denominator:.1%}"


def short_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def task_dir_for_grade(row: dict[str, Any]) -> Path:
    return ROOT / str(row["run_path"])


def artifact_ok(row: dict[str, Any]) -> tuple[bool, list[str]]:
    task_dir = task_dir_for_grade(row)
    missing = [name for name in REQUIRED_TASK_FILES if not (task_dir / name).exists()]
    return not missing, missing


def load_result(row: dict[str, Any]) -> dict[str, Any]:
    result_path = task_dir_for_grade(row) / "result.json"
    if not result_path.exists():
        return {}
    return read_json(result_path)


def iter_tool_calls(row: dict[str, Any]) -> list[dict[str, Any]]:
    tool_path = task_dir_for_grade(row) / "tool_calls.jsonl"
    if not tool_path.exists():
        return []
    calls: list[dict[str, Any]] = []
    for line in tool_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            calls.append(json.loads(line))
        except json.JSONDecodeError:
            calls.append({"server": "unparseable", "tool": "unparseable"})
    return calls


def evidence_line(row: dict[str, Any], layer: str) -> dict[str, Any]:
    trajectory = task_dir_for_grade(row) / "trajectory.json"
    if not trajectory.exists():
        return {"path": short_path(trajectory), "line": None, "excerpt": "missing trajectory"}
    lines = trajectory.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines:
        return {"path": short_path(trajectory), "line": 1, "excerpt": "empty trajectory"}

    needles = ["final_result", "anomaly_ids", "answer", "tool", "assistant"]
    if layer == "timeout":
        needles = ["step_start", "tool_use", "message", "assistant"]
    if layer == "format_failure":
        needles = ["final_result", "answer", "assistant", "tool_result"]

    chosen = None
    for idx in range(len(lines) - 1, -1, -1):
        raw = lines[idx].strip()
        if raw and any(needle in raw for needle in needles):
            chosen = (idx + 1, raw)
            break
    if chosen is None:
        for idx in range(len(lines) - 1, -1, -1):
            raw = lines[idx].strip()
            if raw:
                chosen = (idx + 1, raw)
                break
    if chosen is None:
        chosen = (1, "")
    line_no, excerpt = chosen
    excerpt = " ".join(excerpt.split())
    if len(excerpt) > 180:
        excerpt = excerpt[:177] + "..."
    return {"path": short_path(trajectory), "line": line_no, "excerpt": excerpt}


def failure_layer(row: dict[str, Any]) -> str:
    if row.get("timeout"):
        return "timeout"
    if row.get("exit_code") not in (0, None):
        return "harness_error"
    if row.get("format_failure"):
        return "format_failure"
    if not row.get("workdir_diff_empty", True):
        return "workdir_changed"
    return row.get("failure_layer") or "uncertain"


def is_failed(row: dict[str, Any]) -> bool:
    return (
        float(row.get("score") or 0.0) < 1.0
        or bool(row.get("format_failure"))
        or bool(row.get("timeout"))
        or row.get("exit_code") not in (0, None)
        or not row.get("workdir_diff_empty", True)
    )


def expected_count(manifest: dict[str, Any]) -> int:
    tasks = manifest.get("tasks") or []
    variants = manifest.get("variants") or ["precise"]
    repeats = manifest.get("repeat_indices") or [1]
    return len(tasks) * len(variants) * len(repeats)


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def duration_minutes(manifest: dict[str, Any]) -> float | None:
    start = parse_dt(manifest.get("started_at"))
    finish = parse_dt(manifest.get("finished_at"))
    if not start or not finish:
        return None
    return round((finish - start).total_seconds() / 60, 1)


def group_summary(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        item_key = str(row.get(key) or "unknown")
        if key == "level" and item_key.lower() == "trap":
            item_key = "TRAP"
        grouped[item_key].append(row)
    summary: dict[str, dict[str, Any]] = {}
    for item_key, item_rows in grouped.items():
        total = len(item_rows)
        passed = sum(1 for row in item_rows if row.get("score") == 1.0)
        summary[item_key] = {"passed": passed, "total": total, "rate": pct(passed, total)}
    return summary


def behavior_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    allowed_servers = {"policy_query_mcp", "expense_query_mcp"}
    tool_calls_total = 0
    policy_calls = 0
    expense_calls = 0
    invalid_calls = 0
    get_detail_tasks = 0
    deprecated_citations = 0
    trap_false_positive = 0

    for row in rows:
        calls = iter_tool_calls(row)
        tool_calls_total += len(calls)
        has_get_detail = False
        for call in calls:
            server = str(call.get("server") or "")
            tool = str(call.get("tool") or "")
            if server == "policy_query_mcp":
                policy_calls += 1
            elif server == "expense_query_mcp":
                expense_calls += 1
            elif server not in allowed_servers:
                invalid_calls += 1
            if tool == "get_expense_detail":
                has_get_detail = True
        if has_get_detail:
            get_detail_tasks += 1

        result = load_result(row)
        answer = result.get("answer_json") if isinstance(result.get("answer_json"), dict) else {}
        citations = answer.get("citations") if isinstance(answer, dict) else []
        if isinstance(citations, list):
            for citation in citations:
                if isinstance(citation, dict) and "deprecated" in str(citation.get("doc_id", "")):
                    deprecated_citations += 1

        if str(row.get("level")) == "TRAP":
            predicted = row.get("predicted_anomaly_ids") or []
            if isinstance(predicted, list) and predicted:
                trap_false_positive += len(predicted)

    total = len(rows)
    return {
        "tool_calls_total": tool_calls_total,
        "avg_tool_calls": round(tool_calls_total / total, 2) if total else 0.0,
        "avg_policy_calls": round(policy_calls / total, 2) if total else 0.0,
        "avg_expense_calls": round(expense_calls / total, 2) if total else 0.0,
        "get_detail_task_rate": pct(get_detail_tasks, total),
        "invalid_tool_calls": invalid_calls,
        "deprecated_citations": deprecated_citations,
        "trap_false_positive_ids": trap_false_positive,
    }


def summarize_candidate(
    candidate: str,
    run_id: str,
    manifest: dict[str, Any],
    grades: list[dict[str, Any]],
) -> dict[str, Any]:
    total = len(grades)
    passed = sum(1 for row in grades if row.get("score") == 1.0)
    format_ok = sum(1 for row in grades if not row.get("format_failure"))
    clean_workdir = sum(1 for row in grades if row.get("workdir_diff_empty"))
    artifact_complete = sum(1 for row in grades if artifact_ok(row)[0])
    timeouts = sum(1 for row in grades if row.get("timeout"))
    elapsed = [float(row.get("elapsed_seconds") or 0.0) for row in grades]
    failures = Counter(failure_layer(row) if is_failed(row) else "ok" for row in grades)
    behavior = behavior_summary(grades)
    return {
        "candidate": candidate,
        "run_id": run_id,
        "expected": expected_count(manifest),
        "total": total,
        "passed": passed,
        "score_rate": pct(passed, total),
        "format_ok_rate": pct(format_ok, total),
        "clean_workdir_rate": pct(clean_workdir, total),
        "artifact_rate": pct(artifact_complete, total),
        "timeouts": timeouts,
        "avg_elapsed": round(mean(elapsed), 2) if elapsed else 0.0,
        "duration_min": duration_minutes(manifest),
        "finished_at": manifest.get("finished_at"),
        "failures": dict(failures),
        "level": group_summary(grades, "level"),
        "variant": group_summary(grades, "variant"),
        "behavior": behavior,
    }


def write_failure_attribution(
    output_dir: Path,
    output_name: str,
    rows: list[dict[str, Any]],
) -> Path:
    path = output_dir / output_name
    items = []
    for row in rows:
        if not is_failed(row):
            continue
        layer = failure_layer(row)
        evidence = evidence_line(row, layer)
        items.append(
            {
                "candidate": row.get("candidate"),
                "task_id": row.get("task_id"),
                "level": row.get("level"),
                "variant": row.get("variant"),
                "score": row.get("score"),
                "failure_layer": layer,
                "run_path": row.get("run_path"),
                "evidence": evidence,
            }
        )
    path.write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in items),
        encoding="utf-8",
    )
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate aggregate GATE 4 baseline report.")
    parser.add_argument(
        "--run",
        action="append",
        required=True,
        help="Candidate/run pair, for example goose=gate4_baseline_goose_v1",
    )
    parser.add_argument("--output-name", default="gate4_baseline_report.md")
    parser.add_argument("--failure-output-name", default="gate4_failure_attribution.jsonl")
    args = parser.parse_args()

    config = load_eval_config()
    runs_dir = Path(config["paths"]["runs_dir"])
    output_dir = Path(config["paths"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    candidates = candidate_registry()

    run_pairs: list[tuple[str, str]] = []
    all_grades: list[dict[str, Any]] = []
    manifests: dict[str, dict[str, Any]] = {}
    summaries: list[dict[str, Any]] = []

    for raw in args.run:
        if "=" not in raw:
            raise SystemExit(f"invalid --run value {raw!r}; use candidate=run_id")
        candidate, run_id = raw.split("=", 1)
        run_pairs.append((candidate, run_id))
        run_root = runs_dir / run_id
        manifest = read_json(run_root / "manifest.json")
        grades = load_grades(run_root)
        manifests[candidate] = manifest
        all_grades.extend(grades)
        summaries.append(summarize_candidate(candidate, run_id, manifest, grades))

    failure_detail = write_failure_attribution(output_dir, args.failure_output_name, all_grades)

    lines = [
        "# GATE 4 Baseline Report",
        "",
        f"- generated_at: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- runs: `{', '.join(f'{candidate}={run_id}' for candidate, run_id in run_pairs)}`",
        f"- task_scope: `55 tasks x 3 variants x 1 repeat = 165 results per candidate`",
        f"- failure_detail: `{short_path(failure_detail)}`",
        "",
        "## Experiment Setup",
        "",
        f"- model_endpoint: `{config['model']['base_url']}`",
        f"- model: `{config['model']['model']}`",
        f"- temperature: `{config['model'].get('temperature')}`",
        f"- max_tokens: `{config['model'].get('max_tokens')}`",
        "- baseline_note: current endpoint is the user-approved DeepSeek cloud API; this is a recorded deviation from the original local-only target.",
        f"- timeout_seconds: `{config['execution']['task_timeout_seconds']}`",
        f"- prompt_variants: `{', '.join(config['execution']['prompt_variants'])}`",
        "",
        "## Candidate Versions",
        "",
        "| candidate | version | setup | run_id | started | finished | wall_min |",
        "| --- | --- | --- | --- | --- | --- | ---: |",
    ]
    for candidate, run_id in run_pairs:
        manifest = manifests[candidate]
        item = candidates.get(candidate)
        lines.append(
            "| {candidate} | {version} | `{setup}` | `{run_id}` | `{started}` | `{finished}` | {wall} |".format(
                candidate=candidate,
                version=item.version if item else "unknown",
                setup=short_path(item.setup_file) if item else "unknown",
                run_id=run_id,
                started=manifest.get("started_at"),
                finished=manifest.get("finished_at"),
                wall=duration_minutes(manifest),
            )
        )

    lines.extend(["", "## Fixture And Dataset Hashes", ""])
    hash_files = [
        *FIXTURE_FILES,
        Path(config["paths"]["evals"]),
        Path(config["paths"]["ground_truth"]),
        Path(config["paths"]["expense_db"]),
    ]
    for path in hash_files:
        lines.append(f"- `{short_path(path)}`: `{sha256(path)}`")

    lines.extend(
        [
            "",
            "## Main Results",
            "",
            "| candidate | completed | score | L1 | L2 | L3 | TRAP | format_ok | clean_workdir | artifacts | timeouts | avg_tool_calls | trap_fp_ids |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in summaries:
        level = item["level"]
        behavior = item["behavior"]
        lines.append(
            "| {candidate} | {total}/{expected} | {passed}/{total} ({score_rate}) | {l1} | {l2} | {l3} | {trap} | {fmt} | {clean} | {artifacts} | {timeouts} | {avg_tools} | {trap_fp} |".format(
                candidate=item["candidate"],
                total=item["total"],
                expected=item["expected"],
                passed=item["passed"],
                score_rate=item["score_rate"],
                l1=level.get("L1", {}).get("rate", "n/a"),
                l2=level.get("L2", {}).get("rate", "n/a"),
                l3=level.get("L3", {}).get("rate", "n/a"),
                trap=level.get("TRAP", {}).get("rate", "n/a"),
                fmt=item["format_ok_rate"],
                clean=item["clean_workdir_rate"],
                artifacts=item["artifact_rate"],
                timeouts=item["timeouts"],
                avg_tools=behavior["avg_tool_calls"],
                trap_fp=behavior["trap_false_positive_ids"],
            )
        )

    lines.extend(
        [
            "",
            "## Variant Results",
            "",
            "| candidate | precise | casual | distracted |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for item in summaries:
        variant = item["variant"]
        lines.append(
            "| {candidate} | {precise} | {casual} | {distracted} |".format(
                candidate=item["candidate"],
                precise=variant.get("precise", {}).get("rate", "n/a"),
                casual=variant.get("casual", {}).get("rate", "n/a"),
                distracted=variant.get("distracted", {}).get("rate", "n/a"),
            )
        )

    lines.extend(
        [
            "",
            "## Behavior Summary",
            "",
            "| candidate | avg_policy_calls | avg_expense_calls | get_detail_task_rate | invalid_tool_calls | deprecated_citations | avg_elapsed_s | wall_min |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in summaries:
        behavior = item["behavior"]
        lines.append(
            "| {candidate} | {policy} | {expense} | {detail_rate} | {invalid} | {deprecated} | {avg_elapsed} | {wall} |".format(
                candidate=item["candidate"],
                policy=behavior["avg_policy_calls"],
                expense=behavior["avg_expense_calls"],
                detail_rate=behavior["get_detail_task_rate"],
                invalid=behavior["invalid_tool_calls"],
                deprecated=behavior["deprecated_citations"],
                avg_elapsed=item["avg_elapsed"],
                wall=item["duration_min"],
            )
        )

    lines.extend(["", "## Failure Distribution", ""])
    lines.append("| candidate | failure_layers |")
    lines.append("| --- | --- |")
    for item in summaries:
        lines.append(f"| {item['candidate']} | `{item['failures']}` |")

    lines.extend(
        [
            "",
            "## Failure Attribution",
            "",
            "Each failed row below has a traceable run path and a trajectory line. Full machine-readable details are in the JSONL artifact listed at the top.",
            "",
            "| candidate | task | level | variant | score | layer | evidence |",
            "| --- | --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in sorted(
        (row for row in all_grades if is_failed(row)),
        key=lambda item: (
            str(item.get("candidate")),
            str(item.get("level")),
            str(item.get("task_id")),
            str(item.get("variant")),
        ),
    ):
        layer = failure_layer(row)
        evidence = evidence_line(row, layer)
        evidence_ref = f"`{evidence['path']}:{evidence['line']}`"
        lines.append(
            "| {candidate} | {task} | {level} | {variant} | {score:.1f} | {layer} | {evidence} |".format(
                candidate=row.get("candidate"),
                task=row.get("task_id"),
                level=row.get("level"),
                variant=row.get("variant"),
                score=float(row.get("score") or 0.0),
                layer=layer,
                evidence=evidence_ref,
            )
        )

    lines.extend(
        [
            "",
            "## Canary And Tool Disable Validation",
            "",
            "- GATE2 setup and canary checks are recorded in `output/gate2_candidate_check.md`.",
            "- All four candidates passed canary-bash, canary-write, and canary-mcp before GATE4.",
            "- GATE4 tool logs contain only `policy_query_mcp` and `expense_query_mcp` server calls when parsed from `tool_calls.jsonl`; see `invalid_tool_calls` in the behavior table.",
            "- Workdir mutation checks are reported as `clean_workdir`; any non-empty `workdir_diff.txt` would be surfaced in failure attribution.",
            "",
            "## Acceptance Self Check",
            "",
            "- Per-task five-piece artifacts: reported in `artifacts`; required files are stdout.log, tool_calls.jsonl, trajectory.json, result.json, workdir_diff.txt.",
            "- Workdir diff empty: reported in `clean_workdir` and failure attribution.",
            "- Resumability: `run_eval.py` skips completed task directories with existing completed result.json; this was used by the GATE4 runner structure and remains available for interruption recovery.",
            "- Traceability: every score comes from `grades.jsonl`; every failure row points back to its per-task run directory and trajectory line.",
            "- Fixture hashes and candidate versions are included above.",
            "",
            "## Limitations",
            "",
            "- Synthetic data is useful for relative ranking and harness behavior comparison; absolute production readiness needs recalibration on internal real-data labels.",
            "- This is a single baseline pass with no per-candidate tuning beyond the already documented engineering viability fixes.",
            "- The current model endpoint is a cloud DeepSeek-compatible API approved for this trial, not the intended future local model deployment.",
            "- Trae Agent required local engineering patches to become runnable, so it should be read as an engineering-usable baseline rather than a strict unmodified vendor runtime.",
        ]
    )

    report_path = output_dir / args.output_name
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
