# Rubric v7零区分度题替换说明

## 替换范围

`securities-expense-audit-formal-15-v9`保留15题和五类题型各3题的结构，但删除历史结果中全组满分的`L1-001`、`L2-003`、`L2-008`和`L3-010`，使用四个新ID、新业务对象和新Ground Truth替换。旧题不得进入v7运行或评分。

| 新Case | 替换旧题 | 核查对象 | 关键边界 | 预期结论 |
| --- | --- | --- | --- | --- |
| `PV-CASE-001` | `L1-001` | `R004233` | 9990元低于现行10000元审批线，同时低于X1级一类城市10晚11000元住宿限额 | 无异常；AR-02正确，旧8000元线会造成错误升级 |
| `RA-CASE-001` | `L2-003` | `R000028`、`R004204` | 两条记录使用同一发票且金额均为165.58元 | 1项重复报销风险 |
| `RA-CASE-002` | `L2-008` | `R004209`、`R004210`、`R004211` | 三笔在4天内合计10200元，发票互不相同 | 1项拆分报销风险，不是重复报销 |
| `RR-CASE-001` | `L3-010` | `R000465`、`R000561`、`R000888`、`R001354` | 四笔在7天内合计9764.73元，低于现行10000元但高于废止的8000元线 | 无异常；误用旧线会产生拆分报销误报 |

## 可复算约束

四题的记录集合、员工、费用类型、日期、金额、发票、审批档位和费用标准均由`runner/validate_case_rubrics.py`直接查询`expense_formal.db`复算。生成器还强制校验旧ID完全退出正式集、新旧映射唯一、题面只暴露一个线索记录、无异常题误报封顶40分。

## 区分度Canary

冻结前对六个框架的A/B共12组运行四题，共48次。每题必须同时满足：

- 最高分与最低分极差至少15分；
- 12组总体标准差至少5分；
- 满分组不超过9组；
- 48次格式成功率100%，Judge错误为0。

任一题未通过时，不生成新的GATE3冻结锁。应根据轨迹判断是题面仍过度提示、Rubric过松、工具不可达还是候选普遍具备该能力，再决定继续加难或重新换题。

## 当前执行状态

旧版48次候选运行均完成统一提交，其中28次取得Judge结果，20次因DeepSeek账户返回`HTTP 402 Payment Required`未完成判分。最终复核又发现候选可见制度中的“较高审批线”存在档位歧义，正式库也未显式提供`employee_level`和`city_tier`编码映射；两处均已修正。因此旧轨迹与分数只保留为历史诊断，当前报告状态为`invalidated`，不得仅补判原20个错误项。

账户额度恢复后，应对修正后的四题执行完整12组重跑并重新判分：

```powershell
$env:LLM_API_KEY = [Environment]::GetEnvironmentVariable("LLM_API_KEY", "User")
python runner/run_replacement_discrimination_canary.py --resume --force --workers 12
python runner/grade_replacement_discrimination_canary.py --reset --workers 4
python runner/report_replacement_discrimination_canary.py
```
