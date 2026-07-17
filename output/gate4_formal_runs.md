# GATE4 正式任务运行与轨迹完整性报告

## 结论

GATE4 **通过**。本报告只验证150次正式运行与审计轨迹是否完整，不执行逐题语义判卷；逐题Rubric判卷属于GATE5。

## 十组运行结果

| 实验组 | 已运行 | 已提交 | 超时 | 事件完整 | 产物清单 | 可恢复Checkpoint |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ccb-baseline | 15/15 | 15/15 | 1 | 15/15 | 15/15 | 0/15 |
| ccb-enhanced | 15/15 | 14/15 | 2 | 15/15 | 15/15 | 15/15 |
| codex-baseline | 15/15 | 14/15 | 1 | 15/15 | 15/15 | 0/15 |
| codex-enhanced | 15/15 | 12/15 | 3 | 15/15 | 15/15 | 15/15 |
| openclaude-baseline | 15/15 | 15/15 | 0 | 15/15 | 15/15 | 0/15 |
| openclaude-enhanced | 15/15 | 15/15 | 0 | 15/15 | 15/15 | 15/15 |
| opencode-baseline | 15/15 | 15/15 | 0 | 15/15 | 15/15 | 0/15 |
| opencode-enhanced | 15/15 | 13/15 | 2 | 15/15 | 15/15 | 15/15 |
| oh-my-pi-baseline | 15/15 | 14/15 | 1 | 15/15 | 15/15 | 0/15 |
| oh-my-pi-enhanced | 15/15 | 13/15 | 2 | 15/15 | 15/15 | 15/15 |

## 验收项

| 检查 | 结果 |
| --- | --- |
| frozen_configuration_verified | 通过 |
| fifteen_formal_cases | 通过 |
| one_hundred_fifty_runs_present | 通过 |
| every_task_has_submission_or_terminal_failure | 通过 |
| every_task_has_run_manifest | 通过 |
| every_task_has_artifact_manifest | 通过 |
| every_task_has_complete_event_stream | 通过 |
| every_task_has_tool_trace | 通过 |
| every_task_has_trajectory | 通过 |
| enhanced_checkpoints_recoverable | 通过 |
| subagent_protocol_enforced | 通过 |
| all_reruns_registered_as_infrastructure | 通过 |
| hidden_assets_not_mounted | 通过 |
| secret_not_persisted | 通过 |

## 性能诊断

- 成功提交：140/150
- 超时任务：12
- 超过每组1题超时标准的实验组：ccb-enhanced、codex-enhanced、opencode-enhanced、oh-my-pi-enhanced
- 以上属于GATE5选型硬标准，不影响GATE4对运行和轨迹是否完整的验收。

## 重跑记录

- `opencode-enhanced/L3-006`：infrastructure，gate4_runner_prompt_schema_path_regression
- `oh-my-pi-enhanced/L3-006`：infrastructure，gate4_runner_prompt_schema_path_regression
- `ccb-enhanced/L3-008`：infrastructure，gate4_runner_prompt_schema_path_regression
- `codex-baseline/L3-008`：infrastructure，gate4_runner_prompt_schema_path_regression
- `codex-enhanced/L3-008`：infrastructure，gate4_runner_prompt_schema_path_regression
- `openclaude-baseline/L3-008`：infrastructure，gate4_runner_prompt_schema_path_regression
- `openclaude-enhanced/L3-008`：infrastructure，gate4_runner_prompt_schema_path_regression
- `opencode-baseline/L3-008`：infrastructure，gate4_runner_prompt_schema_path_regression
- `opencode-enhanced/L3-008`：infrastructure，gate4_runner_prompt_schema_path_regression
- `oh-my-pi-baseline/L3-008`：infrastructure，gate4_runner_prompt_schema_path_regression
- `oh-my-pi-enhanced/L3-008`：infrastructure，gate4_runner_prompt_schema_path_regression
- `opencode-enhanced/L2-013`：infrastructure，transient_certificate_verification_error
