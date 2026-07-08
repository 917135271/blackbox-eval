# GATE 4 Agent Task-Type Analysis

生成时间: 2026-07-08

数据来源:

- `runs/*/grades.jsonl`
- `runs/*/*/*/result.json`
- `runs/*/*/*/trajectory.json`
- 汇总报告: `output/gate4_baseline_report.md`

说明: 每个候选共 165 次尝试,即 55 道任务 x 3 种 prompt variant。下面的 `内容错误` 指输出可解析,但确定性判卷未通过; `格式失败` 指无法抽取标准 JSON 或答案结构不合约; `超时` 指 runner 标记 timeout 或任务实际卡住到超时路径。

## 总体结论

最强和最弱题型非常分明:

| 题型 | 总尝试 | 通过 | 主要结论 |
| --- | ---: | ---: | --- |
| `policy_qa` 纯制度问答 | 48 | 47 | 最稳定,四个候选基本都能完成单跳制度检索和事实回答 |
| `two_hop_retrieval` 双跳制度/数据事实 | 12 | 7 | 可以做简单两跳,但事实表达不够稳 |
| `clean_but_suspicious` 陷阱题 | 60 | 22 | 可解析时通常还行,但 Goose/Trae 被格式拖累 |
| `ground_truth_lookup` 指定异常查 record_id | 60 | 6 | 格式失败多,且 record_id 集合不全 |
| `audit_report` 报告式任务 | 24 | 1 | 能写报告,但很难同时满足 rubric 全部断言 |
| `single_anomaly_lookup` 单条异常判断 | 60 | 0 | 经常把 record_id 当 anomaly_id,或返回不存在的异常 ID |
| `policy_data_comparison` 制度+业务交叉核查 | 300 | 1 | GATE4 最大短板,既有格式失败也有大量内容推理错误 |
| `full_year_rule_audit` 全年专项扫描 | 60 | 0 | 全量分页扫描、去重、集合归并基本失败 |

核心问题不是单一的格式问题。Goose 和 Trae 主要被格式/步数限制拖垮; Qwen 和 OpenCode 则有大量可解析但内容错误的问题。真正最难的是 `anomaly_id_set` 类任务: 420 次尝试只通过 1 次。

## Qwen Code

### 题型表现

| 题型 | 总数 | 通过 | 格式失败 | 内容错误 | 超时 | 判断 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| policy_qa | 12 | 11 | 0 | 1 | 0 | 强,纯制度问答基本可靠 |
| version_check | 3 | 1 | 0 | 2 | 0 | 会查制度,但版本陷阱表述不稳 |
| single_anomaly_lookup | 15 | 0 | 3 | 12 | 0 | 主要是内容错,尤其 ID 命名空间错 |
| ground_truth_lookup | 15 | 6 | 3 | 6 | 0 | 四个候选里相对最好,但 record_id 集合仍不稳 |
| policy_data_comparison | 75 | 0 | 21 | 52 | 2 | 很弱,复杂业务规则推理和异常集合对齐失败 |
| full_year_rule_audit | 15 | 0 | 3 | 12 | 0 | 能扫到部分事实,但返回集合错误 |
| version_trap | 3 | 0 | 0 | 3 | 0 | 版本事实缺关键断言 |
| two_hop_retrieval | 3 | 2 | 0 | 1 | 0 | 中等偏好 |
| near_clause_disambiguation | 3 | 0 | 0 | 3 | 0 | 漏掉不能混用标准的关键结论 |
| audit_report | 6 | 0 | 5 | 1 | 0 | 报告式输出和格式约束冲突明显 |
| clean_but_suspicious | 15 | 6 | 5 | 4 | 0 | 陷阱题可解析时尚可 |

### 典型例子

- 好的地方: `policy_qa` 表现稳定。例如 L1-001 四个候选都答对,Qwen 能命中 `现行部门总经理审批线为10000元`。
- 内容错误: `runs/gate4_baseline_qwen_v1/qwen-code/L1-006/trajectory.json:6`。题目要求返回异常 ID `DUP-001`,Qwen 查到了同一发票事实,但把 `R000002`、`R004201` 这两个 record_id 放进 `anomaly_ids`,属于 ID 命名空间错误。
- 全年扫描错误: `runs/gate4_baseline_qwen_v1/qwen-code/L3-001/trajectory.json:13`。Qwen 声称完成全年 4240 条扫描,但最终返回的是 record_id 和拆分报销记录混合列表,真值应为 `DUP-001` 到 `DUP-006` 六个异常 ID。
- 超时/执行层问题: `runs/gate4_baseline_qwen_v1/qwen-code/L2-009__casual__r1/result.json` 标记 timeout,实际 elapsed 为 7277.81 秒。该类问题更像 runner 对子进程树回收不够硬,不是单纯模型内容错误。

### 失败原因判断

Qwen 的主要问题是“查到了事实但最终字段语义不对”。它能使用工具,也能产生较长分析,但在检测题里经常混淆 `anomaly_id`、`record_id`、自造标签。L2/L3 这种需要跨页扫描和集合精确匹配的任务尤其差。

## Goose

### 题型表现

| 题型 | 总数 | 通过 | 格式失败 | 内容错误 | 超时 | 判断 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| policy_qa | 12 | 12 | 0 | 0 | 0 | 最稳定之一 |
| version_check | 3 | 2 | 0 | 1 | 0 | 基本可用 |
| single_anomaly_lookup | 15 | 0 | 10 | 5 | 0 | 格式和 ID 错误并存 |
| ground_truth_lookup | 15 | 0 | 13 | 2 | 0 | 主要被格式/步数限制卡住 |
| policy_data_comparison | 75 | 0 | 52 | 23 | 0 | 大量格式失败,可解析时也常错 |
| full_year_rule_audit | 15 | 0 | 15 | 0 | 0 | 全部格式失败 |
| version_trap | 3 | 0 | 1 | 2 | 0 | 关键事实漏 |
| two_hop_retrieval | 3 | 2 | 0 | 1 | 0 | 中等 |
| near_clause_disambiguation | 3 | 0 | 0 | 3 | 0 | 漏关键比较结论 |
| audit_report | 6 | 0 | 3 | 3 | 0 | 报告任务不稳 |
| clean_but_suspicious | 15 | 5 | 10 | 0 | 0 | 内容上可以,格式失败很多 |

### 典型例子

- 好的地方: `policy_qa` 为 12/12,说明 Goose 对单跳制度问答非常稳。
- 格式失败: `runs/gate4_baseline_goose_v1/goose/L1-006__casual__r1/trajectory.json:547`。最终输出是 `I've reached the maximum number of actions I can do without user input. Would you like me to continue?`,没有给出 JSON,所以直接 format_failure。
- 内容错误: `runs/gate4_baseline_goose_v1/goose/L1-006/trajectory.json:253`。它查到了 R000002 和 R004201 同发票,但返回 `A013`,真值应为 `DUP-001`。
- 全年扫描失败: `runs/gate4_baseline_goose_v1/goose/L3-001/trajectory.json:544`。同样停在最大动作数并请求继续,导致 full_year_rule_audit 15/15 都是格式失败。

### 失败原因判断

Goose 的最大问题是交互式/动作上限行为不适合无人值守评测。它经常在还没形成最终 JSON 前说需要用户继续。可解析输出中的内容错误也存在,但相较 Trae 更少;主要瓶颈是格式合约和长任务收口。

## Trae Agent

### 题型表现

| 题型 | 总数 | 通过 | 格式失败 | 内容错误 | 超时 | 判断 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| policy_qa | 12 | 12 | 0 | 0 | 0 | 纯制度问答强 |
| version_check | 3 | 2 | 1 | 0 | 0 | 主要是格式问题 |
| single_anomaly_lookup | 15 | 0 | 12 | 3 | 0 | 多数任务没能完成标准 JSON |
| ground_truth_lookup | 15 | 0 | 14 | 1 | 0 | 几乎都格式失败 |
| policy_data_comparison | 75 | 0 | 67 | 8 | 0 | 主要格式失败,少量内容错 |
| full_year_rule_audit | 15 | 0 | 14 | 0 | 1 | 长任务基本跑不完 |
| version_trap | 3 | 0 | 1 | 2 | 0 | 关键事实漏 |
| two_hop_retrieval | 3 | 2 | 0 | 1 | 0 | 中等 |
| near_clause_disambiguation | 3 | 0 | 0 | 3 | 0 | 漏关键比较结论 |
| audit_report | 6 | 0 | 5 | 1 | 0 | 报告任务不稳 |
| clean_but_suspicious | 15 | 2 | 13 | 0 | 0 | 内容可能能判断,但格式合约严重失败 |

### 典型例子

- 好的地方: `policy_qa` 为 12/12,说明基础制度检索能力没有问题。
- 格式/步数失败: `runs/gate4_baseline_trae_v1/trae-agent/L1-006/trajectory.json:971`。最终 `final_result` 是 `Task execution exceeded maximum steps without completion.`,没有标准 JSON。
- 超时: `runs/gate4_baseline_trae_v1/trae-agent/L3-003__distracted__r1/trajectory.json:1629`,elapsed 为 20650.35 秒,最终仍是 `Task execution exceeded maximum steps without completion.`。这是执行/收口问题叠加长任务复杂度。
- 陷阱题格式失败: `runs/gate4_baseline_trae_v1/trae-agent/TRAP-001/trajectory.json:1102`。最终同样是 step limit 文本,所以即便可能查过事实,判卷也无法通过。

### 失败原因判断

Trae 的问题最像“工程可跑,但评测合约不稳定”。它对简单制度问答表现很好,但一旦任务需要多步工具调用,很容易耗尽 step 或不调用 `task_done` 产出标准 JSON。内容错误不是最多的;主要失败层是格式/完成信号。

## OpenCode

### 题型表现

| 题型 | 总数 | 通过 | 格式失败 | 内容错误 | 超时 | 判断 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| policy_qa | 12 | 12 | 0 | 0 | 0 | 强 |
| version_check | 3 | 0 | 0 | 3 | 0 | 版本事实/废止线判断不稳 |
| single_anomaly_lookup | 15 | 0 | 7 | 8 | 0 | 格式和内容各半 |
| ground_truth_lookup | 15 | 0 | 10 | 5 | 0 | record_id 集合失败 |
| policy_data_comparison | 75 | 1 | 25 | 48 | 1 | 四者中唯一 L2 通过,但总体仍很差 |
| full_year_rule_audit | 15 | 0 | 7 | 8 | 0 | 全年扫描不完整 |
| version_trap | 3 | 1 | 0 | 2 | 0 | 比其他候选略好 |
| two_hop_retrieval | 3 | 1 | 0 | 2 | 0 | 中等偏弱 |
| near_clause_disambiguation | 3 | 0 | 0 | 3 | 0 | 漏关键比较结论 |
| audit_report | 6 | 1 | 3 | 2 | 0 | 四者里唯一通过报告类一次 |
| clean_but_suspicious | 15 | 9 | 1 | 5 | 0 | 四者最佳 |

### 典型例子

- 好的地方: `policy_qa` 为 12/12; `clean_but_suspicious` 为 9/15,四者最佳。
- 唯一 L2 通过: `runs/gate4_baseline_opencode_v1/opencode/L2-006/trajectory.json:804`。它正确识别 `R004207` 与 `R004208` 在 7 天内同员工同类型拆分,合计 10400 元,最终 `anomaly_ids` 为 `SPLIT-001`。
- 全年扫描失败: `runs/gate4_baseline_opencode_v1/opencode/L3-001/trajectory.json:679`。它明确承认只获取了前 10 页 500 条,还有 75 页没扫完,因此无法完整识别全部重复报销异常。
- 陷阱题通过但理由不完美: `runs/gate4_baseline_opencode_v1/opencode/TRAP-001/trajectory.json:388`。它返回空 `anomaly_ids`,所以判卷通过;但 answer 说系统中不存在 TRAP-001 对应记录,这不是最理想解释。说明当前 no_anomaly 判卷主要看异常集合,对理由质量约束较弱。

### 失败原因判断

OpenCode 是四者中相对最均衡的: 格式失败比 Goose/Trae 少,陷阱题最好,也是唯一在 L2 过了一次的候选。但它仍然无法处理长分页扫描和精确异常集合归并;大量失败是可解析但内容错。

## 按失败类型归因

### 1. 格式失败

高发候选: Trae, Goose。

常见轨迹:

- Goose 输出 `I've reached the maximum number of actions... Would you like me to continue?`
- Trae 输出 `Task execution exceeded maximum steps without completion.`
- OpenCode 在部分长任务中输出报告式进度说明,但没有标准 JSON。

结论: 这是 harness/headless 收口能力问题,尤其是最大步数、动作上限、最终 JSON 合约执行不稳。

### 2. 内容错误

高发候选: Qwen, OpenCode。

典型模式:

- 把 `record_id` 当作 `anomaly_id`: Qwen L1-006 返回 `R000002`, `R004201`,而非 `DUP-001`。
- 自造异常 ID: Goose L1-006 返回 `A013`,而非 `DUP-001`。
- 返回部分集合: 全年扫描只找到前几组,漏掉后续异常。
- 规则混淆: 重复报销、拆分报销、超标准等集合混在同一个专项任务里。

结论: 这是效果问题,不是格式问题。模型/agent 能查到事实,但没有稳定转换成评测要求的标准答案空间。

### 3. 超时或实际卡住

明确样例:

| 候选 | 任务 | elapsed_s | 说明 |
| --- | --- | ---: | --- |
| qwen-code | L2-009 casual | 7277.81 | timeout,并伴随 API/socket 终止信息 |
| qwen-code | L2-009 distracted | timeout | 同一任务复杂查询下卡住 |
| trae-agent | L3-003 distracted | 20650.35 | step limit 后仍长时间未正常收口 |
| opencode | L2-022 precise | timeout | L2 业务核查长任务卡住 |

结论: 超时数量不多,但暴露 runner 对 Windows 子进程树和部分 harness 的 timeout 回收还需要更硬的进程树 kill。大多数失败不是超时,而是格式或内容。

## 题型建议

1. 保留 `policy_qa` 作为 sanity check,但它区分度太低。
2. 把 `single_anomaly_lookup` 单独作为 ID 对齐专项,因为它清楚暴露 `anomaly_id`/`record_id` 混淆。
3. `policy_data_comparison` 是主战场,应重点用于比较 agent 的真实审计能力。
4. `full_year_rule_audit` 当前过难,更像压力测试;如果希望可比较,需要增加分页预算、工具调用预算或提供更适合批量扫描的原语。
5. `clean_but_suspicious` 可以保留,但 no_anomaly 判卷最好增加理由约束,否则只返回空数组也容易过。
6. 对 Goose/Trae 的下一轮优化应先解决 headless JSON 收口;对 Qwen/OpenCode 的下一轮优化应先解决答案 schema 和 ID 命名空间约束。
