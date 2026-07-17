# GATE3 独立开发题试跑与配置冻结报告

## 结论

GATE3 **通过**。12道开发题只用于执行链路调试，不设置逐题Rubric。开发集使用独立的 `R900xxx` 业务记录命名空间，候选容器未挂载15道正式题、正式Ground Truth、Rubric或判卷实现。

允许进入 GATE4 十组正式15题运行。

## 十组结果

| 实验组 | 提交成功 | 语义正确 | 陷阱误报 | 超时 | 平均秒数 | 子智能体调用 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ccb-baseline | 12/12 | 8/12 | 0 | 0 | 183.073 | 0 |
| ccb-enhanced | 12/12 | 7/12 | 0 | 0 | 447.116 | 4 |
| codex-baseline | 12/12 | 8/12 | 0 | 0 | 173.987 | 0 |
| codex-enhanced | 12/12 | 11/12 | 0 | 0 | 346.432 | 4 |
| openclaude-baseline | 12/12 | 6/12 | 0 | 0 | 182.17 | 0 |
| openclaude-enhanced | 12/12 | 9/12 | 0 | 0 | 211.655 | 3 |
| opencode-baseline | 12/12 | 9/12 | 0 | 0 | 145.597 | 0 |
| opencode-enhanced | 12/12 | 9/12 | 0 | 0 | 291.649 | 4 |
| oh-my-pi-baseline | 12/12 | 9/12 | 0 | 0 | 97.017 | 0 |
| oh-my-pi-enhanced | 12/12 | 12/12 | 0 | 0 | 226.032 | 4 |

开发题异常 ID 只检查是否应为空及内部一致性，业务正确性以 `record_ids`、必要事实和制度引用为主，避免用不透明标签替代审计能力。

## 验收项

| 检查 | 结果 |
| --- | --- |
| twelve_independent_development_tasks | 通过 |
| one_hundred_twenty_runs_present | 通过 |
| at_least_eleven_submissions_per_group | 通过 |
| timeouts_at_most_one_per_group | 通过 |
| preflight_used_for_every_task | 通过 |
| baseline_has_no_subagent_calls | 通过 |
| enhanced_uses_controlled_subagents | 通过 |
| enhanced_skill_workflow_loaded | 通过 |
| unified_event_stream_complete | 通过 |
| artifact_manifest_present | 通过 |
| enhanced_checkpoint_recorded | 通过 |
| enhanced_checkpoint_state_recoverable | 通过 |
| enhanced_context_events_recorded | 通过 |
| subagent_completion_protocol_closed | 通过 |
| oh_my_pi_native_hook_recorded | 通过 |
| trap_false_positives_at_most_one | 通过 |
| single_rule_scope_is_exact | 通过 |
| formal_assets_not_mounted | 通过 |
| unit_tests | 通过 |
| secret_not_persisted | 通过 |

## 非阻断诊断

开发题没有冻结逐题Rubric，以下语义命中只用于发现数据重叠、规则边界和框架差异，不作为GATE3准入条件。

| 诊断项 | 结果 |
| --- | --- |
| enhanced_correct_at_least_ten | 未达到 |

## 未通过任务

- `ccb-baseline/DEV-002`：accepted=True，record_f1=0.0，anomaly_presence=False，facts=1.0，citations=1.0
- `ccb-baseline/DEV-007`：accepted=True，record_f1=0.75，anomaly_presence=True，facts=1.0，citations=1.0
- `ccb-baseline/DEV-009`：accepted=True，record_f1=1.0，anomaly_presence=True，facts=0.5，citations=1.0
- `ccb-baseline/DEV-012`：accepted=True，record_f1=0.9231，anomaly_presence=True，facts=1.0，citations=1.0
- `ccb-enhanced/DEV-002`：accepted=True，record_f1=0.0，anomaly_presence=False，facts=1.0，citations=1.0
- `ccb-enhanced/DEV-007`：accepted=True，record_f1=0.75，anomaly_presence=True，facts=1.0，citations=1.0
- `ccb-enhanced/DEV-009`：accepted=True，record_f1=1.0，anomaly_presence=True，facts=0.5，citations=1.0
- `ccb-enhanced/DEV-010`：accepted=True，record_f1=1.0，anomaly_presence=True，facts=0.5，citations=1.0
- `ccb-enhanced/DEV-012`：accepted=True，record_f1=0.96，anomaly_presence=True，facts=1.0，citations=1.0
- `codex-baseline/DEV-004`：accepted=True，record_f1=1.0，anomaly_presence=True，facts=0.5，citations=1.0
- `codex-baseline/DEV-007`：accepted=True，record_f1=0.75，anomaly_presence=True，facts=1.0，citations=1.0
- `codex-baseline/DEV-008`：accepted=True，record_f1=0.1818，anomaly_presence=True，facts=1.0，citations=0.5
- `codex-baseline/DEV-012`：accepted=True，record_f1=0.9286，anomaly_presence=True，facts=1.0，citations=1.0
- `codex-enhanced/DEV-004`：accepted=True，record_f1=1.0，anomaly_presence=True，facts=0.5，citations=1.0
- `openclaude-baseline/DEV-004`：accepted=True，record_f1=1.0，anomaly_presence=True，facts=0.5，citations=1.0
- `openclaude-baseline/DEV-006`：accepted=True，record_f1=1.0，anomaly_presence=True，facts=1.0，citations=0.0
- `openclaude-baseline/DEV-007`：accepted=True，record_f1=0.75，anomaly_presence=True，facts=1.0，citations=1.0
- `openclaude-baseline/DEV-009`：accepted=True，record_f1=1.0，anomaly_presence=True，facts=0.5，citations=1.0
- `openclaude-baseline/DEV-010`：accepted=True，record_f1=1.0，anomaly_presence=True，facts=0.5，citations=1.0
- `openclaude-baseline/DEV-012`：accepted=True，record_f1=0.96，anomaly_presence=True，facts=1.0，citations=1.0
- `openclaude-enhanced/DEV-002`：accepted=True，record_f1=0.0，anomaly_presence=False，facts=1.0，citations=1.0
- `openclaude-enhanced/DEV-007`：accepted=True，record_f1=0.75，anomaly_presence=True，facts=1.0，citations=1.0
- `openclaude-enhanced/DEV-009`：accepted=True，record_f1=1.0，anomaly_presence=True，facts=0.5，citations=1.0
- `opencode-baseline/DEV-002`：accepted=True，record_f1=0.0，anomaly_presence=True，facts=1.0，citations=1.0
- `opencode-baseline/DEV-004`：accepted=True，record_f1=1.0，anomaly_presence=True，facts=0.5，citations=1.0
- `opencode-baseline/DEV-007`：accepted=True，record_f1=0.75，anomaly_presence=True，facts=1.0，citations=1.0
- `opencode-enhanced/DEV-004`：accepted=True，record_f1=1.0，anomaly_presence=True，facts=0.5，citations=1.0
- `opencode-enhanced/DEV-007`：accepted=True，record_f1=0.75，anomaly_presence=True，facts=1.0，citations=1.0
- `opencode-enhanced/DEV-009`：accepted=True，record_f1=1.0，anomaly_presence=True，facts=0.5，citations=1.0
- `oh-my-pi-baseline/DEV-004`：accepted=True，record_f1=1.0，anomaly_presence=True，facts=0.5，citations=1.0
- `oh-my-pi-baseline/DEV-007`：accepted=True，record_f1=0.75，anomaly_presence=True，facts=1.0，citations=1.0
- `oh-my-pi-baseline/DEV-012`：accepted=True，record_f1=0.9167，anomaly_presence=True，facts=1.0，citations=1.0

## 冻结结果

- 冻结文件：`config/gate3_frozen_lock.json`
- 冻结文件数量：55
- 正式运行单题超时：900秒
- 正式实验：Claude Code Best、Codex、OpenClaude、OpenCode、oh-my-pi × 原生基线/领域增强，共10组，每组15题，共150次运行
