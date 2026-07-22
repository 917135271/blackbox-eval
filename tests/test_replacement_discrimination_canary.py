from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "runner" / "run_replacement_discrimination_canary.py"
REPORT_PATH = ROOT / "runner" / "report_replacement_discrimination_canary.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("replacement_canary", RUNNER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_reporter():
    spec = importlib.util.spec_from_file_location("replacement_canary_report", REPORT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_replacement_canary_loads_exactly_four_new_cases() -> None:
    runner = load_runner()
    tasks = runner.load_tasks([])
    assert tuple(task["id"] for task in tasks) == runner.CASE_IDS
    assert len(tasks) == 4
    assert all(task["prompt"] for task in tasks)


def test_replacement_canary_uses_formal_database_and_isolated_run_root() -> None:
    runner = load_runner()
    runner.configure_runtime()
    assert runner.runtime.DEV_DB == runner.FORMAL / "expense_formal.db"
    assert runner.runtime.RUN_ROOT.name == "gate3_replacement_canary"


def test_replacement_canary_prompt_is_not_a_formal_ranked_run() -> None:
    runner = load_runner()
    runner.configure_runtime()
    prompt = runner.task_prompt(runner.load_tasks([])[0], enhanced=False, framework="codex")
    assert "区分度Canary" in prompt
    assert "不进入正式排名" in prompt
    assert "禁止读取 ground_truth" in prompt
    assert "submission_allowed=true" in prompt
    assert "字段名不是allow_submission" in prompt


def test_report_does_not_treat_judge_errors_as_zero_scores_or_format_failures(tmp_path, monkeypatch) -> None:
    reporter = load_reporter()
    cases_path = tmp_path / "cases.json"
    grades_path = tmp_path / "grades.jsonl"
    summary_path = tmp_path / "summary.json"
    cases_path.write_text(
        json.dumps(
            {
                "dataset_id": "test-v9",
                "rubric_version": "test-v7",
                "cases": [
                    {
                        "id": task_id,
                        "replaces": f"old-{task_id}",
                        "rubric": {"checklist": [{"id": "semantic", "metric": "conclusion"}]},
                    }
                    for task_id in reporter.CASE_IDS
                ],
            }
        ),
        encoding="utf-8",
    )
    grades = []
    runs = []
    failed_pair = (reporter.GROUPS[0], reporter.CASE_IDS[0])
    for group in reporter.GROUPS:
        for task_id in reporter.CASE_IDS:
            judge_status = "error" if (group, task_id) == failed_pair else "ok"
            grades.append(
                {
                    "group": group,
                    "task_id": task_id,
                    "judge": {"status": judge_status},
                    "checklist": [{"id": "semantic", "value": 1}],
                }
            )
            runs.append(
                {
                    "group": group,
                    "task_id": task_id,
                    "submission_status": "accepted",
                    "timed_out": False,
                }
            )
    grades_path.write_text("\n".join(json.dumps(row) for row in grades) + "\n", encoding="utf-8")
    summary_path.write_text(json.dumps({"runs": runs}), encoding="utf-8")
    monkeypatch.setattr(reporter, "CASES_PATH", cases_path)
    monkeypatch.setattr(reporter, "GRADES_PATH", grades_path)
    monkeypatch.setattr(reporter, "RUN_SUMMARY_PATH", summary_path)

    report = reporter.build_report()

    assert report["format_success_rate"] == 1.0
    assert report["judge_errors"] == 1
    assert report["status"] == "incomplete"
    affected = report["case_results"][0]
    assert affected["graded_group_count"] == len(reporter.GROUPS) - 1
    assert affected["scores"][failed_pair[0]] is None
