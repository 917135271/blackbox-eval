# GATE1 源码环境与能力验收报告

## 结论

GATE1 **通过**。Claude Code Best 与 Codex 均使用锁定源码构建，接入
`deepseek-v4-pro`，并在隔离容器中完成基础工具、MCP、结构化输出和轨迹留存验证。
允许进入 GATE2。

## 版本锁定

| 候选 | 版本 | 源码标识 | 运行镜像 |
| --- | --- | --- | --- |
| Claude Code Best | 2.8.3 | `v2.8.3 / 7680c291...` | `blackbox-eval/ccb-source-nonroot:2.8.3` |
| Codex | codex-cli 0.144.4 | `rust-v0.144.4 / 8c68d4c8...` | `blackbox-eval/codex-source:0.144.4` |

## 验收结果

| 验收项 | Claude Code Best | Codex |
| --- | --- | --- |
| 源码与版本 | 通过 | 通过 |
| DeepSeek v4 Pro | 通过 | 通过 |
| Shell/Python/SQLite/文件 | 通过 | 通过 |
| 制度与费用 MCP | 通过 | 通过 |
| 结构化结果 | 通过 | 通过 |
| 完整轨迹 | 通过 | 通过 |

Codex 的 Responses-to-Chat 代理成功完成 5 轮真实请求；
Claude Code Best Canary 共执行 12 轮，并在运行中自行发现和修正一次 SQL 元数据表名错误。

## 构建发现

- CCB v2.8.3 source tag requires build-only stubs for absent optional resources.
- CCB must run as a non-root user before bypassPermissions is accepted.
- Codex v0.144.4 source lock is inconsistent with its manifests; a resolved lock is retained and rechecked with --locked.
- Codex v0.144.4 requires Responses API, so DeepSeek is connected through an independent Responses-to-Chat adapter.
- Codex uses an explicit DeepSeek model catalog and source-native base instructions to avoid fallback model metadata.

## 安全检查

- API 密钥仅通过 `LLM_API_KEY` 注入。
- 密钥落盘扫描：未发现匹配。
- Canary 只挂载 MCP 脚本、制度语料和费用数据库；未挂载 Ground Truth、历史答案、判卷代码或其他候选轨迹。
- 两端均以非 root 用户运行，业务输入只读，工作区和轨迹目录可写。

## 证据位置

- Claude Code Best：`runs\gate1_v2_source\claude-code-canary\artifacts\trajectory.jsonl`
- Codex：`runs\gate1_v2_source\codex-canary\artifacts\trajectory.jsonl`
- 机器可读结果：`output/gate1_source_environment.json`
- 完整版本锁定：`config/source_eval_lock.yaml`
