# GATE4 正式任务运行与轨迹完整性报告

## 结论

GATE4 **通过**。本报告只验证180次正式运行与审计轨迹是否完整，不执行逐题语义判卷；逐题Rubric判卷属于GATE5。

## 12组运行结果

| 实验组 | 已运行 | 已提交 | 超时 | 事件完整 | 产物清单 | 可恢复Checkpoint |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ccb-baseline | 15/15 | 15/15 | 0 | 15/15 | 15/15 | 0/15 |
| ccb-enhanced | 15/15 | 13/15 | 0 | 15/15 | 15/15 | 15/15 |
| codex-baseline | 15/15 | 13/15 | 2 | 15/15 | 15/15 | 0/15 |
| codex-enhanced | 15/15 | 14/15 | 1 | 15/15 | 15/15 | 15/15 |
| openclaude-baseline | 15/15 | 15/15 | 0 | 15/15 | 15/15 | 0/15 |
| openclaude-enhanced | 15/15 | 15/15 | 0 | 15/15 | 15/15 | 15/15 |
| opencode-baseline | 15/15 | 15/15 | 0 | 15/15 | 15/15 | 0/15 |
| opencode-enhanced | 15/15 | 14/15 | 1 | 15/15 | 15/15 | 15/15 |
| oh-my-pi-baseline | 15/15 | 14/15 | 1 | 15/15 | 15/15 | 0/15 |
| oh-my-pi-enhanced | 15/15 | 13/15 | 3 | 15/15 | 15/15 | 15/15 |
| pi-agent-baseline | 15/15 | 15/15 | 0 | 15/15 | 15/15 | 0/15 |
| pi-agent-enhanced | 15/15 | 15/15 | 0 | 15/15 | 15/15 | 15/15 |

## 验收项

| 检查 | 结果 |
| --- | --- |
| frozen_configuration_verified | 通过 |
| configured_formal_cases_present | 通过 |
| all_formal_runs_present | 通过 |
| every_task_has_submission_or_terminal_failure | 通过 |
| every_task_has_run_manifest | 通过 |
| every_task_has_artifact_manifest | 通过 |
| every_task_has_complete_event_stream | 通过 |
| every_task_has_tool_trace | 通过 |
| every_task_has_trajectory | 通过 |
| enhanced_checkpoints_recoverable | 通过 |
| subagent_protocol_enforced | 通过 |
| all_reruns_registered_as_infrastructure | 通过 |
| formal_runtime_mounts_verified | 通过 |
| secret_not_persisted | 通过 |

## 性能诊断

- 成功提交：171/180
- 超时任务：8
- 超过每组1题超时标准的实验组：codex-baseline、oh-my-pi-enhanced
- 以上属于GATE5选型硬标准，不影响GATE4对运行和轨迹是否完整的验收。

## 重跑记录

- `ccb-enhanced/L3-006`：infrastructure，gate4_timeout_or_missing_submission_retry
- `ccb-enhanced/L3-003`：infrastructure，gate4_timeout_or_missing_submission_retry
- `oh-my-pi-enhanced/L3-003`：infrastructure，gate4_timeout_or_missing_submission_retry
- `codex-baseline/L3-004`：infrastructure，gate4_timeout_or_missing_submission_retry
- `oh-my-pi-enhanced/L3-004`：infrastructure，gate4_timeout_or_missing_submission_retry
- `ccb-enhanced/L3-009`：infrastructure，gate4_timeout_or_missing_submission_retry
- `codex-baseline/L3-009`：infrastructure，gate4_timeout_or_missing_submission_retry
- `codex-enhanced/L3-009`：infrastructure，gate4_timeout_or_missing_submission_retry
- `opencode-enhanced/L3-009`：infrastructure，gate4_timeout_or_missing_submission_retry
- `oh-my-pi-baseline/L3-009`：infrastructure，gate4_timeout_or_missing_submission_retry
- `oh-my-pi-enhanced/L3-009`：infrastructure，gate4_timeout_or_missing_submission_retry
- `openclaude-enhanced/L3-010`：infrastructure，gate4_timeout_or_missing_submission_retry
- `ccb-enhanced/L3-006`：infrastructure，deepseek_connection_reset_retry
- `ccb-enhanced/L3-003`：infrastructure，deepseek_connection_reset_retry
- `oh-my-pi-enhanced/L3-003`：infrastructure，deepseek_connection_reset_retry
- `codex-baseline/L3-004`：infrastructure，deepseek_connection_reset_retry
- `oh-my-pi-enhanced/L3-004`：infrastructure，deepseek_connection_reset_retry
- `ccb-enhanced/L3-009`：infrastructure，deepseek_connection_reset_retry
- `codex-baseline/L3-009`：infrastructure，deepseek_connection_reset_retry
- `codex-enhanced/L3-009`：infrastructure，deepseek_connection_reset_retry
- `opencode-enhanced/L3-009`：infrastructure，deepseek_connection_reset_retry
- `oh-my-pi-baseline/L3-009`：infrastructure，deepseek_connection_reset_retry
- `oh-my-pi-enhanced/L3-009`：infrastructure，deepseek_connection_reset_retry
- `openclaude-enhanced/L3-010`：infrastructure，deepseek_connection_reset_retry
