# GATE5 可选质量抽查清单

共 65 条。该清单只用于检查Judge稳定性，不参与改分，也不阻塞GATE5。包含全部综合报告、发生实质误报的陷阱题、低置信度题，以及每组每题型20%的固定哈希分层样本。

| 组别 | 题目 | 题型 | Checklist命中率 | 入选原因 |
| --- | --- | --- | ---: | --- |
| Claude Code Best 基线组 | L1-001 | 制度与版本判断 | 100.0% | twenty_percent_stratified_sample |
| Claude Code Best 基线组 | L2-008 | 单案数据核查 | 100.0% | twenty_percent_stratified_sample |
| Claude Code Best 基线组 | L3-001 | 全年批量审计 | 100.0% | twenty_percent_stratified_sample |
| Claude Code Best 基线组 | L3-009 | 检索与综合报告 | 93.2% | all_comprehensive_reports, twenty_percent_stratified_sample |
| Claude Code Best 基线组 | TRAP-002 | 无异常及陷阱 | 85.7% | twenty_percent_stratified_sample |
| Claude Code Best 增强组 | L2-003 | 单案数据核查 | 100.0% | twenty_percent_stratified_sample |
| Claude Code Best 增强组 | L3-004 | 全年批量审计 | 100.0% | twenty_percent_stratified_sample |
| Claude Code Best 增强组 | L3-006 | 制度与版本判断 | 100.0% | twenty_percent_stratified_sample |
| Claude Code Best 增强组 | L3-009 | 检索与综合报告 | 86.3% | all_comprehensive_reports, twenty_percent_stratified_sample |
| Claude Code Best 增强组 | TRAP-003 | 无异常及陷阱 | 100.0% | twenty_percent_stratified_sample |
| Codex 基线组 | L2-008 | 单案数据核查 | 100.0% | twenty_percent_stratified_sample |
| Codex 基线组 | L3-003 | 全年批量审计 | 44.4% | low_judge_confidence, twenty_percent_stratified_sample |
| Codex 基线组 | L3-008 | 制度与版本判断 | 100.0% | twenty_percent_stratified_sample |
| Codex 基线组 | L3-009 | 检索与综合报告 | 1.4% | all_comprehensive_reports, twenty_percent_stratified_sample |
| Codex 基线组 | TRAP-003 | 无异常及陷阱 | 93.8% | twenty_percent_stratified_sample |
| Codex 增强组 | L2-003 | 单案数据核查 | 100.0% | twenty_percent_stratified_sample |
| Codex 增强组 | L3-001 | 全年批量审计 | 100.0% | twenty_percent_stratified_sample |
| Codex 增强组 | L3-008 | 制度与版本判断 | 100.0% | twenty_percent_stratified_sample |
| Codex 增强组 | L3-009 | 检索与综合报告 | 1.4% | all_comprehensive_reports, twenty_percent_stratified_sample |
| Codex 增强组 | TRAP-003 | 无异常及陷阱 | 100.0% | twenty_percent_stratified_sample |
| Oh My Pi 基线组 | L2-008 | 单案数据核查 | 100.0% | twenty_percent_stratified_sample |
| Oh My Pi 基线组 | L3-001 | 全年批量审计 | 100.0% | twenty_percent_stratified_sample |
| Oh My Pi 基线组 | L3-006 | 制度与版本判断 | 100.0% | twenty_percent_stratified_sample |
| Oh My Pi 基线组 | L3-009 | 检索与综合报告 | 1.4% | all_comprehensive_reports |
| Oh My Pi 基线组 | L3-010 | 检索与综合报告 | 100.0% | twenty_percent_stratified_sample |
| Oh My Pi 基线组 | TRAP-002 | 无异常及陷阱 | 85.7% | twenty_percent_stratified_sample |
| Oh My Pi 增强组 | L2-003 | 单案数据核查 | 100.0% | twenty_percent_stratified_sample |
| Oh My Pi 增强组 | L3-001 | 全年批量审计 | 100.0% | twenty_percent_stratified_sample |
| Oh My Pi 增强组 | L3-006 | 制度与版本判断 | 87.5% | twenty_percent_stratified_sample |
| Oh My Pi 增强组 | L3-007 | 检索与综合报告 | 100.0% | twenty_percent_stratified_sample |
| Oh My Pi 增强组 | L3-009 | 检索与综合报告 | 95.9% | all_comprehensive_reports |
| Oh My Pi 增强组 | TRAP-003 | 无异常及陷阱 | 100.0% | twenty_percent_stratified_sample |
| OpenClaude 基线组 | L2-003 | 单案数据核查 | 100.0% | twenty_percent_stratified_sample |
| OpenClaude 基线组 | L3-001 | 全年批量审计 | 100.0% | twenty_percent_stratified_sample |
| OpenClaude 基线组 | L3-007 | 检索与综合报告 | 100.0% | twenty_percent_stratified_sample |
| OpenClaude 基线组 | L3-008 | 制度与版本判断 | 100.0% | twenty_percent_stratified_sample |
| OpenClaude 基线组 | L3-009 | 检索与综合报告 | 64.4% | all_comprehensive_reports |
| OpenClaude 基线组 | TRAP-005 | 无异常及陷阱 | 100.0% | twenty_percent_stratified_sample |
| OpenClaude 增强组 | L2-008 | 单案数据核查 | 100.0% | twenty_percent_stratified_sample |
| OpenClaude 增强组 | L3-001 | 全年批量审计 | 100.0% | twenty_percent_stratified_sample |
| OpenClaude 增强组 | L3-008 | 制度与版本判断 | 100.0% | twenty_percent_stratified_sample |
| OpenClaude 增强组 | L3-009 | 检索与综合报告 | 69.9% | all_comprehensive_reports, twenty_percent_stratified_sample |
| OpenClaude 增强组 | TRAP-005 | 无异常及陷阱 | 88.0% | twenty_percent_stratified_sample |
| OpenCode 基线组 | L2-013 | 单案数据核查 | 81.8% | twenty_percent_stratified_sample |
| OpenCode 基线组 | L3-003 | 全年批量审计 | 70.4% | twenty_percent_stratified_sample |
| OpenCode 基线组 | L3-006 | 制度与版本判断 | 100.0% | twenty_percent_stratified_sample |
| OpenCode 基线组 | L3-009 | 检索与综合报告 | 90.4% | all_comprehensive_reports |
| OpenCode 基线组 | L3-010 | 检索与综合报告 | 100.0% | twenty_percent_stratified_sample |
| OpenCode 基线组 | TRAP-003 | 无异常及陷阱 | 68.8% | low_judge_confidence, twenty_percent_stratified_sample |
| OpenCode 增强组 | L2-008 | 单案数据核查 | 100.0% | twenty_percent_stratified_sample |
| OpenCode 增强组 | L3-001 | 全年批量审计 | 100.0% | twenty_percent_stratified_sample |
| OpenCode 增强组 | L3-008 | 制度与版本判断 | 94.1% | twenty_percent_stratified_sample |
| OpenCode 增强组 | L3-009 | 检索与综合报告 | 1.4% | all_comprehensive_reports |
| OpenCode 增强组 | L3-010 | 检索与综合报告 | 100.0% | twenty_percent_stratified_sample |
| OpenCode 增强组 | TRAP-002 | 无异常及陷阱 | 71.4% | low_judge_confidence, twenty_percent_stratified_sample |
| Pi Agent 基线组 | L2-013 | 单案数据核查 | 100.0% | twenty_percent_stratified_sample |
| Pi Agent 基线组 | L3-004 | 全年批量审计 | 41.7% | twenty_percent_stratified_sample |
| Pi Agent 基线组 | L3-006 | 制度与版本判断 | 87.5% | twenty_percent_stratified_sample |
| Pi Agent 基线组 | L3-009 | 检索与综合报告 | 60.3% | all_comprehensive_reports, twenty_percent_stratified_sample |
| Pi Agent 基线组 | TRAP-003 | 无异常及陷阱 | 100.0% | twenty_percent_stratified_sample |
| Pi Agent 增强组 | L1-001 | 制度与版本判断 | 100.0% | twenty_percent_stratified_sample |
| Pi Agent 增强组 | L2-008 | 单案数据核查 | 100.0% | twenty_percent_stratified_sample |
| Pi Agent 增强组 | L3-004 | 全年批量审计 | 100.0% | twenty_percent_stratified_sample |
| Pi Agent 增强组 | L3-009 | 检索与综合报告 | 90.4% | all_comprehensive_reports, twenty_percent_stratified_sample |
| Pi Agent 增强组 | TRAP-003 | 无异常及陷阱 | 81.2% | twenty_percent_stratified_sample |