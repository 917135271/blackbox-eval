# Pi Agent GATE1 验证报告

生成时间：2026-07-20 23:40:40 +08:00

## 结论

Pi Agent 已通过 GATE1，可以进入领域能力适配。源码版本、源码镜像、非 root 运行、DeepSeek V4 Pro 接入、非交互 JSON 轨迹以及 `read`、`bash`、`write` 基础工具均已验证。

## 版本锁定

| 项目 | 锁定值 |
| --- | --- |
| 仓库 | `https://github.com/earendil-works/pi.git` |
| 版本 | `v0.80.10` |
| 提交 | `8dc78834cde4e329284cf505f9e3f99763df5529` |
| CLI 包 | `@earendil-works/pi-coding-agent@0.80.10` |
| Node.js | `24.18.0` |
| 镜像 | `blackbox-eval/pi-agent-source:0.80.10` |
| 镜像 ID | `sha256:8b06583ef6c3b64fdb82c00aa6af949e21102cea878748a0dda41f1abc8f9b9b` |
| 运行用户 | `agent`，UID `10001` |
| 工作目录 | `/workspace` |

## 构建适配

上游完整构建会在线刷新模型目录，当前在线目录与锁定源码的静态类型存在漂移。评测镜像改为基于仓库锁文件安装依赖，并对工作区包执行确定性的源码编译，保留锁定版本自带的模型目录；未修改 Pi Agent 源码。Debian 证书安装增加了启动引导，以适配当前容器网络环境。

## DeepSeek Canary

Canary 通过自定义 provider `deepseek-eval` 接入 `deepseek-v4-pro`，要求模型读取文件、调用 Python、查询 SQLite 版本并写回文件。

- 进程退出码：`0`
- 最终标记：`PI_AGENT_DEEPSEEK_CANARY_PASS|PI_AGENT_SOURCE_CANARY|42|PI_AGENT_WRITE_OK`
- JSON 轨迹：`runs/gate1_pi_agent/workspace/canary.jsonl`
- 轨迹 SHA-256：`cd13ac9fe37c1b1c574c8971abdff7943b7af4b26f0686c635841005dace837f`

## GATE1 判定

**通过。** Pi Agent 已满足进入 GATE2 的源码可复现、模型可调用和基础工具可用要求。
