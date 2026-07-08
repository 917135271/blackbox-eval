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

## 具体轨迹数据摘录

下面直接放代表性轨迹片段。每个例子都对应真实文件路径和行号,方便回查完整上下文。

### Qwen Code: 查到事实,但把 record_id 放进 anomaly_ids

任务: `L1-006 precise`  
题型: `single_anomaly_lookup`  
真值: `expected_anomaly_ids=["DUP-001"]`  
判卷: `score=0`, `failure_layer=reasoning_or_retrieval_error`  
路径: `runs/gate4_baseline_qwen_v1/qwen-code/L1-006/`

工具调用已经查到了关键事实:

```jsonl
tool_calls.jsonl:2
{"arguments":{"invoice_no":"FP202500000002"},"ok":true,"result_preview":{"invoice_no":"FP202500000002","records":[{"record_id":"R004201","employee_name":"姚瑜","amount":423.79},{"record_id":"R000002","employee_name":"姚瑜","amount":423.79}],"usage_count":2},"server":"expense_query_mcp","tool":"find_invoice_usage"}
```

最终轨迹输出:

```json
trajectory.json:1-13
{
  "anomaly_ids": [
    "R000002",
    "R004201"
  ],
  "answer": "是，R000002使用的发票FP202500000002已在R004201中报销过，构成重复报销",
  "citations": [
    {
      "doc_id": "01_expense_reimbursement_2025.md",
      "clause_no": "第十条"
    }
  ]
}
```

分析: 这不是不会查事实。它已经找到同发票的两条记录,也引用了正确制度条款。失败点是输出字段语义错: `anomaly_ids` 应填异常 ID `DUP-001`,但它填了业务记录 ID `R000002/R004201`。

### Qwen Code: 全年扫描返回了错误集合

任务: `L3-001 precise`  
题型: `full_year_rule_audit`  
真值: `DUP-001` 到 `DUP-006`  
判卷: `score=0`, `failure_layer=reasoning_or_retrieval_error`  
路径: `runs/gate4_baseline_qwen_v1/qwen-code/L3-001/`

结果摘要:

```json
result.json
{
  "timeout": false,
  "format_failure": false,
  "tool_calls_count": 37,
  "answer_json": {
    "anomaly_ids": [
      "R000002",
      "R000005",
      "R004201",
      "R004202",
      "R004207",
      "R004208",
      "R004209",
      "R004210",
      "R004211"
    ]
  }
}
```

轨迹里的最终说明:

```text
trajectory.json:13
"answer": "对全年费用报销记录（共计4240条）进行重复报销专项扫描，共发现4组异常，涉及9条记录ID..."
```

分析: 它声称完成全年扫描,但返回的是 record_id,还混入了拆分报销记录 `R004207/R004208/R004209/R004210/R004211`。专项任务要求的是重复报销异常 ID 集合,所以这是集合归并和答案空间双重错误。

### Qwen Code: 超时不是普通内容错误

任务: `L2-009 casual`  
题型: `policy_data_comparison`  
判卷: `timeout=true`, `format_failure=true`  
路径: `runs/gate4_baseline_qwen_v1/qwen-code/L2-009__casual__r1/`

```json
result.json
{
  "elapsed_seconds": 7277.81,
  "exit_code": null,
  "timeout": true,
  "format_failure": true,
  "parse_error": "Expecting value: line 1 column 1 (char 0)",
  "tool_calls_count": 35,
  "final_text": "(node:77004) [UNDICI-EHPA] Warning... [API Error: terminated (cause: UND_ERR_SOCKET: other side closed)]"
}
```

分析: 这个不是“答错了”,而是执行层和网络/API 调用卡住。`elapsed_seconds` 远超 900 秒,说明当时 Windows 下对子进程树的 timeout 回收不够硬。

### Goose: 查到事实但自造异常 ID

任务: `L1-006 precise`  
题型: `single_anomaly_lookup`  
真值: `expected_anomaly_ids=["DUP-001"]`  
判卷: `score=0`, `failure_layer=reasoning_or_retrieval_error`  
路径: `runs/gate4_baseline_goose_v1/goose/L1-006/`

工具调用:

```jsonl
tool_calls.jsonl:3
{"arguments":{"invoice_no":"FP202500000002"},"ok":true,"result_preview":{"invoice_no":"FP202500000002","records":[{"record_id":"R004201","amount":423.79},{"record_id":"R000002","amount":423.79}],"usage_count":2},"server":"expense_query_mcp","tool":"find_invoice_usage"}
```

轨迹最终输出:

```json
trajectory.json:253
{
  "anomaly_ids": ["A013"],
  "answer": "报销记录R000002...与报销记录R004201使用了同一张发票FP202500000002...构成重复报销。",
  "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "费用报销管理办法-第十条"}]
}
```

分析: Goose 查到了正确的两条记录,也理解了重复报销规则,但最终异常 ID 写成了不存在的 `A013`。这是答案 ID 对齐问题。

### Goose: 最大动作数导致无法输出 JSON

任务: `L1-006 casual`  
题型: `single_anomaly_lookup`  
判卷: `format_failure=true`  
路径: `runs/gate4_baseline_goose_v1/goose/L1-006__casual__r1/`

```text
trajectory.json:547-552
"role": "assistant",
"content": [
  {
    "type": "text",
    "text": "I've reached the maximum number of actions I can do without user input. Would you like me to continue?"
  }
]
```

分析: 这是典型 headless 收口失败。它没有输出标准 JSON,而是停在交互式“是否继续”。Goose 在 `full_year_rule_audit` 里更严重,15 次全部格式失败。

### Trae Agent: 工具查过事实,但最终仍是 step limit

任务: `L1-006 precise`  
题型: `single_anomaly_lookup`  
判卷: `format_failure=true`  
路径: `runs/gate4_baseline_trae_v1/trae-agent/L1-006/`

轨迹中后段仍在查制度:

```json
trajectory.json:957-961
"tool_results": [
  {
    "success": true,
    "result": "{\"query\": \"异常 A001 重复 风险 审计\", \"top_k\": 5, \"results\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"snippets\": [\"第十条 同一发票最多报销1次。发现同一发票在不同报销单中重复出现的,应认定为重复报销风险。\"]}]}"
  }
]
```

最终状态:

```json
trajectory.json:970-972
{
  "success": false,
  "final_result": "Task execution exceeded maximum steps without completion.",
  "execution_time": 23.829715
}
```

分析: Trae 并不是完全不会调用工具,但多步任务很容易在 step budget 内没有完成 `task_done(result=...)`。所以判卷看到的是格式失败,根因是完成信号/步数控制。

### Trae Agent: 长任务超时

任务: `L3-003 distracted`  
题型: `full_year_rule_audit`  
判卷: `timeout=true`, `format_failure=true`  
路径: `runs/gate4_baseline_trae_v1/trae-agent/L3-003__distracted__r1/`

```json
result.json
{
  "elapsed_seconds": 20650.35,
  "exit_code": null,
  "timeout": true,
  "format_failure": true,
  "tool_calls_count": 22,
  "final_text": "Task execution exceeded maximum steps without completion."
}
```

```json
trajectory.json:1629
"final_result": "Task execution exceeded maximum steps without completion."
```

分析: 这是超时和 step limit 叠加。Trae 在长扫描任务里既不能完成全量遍历,也不能稳定返回 JSON。

### Trae Agent: 陷阱题也常因格式失败而不是内容失败

任务: `TRAP-001 precise`  
题型: `clean_but_suspicious`  
判卷: `format_failure=true`  
路径: `runs/gate4_baseline_trae_v1/trae-agent/TRAP-001/`

工具调用片段:

```jsonl
tool_calls.jsonl:3
{"arguments":{"query":"TRAP-001","top_k":10},"ok":true,"result_preview":{"query":"TRAP-001","results":[]},"server":"policy_query_mcp","tool":"search_policy"}
```

最终轨迹:

```json
trajectory.json:1102
"final_result": "Task execution exceeded maximum steps without completion."
```

分析: 该题本该返回空 `anomaly_ids`。Trae 查了制度、列表、部门授权等,但没有收口,所以失败原因主要是格式/完成信号,不是明确业务判断错。

### OpenCode: 唯一一个 L2 通过样例

任务: `L2-006 precise`  
题型: `policy_data_comparison`  
真值: `expected_anomaly_ids=["SPLIT-001"]`  
判卷: `score=1`  
路径: `runs/gate4_baseline_opencode_v1/opencode/L2-006/`

工具调用抓到了制度和关联记录:

```jsonl
tool_calls.jsonl:4
{"arguments":{"date_from":"2025-01-03","date_to":"2025-01-17","employee_id":"E0007","expense_type":"travel_lodging"},"ok":true,"result_preview":{"records":[{"record_id":"R004207","amount":5200.0,"expense_date":"2025-01-10","reason":"拆分报销注入样本1"},{"record_id":"R004208","amount":5200.0,"expense_date":"2025-01-12","reason":"拆分报销注入样本1"}]}}

tool_calls.jsonl:8
{"arguments":{"doc_id":"01_expense_reimbursement_2025.md","query":"拆分报销 第十一条 同一事项 同类事项 拆分"},"ok":true,"result_preview":{"excerpts":["第十一条 不得将同一事项或同类事项拆分为多笔报销以规避审批权限。同一员工、同一费用类型在7天内出现2笔及以上报销..."]}}
```

最终判卷抽取到的 JSON:

```json
result.json
{
  "answer_json": {
    "anomaly_ids": ["SPLIT-001"],
    "answer": "以R004207为线索发现拆分报销异常。员工李丽娟(E0007...)于2025年1月10日提交R004207...又于1月12日提交R004208...两笔合计10400元..."
  }
}
```

分析: 这个样例说明 OpenCode 可以完成中等复杂的制度+业务交叉核查: 查同员工同费用类型时间窗、算合计金额、引用第十一条和授权附件二,最后异常 ID 也对齐到 `SPLIT-001`。

### OpenCode: 全年扫描承认没有完成

任务: `L3-001 precise`  
题型: `full_year_rule_audit`  
判卷: `format_failure=true`  
路径: `runs/gate4_baseline_opencode_v1/opencode/L3-001/`

工具调用显示它只从分页开始扫:

```jsonl
tool_calls.jsonl:5-10
{"arguments":{"page":1},"ok":true,"tool":"list_expenses"}
{"arguments":{"page":2},"ok":true,"tool":"list_expenses"}
{"arguments":{"page":3},"ok":true,"tool":"list_expenses"}
{"arguments":{"page":4},"ok":true,"tool":"list_expenses"}
{"arguments":{"page":5},"ok":true,"tool":"list_expenses"}
{"arguments":{"page":6},"ok":true,"tool":"list_expenses"}
```

最终轨迹:

```text
trajectory.json:679
"我已经达到了最大步骤限制... 已获取了前10页（共85页）的报销记录，共计500条记录... 未完成全量数据扫描... 4240条记录中仅获取了500条（约12%）..."
```

分析: 这是很典型的 L3 失败: 不是完全无能力,而是工具预算/步数预算不足以做 85 页全量扫描。它诚实说明未完成,但这不满足 benchmark 的全量异常集合要求。

### OpenCode: 陷阱题通过,但理由质量一般

任务: `TRAP-001 precise`  
题型: `clean_but_suspicious`  
判卷: `score=1`  
路径: `runs/gate4_baseline_opencode_v1/opencode/TRAP-001/`

最终轨迹:

```json
trajectory.json:388
{
  "anomaly_ids": [],
  "answer": "经核查，费用报销系统与政策文件中均不存在TRAP-001对应的记录，未发现任何异常。",
  "citations": []
}
```

分析: 判卷通过,因为 `no_anomaly` 主要检查 `anomaly_ids=[]`。但理由并不理想: TRAP 任务真正期望的是说明该陷阱记录为什么不构成异常,而不是说记录不存在。这说明当前陷阱题评分对理由质量约束偏弱。

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
