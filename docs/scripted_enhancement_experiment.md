# 脚本化增强对比实验

## 目标

新增第三组 `*-scripted-enhanced`，验证原增强组中的负优化是否来自模型承担了过多工作流、Memory、Checkpoint、证据文件和格式校验任务。原生基线组和原增强组保持不变。

## 三组关系

- A组：`*-baseline`，原生框架与业务MCP。
- B组：`*-enhanced`，原完整Skills流程。
- C组：`*-scripted-enhanced`，薄Skills与确定性脚本流程。

对比时分别计算B-A、C-B和C-A。正式正确性Q按逐题语义Checklist得分宏平均计算，格式项不进入Q；全量Checklist微平均只保留为诊断指标，不用于判断增强方向。

## 职责拆分

模型继续负责制度与业务证据检索、制度适用和例外解释、审计结论及四个语义结果字段，并更新预置的 `work/final_result.json`。模型还需在 `work/evidence_input.json` 中逐异常登记实际记录、条款和事实；无异常时登记核查范围与查询条件。校验和提交工具以空参数读取这两个文件，避免兼容框架生成长嵌套MCP参数时发生JSON损坏。脚本负责公开题型路由、初始与最终任务状态快照、阶段Checkpoint、证据输入归一化、集合一致性校验、Schema和ID校验以及提交准备。脚本不得推断业务证据，也不得把全部记录和条款复制给每个异常。

C组保留 `audit-query-planner`、`policy-version-check`、`batch-expense-analysis`、`false-positive-review` 和 `audit-report` 五个薄Skills。`evidence-coverage-check` 与 `result-validator` 不再进入模型上下文，其职责由脚本控制MCP执行。

子智能体角色由路由给出，但不强制调用。简单制度问答、单记录核查和直接交叉引用留在主智能体；批量核查、制度冲突或独立复核只有在确有独立任务时才授权。

## 隔离边界

C组适配器位于 `domain-enhancement/scripted-adapters/`，运行结果位于 `runs/gate3_scripted/` 和 `runs/gate4_scripted/`。原 `domain-enhancement/adapters/` 与 `runs/gate4_formal/` 不被覆盖。

脚本只根据题目公开的category选择工作流，不读取Rubric、Ground Truth或历史轨迹。Checkpoint采用阶段触发并记录 `estimation_method=external_scripted_stage`，只证明任务状态可恢复，不宣称存在运行中Task Memory调度或第三方框架原生上下文压缩。

GATE3全部通过后生成 `config/scripted_gate3_frozen_lock.json`。GATE4会核验工作流版本和实现指纹；历史运行只有在版本、实现指纹和数据指纹均一致时才允许复用。C-B同时包含薄Skills、可选子智能体、文件化提交和脚本校验等变化，因此报告将其称为“脚本下沉增强包差值”，不把差值归因于单一脚本因素。

## 执行顺序

先执行6道代表性开发题的六框架Canary，共36次：

```powershell
$env:LLM_API_KEY = [Environment]::GetEnvironmentVariable("LLM_API_KEY", "User")
python runner/run_gate3_scripted.py --workers 6 `
  --task-id DEV-001 --task-id DEV-002 --task-id DEV-003 `
  --task-id DEV-007 --task-id DEV-009 --task-id DEV-012
```

Canary通过后运行六框架15道正式题，共90次：

```powershell
python runner/run_gate4_scripted.py --workers 6
```

完成后使用相同GATE5 Checklist判卷，并生成三组对比报告：

```powershell
python runner/grade_gate5_scripted.py --workers 6
python runner/report_scripted_comparison.py
```

最终报告输出到 `output/scripted_enhancement_comparison.md`，逐框架列出三组Checklist命中率、完成率、超时和耗时，并逐题列出从原增强组到脚本增强组的修复项与回退项。
