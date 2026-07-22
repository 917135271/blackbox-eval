from __future__ import annotations

import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "runner" / "run_gate3_development.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("run_gate3_development_test", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class Gate3RunnerTimeoutTests(unittest.TestCase):
    def test_openclaude_enhanced_explicitly_registers_audit_control(self) -> None:
        runner = load_runner()
        config = runner.openclaude_mcp_config(enhanced=True)
        control = config["mcpServers"]["audit_control"]
        self.assertEqual(
            control["args"],
            ["/plugin/shared/control-mcp/audit_control_mcp.py"],
        )
        self.assertEqual(control["env"]["AUDIT_SUBAGENTS_ENABLED"], "1")

    def test_task_prompt_uses_unambiguous_absolute_schema_paths(self) -> None:
        runner = load_runner()
        prompt = runner.task_prompt(
            {
                "id": "DEV-001",
                "category": "record_audit",
                "prompt": "test",
            },
            enhanced=False,
        )
        self.assertIn("/runtime-schemas", prompt)
        self.assertIn("/workspace/runtime-schemas", prompt)
        self.assertIn("禁止拼成/workspace/workspace", prompt)

    def test_openclaude_prompt_uses_only_exposed_file_tools(self) -> None:
        runner = load_runner()
        prompt = runner.task_prompt(
            {
                "id": "DEV-001",
                "category": "record_audit",
                "prompt": "test",
            },
            enhanced=True,
            framework="openclaude",
        )
        self.assertIn("必须使用Edit或Bash中的安全脚本更新", prompt)
        self.assertIn("禁止调用Write、Grep等未暴露工具", prompt)

    def test_resume_reuses_only_accepted_results_within_time_budget(self) -> None:
        runner = load_runner()
        self.assertTrue(
            runner.is_reusable_result(
                {
                    "submission_status": "accepted",
                    "timed_out": False,
                    "elapsed_seconds": 899.9,
                },
                900,
            )
        )
        self.assertFalse(
            runner.is_reusable_result(
                {
                    "submission_status": "accepted",
                    "timed_out": False,
                    "elapsed_seconds": 901,
                },
                900,
            )
        )
        self.assertFalse(
            runner.is_reusable_result(
                {
                    "submission_status": "accepted",
                    "timed_out": True,
                    "elapsed_seconds": 100,
                },
                900,
            )
        )

    def test_prepare_task_writes_canonical_and_compatibility_schema_names(self) -> None:
        runner = load_runner()
        with tempfile.TemporaryDirectory() as temp:
            runner.RUN_ROOT = Path(temp) / "gate3_development"
            _, workspace, _ = runner.prepare_task(
                "openclaude-baseline",
                {
                    "id": "DEV-001",
                    "category": "record_audit",
                    "prompt": "test",
                },
            )

            schemas = workspace / "runtime-schemas"
            for canonical, compatibility in (
                ("final_result.schema.json", "final_result_schema.json"),
                ("evidence_matrix.schema.json", "evidence_matrix_schema.json"),
                ("validation_report.schema.json", "validation_report_schema.json"),
            ):
                self.assertTrue((schemas / canonical).exists())
                self.assertEqual(
                    (schemas / canonical).read_bytes(),
                    (schemas / compatibility).read_bytes(),
                )

    def test_safe_reset_removes_readonly_runtime_files(self) -> None:
        runner = load_runner()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runner.ROOT = root
            runner.RUN_ROOT = root / "runs" / "gate3_development"
            readonly = runner.RUN_ROOT / "codex-home" / ".tmp" / "pack.idx"
            readonly.parent.mkdir(parents=True)
            readonly.write_text("locked", encoding="utf-8")
            os.chmod(readonly, 0o444)

            runner.safe_reset()

            self.assertTrue(runner.RUN_ROOT.exists())
            self.assertFalse(readonly.exists())

    def test_safe_reset_tolerates_already_missing_entries(self) -> None:
        runner = load_runner()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runner.ROOT = root
            runner.RUN_ROOT = root / "runs" / "gate3_development"
            runner.RUN_ROOT.mkdir(parents=True)
            callback = None

            def fake_rmtree(_target, *, onexc):
                nonlocal callback
                callback = onexc
                onexc(os.unlink, str(runner.RUN_ROOT / "gone"), FileNotFoundError())
                runner.RUN_ROOT.rmdir()

            with mock.patch.object(runner.shutil, "rmtree", side_effect=fake_rmtree):
                runner.safe_reset()

            self.assertIsNotNone(callback)
            self.assertTrue(runner.RUN_ROOT.exists())

    def test_safe_reset_archives_runtime_when_windows_cleanup_stays_busy(self) -> None:
        runner = load_runner()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runner.ROOT = root
            runner.RUN_ROOT = root / "runs" / "gate3_development"
            runner.RUN_ROOT.mkdir(parents=True)
            (runner.RUN_ROOT / "busy.txt").write_text("busy", encoding="utf-8")

            with mock.patch.object(runner.shutil, "rmtree", side_effect=OSError("directory not empty")):
                runner.safe_reset()

            stale = list((root / "runs").glob("gate3_development-stale-*"))
            self.assertEqual(len(stale), 1)
            self.assertTrue((stale[0] / "busy.txt").exists())
            self.assertTrue(runner.RUN_ROOT.exists())

    def test_codex_config_returns_toml_with_governance_environment(self) -> None:
        runner = load_runner()
        config = runner.codex_config("DEV-001", enhanced=True)
        self.assertIsInstance(config, str)
        self.assertIn('AUDIT_TASK_ID = "DEV-001"', config)
        self.assertIn('AUDIT_FRAMEWORK = "codex"', config)
        self.assertIn("[agents.policy_researcher]", config)

    def test_oh_my_pi_config_uses_native_model_mcp_and_twelve_groups(self) -> None:
        runner = load_runner()
        models = runner.oh_my_pi_models_config()
        mcp = runner.oh_my_pi_mcp_config("DEV-001", enhanced=True)
        self.assertIn("baseUrl: https://api.deepseek.com/v1", models)
        self.assertIn("apiKey: LLM_API_KEY", models)
        self.assertEqual(
            mcp["mcpServers"]["audit_control"]["env"]["AUDIT_FRAMEWORK"],
            "oh-my-pi",
        )
        self.assertIn("/plugin/shared/control-mcp", mcp["mcpServers"]["audit_control"]["args"][0])
        self.assertEqual(len(runner.GROUPS), 12)
        self.assertIn("oh-my-pi-enhanced", runner.GROUPS)

    def test_oh_my_pi_baseline_command_excludes_native_subagent_tool(self) -> None:
        runner = load_runner()
        with mock.patch.object(runner, "prepare_task") as prepare:
            base = ROOT / "runs" / "unit-oh-my-pi"
            prepare.return_value = (base, base / "workspace", base / "artifacts")
            command, _ = runner.oh_my_pi_command(
                "oh-my-pi-baseline",
                {"id": "DEV-001", "category": "record_audit", "prompt": "test"},
                ROOT / "baseline",
                {"LLM_API_KEY": "test"},
            )
        tools = command[command.index("--tools") + 1].split(",")
        self.assertNotIn("task", tools)
        self.assertNotIn("hub", tools)

    def test_pi_agent_baseline_excludes_subagent_and_enhanced_loads_seven_skills(self) -> None:
        runner = load_runner()
        with mock.patch.object(runner, "prepare_task") as prepare:
            base = ROOT / "runs" / "unit-pi-agent"
            prepare.return_value = (base, base / "workspace", base / "artifacts")
            baseline, _ = runner.pi_agent_command(
                "pi-agent-baseline",
                {"id": "DEV-001", "category": "record_audit", "prompt": "test"},
                ROOT / "baseline",
                {"LLM_API_KEY": "test"},
            )
            enhanced, _ = runner.pi_agent_command(
                "pi-agent-enhanced",
                {"id": "DEV-001", "category": "record_audit", "prompt": "test"},
                ROOT / "baseline",
                {"LLM_API_KEY": "test"},
            )
        baseline_tools = baseline[baseline.index("--tools") + 1].split(",")
        enhanced_tools = enhanced[enhanced.index("--tools") + 1].split(",")
        self.assertNotIn("subagent", baseline_tools)
        self.assertIn("subagent", enhanced_tools)
        self.assertEqual(enhanced.count("--skill"), 7)
        self.assertIn("/plugin/.pi/extensions/business-tools.ts", baseline)

    def test_timeout_removes_container_before_collecting_output(self) -> None:
        runner = load_runner()

        class FakeProcess:
            returncode = 0

            def __init__(self) -> None:
                self.communicate_calls = 0
                self.killed = False

            def communicate(self, timeout: int):
                self.communicate_calls += 1
                if self.communicate_calls == 1:
                    raise subprocess.TimeoutExpired("docker run", timeout, output="partial")
                return "complete output", "complete error"

            def kill(self) -> None:
                self.killed = True

        process = FakeProcess()
        with mock.patch.object(runner.subprocess, "Popen", return_value=process), mock.patch.object(
            runner.subprocess,
            "run",
        ) as cleanup:
            returncode, timed_out, stdout, stderr = runner._run_captured_command(
                ["docker", "run"],
                {},
                15,
                "g3-ccb-enhanced-dev-012",
            )

        self.assertIsNone(returncode)
        self.assertTrue(timed_out)
        self.assertEqual(stdout, "complete output")
        self.assertEqual(stderr, "complete error")
        cleanup.assert_called_once_with(
            ["docker", "rm", "-f", "g3-ccb-enhanced-dev-012"],
            capture_output=True,
            check=False,
            timeout=30,
        )


if __name__ == "__main__":
    unittest.main()
