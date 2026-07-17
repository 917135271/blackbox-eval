# GATE2 领域增强能力验收报告

## 结论

GATE2治理层 **通过**。已形成一份共享证券费用审计核心、四套现有框架适配器、七个领域 Skill、三个受控子智能体、单题任务状态、上下文Checkpoint、统一Hooks事件和结果提交工具。Claude Code Best与Codex完成真实运行时Canary，并通过“授权、原生执行、完成登记、校验、首次提交”全链路。

允许对现有四个框架执行治理版GATE3开发题复跑；新增oh-my-pi仍需先完成GATE1和适配器构建。

## 交付内容

- 共享核心：`domain-enhancement/shared-audit-core/`
- Claude Code Best 包装：`domain-enhancement/adapters/claude-code-best/securities-expense-audit/`
- Codex 包装：`domain-enhancement/adapters/codex/securities-expense-audit/`
- OpenClaude 包装：`domain-enhancement/adapters/openclaude/securities-expense-audit/`
- OpenCode 包装：`domain-enhancement/adapters/opencode/securities-expense-audit/`
- 统一控制 MCP：`domain-enhancement/control-mcp/audit_control_mcp.py`
- 四端构建脚本：`domain-enhancement/build_adapters.py`
- 集成 Canary：`runner/run_gate2_domain_canary.py`
- 自动化测试：`tests/test_domain_enhancement.py`

## 运行时结果

| 候选 | Skill | 子智能体 | 控制 MCP | 提交结果 | 修复次数 |
| --- | ---: | --- | --- | --- | ---: |
| Claude Code Best 2.8.3 | 7 | 原生 Agent 完成 | 已连接 | accepted | 0 |
| Codex 0.144.4 | 7 | V1 spawn/wait 完成 | 已连接 | accepted | 0 |

两个回执都验证了 `R000001` 的业务库存在性，且均记录 `hidden_answer_mapping_used=false`。两次运行均生成统一事件、工具、子智能体、上下文、产物和运行清单。Canary只验证能力装配与执行链路，不计入开发题或15道正式案例成绩。

## 验收项

| 检查 | 结果 |
| --- | --- |
| seven_canonical_skills | 通过 |
| shared_skill_hashes_identical | 通过 |
| thirteen_business_and_governance_schemas | 通过 |
| three_roles_each_adapter | 通过 |
| unit_tests | 通过 |
| all_skills_validate | 通过 |
| both_plugins_validate | 通过 |
| ccb_runtime_discovered_seven_skills | 通过 |
| ccb_runtime_discovered_three_agents | 通过 |
| ccb_control_mcp_connected | 通过 |
| ccb_native_subagent_completed | 通过 |
| ccb_submit_via_mcp | 通过 |
| ccb_canary_success | 通过 |
| codex_native_subagent_completed | 通过 |
| codex_submit_via_mcp | 通过 |
| codex_canary_success | 通过 |
| both_submissions_first_attempt | 通过 |
| subagent_call_limits_enforced | 通过 |
| subagent_completion_registered | 通过 |
| governance_traces_present | 通过 |
| no_direct_control_import_bypass | 通过 |
| hidden_answer_mapping_not_used | 通过 |
| hidden_assets_not_mounted | 通过 |
| secret_not_persisted | 通过 |

## 修复记录

1. 首次运行发现 Claude 的 `--bare` 模式没有开放插件 MCP 和原生 Agent；已切换为完整非交互模式，并禁止 Bash 直调控制代码。
2. 首次 Codex 运行发现本地占位令牌被转发到 DeepSeek，且只读 `CODEX_HOME` 阻止系统 Skill 初始化；已改为安全继承密钥和隔离可写 `CODEX_HOME`。
3. Codex `multi_agent_v2` 在 Responses-to-Chat 适配下出现无真实子线程的假 spawn；已切回源码稳定的 `multi_agent` V1，真实返回 child thread 并完成 wait。
4. Codex 曾在第二次提交后才完成文件修复；提交器维持最多一次修复，不放宽约束。V1 重跑按正确顺序首轮通过。

## 证据位置

- Claude 轨迹：`runs/gate2_domain_enhancement/claude-code-best/artifacts/trajectory.jsonl`
- Codex 轨迹：`runs/gate2_domain_enhancement/codex/artifacts/trajectory.jsonl`
- 首次失败归因：`runs/gate2_domain_enhancement_attempt1/`
- Codex V2 失败归因：`runs/gate2_domain_enhancement/codex_attempt2_v2/`
- 机器可读报告：`output/gate2_domain_enhancement.json`
