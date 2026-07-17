# GATE5 可选质量抽查清单

共 75 条。该清单只用于检查Judge稳定性，不参与改分，也不阻塞GATE5。包含全部综合报告、未通过陷阱题、关键错误、低置信度题，以及每组每题型20%的固定哈希分层样本。

| 组别 | 题目 | 题型 | 分数 | 入选原因 |
| --- | --- | --- | ---: | --- |
| Claude Code Best 基线组 | L1-001 | 制度与版本判断 | 100.0 | twenty_percent_stratified_sample |
| Claude Code Best 基线组 | L2-008 | 单案数据核查 | 100.0 | twenty_percent_stratified_sample |
| Claude Code Best 基线组 | L3-001 | 全年批量审计 | 100.0 | twenty_percent_stratified_sample |
| Claude Code Best 基线组 | L3-009 | 检索与综合报告 | 50.0 | all_comprehensive_reports, critical_failure_triggered, twenty_percent_stratified_sample |
| Claude Code Best 基线组 | TRAP-002 | 无异常及陷阱 | 20.0 | critical_failure_triggered, failed_clean_or_trap_case, low_judge_confidence, twenty_percent_stratified_sample |
| Claude Code Best 基线组 | TRAP-003 | 无异常及陷阱 | 20.0 | critical_failure_triggered, failed_clean_or_trap_case |
| Claude Code Best 基线组 | TRAP-005 | 无异常及陷阱 | 45.0 | failed_clean_or_trap_case |
| Claude Code Best 增强组 | L2-003 | 单案数据核查 | 100.0 | twenty_percent_stratified_sample |
| Claude Code Best 增强组 | L3-004 | 全年批量审计 | 55.0 | twenty_percent_stratified_sample |
| Claude Code Best 增强组 | L3-006 | 制度与版本判断 | 87.5 | twenty_percent_stratified_sample |
| Claude Code Best 增强组 | L3-009 | 检索与综合报告 | 77.0 | all_comprehensive_reports, twenty_percent_stratified_sample |
| Claude Code Best 增强组 | TRAP-002 | 无异常及陷阱 | 15.0 | critical_failure_triggered, failed_clean_or_trap_case |
| Claude Code Best 增强组 | TRAP-003 | 无异常及陷阱 | 85.0 | twenty_percent_stratified_sample |
| Claude Code Best 增强组 | TRAP-005 | 无异常及陷阱 | 15.0 | failed_clean_or_trap_case |
| Codex 基线组 | L2-008 | 单案数据核查 | 100.0 | twenty_percent_stratified_sample |
| Codex 基线组 | L3-003 | 全年批量审计 | 15.0 | critical_failure_triggered, twenty_percent_stratified_sample |
| Codex 基线组 | L3-008 | 制度与版本判断 | 100.0 | twenty_percent_stratified_sample |
| Codex 基线组 | L3-009 | 检索与综合报告 | 47.5 | all_comprehensive_reports, twenty_percent_stratified_sample |
| Codex 基线组 | TRAP-002 | 无异常及陷阱 | 45.0 | failed_clean_or_trap_case |
| Codex 基线组 | TRAP-003 | 无异常及陷阱 | 75.0 | twenty_percent_stratified_sample |
| Codex 基线组 | TRAP-005 | 无异常及陷阱 | 15.0 | critical_failure_triggered, failed_clean_or_trap_case |
| Codex 增强组 | L2-003 | 单案数据核查 | 100.0 | twenty_percent_stratified_sample |
| Codex 增强组 | L3-001 | 全年批量审计 | 100.0 | twenty_percent_stratified_sample |
| Codex 增强组 | L3-008 | 制度与版本判断 | 100.0 | twenty_percent_stratified_sample |
| Codex 增强组 | L3-009 | 检索与综合报告 | 15.0 | all_comprehensive_reports, twenty_percent_stratified_sample |
| Codex 增强组 | TRAP-002 | 无异常及陷阱 | 20.0 | critical_failure_triggered, failed_clean_or_trap_case |
| Codex 增强组 | TRAP-003 | 无异常及陷阱 | 45.0 | failed_clean_or_trap_case, twenty_percent_stratified_sample |
| Codex 增强组 | TRAP-005 | 无异常及陷阱 | 45.0 | failed_clean_or_trap_case |
| Oh My Pi 基线组 | L2-008 | 单案数据核查 | 100.0 | twenty_percent_stratified_sample |
| Oh My Pi 基线组 | L3-001 | 全年批量审计 | 100.0 | twenty_percent_stratified_sample |
| Oh My Pi 基线组 | L3-006 | 制度与版本判断 | 100.0 | twenty_percent_stratified_sample |
| Oh My Pi 基线组 | L3-007 | 检索与综合报告 | 65.0 | low_judge_confidence |
| Oh My Pi 基线组 | L3-009 | 检索与综合报告 | 50.0 | all_comprehensive_reports, low_judge_confidence |
| Oh My Pi 基线组 | L3-010 | 检索与综合报告 | 100.0 | twenty_percent_stratified_sample |
| Oh My Pi 基线组 | TRAP-002 | 无异常及陷阱 | 92.5 | twenty_percent_stratified_sample |
| Oh My Pi 基线组 | TRAP-005 | 无异常及陷阱 | 15.0 | critical_failure_triggered, failed_clean_or_trap_case |
| Oh My Pi 增强组 | L2-003 | 单案数据核查 | 100.0 | twenty_percent_stratified_sample |
| Oh My Pi 增强组 | L3-001 | 全年批量审计 | 100.0 | twenty_percent_stratified_sample |
| Oh My Pi 增强组 | L3-006 | 制度与版本判断 | 77.5 | twenty_percent_stratified_sample |
| Oh My Pi 增强组 | L3-007 | 检索与综合报告 | 100.0 | twenty_percent_stratified_sample |
| Oh My Pi 增强组 | L3-009 | 检索与综合报告 | 15.0 | all_comprehensive_reports |
| Oh My Pi 增强组 | TRAP-002 | 无异常及陷阱 | 15.0 | critical_failure_triggered, failed_clean_or_trap_case |
| Oh My Pi 增强组 | TRAP-003 | 无异常及陷阱 | 45.0 | failed_clean_or_trap_case, twenty_percent_stratified_sample |
| OpenClaude 基线组 | L2-003 | 单案数据核查 | 100.0 | twenty_percent_stratified_sample |
| OpenClaude 基线组 | L3-001 | 全年批量审计 | 100.0 | twenty_percent_stratified_sample |
| OpenClaude 基线组 | L3-007 | 检索与综合报告 | 65.0 | twenty_percent_stratified_sample |
| OpenClaude 基线组 | L3-008 | 制度与版本判断 | 100.0 | twenty_percent_stratified_sample |
| OpenClaude 基线组 | L3-009 | 检索与综合报告 | 57.5 | all_comprehensive_reports |
| OpenClaude 基线组 | TRAP-002 | 无异常及陷阱 | 15.0 | critical_failure_triggered, failed_clean_or_trap_case |
| OpenClaude 基线组 | TRAP-005 | 无异常及陷阱 | 15.0 | critical_failure_triggered, failed_clean_or_trap_case, twenty_percent_stratified_sample |
| OpenClaude 增强组 | L2-008 | 单案数据核查 | 100.0 | twenty_percent_stratified_sample |
| OpenClaude 增强组 | L3-001 | 全年批量审计 | 100.0 | twenty_percent_stratified_sample |
| OpenClaude 增强组 | L3-003 | 全年批量审计 | 15.0 | critical_failure_triggered, low_judge_confidence |
| OpenClaude 增强组 | L3-008 | 制度与版本判断 | 100.0 | twenty_percent_stratified_sample |
| OpenClaude 增强组 | L3-009 | 检索与综合报告 | 77.0 | all_comprehensive_reports, twenty_percent_stratified_sample |
| OpenClaude 增强组 | TRAP-002 | 无异常及陷阱 | 45.0 | failed_clean_or_trap_case |
| OpenClaude 增强组 | TRAP-005 | 无异常及陷阱 | 20.0 | critical_failure_triggered, failed_clean_or_trap_case, twenty_percent_stratified_sample |
| OpenCode 基线组 | L2-013 | 单案数据核查 | 85.0 | twenty_percent_stratified_sample |
| OpenCode 基线组 | L3-001 | 全年批量审计 | 50.0 | critical_failure_triggered |
| OpenCode 基线组 | L3-003 | 全年批量审计 | 11.0 | critical_failure_triggered, twenty_percent_stratified_sample |
| OpenCode 基线组 | L3-006 | 制度与版本判断 | 87.5 | twenty_percent_stratified_sample |
| OpenCode 基线组 | L3-007 | 检索与综合报告 | 20.0 | critical_failure_triggered, low_judge_confidence |
| OpenCode 基线组 | L3-009 | 检索与综合报告 | 62.0 | all_comprehensive_reports |
| OpenCode 基线组 | L3-010 | 检索与综合报告 | 100.0 | twenty_percent_stratified_sample |
| OpenCode 基线组 | TRAP-002 | 无异常及陷阱 | 20.0 | critical_failure_triggered, failed_clean_or_trap_case |
| OpenCode 基线组 | TRAP-003 | 无异常及陷阱 | 70.0 | twenty_percent_stratified_sample |
| OpenCode 基线组 | TRAP-005 | 无异常及陷阱 | 15.0 | critical_failure_triggered, failed_clean_or_trap_case |
| OpenCode 增强组 | L2-008 | 单案数据核查 | 100.0 | twenty_percent_stratified_sample |
| OpenCode 增强组 | L3-001 | 全年批量审计 | 50.0 | critical_failure_triggered, twenty_percent_stratified_sample |
| OpenCode 增强组 | L3-008 | 制度与版本判断 | 100.0 | twenty_percent_stratified_sample |
| OpenCode 增强组 | L3-009 | 检索与综合报告 | 78.0 | all_comprehensive_reports |
| OpenCode 增强组 | L3-010 | 检索与综合报告 | 100.0 | twenty_percent_stratified_sample |
| OpenCode 增强组 | TRAP-002 | 无异常及陷阱 | 20.0 | critical_failure_triggered, failed_clean_or_trap_case, twenty_percent_stratified_sample |
| OpenCode 增强组 | TRAP-003 | 无异常及陷阱 | 10.0 | failed_clean_or_trap_case |
| OpenCode 增强组 | TRAP-005 | 无异常及陷阱 | 60.0 | failed_clean_or_trap_case |