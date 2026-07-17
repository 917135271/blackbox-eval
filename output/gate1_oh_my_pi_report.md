# Oh My Pi GATE1 验证报告

生成时间：2026-07-16 18:00:29 +08:00

## 结论

Oh My Pi 已通过候选框架 GATE1，可以进入统一审计能力适配与开发题试跑。通过项包括源码锁定、源码镜像构建、版本核验、非 root 运行、DeepSeek V4 Pro 接入、JSON 轨迹输出以及 `read`、`bash` 基础工具调用。

## 版本锁定

| 项目 | 锁定值 |
| --- | --- |
| 仓库 | `https://github.com/can1357/oh-my-pi.git` |
| 版本 | `v17.0.1` |
| 提交 | `6ae7cdbf97bbe7b608ce71ff7b3e0532955bd94a` |
| Bun | `1.3.14` |
| 镜像 | `blackbox-eval/oh-my-pi-source:17.0.1` |
| 镜像 ID | `sha256:b82b82c1f7aef629e0ed4b443e0c253b559bf21e5d2c09fe8c1d37cb0aea3b87` |
| 运行用户 | `agent`，UID `10001` |
| 工作目录 | `/workspace` |

## 工程可用性修复

官方 Dockerfile 在当前网络环境中出现 Debian HTTP 软件源失败和 Bun 依赖安装长期挂起。评测专用 `Dockerfile.source` 保持源码逻辑不变，仅增加以下构建稳定性与运行隔离措施：

- Debian 软件源切换为 HTTPS，并增加下载重试和超时；
- Bun 安装脚本增加网络重试；
- `bun install` 固定 npm 官方 registry、限制网络并发并输出详细日志；
- 最终运行阶段使用固定 UID `10001` 的非 root 用户。

## Canary 结果

Canary 使用 `deepseek/deepseek-v4-pro`、`--mode json`、`--print` 和隔离工作区运行。任务强制模型读取 `canary_input.txt`，并通过 Bash 调用 Python 计算 `7 × 6`。

验证结果：

- 进程退出码：`0`
- Provider：`deepseek`
- Model：`deepseek-v4-pro`
- `read` 工具：已调用并读取 `OH_MY_PI_SOURCE_CANARY`
- `bash` 工具：已调用并返回 `42`
- 最终标记：`OMP_DEEPSEEK_CANARY_PASS|OH_MY_PI_SOURCE_CANARY|42`
- JSON 轨迹：`runs/gate1_oh_my_pi/artifacts/canary-nonroot.jsonl`
- 轨迹 SHA-256：`21ee1fd8f3c88ffc02dbd7cbabe9bca122f41fb9efb493a1a0664b57c0175652`

## GATE1 判定

**通过。** 下一步为 GATE2：新增 Oh My Pi 适配器，将共享审计 Skills、统一 MCP、Hooks 事件、Task Memory、上下文压缩和受控子智能体协议包装为 Oh My Pi 可加载形式。
