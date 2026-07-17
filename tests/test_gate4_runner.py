from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "runner" / "run_gate4_formal.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("run_gate4_formal_test", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class Gate4RunnerTests(unittest.TestCase):
    def test_loads_fifteen_formal_tasks_with_precise_prompts(self) -> None:
        runner = load_runner()
        tasks = runner.load_tasks([])
        self.assertEqual(len(tasks), 15)
        self.assertTrue(all(task.get("prompt") for task in tasks))
        self.assertEqual(len({task["case_family"] for task in tasks}), 5)

    def test_prompt_forbids_hidden_assets_and_names_gate4(self) -> None:
        runner = load_runner()
        prompt = runner.task_prompt(runner.load_tasks([])[0], enhanced=True)
        self.assertIn("GATE4 正式", prompt)
        self.assertIn("禁止读取 ground_truth、cases.json、Rubric、判卷代码", prompt)
        self.assertIn("GATE4_TASK_PASS", prompt)
        self.assertIn("/runtime-schemas/final_result.schema.json", prompt)
        self.assertIn("禁止把 .schema.json 猜成普通 .json", prompt)

    def test_frozen_configuration_is_current(self) -> None:
        runner = load_runner()
        freeze = runner.verify_frozen_configuration()
        self.assertEqual(freeze["formal_task_count_per_group"], 15)
        self.assertEqual(freeze["task_timeout_seconds"], 900)

    def test_safe_reset_rejects_unexpected_target(self) -> None:
        runner = load_runner()
        with tempfile.TemporaryDirectory() as temp:
            runner.RUN_ROOT = Path(temp) / "unexpected"
            with self.assertRaises(ValueError):
                runner.safe_reset()

    def test_full_summary_targets_all_groups_and_tasks(self) -> None:
        runner = load_runner()
        self.assertEqual(len(runner.GROUPS), 10)
        self.assertEqual(len(runner.load_tasks([])), 15)


if __name__ == "__main__":
    unittest.main()
