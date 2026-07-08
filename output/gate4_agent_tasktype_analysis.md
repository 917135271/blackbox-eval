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

### 各题型典型轨迹

下面每个题型放一个代表样例。样例选择规则: 通过率较高的题型选通过样例; 失败为主的题型选该题型最常见失败层。

#### policy_qa (纯制度问答)

表现: 11/12 通过, 格式失败 0, 内容错误 1, 超时 0。
代表样例: `L1-001` / `precise` / `通过` / `score=1.0` / `failure_layer=ok`。
题面: 现行制度下,单笔费用报销达到多少金额需要部门总经理审批?

工具轨迹摘录 `runs/gate4_baseline_qwen_v1/qwen-code/L1-001/tool_calls.jsonl:2`:

````text
{"arguments": {"doc_id": "01_expense_reimbursement_2025.md"}, "error": null, "ok": true, "result_preview": {"doc_id": "01_expense_reimbursement_2025.md", "text": "<!-- SYNTHETIC TEST FIXTURE — 虚构测试数据,禁止用于交付 -->\n\n# XX证券费用报销管理办法(2025修订版)\n\n发文字号: XX证财规〔2025〕甲号\n\n## 第一章 总则\n\n第一条 为规范XX证券费用报销行为,保证费用真实性、合规性和可追溯性,制定本办法。\n\n第二条 本办法适用于XX证券各部门、分支机构及全体员工发生的差旅、培训、招待、办公、通讯等费用报销事项。\n\n第三条 费用报销实行经办人真实性承诺、部门负责人业务审核、财务复核和授权审批相结合的管理原则。\n\n## 第二章 报销申请与审批\n\n第四条 报销申请应通过费用系统提交,经办人应上传合法有效票据、业务说明和必要的审批依据。\n\n第五条 ...
````

最终轨迹摘录 `runs/gate4_baseline_qwen_v1/qwen-code/L1-001/trajectory.json:3`:

````text
"answer": "单笔费用报销金额达到10,000元（含）及以上需要部门总经理审批，适用于单笔金额≥10,000元且<50,000元的区间。",
````

判卷摘录:

````text
{"anomaly_ids": [], "answer": "单笔费用报销金额达到10,000元（含）及以上需要部门总经理审批，适用于单笔金额≥10,000元且<50,000元的区间。", "citations": [{"doc_id": "03_authorization_management.md", "clause_no": "附件二"}]}
````

原因分析: 通过样例。轨迹显示该题型在此样本上能按要求调用工具并生成可判卷答案。

#### version_check (版本检查)

表现: 1/3 通过, 格式失败 0, 内容错误 2, 超时 0。
代表样例: `L1-003` / `casual` / `内容错误` / `score=0.0` / `failure_layer=fact_miss`。
题面: 旧版费用报销办法里的部门总经理金额是多少?

工具轨迹摘录 `runs/gate4_baseline_qwen_v1/qwen-code/L1-003__casual__r1/tool_calls.jsonl:2`:

````text
{"arguments": {"doc_id": "02_expense_reimbursement_2022_deprecated.md"}, "error": null, "ok": true, "result_preview": {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "text": "<!-- SYNTHETIC TEST FIXTURE — 虚构测试数据,禁止用于交付 -->\n\n# XX证券费用报销管理办法(2022版)\n\n发文字号: XX证财规〔2022〕乙号\n\n## 第一章 总则\n\n第一条 本办法为XX证券旧版费用报销制度文本,仅作为制度沿革留档。现行制度应以《XX证券费用报销管理办法(2025修订版)》为准。\n\n## 第二章 审批权限\n\n第二条 旧版制度曾规定,单笔报销金额达到8000元的,应提交部门总经理审批。\n\n第三条 旧版制度曾规定,单笔报销金额达到30000元的,应提交分管副总审批。\n\n## 第三章 附则\n\n第四条 本办法的审批金额已被后续制度替代,不得作为现行审批依据。\n", ...
````

最终轨迹摘录 `runs/gate4_baseline_qwen_v1/qwen-code/L1-003__casual__r1/trajectory.json:3`:

````text
"answer": "旧版费用报销管理办法(2022版)规定，单笔报销金额达到8000元的，应提交部门总经理审批，即部门总经理的审批权限金额为8000元。",
````

判卷摘录:

````text
{"anomaly_ids": [], "answer": "旧版费用报销管理办法(2022版)规定，单笔报销金额达到8000元的，应提交部门总经理审批，即部门总经理的审批权限金额为8000元。", "citations": [{"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第二条"}]}
````

原因分析: 内容错误样例。输出可解析,但关键事实断言没命中。missing_facts=['该值已废止']

#### single_anomaly_lookup (单条异常判断)

表现: 0/15 通过, 格式失败 3, 内容错误 12, 超时 0。
代表样例: `L1-006` / `precise` / `内容错误` / `score=0.0` / `failure_layer=reasoning_or_retrieval_error`。
题面: 请判断报销记录R000002是否命中重复报销,如命中请返回异常ID。

工具轨迹摘录 `runs/gate4_baseline_qwen_v1/qwen-code/L1-006/tool_calls.jsonl:2`:

````text
{"arguments": {"invoice_no": "FP202500000002"}, "error": null, "ok": true, "result_preview": {"invoice_no": "FP202500000002", "records": [{"amount": 423.79, "department_id": "D008", "employee_id": "E0050", "employee_name": "姚瑜", "expense_date": "2025-02-10", "expense_type": "office_supplies", "invoice_no": "FP202500000002", "record_id": "R004201", "record_no": "BX2025X004201", "reimburse_date": "2025-02-18"}, {"amount": 423.79, "department_id": "D008", "employee_id": "E0050", "employee_name": "姚瑜", ...
````

最终轨迹摘录 `runs/gate4_baseline_qwen_v1/qwen-code/L1-006/trajectory.json:6`:

````text
"answer": "是，R000002使用的发票FP202500000002已在R004201中报销过，构成重复报销",
````

判卷摘录:

````text
{"anomaly_ids": ["R000002", "R004201"], "answer": "是，R000002使用的发票FP202500000002已在R004201中报销过，构成重复报销", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"}]}
````

原因分析: 内容错误样例。输出可解析,但异常集合或答案空间不符合真值。expected_anomaly_ids=['DUP-001'], predicted=['R000002', 'R004201']

#### ground_truth_lookup (异常查记录集合)

表现: 6/15 通过, 格式失败 3, 内容错误 6, 超时 0。
代表样例: `L1-011` / `distracted` / `内容错误` / `score=0.0` / `failure_layer=record_id_miss`。
题面: 只返回真值清单中DUP-002对应的记录集合。

工具轨迹摘录 `runs/gate4_baseline_qwen_v1/qwen-code/L1-011__distracted__r1/tool_calls.jsonl:10`:

````text
{"arguments": {"invoice_no": "FP202500000339"}, "error": null, "ok": true, "result_preview": {"invoice_no": "FP202500000339", "records": [{"amount": 661.56, "department_id": "D005", "employee_id": "E0072", "employee_name": "谢辉", "expense_date": "2025-01-01", "expense_type": "business_entertainment", "invoice_no": "FP202500000339", "record_id": "R000339", "record_no": "BX2025000339", "reimburse_date": "2025-01-03"}], "usage_count": 1}, "server": "expense_query_mcp", "tool": "find_invoice_usage", "ts": ...
````

最终轨迹摘录 `runs/gate4_baseline_qwen_v1/qwen-code/L1-011__distracted__r1/trajectory.json:5`:

````text
"answer": "DUP-002异常（拆分报销）涉及的记录集合：[R001476, R002476] 孔凤兰 training_fee 2025-02-10(2623.87)与2025-02-15(2179.99)，合计4803.86；[R001800, R001996] 孔凤兰 training_fee 2025-03-09(2544.89)与2025-03-11(2722.92)，合计5267.81；[R000242, R003710] 孔凤兰 training_fee 2025-06-16(2743.26)与2025-06-17(1235.80)，合计3979.06；[R003543, R001413] 桂玉梅 training_fee 2025-05-09(3079.24)与2025-05-11(2409.22)，合计5488.46；[R001217, R001447] 谢辉 training_fee 2025-01-13(2768.17)与2025-01-16(3097.73)，合计5865.90；[R001979, R003574] 张亮 training_fee ...
````

判卷摘录:

````text
{"anomaly_ids": ["DUP-002"], "answer": "DUP-002异常（拆分报销）涉及的记录集合：[R001476, R002476] 孔凤兰 training_fee 2025-02-10(2623.87)与2025-02-15(2179.99)，合计4803.86；[R001800, R001996] 孔凤兰 training_fee 2025-03-09(2544.89)与2025-03-11(2722.92)，合计5267.81；[R000242, R003710] 孔凤兰 training_fee ...", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十一条"}]}
````

原因分析: 内容错误样例。异常 ID 可能对了,但 record_id 集合不全或不准。expected_anomaly_ids=['DUP-002'], predicted=['DUP-002']; missing_record_ids=['R000005', 'R004202']

#### policy_data_comparison (制度+业务交叉核查)

表现: 0/75 通过, 格式失败 21, 内容错误 52, 超时 2。
代表样例: `L2-009` / `casual` / `超时` / `score=0.0` / `failure_layer=format_failure`。
题面: 从闭想的报销记录入手,判断是否存在拆分报销问题。

工具轨迹摘录 `runs/gate4_baseline_qwen_v1/qwen-code/L2-009__casual__r1/tool_calls.jsonl:2`:

````text
{"arguments": {"page": 1}, "error": null, "ok": true, "result_preview": {"preview": "{\"has_next\": true, \"page\": 1, \"page_size\": 50, \"records\": [{\"amount\": 661.56, \"department_id\": \"D005\", \"department_name\": \"机构业务部\", \"employee_id\": \"E0072\", \"employee_name\": \"谢辉\", \"expense_date\": \"2025-01-01\", \"expense_type\": \"business_entertainment\", \"invoice_no\": \"FP202500000339\", \"reason\": \"重点客户维护业务招待费\", \"record_id\": \"R000339\", \"record_no\": \"BX2025000339\", \"reimburse_date\": ...
````

最终轨迹摘录 `runs/gate4_baseline_qwen_v1/qwen-code/L2-009__casual__r1/trajectory.json:n/a`:

````text
empty trajectory
````

判卷摘录:

````text
(node:77004) [UNDICI-EHPA] Warning: EnvHttpProxyAgent is experimental, expect them to change at any time. (Use `node --trace-warnings ...` to show where the warning was created) [API Error: terminated (cause: UND_ERR_SOCKET: other side closed)]
````

原因分析: 超时样例。elapsed=7277.81s, 未能稳定收口; 这更偏执行层/长任务预算问题。

#### full_year_rule_audit (全年专项扫描)

表现: 0/15 通过, 格式失败 3, 内容错误 12, 超时 0。
代表样例: `L3-001` / `precise` / `内容错误` / `score=0.0` / `failure_layer=reasoning_or_retrieval_error`。
题面: 请对全年数据做重复报销专项扫描,返回全部异常ID和记录ID集合。

工具轨迹摘录 `runs/gate4_baseline_qwen_v1/qwen-code/L3-001/tool_calls.jsonl:6`:

````text
{"arguments": {"page": 1}, "error": null, "ok": true, "result_preview": {"preview": "{\"has_next\": true, \"page\": 1, \"page_size\": 50, \"records\": [{\"amount\": 661.56, \"department_id\": \"D005\", \"department_name\": \"机构业务部\", \"employee_id\": \"E0072\", \"employee_name\": \"谢辉\", \"expense_date\": \"2025-01-01\", \"expense_type\": \"business_entertainment\", \"invoice_no\": \"FP202500000339\", \"reason\": \"重点客户维护业务招待费\", \"record_id\": \"R000339\", \"record_no\": \"BX2025000339\", \"reimburse_date\": ...
````

最终轨迹摘录 `runs/gate4_baseline_qwen_v1/qwen-code/L3-001/trajectory.json:13`:

````text
"answer": "对全年费用报销记录（共计4240条）进行重复报销专项扫描，共发现4组异常，涉及9条记录ID，具体如下：\n\n一、重复发票异常（违反《XX证券费用报销管理办法(2025修订版)》第十条：同一发票最多报销1次）\n\n1. 发票FP202500000002被重复报销2次：\n - R000002（BX2025000002）：姚瑜，合规风控部，办公用品，423.79元，2025-08-19\n - R004201（BX2025X004201）：姚瑜，合规风控部，办公用品，423.79元，2025-02-10\n 同一员工使用相同发票号在不同时间报销同一金额，构成重复报销。\n\n2. 发票FP202500000005被重复报销2次：\n - R000005（BX2025000005）：刘冬梅，信息技术部，市内交通，88.83元，2025-06-07\n - R004202（BX2025X004202）：刘冬梅，信息技术部，市内交通，88.83元，2025-03-10\n ...
````

判卷摘录:

````text
{"anomaly_ids": ["R000002", "R004201", "R000005", "R004202", "R004207", "R004208", "R004209", "R004210", "R004211"], "answer": "对全年费用报销记录（共计4240条）进行重复报销专项扫描，共发现4组异常，涉及9条记录ID，具体如下： 一、重复发票异常（违反《XX证券费用报销管理办法(2025修订版)》第十条：同一发票最多报销1次） 1. 发票FP202500000002被重复报销2次： - R000002（BX2025000002）：姚瑜，合规风控部，办公用品，423.79元，2025-08-19 - ...", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"}, {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十一条"}]}
````

原因分析: 内容错误样例。输出可解析,但异常集合或答案空间不符合真值。expected_anomaly_ids=['DUP-001', 'DUP-002', 'DUP-003', 'DUP-004', 'DUP-005', 'DUP-006'], predicted=['R000002', 'R000005', 'R004201', 'R004202', 'R004207', 'R004208', 'R004209', 'R004210', 'R004211']

#### version_trap (版本陷阱)

表现: 0/3 通过, 格式失败 0, 内容错误 3, 超时 0。
代表样例: `L3-006` / `precise` / `内容错误` / `score=0.0` / `failure_layer=fact_miss`。
题面: 请判断费用报销审批线应采用2022版还是2025修订版,并指出部门总经理审批线。

工具轨迹摘录 `runs/gate4_baseline_qwen_v1/qwen-code/L3-006/tool_calls.jsonl:2`:

````text
{"arguments": {"doc_id": "01_expense_reimbursement_2025.md"}, "error": null, "ok": true, "result_preview": {"doc_id": "01_expense_reimbursement_2025.md", "text": "<!-- SYNTHETIC TEST FIXTURE — 虚构测试数据,禁止用于交付 -->\n\n# XX证券费用报销管理办法(2025修订版)\n\n发文字号: XX证财规〔2025〕甲号\n\n## 第一章 总则\n\n第一条 为规范XX证券费用报销行为,保证费用真实性、合规性和可追溯性,制定本办法。\n\n第二条 本办法适用于XX证券各部门、分支机构及全体员工发生的差旅、培训、招待、办公、通讯等费用报销事项。\n\n第三条 费用报销实行经办人真实性承诺、部门负责人业务审核、财务复核和授权审批相结合的管理原则。\n\n## 第二章 报销申请与审批\n\n第四条 报销申请应通过费用系统提交,经办人应上传合法有效票据、业务说明和必要的审批依据。\n\n第五条 ...
````

最终轨迹摘录 `runs/gate4_baseline_qwen_v1/qwen-code/L3-006/trajectory.json:6`:

````text
]
````

判卷摘录:

````text
{"anomaly_ids": [], "answer": "应采2025修订版。根据《XX证券授权管理办法》附件二，部门总经理的审批线为：单笔金额大于等于10,000元且小于50,000元。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十四条"}, {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"}]}
````

原因分析: 内容错误样例。输出可解析,但关键事实断言没命中。missing_facts=['2022旧值8000元已废止']

#### two_hop_retrieval (双跳检索)

表现: 2/3 通过, 格式失败 0, 内容错误 1, 超时 0。
代表样例: `L3-007` / `precise` / `通过` / `score=1.0` / `failure_layer=ok`。
题面: 报销办法没有直接列审批金额时,请通过交叉引用找到单笔费用审批档位。

工具轨迹摘录 `runs/gate4_baseline_qwen_v1/qwen-code/L3-007/tool_calls.jsonl:3`:

````text
{"arguments": {"query": "审批金额 审批档位 授权 单笔费用", "top_k": 5}, "error": null, "ok": true, "result_preview": {"preview": "{\"query\": \"审批金额 审批档位 授权 单笔费用\", \"results\": [{\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"score\": 17.844, \"snippets\": [\"第四条 本办法的审批金额已被后续制度替代,不得作为现行审批依据。\", \"第二条 旧版制度曾规定,单笔报销金额达到8000元的,应提交部门总经理审批。\", \"第三条 旧版制度曾规定,单笔报销金额达到30000元的,应提交分管副总审批。\"], \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"score\": 15.5787, \"snippets\": [\"第二条 ...
````

最终轨迹摘录 `runs/gate4_baseline_qwen_v1/qwen-code/L3-007/trajectory.json:6`:

````text
]
````

判卷摘录:

````text
{"anomaly_ids": [], "answer": "《XX证券费用报销管理办法(2025修订版)》第五条明确单笔费用的审批权限不在本办法正文列示具体金额，统一按《XX证券授权管理办法》附件二执行。附件二《费用报销审批权限表》将单笔费用分为五个档位：AR-01（0元至3000元以下，部门经理审批）；AR-02（3000元至10000元以下，部门经理加财务复核）；AR-03（10000元至50000元以下，部门总经理审批）；AR-04（50000元至200000元以下，分管副总审批）；AR- ...", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"}, {"doc_id": "03_authorization_management.md", "clause_no": "第二条"}]}
````

原因分析: 通过样例。轨迹显示该题型在此样本上能按要求调用工具并生成可判卷答案。

#### near_clause_disambiguation (近似条款辨析)

表现: 0/3 通过, 格式失败 0, 内容错误 3, 超时 0。
代表样例: `L3-008` / `precise` / `内容错误` / `score=0.0` / `failure_layer=fact_miss`。
题面: 比较差旅住宿和培训住宿标准,说明为什么不能混用。

工具轨迹摘录 `runs/gate4_baseline_qwen_v1/qwen-code/L3-008/tool_calls.jsonl:5`:

````text
{"arguments": {"doc_id": "04_travel_expense.md", "max_chars": 2000, "query": "差旅住宿标准 职级 城市档位"}, "error": null, "ok": true, "result_preview": {"doc_id": "04_travel_expense.md", "excerpts": ["第三条 住宿标准按员工职级和城市档位确定。员工职级包括员工级、经理级、部门负责人级和高管级;城市档位包括一类城市、二类城市和三类城市。", "第六条 出差期间市内交通实行包干标准:一类城市每日120元,二类城市每日100元,三类城市每日80元。", "第二条 差旅费包括城市间交通费、住宿费、市内交通包干等与公务出差直接相关的费用。", "| 职级 | 一类城市 | 二类城市 | 三类城市 |", "第四条 差旅住宿费标准如下,单位为元/人/晚。", "## 第二章 城市与职级"], "query": "差旅住宿标准 职级 城市档位", "title": "XX证券差旅费管理办法"}, "server": "policy_query_mcp", ...
````

最终轨迹摘录 `runs/gate4_baseline_qwen_v1/qwen-code/L3-008/trajectory.json:3`:

````text
"answer": "一、标准对比\n\n差旅住宿标准（XX证券差旅费管理办法 第四条）：\n - 按员工职级（员工级/经理级/部门负责人级/高管级）和城市档位（一类/二类/三类）双重维度确定。\n - 员工级：一类450元/晚，二类380元/晚，三类300元/晚。\n - 经理级：一类650元/晚，二类550元/晚，三类450元/晚。\n - 部门负责人级：一类850元/晚，二类700元/晚，三类600元/晚。\n - 高管级：一类1100元/晚，二类900元/晚，三类750元/晚。\n\n培训住宿标准（XX证券培训费管理办法 第五条）：\n - 仅按城市档位确定，不区分职级。\n - 一类城市500元/晚，二类城市420元/晚，三类城市350元/晚。\n\n二、不能混用的原因\n\n1. 制度依据不同。差旅住宿受《差旅费管理办法》管辖，培训住宿受《培训费管理办法》管辖，两份制度独立并行，互不替代。\n2. ...
````

判卷摘录:

````text
{"anomaly_ids": [], "answer": "一、标准对比 差旅住宿标准（XX证券差旅费管理办法 第四条）： - 按员工职级（员工级/经理级/部门负责人级/高管级）和城市档位（一类/二类/三类）双重维度确定。 - 员工级：一类450元/晚，二类380元/晚，三类300元/晚。 - 经理级：一类650元/晚，二类550元/晚，三类450元/晚。 - 部门负责人级：一类850元/晚，二类700元/晚，三类600元/晚。 - 高管级：一类1100元/晚，二类900元/晚，三类750元/晚。 ...", "citations": [{"doc_id": "04_travel_expense.md", "clause_no": "第三条"}, {"doc_id": "04_travel_expense.md", "clause_no": "第四条"}]}
````

原因分析: 内容错误样例。输出可解析,但关键事实断言没命中。missing_facts=['两组数值不同不得混用']

#### audit_report (报告式任务)

表现: 0/6 通过, 格式失败 5, 内容错误 1, 超时 0。
代表样例: `L3-009` / `precise` / `格式失败` / `score=0.0` / `failure_layer=format_failure`。
题面: 请基于全年数据出一份异常审计摘要报告,覆盖五类规则并列出关键异常ID。

工具轨迹摘录 `runs/gate4_baseline_qwen_v1/qwen-code/L3-009/tool_calls.jsonl:40`:

````text
{"arguments": {"query": "BX2025X 注入样本 异常", "top_k": 10}, "error": null, "ok": true, "result_preview": {"preview": "{\"query\": \"BX2025X 注入样本 异常\", \"results\": [{\"doc_id\": \"11_attendance_management.md\", \"score\": 5.3079, \"snippets\": [\"第一条 为规范XX证券考勤记录、请假申请、外勤登记和异常处理相关管理事项,制定本办法。\", \"第二条 本办法适用于XX证券总部、分支机构及相关工作人员。\", \"第六条 审核人员应关注事项真实性、授权完整性和资料一致性。\"], \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"score\": 2.6653, \"snippets\": [\"第一条 为规范XX证券日常办公费用和通讯费用报销,制定本办法。\"], ...
````

最终轨迹摘录 `runs/gate4_baseline_qwen_v1/qwen-code/L3-009/trajectory.json:20`:

````text
"answer": "全年异常审计摘要报告\n\n基于《XX证券费用报销管理办法(2025修订版)》及配套制度,覆盖五类规则核查,发现以下关键异常:\n\n【规则一：重复发票(第十条)】\n异常记录: R004201(BX2025X004201)与R000002(BX2025000002)\n员工姚瑜(合规风控部)以同一张发票FP202500000002先后报销两笔办公用品费,金额均为423.79元,违反"同一发票最多报销1次"的规定。\n\n【规则二：拆分报销规避审批(第十一条)】\n异常记录: R004207与R004208(BX2025X004207/BX2025X004208)\n信息技术部部门经理李丽娟(E0007)在2025年1月10日和1月12日(间隔仅2天),以同一费用类型"差旅住宿"分别报销5200元(2笔合计10400元)。单笔均走AR-02审批(仅需部门经理),合并金额已达AR-03档位(≥10000元需部门总经理审批),涉嫌拆分报销规避高级审批。\n\n【规则三：超标准报销(第十二条)】\n异常记录: ...
````

判卷摘录:

````text
以下是基于全年数据的异常审计摘要报告： ```json { "anomaly_ids": [ "R004201", "R000002", "R004207", "R004208", "R004221", "D001", "D002", "D003", "D004", "D005", "D006", "R004227", "R004228" ], "answer": "全年异常审计摘要报告\n\n基于《XX证券费用报销管理办法(2025修订版)》及配套制度,覆盖五类规则核查,发现以下关键异常:\n\n【规则一：重复发票(第十条)】\n异常记录: R004201(BX2025X004201)与R000002(BX2025000002)\n员工姚瑜(合规风控部)以同一张发票FP202500000002先后报销两笔办公用品费,金额均为423.79元,违反"同一发票最多报销1次"的规定。\n\n【规则二：拆分报销规避审批(第十一条)】\n异常记录: ...
````

原因分析: 格式失败样例。最终文本无法抽取出符合契约的 JSON。

#### clean_but_suspicious (陷阱题)

表现: 6/15 通过, 格式失败 5, 内容错误 4, 超时 0。
代表样例: `TRAP-002` / `distracted` / `格式失败` / `score=0.0` / `failure_layer=format_failure`。
题面: 请注意不要因接近阈值、同日同额或近似金额就误报异常。

工具轨迹摘录 `runs/gate4_baseline_qwen_v1/qwen-code/TRAP-002__distracted__r1/tool_calls.jsonl:39`:

````text
{"arguments": {"record_id": "R004207"}, "error": null, "ok": true, "result_preview": {"approvals": [{"approval_id": "A004207", "approval_status": "approved", "approved_at": "2025-01-16", "approver_employee_id": "E0007", "approver_role": "部门经理", "tier_id": "AR-02"}], "record": {"amount": 5200.0, "annual_budget": 301500.0, "budget_year": 2025, "city_tier": "A", "days": null, "department_id": "D007", "department_name": "信息技术部", "employee_id": "E0007", "employee_level": "D1", "employee_name": "李丽娟", "expense_date": ...
````

最终轨迹摘录 `runs/gate4_baseline_qwen_v1/qwen-code/TRAP-002__distracted__r1/trajectory.json:6`:

````text
]
````

判卷摘录:

````text
现在我已收集到所有必要的信息，下面给出完整的审计结果。 ```json { "anomaly_ids": [ "ANOMALY-001", "ANOMALY-002", "ANOMALY-003", "ANOMALY-004", "ANOMALY-005", "ANOMALY-006", "ANOMALY-007", "ANOMALY-008", "ANOMALY-009", "ANOMALY-010" ], "answer": "共发现10项异常，涉及5组拆分报销、3项超标报销和2笔超期报销，全部为注入样本（record_id含X标识、发票号FP2025X开头）。\n\n【拆分报销】\nANOMALY-001：李丽娟（信息技术部部门经理）分别于2025-01-10和2025-01-12报销两笔差旅住宿费各5200元，合计10400元达到AR-03审批线（≥10000元），但每笔仅按AR-02（部门经理+财务复核）处理，且由本人自批，违反《费用报销管理办法》第十一条禁止拆分规避审批的规定。\nANOMALY-002：杨丹（合规风控部部门经理）分别于2025-02-26、2025-02-28、2025-03- ...
````

原因分析: 格式失败样例。最终文本无法抽取出符合契约的 JSON。

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

### 各题型典型轨迹

下面每个题型放一个代表样例。样例选择规则: 通过率较高的题型选通过样例; 失败为主的题型选该题型最常见失败层。

#### policy_qa (纯制度问答)

表现: 12/12 通过, 格式失败 0, 内容错误 0, 超时 0。
代表样例: `L1-001` / `precise` / `通过` / `score=1.0` / `failure_layer=ok`。
题面: 现行制度下,单笔费用报销达到多少金额需要部门总经理审批?

工具轨迹摘录 `runs/gate4_baseline_goose_v1/goose/L1-001/tool_calls.jsonl:3`:

````text
{"arguments": {"doc_id": "03_authorization_management.md", "max_chars": 3000, "query": "附件二 费用报销审批权限表 档位 金额 部门总经理"}, "error": null, "ok": true, "result_preview": {"doc_id": "03_authorization_management.md", "excerpts": ["第二条 本办法附件二适用于费用报销系统自动派生审批角色,相关金额为现行有效审批线。", "## 附件二 费用报销审批权限表", "| 档位 | 单笔金额区间 | 必要审批角色 |", "第一条 为明确XX证券经营管理授权边界,提升审批效率,制定本办法。", "第三条 各部门应按系统派生结果提交审批,不得以口头授权替代系统流程。", "| AR-02 | 大于等于3000元且小于10000元 | 部门经理,并经财务复核 |"], "query": "附件二 费用报销审批权限表 档位 金额 部门总经理", "title": "XX证券授权管理办法"}, "server": ...
````

最终轨迹摘录 `runs/gate4_baseline_goose_v1/goose/L1-001/trajectory.json:312`:

````text
"text": "根据现行制度查询结果，结论如下：\n\n现行《XX证券授权管理办法》附件二《费用报销审批权限表》明确：单笔费用报销金额达到 **10,000元（含）及以上且小于50,000元** 时，必要审批角色为 **部门总经理**（档位 AR-03）。当单笔金额达到50,000元及以上时，上升至分管副总或总经理办公会审批。该金额规定由《XX证券费用报销管理办法(2025修订版)》第五条明确指向授权管理办法附件二执行。\n\n```json\n{\"anomaly_ids\": [], \"answer\": \"单笔费用报销金额达到10000元（含）时，需要部门总经理审批。根据《授权管理办法》附件二，档位AR-03（单笔金额区间≥10000元且<50000元）的必要审批角色为部门总经理。\", \"citations\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"clause_no\": \"第五条\"}, {\"doc_id\": \"03_authorization_management.md\", \"clause_no\": \"附件二 ...
````

判卷摘录:

````text
{"anomaly_ids": [], "answer": "单笔费用报销金额达到10000元（含）时，需要部门总经理审批。根据《授权管理办法》附件二，档位AR-03（单笔金额区间≥10000元且<50000元）的必要审批角色为部门总经理。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"}, {"doc_id": "03_authorization_management.md", "clause_no": "附件二 AR-03"}]}
````

原因分析: 通过样例。轨迹显示该题型在此样本上能按要求调用工具并生成可判卷答案。

#### version_check (版本检查)

表现: 2/3 通过, 格式失败 0, 内容错误 1, 超时 0。
代表样例: `L1-003` / `precise` / `通过` / `score=1.0` / `failure_layer=ok`。
题面: 2022版中部门总经理审批线是多少,它现在是否有效?

工具轨迹摘录 `runs/gate4_baseline_goose_v1/goose/L1-003/tool_calls.jsonl:3`:

````text
{"arguments": {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "max_chars": 2000, "query": "部门总经理 审批 金额 8000"}, "error": null, "ok": true, "result_preview": {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "excerpts": ["第二条 旧版制度曾规定,单笔报销金额达到8000元的,应提交部门总经理审批。", "第四条 本办法的审批金额已被后续制度替代,不得作为现行审批依据。", "第三条 旧版制度曾规定,单笔报销金额达到30000元的,应提交分管副总审批。", "## 第二章 审批权限", "# XX证券费用报销管理办法(2022版)", "## 第一章 总则"], "query": "部门总经理 审批 金额 8000", "title": "XX证券费用报销管理办法(2022版)"}, "server": "policy_query_mcp", "tool": ...
````

最终轨迹摘录 `runs/gate4_baseline_goose_v1/goose/L1-003/trajectory.json:400`:

````text
"text": "```json\n{\"anomaly_ids\": [], \"answer\": \"2022版（已废止）中部门总经理审批线为单笔报销金额达到8000元。该条款现已无效，原因如下：1）2022版自身第1条明确说明以现行制度为准，第4条明确审批金额已被后续制度替代、不得作为现行依据；2）《XX证券费用报销管理办法(2025修订版)》第14条已明令废止2022版；3）现行有效的部门总经理审批线规定于《XX证券授权管理办法》附件二AR-03档位，单笔金额大于等于10000元且小于50000元需经部门总经理审批。\", \"citations\": [{\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"clause_no\": \"第二条\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"clause_no\": \"第四条\"}, {\"doc_id\": \"01_expense_reimbursement_2025.md\", ...
````

判卷摘录:

````text
{"anomaly_ids": [], "answer": "2022版（已废止）中部门总经理审批线为单笔报销金额达到8000元。该条款现已无效，原因如下：1）2022版自身第1条明确说明以现行制度为准，第4条明确审批金额已被后续制度替代、不得作为现行依据；2）《XX证券费用报销管理办法(2025修订版)》第14条已明令废止2022版；3）现行有效的部门总经理审批线规定于《XX证券授权管理办法》附件二AR-03档位，单笔金额大于等于10000元且小于50000元需经部门总经理审批。", "citations": [{"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第二条"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第四条"}]}
````

原因分析: 通过样例。轨迹显示该题型在此样本上能按要求调用工具并生成可判卷答案。

#### single_anomaly_lookup (单条异常判断)

表现: 0/15 通过, 格式失败 10, 内容错误 5, 超时 0。
代表样例: `L1-006` / `casual` / `格式失败` / `score=0.0` / `failure_layer=format_failure`。
题面: 看一下BX2025000002这笔有没有重复报销问题。

工具轨迹摘录 `runs/gate4_baseline_goose_v1/goose/L1-006__casual__r1/tool_calls.jsonl:7`:

````text
{"arguments": {"invoice_no": "FP202500000002"}, "error": null, "ok": true, "result_preview": {"invoice_no": "FP202500000002", "records": [{"amount": 423.79, "department_id": "D008", "employee_id": "E0050", "employee_name": "姚瑜", "expense_date": "2025-02-10", "expense_type": "office_supplies", "invoice_no": "FP202500000002", "record_id": "R004201", "record_no": "BX2025X004201", "reimburse_date": "2025-02-18"}, {"amount": 423.79, "department_id": "D008", "employee_id": "E0050", "employee_name": "姚瑜", ...
````

最终轨迹摘录 `runs/gate4_baseline_goose_v1/goose/L1-006__casual__r1/trajectory.json:552`:

````text
"text": "I've reached the maximum number of actions I can do without user input. Would you like me to continue?"
````

判卷摘录:

````text
I've reached the maximum number of actions I can do without user input. Would you like me to continue?
````

原因分析: 格式失败样例。轨迹停在动作数/步骤数上限或交互式继续提示,没有输出标准 JSON。

#### ground_truth_lookup (异常查记录集合)

表现: 0/15 通过, 格式失败 13, 内容错误 2, 超时 0。
代表样例: `L1-011` / `precise` / `格式失败` / `score=0.0` / `failure_layer=format_failure`。
题面: 异常DUP-002涉及哪些报销记录?

工具轨迹摘录 `runs/gate4_baseline_goose_v1/goose/L1-011/tool_calls.jsonl:8`:

````text
{"arguments": {"invoice_no": "FP202500000339"}, "error": null, "ok": true, "result_preview": {"invoice_no": "FP202500000339", "records": [{"amount": 661.56, "department_id": "D005", "employee_id": "E0072", "employee_name": "谢辉", "expense_date": "2025-01-01", "expense_type": "business_entertainment", "invoice_no": "FP202500000339", "record_id": "R000339", "record_no": "BX2025000339", "reimburse_date": "2025-01-03"}], "usage_count": 1}, "server": "expense_query_mcp", "tool": "find_invoice_usage", "ts": ...
````

最终轨迹摘录 `runs/gate4_baseline_goose_v1/goose/L1-011/trajectory.json:502`:

````text
"text": "I've reached the maximum number of actions I can do without user input. Would you like me to continue?"
````

判卷摘录:

````text
I've reached the maximum number of actions I can do without user input. Would you like me to continue?
````

原因分析: 格式失败样例。轨迹停在动作数/步骤数上限或交互式继续提示,没有输出标准 JSON。

#### policy_data_comparison (制度+业务交叉核查)

表现: 0/75 通过, 格式失败 52, 内容错误 23, 超时 0。
代表样例: `L2-001` / `casual` / `格式失败` / `score=0.0` / `failure_layer=format_failure`。
题面: 从姚瑜的报销记录入手,判断是否存在重复报销问题。

工具轨迹摘录 `runs/gate4_baseline_goose_v1/goose/L2-001__casual__r1/tool_calls.jsonl:3`:

````text
{"arguments": {"employee_id": "E0050"}, "error": null, "ok": true, "result_preview": {"preview": "{\"has_next\": true, \"page\": 1, \"page_size\": 50, \"records\": [{\"amount\": 215.07, \"department_id\": \"D008\", \"department_name\": \"合规风控部\", \"employee_id\": \"E0050\", \"employee_name\": \"姚瑜\", \"expense_date\": \"2025-01-05\", \"expense_type\": \"communication\", \"invoice_no\": \"FP202500002678\", \"reason\": \"客户回访电话费用\", \"record_id\": \"R002678\", \"record_no\": \"BX2025002678\", \"reimburse_date\": ...
````

最终轨迹摘录 `runs/gate4_baseline_goose_v1/goose/L2-001__casual__r1/trajectory.json:332`:

````text
"text": "Ran into this error: Request failed: Bad request (400): The `reasoning_content` in the thinking mode must be passed back to the API..\n\nPlease retry if you think this is a transient or recoverable error."
````

判卷摘录:

````text
Ran into this error: Request failed: Bad request (400): The `reasoning_content` in the thinking mode must be passed back to the API.. Please retry if you think this is a transient or recoverable error.
````

原因分析: 格式失败样例。最终文本无法抽取出符合契约的 JSON。

#### full_year_rule_audit (全年专项扫描)

表现: 0/15 通过, 格式失败 15, 内容错误 0, 超时 0。
代表样例: `L3-001` / `precise` / `格式失败` / `score=0.0` / `failure_layer=format_failure`。
题面: 请对全年数据做重复报销专项扫描,返回全部异常ID和记录ID集合。

工具轨迹摘录 `runs/gate4_baseline_goose_v1/goose/L3-001/tool_calls.jsonl:7`:

````text
{"arguments": {"page": 1}, "error": null, "ok": true, "result_preview": {"preview": "{\"has_next\": true, \"page\": 1, \"page_size\": 50, \"records\": [{\"amount\": 661.56, \"department_id\": \"D005\", \"department_name\": \"机构业务部\", \"employee_id\": \"E0072\", \"employee_name\": \"谢辉\", \"expense_date\": \"2025-01-01\", \"expense_type\": \"business_entertainment\", \"invoice_no\": \"FP202500000339\", \"reason\": \"重点客户维护业务招待费\", \"record_id\": \"R000339\", \"record_no\": \"BX2025000339\", \"reimburse_date\": ...
````

最终轨迹摘录 `runs/gate4_baseline_goose_v1/goose/L3-001/trajectory.json:549`:

````text
"text": "I've reached the maximum number of actions I can do without user input. Would you like me to continue?"
````

判卷摘录:

````text
I've reached the maximum number of actions I can do without user input. Would you like me to continue?
````

原因分析: 格式失败样例。轨迹停在动作数/步骤数上限或交互式继续提示,没有输出标准 JSON。

#### version_trap (版本陷阱)

表现: 0/3 通过, 格式失败 1, 内容错误 2, 超时 0。
代表样例: `L3-006` / `precise` / `内容错误` / `score=0.0` / `failure_layer=fact_miss`。
题面: 请判断费用报销审批线应采用2022版还是2025修订版,并指出部门总经理审批线。

工具轨迹摘录 `runs/gate4_baseline_goose_v1/goose/L3-006/tool_calls.jsonl:3`:

````text
{"arguments": {"doc_id": "01_expense_reimbursement_2025.md", "max_chars": 4000, "query": "审批权限 部门总经理 审批线 金额"}, "error": null, "ok": true, "result_preview": {"doc_id": "01_expense_reimbursement_2025.md", "excerpts": ["第十一条 不得将同一事项或同类事项拆分为多笔报销以规避审批权限。同一员工、同一费用类型在7天内出现2笔及以上报销,且合计金额达到《授权管理办法》附件二较高审批线的,应重点核查拆分规避审批。", "第五条 单笔费用报销的审批权限,不在本办法正文列示具体金额,统一按《XX证券授权管理办法》附件二执行。费用系统应按附件二自动派生审批角色。", "第三条 费用报销实行经办人真实性承诺、部门负责人业务审核、财务复核和授权审批相结合的管理原则。", "第十三条 部门年度预算不足时不得继续报销。预算使用达到预算额度的1.0倍后,确需发生的费用应履行专项审批。", "第十二条 ...
````

最终轨迹摘录 `runs/gate4_baseline_goose_v1/goose/L3-006/trajectory.json:418`:

````text
"text": "```json\n{\"anomaly_ids\": [], \"answer\": \"应采用2025修订版作为现行审批依据，2022版已废止不得使用。依据《XX证券授权管理办法》附件二，部门总经理审批线为：单笔报销金额大于等于10000元且小于50000元（AR-03档位），该档位必要审批角色为部门总经理。\", \"citations\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"clause_no\": \"费用报销管理办法-第五条\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"clause_no\": \"费用报销管理办法(2022版)-第一条\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"clause_no\": \"费用报销管理办法(2022版)-第四条\"}, {\"doc_id\": ...
````

判卷摘录:

````text
{"anomaly_ids": [], "answer": "应采用2025修订版作为现行审批依据，2022版已废止不得使用。依据《XX证券授权管理办法》附件二，部门总经理审批线为：单笔报销金额大于等于10000元且小于50000元（AR-03档位），该档位必要审批角色为部门总经理。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "费用报销管理办法-第五条"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "费用报销管理办法(2022版)-第一条"}]}
````

原因分析: 内容错误样例。输出可解析,但关键事实断言没命中。missing_facts=['2022旧值8000元已废止']

#### two_hop_retrieval (双跳检索)

表现: 2/3 通过, 格式失败 0, 内容错误 1, 超时 0。
代表样例: `L3-007` / `precise` / `通过` / `score=1.0` / `failure_layer=ok`。
题面: 报销办法没有直接列审批金额时,请通过交叉引用找到单笔费用审批档位。

工具轨迹摘录 `runs/gate4_baseline_goose_v1/goose/L3-007/tool_calls.jsonl:3`:

````text
{"arguments": {"doc_id": "03_authorization_management.md", "max_chars": 2000, "query": "附件二 费用报销审批权限表 档位 金额"}, "error": null, "ok": true, "result_preview": {"doc_id": "03_authorization_management.md", "excerpts": ["第二条 本办法附件二适用于费用报销系统自动派生审批角色,相关金额为现行有效审批线。", "## 附件二 费用报销审批权限表", "| 档位 | 单笔金额区间 | 必要审批角色 |", "第一条 为明确XX证券经营管理授权边界,提升审批效率,制定本办法。", "第三条 各部门应按系统派生结果提交审批,不得以口头授权替代系统流程。", "第四条 授权事项发生调整的,以最新修订版附件为准。"], "query": "附件二 费用报销审批权限表 档位 金额", "title": "XX证券授权管理办法"}, "server": "policy_query_mcp", "tool": ...
````

最终轨迹摘录 `runs/gate4_baseline_goose_v1/goose/L3-007/trajectory.json:373`:

````text
"text": "```json\n{\"anomaly_ids\": [], \"answer\": \"《XX证券费用报销管理办法(2025修订版)》第五条明确单笔费用报销的审批金额不在正文列示,统一按《XX证券授权管理办法》附件二执行。交叉引用附件二费用报销审批权限表,得到5个档位:AR-01(>=0且<3000元,部门经理审批)、AR-02(>=3000且<10000元,部门经理+财务复核)、AR-03(>=10000且<50000元,部门总经理审批)、AR-04(>=50000且<200000元,分管副总审批)、AR-05(>=200000元,总经理办公会审批)。\", \"citations\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"clause_no\": \"第五条\"}, {\"doc_id\": \"03_authorization_management.md\", \"clause_no\": \"附件二\"}]}\n```"
````

判卷摘录:

````text
{"anomaly_ids": [], "answer": "《XX证券费用报销管理办法(2025修订版)》第五条明确单笔费用报销的审批金额不在正文列示,统一按《XX证券授权管理办法》附件二执行。交叉引用附件二费用报销审批权限表,得到5个档位:AR-01(>=0且<3000元,部门经理审批)、AR-02(>=3000且<10000元,部门经理+财务复核)、AR-03(>=10000且<50000元,部门总经理审批)、AR-04(>=50000且<200000元,分管副总审批)、AR-05(>=200000元,总经理办公会审批)。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"}, {"doc_id": "03_authorization_management.md", "clause_no": "附件二"}]}
````

原因分析: 通过样例。轨迹显示该题型在此样本上能按要求调用工具并生成可判卷答案。

#### near_clause_disambiguation (近似条款辨析)

表现: 0/3 通过, 格式失败 0, 内容错误 3, 超时 0。
代表样例: `L3-008` / `precise` / `内容错误` / `score=0.0` / `failure_layer=fact_miss`。
题面: 比较差旅住宿和培训住宿标准,说明为什么不能混用。

工具轨迹摘录 `runs/gate4_baseline_goose_v1/goose/L3-008/tool_calls.jsonl:5`:

````text
{"arguments": {"doc_id": "05_training_expense.md", "max_chars": 500, "query": "培训住宿标准 不得与差旅住宿标准混用"}, "error": null, "ok": true, "result_preview": {"doc_id": "05_training_expense.md", "excerpts": ["第六条 培训住宿标准仅适用于培训期间住宿,不得与差旅住宿标准混用。", "第五条 培训期间住宿标准如下,单位为元/人/晚。", "| 城市档位 | 培训住宿标准 |", "第一条 为加强XX证券培训经费管理,规范内部培训和外部培训费用支出,制定本办法。", "## 第二章 培训费用标准", "第三条 内部培训综合费用每日不超过800元。"], "query": "培训住宿标准 不得与差旅住宿标准混用", "title": "XX证券培训费管理办法"}, "server": "policy_query_mcp", "tool": "get_policy_excerpt", "ts": 1783415411.2589283}
````

最终轨迹摘录 `runs/gate4_baseline_goose_v1/goose/L3-008/trajectory.json:339`:

````text
"text": "```json\n{\"anomaly_ids\": [], \"answer\": \"差旅住宿标准与培训住宿标准在确定维度和金额上均不同,制度明确规定不得混用。差异如下:1)差旅住宿标准按职级和城市档位双维度确定,员工级/经理级/部门负责人级/高管级在一类城市分别为450/650/850/1100元/人/晚;2)培训住宿标准仅按城市档位区分,不区分职级,一类城市500元、二类城市420元、三类城市350元/人/晚。3)混用会导致:若按差旅低职级标准报销培训住宿会产生金额缺口,若按培训标准报销差旅则对高职级人员偏低;且制度依据不同,差旅费管理办法第七条明确培训期间住宿不适用差旅住宿表,培训费管理办法第六条明确培训住宿标准不得与差旅住宿标准混用。\", \"citations\": [{\"doc_id\": \"04_travel_expense.md\", \"clause_no\": \"XX证券差旅费管理办法-第三条\"}, {\"doc_id\": \"04_travel_expense.md\", \"clause_no\": \"XX证券差旅费管理办法-第四条\"}, ...
````

判卷摘录:

````text
{"anomaly_ids": [], "answer": "...", "citations": [{"doc_id": "04_travel_expense.md", "clause_no": "XX证券差旅费管理办法-第三条"}, {"doc_id": "04_travel_expense.md", "clause_no": "XX证券差旅费管理办法-第四条"}]}
````

原因分析: 内容错误样例。输出可解析,但关键事实断言没命中。missing_facts=['两组数值不同不得混用']

#### audit_report (报告式任务)

表现: 0/6 通过, 格式失败 3, 内容错误 3, 超时 0。
代表样例: `L3-009` / `precise` / `格式失败` / `score=0.0` / `failure_layer=format_failure`。
题面: 请基于全年数据出一份异常审计摘要报告,覆盖五类规则并列出关键异常ID。

工具轨迹摘录 `runs/gate4_baseline_goose_v1/goose/L3-009/tool_calls.jsonl:3`:

````text
{"arguments": {"doc_id": "01_expense_reimbursement_2025.md"}, "error": null, "ok": true, "result_preview": {"doc_id": "01_expense_reimbursement_2025.md", "text": "<!-- SYNTHETIC TEST FIXTURE — 虚构测试数据,禁止用于交付 -->\n\n# XX证券费用报销管理办法(2025修订版)\n\n发文字号: XX证财规〔2025〕甲号\n\n## 第一章 总则\n\n第一条 为规范XX证券费用报销行为,保证费用真实性、合规性和可追溯性,制定本办法。\n\n第二条 本办法适用于XX证券各部门、分支机构及全体员工发生的差旅、培训、招待、办公、通讯等费用报销事项。\n\n第三条 费用报销实行经办人真实性承诺、部门负责人业务审核、财务复核和授权审批相结合的管理原则。\n\n## 第二章 报销申请与审批\n\n第四条 报销申请应通过费用系统提交,经办人应上传合法有效票据、业务说明和必要的审批依据。\n\n第五条 ...
````

最终轨迹摘录 `runs/gate4_baseline_goose_v1/goose/L3-009/trajectory.json:1035`:

````text
"text": "Ran into this error: Request failed: Bad request (400): The `reasoning_content` in the thinking mode must be passed back to the API..\n\nPlease retry if you think this is a transient or recoverable error."
````

判卷摘录:

````text
Ran into this error: Request failed: Bad request (400): The `reasoning_content` in the thinking mode must be passed back to the API.. Please retry if you think this is a transient or recoverable error.
````

原因分析: 格式失败样例。最终文本无法抽取出符合契约的 JSON。

#### clean_but_suspicious (陷阱题)

表现: 5/15 通过, 格式失败 10, 内容错误 0, 超时 0。
代表样例: `TRAP-001` / `precise` / `格式失败` / `score=0.0` / `failure_layer=format_failure`。
题面: 请核查TRAP-001涉及的记录是否构成异常,正确时应说明无异常。

工具轨迹摘录 `runs/gate4_baseline_goose_v1/goose/TRAP-001/tool_calls.jsonl:2`:

````text
{"arguments": {}, "error": null, "ok": true, "result_preview": {"preview": "{\"has_next\": true, \"page\": 1, \"page_size\": 50, \"records\": [{\"amount\": 661.56, \"department_id\": \"D005\", \"department_name\": \"机构业务部\", \"employee_id\": \"E0072\", \"employee_name\": \"谢辉\", \"expense_date\": \"2025-01-01\", \"expense_type\": \"business_entertainment\", \"invoice_no\": \"FP202500000339\", \"reason\": \"重点客户维护业务招待费\", \"record_id\": \"R000339\", \"record_no\": \"BX2025000339\", \"reimburse_date\": ...
````

最终轨迹摘录 `runs/gate4_baseline_goose_v1/goose/TRAP-001/trajectory.json:537`:

````text
"text": "I've reached the maximum number of actions I can do without user input. Would you like me to continue?"
````

判卷摘录:

````text
I've reached the maximum number of actions I can do without user input. Would you like me to continue?
````

原因分析: 格式失败样例。轨迹停在动作数/步骤数上限或交互式继续提示,没有输出标准 JSON。

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

### 各题型典型轨迹

下面每个题型放一个代表样例。样例选择规则: 通过率较高的题型选通过样例; 失败为主的题型选该题型最常见失败层。

#### policy_qa (纯制度问答)

表现: 12/12 通过, 格式失败 0, 内容错误 0, 超时 0。
代表样例: `L1-001` / `precise` / `通过` / `score=1.0` / `failure_layer=ok`。
题面: 现行制度下,单笔费用报销达到多少金额需要部门总经理审批?

工具轨迹摘录 `runs/gate4_baseline_trae_v1/trae-agent/L1-001/tool_calls.jsonl:5`:

````text
{"arguments": {"doc_id": "01_expense_reimbursement_2025.md", "max_chars": 2000, "query": "单笔费用报销审批权限 附件二"}, "error": null, "ok": true, "result_preview": {"doc_id": "01_expense_reimbursement_2025.md", "excerpts": ["第五条 单笔费用报销的审批权限,不在本办法正文列示具体金额,统一按《XX证券授权管理办法》附件二执行。费用系统应按附件二自动派生审批角色。", "第十一条 不得将同一事项或同类事项拆分为多笔报销以规避审批权限。同一员工、同一费用类型在7天内出现2笔及以上报销,且合计金额达到《授权管理办法》附件二较高审批线的,应重点核查拆分规避审批。", "第三条 费用报销实行经办人真实性承诺、部门负责人业务审核、财务复核和授权审批相结合的管理原则。", "第七条 员工应在费用发生后60天内提交报销申请;超过期限的,原则上不得报销。", "第十条 ...
````

最终轨迹摘录 `runs/gate4_baseline_trae_v1/trae-agent/L1-001/trajectory.json:665`:

````text
"final_result": "{\"anomaly_ids\": [], \"answer\": \"现行制度下,单笔费用报销达到10000元(含)需要部门总经理审批。根据《XX证券授权管理办法》附件二费用报销审批权限表,档位AR-03规定单笔金额大于等于10000元且小于50000元的必要审批角色为部门总经理。\", \"citations\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"clause_no\": \"第五条\"}, {\"doc_id\": \"03_authorization_management.md\", \"clause_no\": \"附件二-AR-03\"}]}",
````

判卷摘录:

````text
{"anomaly_ids": [], "answer": "现行制度下,单笔费用报销达到10000元(含)需要部门总经理审批。根据《XX证券授权管理办法》附件二费用报销审批权限表,档位AR-03规定单笔金额大于等于10000元且小于50000元的必要审批角色为部门总经理。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"}, {"doc_id": "03_authorization_management.md", "clause_no": "附件二-AR-03"}]}
````

原因分析: 通过样例。轨迹显示该题型在此样本上能按要求调用工具并生成可判卷答案。

#### version_check (版本检查)

表现: 2/3 通过, 格式失败 1, 内容错误 0, 超时 0。
代表样例: `L1-003` / `precise` / `通过` / `score=1.0` / `failure_layer=ok`。
题面: 2022版中部门总经理审批线是多少,它现在是否有效?

工具轨迹摘录 `runs/gate4_baseline_trae_v1/trae-agent/L1-003/tool_calls.jsonl:2`:

````text
{"arguments": {"doc_id": "02_expense_reimbursement_2022_deprecated.md"}, "error": null, "ok": true, "result_preview": {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "text": "<!-- SYNTHETIC TEST FIXTURE — 虚构测试数据,禁止用于交付 -->\n\n# XX证券费用报销管理办法(2022版)\n\n发文字号: XX证财规〔2022〕乙号\n\n## 第一章 总则\n\n第一条 本办法为XX证券旧版费用报销制度文本,仅作为制度沿革留档。现行制度应以《XX证券费用报销管理办法(2025修订版)》为准。\n\n## 第二章 审批权限\n\n第二条 旧版制度曾规定,单笔报销金额达到8000元的,应提交部门总经理审批。\n\n第三条 旧版制度曾规定,单笔报销金额达到30000元的,应提交分管副总审批。\n\n## 第三章 附则\n\n第四条 本办法的审批金额已被后续制度替代,不得作为现行审批依据。\n", ...
````

最终轨迹摘录 `runs/gate4_baseline_trae_v1/trae-agent/L1-003/trajectory.json:547`:

````text
"final_result": "```json\n{\"anomaly_ids\": [], \"answer\": \"2022版规定部门总经理审批线为单笔报销金额达到8000元（即≥8000元需部门总经理审批）。但该制度已随2025修订版施行而废止，不再有效。现行有效规定依据《XX证券授权管理办法》附件二，部门总经理审批线为单笔≥10000元且<50000元（AR-03档位）。\", \"citations\": [{\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"clause_no\": \"第二条\"}, {\"doc_id\": \"01_expense_reimbursement_2025.md\", \"clause_no\": \"第十四条\"}]}\n```",
````

判卷摘录:

````text
{"anomaly_ids": [], "answer": "2022版规定部门总经理审批线为单笔报销金额达到8000元（即≥8000元需部门总经理审批）。但该制度已随2025修订版施行而废止，不再有效。现行有效规定依据《XX证券授权管理办法》附件二，部门总经理审批线为单笔≥10000元且<50000元（AR-03档位）。", "citations": [{"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第二条"}, {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十四条"}]}
````

原因分析: 通过样例。轨迹显示该题型在此样本上能按要求调用工具并生成可判卷答案。

#### single_anomaly_lookup (单条异常判断)

表现: 0/15 通过, 格式失败 12, 内容错误 3, 超时 0。
代表样例: `L1-006` / `precise` / `格式失败` / `score=0.0` / `failure_layer=format_failure`。
题面: 请判断报销记录R000002是否命中重复报销,如命中请返回异常ID。

工具轨迹摘录 `runs/gate4_baseline_trae_v1/trae-agent/L1-006/tool_calls.jsonl:3`:

````text
{"arguments": {"invoice_no": "FP202500000002"}, "error": null, "ok": true, "result_preview": {"invoice_no": "FP202500000002", "records": [{"amount": 423.79, "department_id": "D008", "employee_id": "E0050", "employee_name": "姚瑜", "expense_date": "2025-02-10", "expense_type": "office_supplies", "invoice_no": "FP202500000002", "record_id": "R004201", "record_no": "BX2025X004201", "reimburse_date": "2025-02-18"}, {"amount": 423.79, "department_id": "D008", "employee_id": "E0050", "employee_name": "姚瑜", ...
````

最终轨迹摘录 `runs/gate4_baseline_trae_v1/trae-agent/L1-006/trajectory.json:971`:

````text
"final_result": "Task execution exceeded maximum steps without completion.",
````

判卷摘录:

````text
Task execution exceeded maximum steps without completion.
````

原因分析: 格式失败样例。轨迹停在动作数/步骤数上限或交互式继续提示,没有输出标准 JSON。

#### ground_truth_lookup (异常查记录集合)

表现: 0/15 通过, 格式失败 14, 内容错误 1, 超时 0。
代表样例: `L1-011` / `precise` / `格式失败` / `score=0.0` / `failure_layer=format_failure`。
题面: 异常DUP-002涉及哪些报销记录?

工具轨迹摘录 `runs/gate4_baseline_trae_v1/trae-agent/L1-011/tool_calls.jsonl:8`:

````text
{"arguments": {"page": 1}, "error": null, "ok": true, "result_preview": {"preview": "{\"has_next\": true, \"page\": 1, \"page_size\": 50, \"records\": [{\"amount\": 661.56, \"department_id\": \"D005\", \"department_name\": \"机构业务部\", \"employee_id\": \"E0072\", \"employee_name\": \"谢辉\", \"expense_date\": \"2025-01-01\", \"expense_type\": \"business_entertainment\", \"invoice_no\": \"FP202500000339\", \"reason\": \"重点客户维护业务招待费\", \"record_id\": \"R000339\", \"record_no\": \"BX2025000339\", \"reimburse_date\": ...
````

最终轨迹摘录 `runs/gate4_baseline_trae_v1/trae-agent/L1-011/trajectory.json:1192`:

````text
"final_result": "Task execution exceeded maximum steps without completion.",
````

判卷摘录:

````text
Task execution exceeded maximum steps without completion.
````

原因分析: 格式失败样例。轨迹停在动作数/步骤数上限或交互式继续提示,没有输出标准 JSON。

#### policy_data_comparison (制度+业务交叉核查)

表现: 0/75 通过, 格式失败 67, 内容错误 8, 超时 0。
代表样例: `L2-001` / `precise` / `格式失败` / `score=0.0` / `failure_layer=format_failure`。
题面: 结合制度和业务数据,核查以R000002为线索的重复报销异常,返回异常ID和记录ID集合。

工具轨迹摘录 `runs/gate4_baseline_trae_v1/trae-agent/L2-001/tool_calls.jsonl:3`:

````text
{"arguments": {"record_id": "R000002"}, "error": null, "ok": true, "result_preview": {"approvals": [{"approval_id": "A000002", "approval_status": "approved", "approved_at": "2025-09-09", "approver_employee_id": "E0008", "approver_role": "部门经理", "tier_id": "AR-01"}], "record": {"amount": 423.79, "annual_budget": 381600.0, "budget_year": 2025, "city_tier": null, "days": null, "department_id": "D008", "department_name": "合规风控部", "employee_id": "E0050", "employee_level": "X1", "employee_name": "姚瑜", "expense_date": ...
````

最终轨迹摘录 `runs/gate4_baseline_trae_v1/trae-agent/L2-001/trajectory.json:833`:

````text
"final_result": "```json\n{\"anomaly_ids\": [\"A001\"], \"answer\": \"发现重复报销异常：发票FP202500000002在报销单R000002（2025-09-09，姚瑜，合规风控部，办公用品，423.79元）与报销单R004201（2025-02-18，姚瑜，合规风控部，办公用品，423.79元）中被重复使用。两笔报销均属同一员工（E0050）、同一部门（D008）、同一费用类型（办公用品）、同一金额（423.79元），违反了《XX证券费用报销管理办法(2025修订版)》第十条\"同一发票最多报销1次\"的规定，应认定为重复报销风险。涉及记录ID：R000002、R004201。\", \"citations\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"clause_no\": \"第十条\"}]}\n```",
````

判卷摘录:

````text
```json {"anomaly_ids": ["A001"], "answer": "发现重复报销异常：发票FP202500000002在报销单R000002（2025-09-09，姚瑜，合规风控部，办公用品，423.79元）与报销单R004201（2025-02-18，姚瑜，合规风控部，办公用品，423.79元）中被重复使用。两笔报销均属同一员工（E0050）、同一部门（D008）、同一费用类型（办公用品）、同一金额（423.79元），违反了《XX证券费用报销管理办法(2025修订版)》第十条"同一发票最多报销1次"的规定，应认定为重复报销风险。涉及记录ID：R000002、R004201。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"}]} ```
````

原因分析: 格式失败样例。最终文本无法抽取出符合契约的 JSON。

#### full_year_rule_audit (全年专项扫描)

表现: 0/15 通过, 格式失败 14, 内容错误 0, 超时 1。
代表样例: `L3-003` / `distracted` / `超时` / `score=0.0` / `failure_layer=format_failure`。
题面: 只输出超标准专项结果,并给出对应制度条款。

工具轨迹摘录 `runs/gate4_baseline_trae_v1/trae-agent/L3-003__distracted__r1/tool_calls.jsonl:9`:

````text
{"arguments": {"page": 1}, "error": null, "ok": true, "result_preview": {"preview": "{\"has_next\": true, \"page\": 1, \"page_size\": 50, \"records\": [{\"amount\": 661.56, \"department_id\": \"D005\", \"department_name\": \"机构业务部\", \"employee_id\": \"E0072\", \"employee_name\": \"谢辉\", \"expense_date\": \"2025-01-01\", \"expense_type\": \"business_entertainment\", \"invoice_no\": \"FP202500000339\", \"reason\": \"重点客户维护业务招待费\", \"record_id\": \"R000339\", \"record_no\": \"BX2025000339\", \"reimburse_date\": ...
````

最终轨迹摘录 `runs/gate4_baseline_trae_v1/trae-agent/L3-003__distracted__r1/trajectory.json:1629`:

````text
"final_result": "Task execution exceeded maximum steps without completion.",
````

判卷摘录:

````text
Task execution exceeded maximum steps without completion.
````

原因分析: 超时样例。elapsed=20650.35s, 未能稳定收口; 这更偏执行层/长任务预算问题。

#### version_trap (版本陷阱)

表现: 0/3 通过, 格式失败 1, 内容错误 2, 超时 0。
代表样例: `L3-006` / `precise` / `内容错误` / `score=0.0` / `failure_layer=fact_miss`。
题面: 请判断费用报销审批线应采用2022版还是2025修订版,并指出部门总经理审批线。

工具轨迹摘录 `runs/gate4_baseline_trae_v1/trae-agent/L3-006/tool_calls.jsonl:6`:

````text
{"arguments": {"doc_id": "01_expense_reimbursement_2025.md", "max_chars": 1000, "query": "废止 2022版 施行 2025修订版"}, "error": null, "ok": true, "result_preview": {"doc_id": "01_expense_reimbursement_2025.md", "excerpts": ["第十四条 本办法自二〇二五年一月一日起施行。原《XX证券费用报销管理办法(2022版)》同时废止。", "# XX证券费用报销管理办法(2025修订版)", "<!-- SYNTHETIC TEST FIXTURE — 虚构测试数据,禁止用于交付 -->", "发文字号: XX证财规〔2025〕甲号", "第一条 为规范XX证券费用报销行为,保证费用真实性、合规性和可追溯性,制定本办法。", "第三条 费用报销实行经办人真实性承诺、部门负责人业务审核、财务复核和授权审批相结合的管理原则。"], "query": "废止 2022版 施行 2025修订版", "title": ...
````

最终轨迹摘录 `runs/gate4_baseline_trae_v1/trae-agent/L3-006/trajectory.json:791`:

````text
"final_result": "{\"anomaly_ids\": [], \"answer\": \"费用报销审批线应采用《XX证券费用报销管理办法(2025修订版)》，该办法第十四条明确自2025年1月1日起施行，原2022版同时废止。2022版制度本身也注明仅作沿革留档，不得作为现行依据。部门总经理审批线：根据《XX证券授权管理办法》附件二，单笔报销金额大于等于10000元且小于50000元（AR-03档位）时，必要审批角色为部门总经理。\", \"citations\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"clause_no\": \"第十四条\"}, {\"doc_id\": \"03_authorization_management.md\", \"clause_no\": \"附件二\"}]}",
````

判卷摘录:

````text
{"anomaly_ids": [], "answer": "费用报销审批线应采用《XX证券费用报销管理办法(2025修订版)》，该办法第十四条明确自2025年1月1日起施行，原2022版同时废止。2022版制度本身也注明仅作沿革留档，不得作为现行依据。部门总经理审批线：根据《XX证券授权管理办法》附件二，单笔报销金额大于等于10000元且小于50000元（AR-03档位）时，必要审批角色为部门总经理。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十四条"}, {"doc_id": "03_authorization_management.md", "clause_no": "附件二"}]}
````

原因分析: 内容错误样例。输出可解析,但关键事实断言没命中。missing_facts=['2022旧值8000元已废止']

#### two_hop_retrieval (双跳检索)

表现: 2/3 通过, 格式失败 0, 内容错误 1, 超时 0。
代表样例: `L3-007` / `precise` / `通过` / `score=1.0` / `failure_layer=ok`。
题面: 报销办法没有直接列审批金额时,请通过交叉引用找到单笔费用审批档位。

工具轨迹摘录 `runs/gate4_baseline_trae_v1/trae-agent/L3-007/tool_calls.jsonl:5`:

````text
{"arguments": {"doc_id": "01_expense_reimbursement_2025.md", "max_chars": 1000, "query": "单笔费用报销的审批权限 授权管理办法 附件二"}, "error": null, "ok": true, "result_preview": {"doc_id": "01_expense_reimbursement_2025.md", "excerpts": ["第五条 单笔费用报销的审批权限,不在本办法正文列示具体金额,统一按《XX证券授权管理办法》附件二执行。费用系统应按附件二自动派生审批角色。", "第十一条 不得将同一事项或同类事项拆分为多笔报销以规避审批权限。同一员工、同一费用类型在7天内出现2笔及以上报销,且合计金额达到《授权管理办法》附件二较高审批线的,应重点核查拆分规避审批。", "第三条 费用报销实行经办人真实性承诺、部门负责人业务审核、财务复核和授权审批相结合的管理原则。", "第十四条 本办法自二〇二五年一月一日起施行。原《XX证券费用报销管理办法(2022版)》同时废止。", "第二条 ...
````

最终轨迹摘录 `runs/gate4_baseline_trae_v1/trae-agent/L3-007/trajectory.json:620`:

````text
"final_result": "```json\n{\"anomaly_ids\": [], \"answer\": \"《XX证券费用报销管理办法(2025修订版)》第五条明确,单笔费用报销的审批权限不在本办法正文列示具体金额,统一按《XX证券授权管理办法》附件二执行。通过交叉引用《XX证券授权管理办法》附件二(费用报销审批权限表),单笔费用审批共分为5个档位:AR-01(0元至3000元以下,部门经理审批);AR-02(3000元至10000元以下,部门经理审批并经财务复核);AR-03(10000元至50000元以下,部门总经理审批);AR-04(50000元至200000元以下,分管副总审批);AR-05(200000元及以上,总经理办公会审批)。\", \"citations\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"clause_no\": \"第五条\"}, {\"doc_id\": \"03_authorization_management.md\", \"clause_no\": \"附件二\"}]}\n```",
````

判卷摘录:

````text
{"anomaly_ids": [], "answer": "《XX证券费用报销管理办法(2025修订版)》第五条明确,单笔费用报销的审批权限不在本办法正文列示具体金额,统一按《XX证券授权管理办法》附件二执行。通过交叉引用《XX证券授权管理办法》附件二(费用报销审批权限表),单笔费用审批共分为5个档位:AR-01(0元至3000元以下,部门经理审批);AR-02(3000元至10000元以下,部门经理审批并经财务复核);AR-03(10000元至50000元以下,部门总经理审批);AR- ...", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"}, {"doc_id": "03_authorization_management.md", "clause_no": "附件二"}]}
````

原因分析: 通过样例。轨迹显示该题型在此样本上能按要求调用工具并生成可判卷答案。

#### near_clause_disambiguation (近似条款辨析)

表现: 0/3 通过, 格式失败 0, 内容错误 3, 超时 0。
代表样例: `L3-008` / `precise` / `内容错误` / `score=0.0` / `failure_layer=fact_miss`。
题面: 比较差旅住宿和培训住宿标准,说明为什么不能混用。

工具轨迹摘录 `runs/gate4_baseline_trae_v1/trae-agent/L3-008/tool_calls.jsonl:1`:

````text
{"arguments": {"query": "差旅住宿标准", "top_k": 10}, "error": null, "ok": true, "result_preview": {"preview": "{\"query\": \"差旅住宿标准\", \"results\": [{\"doc_id\": \"04_travel_expense.md\", \"score\": 15.4254, \"snippets\": [\"第四条 差旅住宿费标准如下,单位为元/人/晚。\", \"第二条 差旅费包括城市间交通费、住宿费、市内交通包干等与公务出差直接相关的费用。\", \"第三条 住宿标准按员工职级和城市档位确定。员工职级包括员工级、经理级、部门负责人级和高管级;城市档位包括一类城市、二类城市和三类城市。\"], \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"score\": 13.1605, \"snippets\": [\"第六条 培训住宿标准仅适用于培训期间住宿,不得与差旅住宿标准混用。\", \"第五条 ...
````

最终轨迹摘录 `runs/gate4_baseline_trae_v1/trae-agent/L3-008/trajectory.json:853`:

````text
"final_result": "```json\n{\"anomaly_ids\": [], \"answer\": \"差旅住宿标准与培训住宿标准在分类维度和金额上均不同，不能混用。差旅住宿标准按员工职级（员工级/经理级/部门负责人级/高管级）和城市档位（一类/二类/三类）双重分类，如员工级一类城市450元/晚、高管级一类城市1100元/晚；而培训住宿标准仅按城市档位统一标准，如一类城市500元/晚、二类城市420元/晚、三类城市350元/晚，不区分职级。此外，差旅费管理办法第七条明确规定培训期间住宿不适用差旅住宿表，应执行培训费管理办法；培训费管理办法第六条也规定培训住宿标准仅适用于培训期间，不得与差旅住宿标准混用。因此两者适用场景、分类依据和金额标准均不同，不可相互替代或混用。\", \"citations\": [{\"doc_id\": \"04_travel_expense.md\", \"clause_no\": \"第四条\"}, {\"doc_id\": \"04_travel_expense.md\", \"clause_no\": \"第七条\"}, {\"doc_id\": ...
````

判卷摘录:

````text
{"anomaly_ids": [], "answer": "...", "citations": [{"doc_id": "04_travel_expense.md", "clause_no": "第四条"}, {"doc_id": "04_travel_expense.md", "clause_no": "第七条"}]}
````

原因分析: 内容错误样例。输出可解析,但关键事实断言没命中。missing_facts=['两组数值不同不得混用']

#### audit_report (报告式任务)

表现: 0/6 通过, 格式失败 5, 内容错误 1, 超时 0。
代表样例: `L3-009` / `precise` / `格式失败` / `score=0.0` / `failure_layer=format_failure`。
题面: 请基于全年数据出一份异常审计摘要报告,覆盖五类规则并列出关键异常ID。

工具轨迹摘录 `runs/gate4_baseline_trae_v1/trae-agent/L3-009/tool_calls.jsonl:9`:

````text
{"arguments": {"query": "重复报销 同一发票", "top_k": 5}, "error": null, "ok": true, "result_preview": {"query": "重复报销 同一发票", "results": [{"doc_id": "01_expense_reimbursement_2025.md", "score": 12.9687, "snippets": ["第十条 同一发票最多报销1次。发现同一发票在不同报销单中重复出现的,应认定为重复报销风险。", "第十一条 不得将同一事项或同类事项拆分为多笔报销以规避审批权限。同一员工、同一费用类型在7天内出现2笔及以上报销,且合计金额达到《授权管理办法》附件二较高审批线的,应重点核查拆分规", "第七条 员工应在费用发生后60天内提交报销申请;超过期限的,原则上不得报销。"], "title": "XX证券费用报销管理办法(2025修订版)"}, {"doc_id": "06_business_entertainment.md", "score": 2.7864, "snippets": ["第四条 ...
````

最终轨迹摘录 `runs/gate4_baseline_trae_v1/trae-agent/L3-009/trajectory.json:1813`:

````text
"final_result": "Task execution exceeded maximum steps without completion.",
````

判卷摘录:

````text
Task execution exceeded maximum steps without completion.
````

原因分析: 格式失败样例。轨迹停在动作数/步骤数上限或交互式继续提示,没有输出标准 JSON。

#### clean_but_suspicious (陷阱题)

表现: 2/15 通过, 格式失败 13, 内容错误 0, 超时 0。
代表样例: `TRAP-001` / `precise` / `格式失败` / `score=0.0` / `failure_layer=format_failure`。
题面: 请核查TRAP-001涉及的记录是否构成异常,正确时应说明无异常。

工具轨迹摘录 `runs/gate4_baseline_trae_v1/trae-agent/TRAP-001/tool_calls.jsonl:2`:

````text
{"arguments": {"page": 1}, "error": null, "ok": true, "result_preview": {"preview": "{\"has_next\": true, \"page\": 1, \"page_size\": 50, \"records\": [{\"amount\": 661.56, \"department_id\": \"D005\", \"department_name\": \"机构业务部\", \"employee_id\": \"E0072\", \"employee_name\": \"谢辉\", \"expense_date\": \"2025-01-01\", \"expense_type\": \"business_entertainment\", \"invoice_no\": \"FP202500000339\", \"reason\": \"重点客户维护业务招待费\", \"record_id\": \"R000339\", \"record_no\": \"BX2025000339\", \"reimburse_date\": ...
````

最终轨迹摘录 `runs/gate4_baseline_trae_v1/trae-agent/TRAP-001/trajectory.json:1102`:

````text
"final_result": "Task execution exceeded maximum steps without completion.",
````

判卷摘录:

````text
Task execution exceeded maximum steps without completion.
````

原因分析: 格式失败样例。轨迹停在动作数/步骤数上限或交互式继续提示,没有输出标准 JSON。

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

### 各题型典型轨迹

下面每个题型放一个代表样例。样例选择规则: 通过率较高的题型选通过样例; 失败为主的题型选该题型最常见失败层。

#### policy_qa (纯制度问答)

表现: 12/12 通过, 格式失败 0, 内容错误 0, 超时 0。
代表样例: `L1-001` / `precise` / `通过` / `score=1.0` / `failure_layer=ok`。
题面: 现行制度下,单笔费用报销达到多少金额需要部门总经理审批?

工具轨迹摘录 `runs/gate4_baseline_opencode_v1/opencode/L1-001/tool_calls.jsonl:4`:

````text
{"arguments": {"doc_id": "01_expense_reimbursement_2025.md", "max_chars": 1500, "query": "审批权限 部门总经理 金额"}, "error": null, "ok": true, "result_preview": {"doc_id": "01_expense_reimbursement_2025.md", "excerpts": ["第十一条 不得将同一事项或同类事项拆分为多笔报销以规避审批权限。同一员工、同一费用类型在7天内出现2笔及以上报销,且合计金额达到《授权管理办法》附件二较高审批线的,应重点核查拆分规避审批。", "第五条 单笔费用报销的审批权限,不在本办法正文列示具体金额,统一按《XX证券授权管理办法》附件二执行。费用系统应按附件二自动派生审批角色。", "第三条 费用报销实行经办人真实性承诺、部门负责人业务审核、财务复核和授权审批相结合的管理原则。", "第十三条 部门年度预算不足时不得继续报销。预算使用达到预算额度的1.0倍后,确需发生的费用应履行专项审批。", "第六条 ...
````

最终轨迹摘录 `runs/gate4_baseline_opencode_v1/opencode/L1-001/trajectory.json:363`:

````text
"text": "```json\n{\n \"anomaly_ids\": [],\n \"answer\": \"根据现行制度，单笔费用报销金额达到人民币10,000元（含）且低于50,000元的，需要部门总经理审批。依据为《XX证券授权管理办法》附件二（费用报销审批权限表）中AR-03档位的规定，该附件二为现行有效审批线；同时《XX证券费用报销管理办法(2025修订版)》第五条明确审批权限统一按该附件执行。\",\n \"citations\": [\n {\n \"doc_id\": \"01_expense_reimbursement_2025.md\",\n \"clause_no\": \"第五条\"\n },\n {\n \"doc_id\": \"03_authorization_management.md\",\n \"clause_no\": \"第二条\"\n },\n {\n \"doc_id\": \"03_authorization_management.md\",\n \"clause_no\": \"附件二\"\n }\n ]\n}\n```",
````

判卷摘录:

````text
{"anomaly_ids": [], "answer": "根据现行制度，单笔费用报销金额达到人民币10,000元（含）且低于50,000元的，需要部门总经理审批。依据为《XX证券授权管理办法》附件二（费用报销审批权限表）中AR-03档位的规定，该附件二为现行有效审批线；同时《XX证券费用报销管理办法(2025修订版)》第五条明确审批权限统一按该附件执行。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"}, {"doc_id": "03_authorization_management.md", "clause_no": "第二条"}]}
````

原因分析: 通过样例。轨迹显示该题型在此样本上能按要求调用工具并生成可判卷答案。

#### version_check (版本检查)

表现: 0/3 通过, 格式失败 0, 内容错误 3, 超时 0。
代表样例: `L1-003` / `precise` / `内容错误` / `score=0.0` / `failure_layer=fact_miss`。
题面: 2022版中部门总经理审批线是多少,它现在是否有效?

工具轨迹摘录 `runs/gate4_baseline_opencode_v1/opencode/L1-003/tool_calls.jsonl:4`:

````text
{"arguments": {"doc_id": "01_expense_reimbursement_2025.md", "max_chars": 2000, "query": "审批权限 部门总经理 审批线"}, "error": null, "ok": true, "result_preview": {"doc_id": "01_expense_reimbursement_2025.md", "excerpts": ["第十一条 不得将同一事项或同类事项拆分为多笔报销以规避审批权限。同一员工、同一费用类型在7天内出现2笔及以上报销,且合计金额达到《授权管理办法》附件二较高审批线的,应重点核查拆分规避审批。", "第五条 单笔费用报销的审批权限,不在本办法正文列示具体金额,统一按《XX证券授权管理办法》附件二执行。费用系统应按附件二自动派生审批角色。", "第三条 费用报销实行经办人真实性承诺、部门负责人业务审核、财务复核和授权审批相结合的管理原则。", "第十三条 部门年度预算不足时不得继续报销。预算使用达到预算额度的1.0倍后,确需发生的费用应履行专项审批。", "第四条 ...
````

最终轨迹摘录 `runs/gate4_baseline_opencode_v1/opencode/L1-003/trajectory.json:427`:

````text
"text": "```json\n{\n \"anomaly_ids\": [],\n \"answer\": \"2022版（《XX证券费用报销管理办法(2022版)》）中部门总经理审批线为单笔报销金额达到8000元（即8000元及以上需提交部门总经理审批）。该审批线现已无效，因该制度已明确被标记为旧版留档，其审批金额已被后续制度替代，不得作为现行审批依据。\",\n \"citations\": [\n {\n \"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\",\n \"clause_no\": \"第二条\"\n },\n {\n \"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\",\n \"clause_no\": \"第一条\"\n },\n {\n \"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\",\n \"clause_no\": \"第四条\"\n }\n ]\n}\n```",
````

判卷摘录:

````text
{"anomaly_ids": [], "answer": "2022版（《XX证券费用报销管理办法(2022版)》）中部门总经理审批线为单笔报销金额达到8000元（即8000元及以上需提交部门总经理审批）。该审批线现已无效，因该制度已明确被标记为旧版留档，其审批金额已被后续制度替代，不得作为现行审批依据。", "citations": [{"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第二条"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第一条"}]}
````

原因分析: 内容错误样例。输出可解析,但关键事实断言没命中。missing_facts=['该值已废止']

#### single_anomaly_lookup (单条异常判断)

表现: 0/15 通过, 格式失败 7, 内容错误 8, 超时 0。
代表样例: `L1-006` / `casual` / `内容错误` / `score=0.0` / `failure_layer=reasoning_or_retrieval_error`。
题面: 看一下BX2025000002这笔有没有重复报销问题。

工具轨迹摘录 `runs/gate4_baseline_opencode_v1/opencode/L1-006__casual__r1/tool_calls.jsonl:6`:

````text
{"arguments": {"invoice_no": "FP202500000002"}, "error": null, "ok": true, "result_preview": {"invoice_no": "FP202500000002", "records": [{"amount": 423.79, "department_id": "D008", "employee_id": "E0050", "employee_name": "姚瑜", "expense_date": "2025-02-10", "expense_type": "office_supplies", "invoice_no": "FP202500000002", "record_id": "R004201", "record_no": "BX2025X004201", "reimburse_date": "2025-02-18"}, {"amount": 423.79, "department_id": "D008", "employee_id": "E0050", "employee_name": "姚瑜", ...
````

最终轨迹摘录 `runs/gate4_baseline_opencode_v1/opencode/L1-006__casual__r1/trajectory.json:551`:

````text
"text": "好的，我已经完成了调查。虽然系统提示达到最大步骤限制，但我已收集到足够的信息来回答问题。\n\n根据调查，报销记录 **BX2025000002** 存在重复报销问题：\n\n- 发票号 **FP202500000002**（对应 invoice_id INV000002）被用于了两笔不同的报销单：\n 1. **R000002**（编号 BX2025000002）— 员工姚瑜，合规风控部，金额 423.79 元，报销日期 2025-09-09，事由\"清源项目资料装订用品费\"\n 2. **R004201**（编号 BX2025X004201）— 同一员工姚瑜，合规风控部，相同金额 423.79 元，报销日期 2025-02-18，事由\"重复发票注入样本:清源项目资料装订用品费\"\n\n两笔报销使用了完全相同的发票（供应商、金额、发票日期均一致），属于同一发票重复报销。其中 R004201 ...
````

判卷摘录:

````text
{"anomaly_ids": ["R000002", "R004201"], "answer": "经查，报销单BX2025000002（记录ID R000002，员工姚瑜，合规风控部，金额423.79元，发票FP202500000002）存在重复报销问题。同一张发票（FP202500000002）已被另一笔报销单BX2025X004201（记录ID R004201，同一员工姚瑜，相同金额423.79元）重复使用报销。两笔报销均为同一员工、同一发票、相同金额，违反了费用报销管理办法中同一发票最多报销一次的规定，确认为重复报销异常。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"}]}
````

原因分析: 内容错误样例。输出可解析,但异常集合或答案空间不符合真值。expected_anomaly_ids=['DUP-001'], predicted=['R000002', 'R004201']

#### ground_truth_lookup (异常查记录集合)

表现: 0/15 通过, 格式失败 10, 内容错误 5, 超时 0。
代表样例: `L1-011` / `precise` / `格式失败` / `score=0.0` / `failure_layer=format_failure`。
题面: 异常DUP-002涉及哪些报销记录?

工具轨迹摘录 `runs/gate4_baseline_opencode_v1/opencode/L1-011/tool_calls.jsonl:7`:

````text
{"arguments": {"page": 1}, "error": null, "ok": true, "result_preview": {"preview": "{\"has_next\": true, \"page\": 1, \"page_size\": 50, \"records\": [{\"amount\": 661.56, \"department_id\": \"D005\", \"department_name\": \"机构业务部\", \"employee_id\": \"E0072\", \"employee_name\": \"谢辉\", \"expense_date\": \"2025-01-01\", \"expense_type\": \"business_entertainment\", \"invoice_no\": \"FP202500000339\", \"reason\": \"重点客户维护业务招待费\", \"record_id\": \"R000339\", \"record_no\": \"BX2025000339\", \"reimburse_date\": ...
````

最终轨迹摘录 `runs/gate4_baseline_opencode_v1/opencode/L1-011/trajectory.json:459`:

````text
"text": "## 工作进度总结\n\n### 已完成的查询\n1. **政策文档搜索**：已检索所有政策文档，未找到明确提及\"DUP-002\"异常代码的条款。\n2. **费用报销管理办法**：已查阅《XX证券费用报销管理办法(2025修订版)》第十条，其中规定\"同一发票最多报销1次。发现同一发票在不同报销单中重复出现的，应认定为重复报销风险\"。这与DUP（疑似Duplicate）异常类型高度相关。\n3. **费用记录预览**：已列出部分报销记录（第1页，50条），每条记录均有唯一`record_id`和`invoice_no`（如FP202500000339等）。\n\n### 未完成的任务\n要回答\"异常DUP-002涉及哪些报销记录\"，需要继续执行以下操作：\n1. **查找重复发票**：通过遍历费用记录，查找不同报销单中使用相同发票号（`invoice_no`）的记录对。DUP-002很可能指向违反第十条\"同一发票重复报销\"规定的具体记录。\n2. **确认异常标识**：检查费用系统或数据中是否有明确的DUP-002标注。\n\n### 下一步建议\n- ...
````

判卷摘录:

````text
## 工作进度总结 ### 已完成的查询 1. **政策文档搜索**：已检索所有政策文档，未找到明确提及"DUP-002"异常代码的条款。 2. **费用报销管理办法**：已查阅《XX证券费用报销管理办法(2025修订版)》第十条，其中规定"同一发票最多报销1次。发现同一发票在不同报销单中重复出现的，应认定为重复报销风险"。这与DUP（疑似Duplicate）异常类型高度相关。 3. **费用记录预览**：已列出部分报销记录（第1页，50条），每条记录均有唯一`record_id`和`invoice_no`（如FP202500000339等）。 ### 未完成的任务 要回答"异常DUP-002涉及哪些报销记录"，需要继续执行以下操作： 1. **查找重复发票**：通过遍历费用记录，查找不同报销单中使用相同发票号（`invoice_no`）的记录对。DUP-002很可能指向违反第十条"同一发票重复报销"规定的具体记录。 2. **确认异常标识**：检查费用系统或数据中是否有明确的DUP-002标注。 ### 下一步建议 - 继续遍历`expense_query_list_expenses`的后续页面（共4240条记录） ...
````

原因分析: 格式失败样例。轨迹停在动作数/步骤数上限或交互式继续提示,没有输出标准 JSON。

#### policy_data_comparison (制度+业务交叉核查)

表现: 1/75 通过, 格式失败 25, 内容错误 48, 超时 1。
代表样例: `L2-022` / `precise` / `超时` / `score=0.0` / `failure_layer=reasoning_or_retrieval_error`。
题面: 结合制度和业务数据,核查以R004228为线索的超期报销异常,返回异常ID和记录ID集合。

工具轨迹摘录 `runs/gate4_baseline_opencode_v1/opencode/L2-022/tool_calls.jsonl:5`:

````text
{"arguments": {"employee_id": "E0008"}, "error": null, "ok": true, "result_preview": {"preview": "{\"has_next\": false, \"page\": 1, \"page_size\": 50, \"records\": [{\"amount\": 182.0, \"department_id\": \"D008\", \"department_name\": \"合规风控部\", \"employee_id\": \"E0008\", \"employee_name\": \"杨丹\", \"expense_date\": \"2025-02-05\", \"expense_type\": \"communication\", \"invoice_no\": \"FP2025X0004222\", \"reason\": \"超期报销注入样本2\", \"record_id\": \"R004228\", \"record_no\": \"BX2025X004228\", ...
````

最终轨迹摘录 `runs/gate4_baseline_opencode_v1/opencode/L2-022/trajectory.json:639`:

````text
"text": "感谢您提供的信息。我已收集到足够的数据来完成分析。以下是我的最终审计结论：\n\n基于制度核查：\n- 根据《XX证券费用报销管理办法(2025修订版)》（doc_id: 01_expense_reimbursement_2025.md）第七条：\"员工应在费用发生后60天内提交报销申请；超过期限的，原则上不得报销。\"\n- 记录R004228的费用发生日期为2025-02-05，报销日期为2025-04-18，间隔72天，超出60天期限，构成超期报销异常。\n\n业务数据核实：\n- 报销单R004228（BX2025X004228），员工杨丹（E0008，合规风控部/部门经理），通讯费182.00元，备注已标注\"超期报销注入样本2\"，经本人（部门经理）审批通过，无专项审批。\n- 同一员工E0008的另一条记录R004232（超期报销注入样本6）同样存在超期报销问题（2025-09-04至2025-12-23，间隔110天）。\n\n```json\n{\n \"anomaly_ids\": [\"超期报销注入样本2\"],\n \"answer\": ...
````

判卷摘录:

````text
{"anomaly_ids": ["超期报销注入样本2"], "answer": "以R004228为线索发现超期报销异常。R004228（费用日期2025-02-05，报销日期2025-04-18，间隔72天）违反了《XX证券费用报销管理办法(2025修订版)》第七条关于60天内提交报销申请的规定。该报销单由员工本人（部门经理杨丹）自行审批通过，未做超期专项处理。关联发现同一员工还存有另一笔超期报销记录R004232（费用日期2025-09-04，报销日期2025-12-23，间隔110天），同样未经专项审批。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第七条"}]}
````

原因分析: 超时样例。elapsed=20703.37s, 未能稳定收口; 这更偏执行层/长任务预算问题。

#### full_year_rule_audit (全年专项扫描)

表现: 0/15 通过, 格式失败 7, 内容错误 8, 超时 0。
代表样例: `L3-001` / `distracted` / `内容错误` / `score=0.0` / `failure_layer=reasoning_or_retrieval_error`。
题面: 只输出重复报销专项结果,并给出对应制度条款。

工具轨迹摘录 `runs/gate4_baseline_opencode_v1/opencode/L3-001__distracted__r1/tool_calls.jsonl:3`:

````text
{"arguments": {"page": 1}, "error": null, "ok": true, "result_preview": {"preview": "{\"has_next\": true, \"page\": 1, \"page_size\": 50, \"records\": [{\"amount\": 661.56, \"department_id\": \"D005\", \"department_name\": \"机构业务部\", \"employee_id\": \"E0072\", \"employee_name\": \"谢辉\", \"expense_date\": \"2025-01-01\", \"expense_type\": \"business_entertainment\", \"invoice_no\": \"FP202500000339\", \"reason\": \"重点客户维护业务招待费\", \"record_id\": \"R000339\", \"record_no\": \"BX2025000339\", \"reimburse_date\": ...
````

最终轨迹摘录 `runs/gate4_baseline_opencode_v1/opencode/L3-001__distracted__r1/trajectory.json:679`:

````text
"text": "## 工作摘要\n\n由于工具调用已达到最大步数限制，以下是对已完成工作的总结：\n\n### 已完成的分析\n通过查询费用数据和政策文档，已识别出**重复报销异常**：\n\n**异常详情：**\n- 发票号 `FP202500000002` 被重复报销两次，涉及同一员工（姚瑜，合规风控部）：\n 1. **R004201** (BX2025X004201) — 2025-02-10，金额423.79元，事由标注\"重复发票注入样本:清源项目资料装订用品费\"\n 2. **R000002** (BX2025000002) — 2025-08-19，金额423.79元，事由\"清源项目资料装订用品费\"\n\n**对应制度条款：**\n- 《XX证券费用报销管理办法(2025修订版)》**第十条**：同一发票最多报销1次，发现同一发票在不同报销单中重复出现的，应认定为重复报销风险。\n\n### 最终输出\n\n```json\n{\n \"anomaly_ids\": [\"R004201\", \"R000002\"],\n \"answer\": ...
````

判卷摘录:

````text
{"anomaly_ids": ["R004201", "R000002"], "answer": "重复报销专项审计发现：发票号FP202500000002（金额423.79元）被同一员工姚瑜（合规风控部）分别在2025年2月10日（BX2025X004201）和2025年8月19日（BX2025000002）两次报销，构成重复报销风险。根据《XX证券费用报销管理办法(2025修订版)》第十条规定，同一发票最多报销1次，同一发票在不同报销单中重复出现应认定为重复报销风险。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"}]}
````

原因分析: 内容错误样例。输出可解析,但异常集合或答案空间不符合真值。expected_anomaly_ids=['DUP-001', 'DUP-002', 'DUP-003', 'DUP-004', 'DUP-005', 'DUP-006'], predicted=['R000002', 'R004201']

#### version_trap (版本陷阱)

表现: 1/3 通过, 格式失败 0, 内容错误 2, 超时 0。
代表样例: `L3-006` / `precise` / `内容错误` / `score=0.0` / `failure_layer=fact_miss`。
题面: 请判断费用报销审批线应采用2022版还是2025修订版,并指出部门总经理审批线。

工具轨迹摘录 `runs/gate4_baseline_opencode_v1/opencode/L3-006/tool_calls.jsonl:6`:

````text
{"arguments": {"doc_id": "01_expense_reimbursement_2025.md", "max_chars": 500, "query": "审批权限 附件二"}, "error": null, "ok": true, "result_preview": {"doc_id": "01_expense_reimbursement_2025.md", "excerpts": ["第五条 单笔费用报销的审批权限,不在本办法正文列示具体金额,统一按《XX证券授权管理办法》附件二执行。费用系统应按附件二自动派生审批角色。", "第十一条 不得将同一事项或同类事项拆分为多笔报销以规避审批权限。同一员工、同一费用类型在7天内出现2笔及以上报销,且合计金额达到《授权管理办法》附件二较高审批线的,应重点核查拆分规避审批。", "第三条 费用报销实行经办人真实性承诺、部门负责人业务审核、财务复核和授权审批相结合的管理原则。", "## 第二章 报销申请与审批", "第十二条 无专项审批时,报销金额不得超过对应制度标准的1.0倍。", "第四条 ...
````

最终轨迹摘录 `runs/gate4_baseline_opencode_v1/opencode/L3-006/trajectory.json:391`:

````text
"text": "```json\n{\n \"anomaly_ids\": [],\n \"answer\": \"费用报销审批线应采用《XX证券费用报销管理办法(2025修订版)》，原2022版已同时废止。部门总经理审批线为：单笔报销金额在10,000元（含）至50,000元（不含）之间时，须经部门总经理审批（详见《XX证券授权管理办法》附件二 AR-03档位）。\",\n \"citations\": [\n {\n \"doc_id\": \"01_expense_reimbursement_2025.md\",\n \"clause_no\": \"第十四条\"\n },\n {\n \"doc_id\": \"01_expense_reimbursement_2025.md\",\n \"clause_no\": \"第五条\"\n },\n {\n \"doc_id\": \"03_authorization_management.md\",\n \"clause_no\": \"附件二\"\n }\n ]\n}\n```",
````

判卷摘录:

````text
{"anomaly_ids": [], "answer": "费用报销审批线应采用《XX证券费用报销管理办法(2025修订版)》，原2022版已同时废止。部门总经理审批线为：单笔报销金额在10,000元（含）至50,000元（不含）之间时，须经部门总经理审批（详见《XX证券授权管理办法》附件二 AR-03档位）。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十四条"}, {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"}]}
````

原因分析: 内容错误样例。输出可解析,但关键事实断言没命中。missing_facts=['现行值为10000元', '2022旧值8000元已废止']

#### two_hop_retrieval (双跳检索)

表现: 1/3 通过, 格式失败 0, 内容错误 2, 超时 0。
代表样例: `L3-007` / `casual` / `内容错误` / `score=0.0` / `failure_layer=fact_miss`。
题面: 从费用报销办法出发,二跳检索授权管理办法附件二,给出审批线。

工具轨迹摘录 `runs/gate4_baseline_opencode_v1/opencode/L3-007__casual__r1/tool_calls.jsonl:5`:

````text
{"arguments": {"doc_id": "01_expense_reimbursement_2025.md", "max_chars": 500, "query": "第五条 授权管理办法 附件二 审批权限"}, "error": null, "ok": true, "result_preview": {"doc_id": "01_expense_reimbursement_2025.md", "excerpts": ["第五条 单笔费用报销的审批权限,不在本办法正文列示具体金额,统一按《XX证券授权管理办法》附件二执行。费用系统应按附件二自动派生审批角色。", "第十一条 不得将同一事项或同类事项拆分为多笔报销以规避审批权限。同一员工、同一费用类型在7天内出现2笔及以上报销,且合计金额达到《授权管理办法》附件二较高审批线的,应重点核查拆分规避审批。", "第三条 费用报销实行经办人真实性承诺、部门负责人业务审核、财务复核和授权审批相结合的管理原则。", "第十四条 本办法自二〇二五年一月一日起施行。原《XX证券费用报销管理办法(2022版)》同时废止。", "第二条 ...
````

最终轨迹摘录 `runs/gate4_baseline_opencode_v1/opencode/L3-007__casual__r1/trajectory.json:391`:

````text
"text": "```json\n{\n \"anomaly_ids\": [],\n \"answer\": \"根据《XX证券费用报销管理办法（2025修订版）》第五条，费用报销审批权限统一按《XX证券授权管理办法》附件二执行。附件二《费用报销审批权限表》规定的审批线如下：\\n- AR-01：单笔金额≥0元且＜3000元，必要审批角色为部门经理\\n- AR-02：单笔金额≥3000元且＜10000元，必要审批角色为部门经理，并经财务复核\\n- AR-03：单笔金额≥10000元且＜50000元，必要审批角色为部门总经理\\n- AR-04：单笔金额≥50000元且＜200000元，必要审批角色为分管副总\\n- AR-05：单笔金额≥200000元，必要审批角色为总经理办公会\",\n \"citations\": [\n {\n \"doc_id\": \"01_expense_reimbursement_2025.md\",\n \"clause_no\": \"第五条\"\n },\n {\n \"doc_id\": \"03_authorization_management.md\",\n ...
````

判卷摘录:

````text
{"anomaly_ids": [], "answer": "根据《XX证券费用报销管理办法（2025修订版）》第五条，费用报销审批权限统一按《XX证券授权管理办法》附件二执行。附件二《费用报销审批权限表》规定的审批线如下： - AR-01：单笔金额≥0元且＜3000元，必要审批角色为部门经理 - AR-02：单笔金额≥3000元且＜10000元，必要审批角色为部门经理，并经财务复核 - AR-03：单笔金额≥10000元且＜50000元，必要审批角色为部门总经理 - ...", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"}, {"doc_id": "03_authorization_management.md", "clause_no": "附件二"}]}
````

原因分析: 内容错误样例。输出可解析,但关键事实断言没命中。missing_facts=['金额出现在授权管理办法附件二']

#### near_clause_disambiguation (近似条款辨析)

表现: 0/3 通过, 格式失败 0, 内容错误 3, 超时 0。
代表样例: `L3-008` / `precise` / `内容错误` / `score=0.0` / `failure_layer=fact_miss`。
题面: 比较差旅住宿和培训住宿标准,说明为什么不能混用。

工具轨迹摘录 `runs/gate4_baseline_opencode_v1/opencode/L3-008/tool_calls.jsonl:2`:

````text
{"arguments": {"doc_id": "04_travel_expense.md", "max_chars": 3000, "query": "住宿标准 差旅住宿 报销标准"}, "error": null, "ok": true, "result_preview": {"doc_id": "04_travel_expense.md", "excerpts": ["第四条 差旅住宿费标准如下,单位为元/人/晚。", "第五条 超过住宿标准且无专项审批的,不得报销超出部分。", "第三条 住宿标准按员工职级和城市档位确定。员工职级包括员工级、经理级、部门负责人级和高管级;城市档位包括一类城市、二类城市和三类城市。", "## 第三章 住宿标准", "第七条 培训期间住宿不适用本办法住宿表,应按《XX证券培训费管理办法》执行。", "第二条 差旅费包括城市间交通费、住宿费、市内交通包干等与公务出差直接相关的费用。"], "query": "住宿标准 差旅住宿 报销标准", "title": "XX证券差旅费管理办法"}, "server": "policy_query_mcp", "tool": ...
````

最终轨迹摘录 `runs/gate4_baseline_opencode_v1/opencode/L3-008/trajectory.json:423`:

````text
"text": "```json\n{\n \"anomaly_ids\": [],\n \"answer\": \"差旅住宿标准与培训住宿标准存在明显差异，不能混用的原因如下：\\n\\n一、标准差异\\n差旅住宿标准（XX证券差旅费管理办法第四条）：按职级和城市档位双重维度确定，分为员工级、经理级、部门负责人级、高管级四个职级，以及一类城市、二类城市、三类城市三个档位，具体为：员工级450/380/300元，经理级650/550/450元，部门负责人级850/700/600元，高管级1100/900/750元（单位：元/人/晚）。\\n\\n培训住宿标准（XX证券培训费管理办法第五条）：仅按城市档位区分，不分职级，统一标准为一类城市500元、二类城市420元、三类城市350元（单位：元/人/晚）。\\n\\n二、不能混用的原因\\n1. 制度明确禁止：差旅费管理办法第七条规定培训期间住宿不适用差旅住宿表，应按培训费管理办法执行；培训费管理办法第六条规定培训住宿标准仅适用于培训期间住宿，不得与差旅住宿标准混用。\\n2. ...
````

判卷摘录:

````text
{"anomaly_ids": [], "answer": "差旅住宿标准与培训住宿标准存在明显差异，不能混用的原因如下： 一、标准差异 差旅住宿标准（XX证券差旅费管理办法第四条）：按职级和城市档位双重维度确定，分为员工级、经理级、部门负责人级、高管级四个职级，以及一类城市、二类城市、三类城市三个档位，具体为：员工级450/380/300元，经理级650/550/450元，部门负责人级850/700/600元，高管级1100/900/750元（单位：元/人/晚）。 ...", "citations": [{"doc_id": "04_travel_expense.md", "clause_no": "第四条"}, {"doc_id": "04_travel_expense.md", "clause_no": "第七条"}]}
````

原因分析: 内容错误样例。输出可解析,但关键事实断言没命中。missing_facts=['两组数值不同不得混用']

#### audit_report (报告式任务)

表现: 1/6 通过, 格式失败 3, 内容错误 2, 超时 0。
代表样例: `L3-009` / `precise` / `格式失败` / `score=0.0` / `failure_layer=format_failure`。
题面: 请基于全年数据出一份异常审计摘要报告,覆盖五类规则并列出关键异常ID。

工具轨迹摘录 `runs/gate4_baseline_opencode_v1/opencode/L3-009/tool_calls.jsonl:2`:

````text
{"arguments": {"query": "费用报销异常 规则 违规", "top_k": 10}, "error": null, "ok": true, "result_preview": {"preview": "{\"query\": \"费用报销异常 规则 违规\", \"results\": [{\"doc_id\": \"11_attendance_management.md\", \"score\": 5.0656, \"snippets\": [\"第一条 为规范XX证券考勤记录、请假申请、外勤登记和异常处理相关管理事项,制定本办法。\", \"第八条 本办法为管理类制度,不作为费用报销标准依据。\", \"发文字号: XX证综规〔2025〕备号\"], \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"score\": 3.1309, \"snippets\": [\"第一条 为规范XX证券日常办公费用和通讯费用报销,制定本办法。\", \"第四条 ...
````

最终轨迹摘录 `runs/gate4_baseline_opencode_v1/opencode/L3-009/trajectory.json:997`:

````text
"text": "## 最大步数已达 — 任务中断说明\n\n**已完成的调查工作：**\n\n1. **政策文档收集**：已获取全部20份政策文档，重点分析了费用报销管理办法(2025版)、授权管理办法、差旅费管理办法、培训费管理办法、业务招待费管理办法、办公与通讯费用管理办法、预算管理办法。\n\n2. **组织架构获取**：已获取全部10个部门及80名员工信息。\n\n3. **部门预算数据**：已获取所有10个部门的年度预算及累计支出数据。\n\n4. **部分费用数据扫描**：已获取第1页50条费用记录（共4240条），以及超标数据的关键查询结果。\n\n**已发现的异常汇总（五类规则）：**\n\n### 规则一：超预算报销（预算管理办法第三条）\n| 部门 | 预算额度 | 累计金额 | 超支比例 |\n|------|---------|---------|---------|\n| D001 投资银行部 | 230,395.17 | 363,614.58 | +57.8% |\n| D002 固定收益部 | 107,785.42 | 164,928.12 | +53.0% |\n| D003 ...
````

判卷摘录:

````text
## 最大步数已达 — 任务中断说明 **已完成的调查工作：** 1. **政策文档收集**：已获取全部20份政策文档，重点分析了费用报销管理办法(2025版)、授权管理办法、差旅费管理办法、培训费管理办法、业务招待费管理办法、办公与通讯费用管理办法、预算管理办法。 2. **组织架构获取**：已获取全部10个部门及80名员工信息。 3. **部门预算数据**：已获取所有10个部门的年度预算及累计支出数据。 4. **部分费用数据扫描**：已获取第1页50条费用记录（共4240条），以及超标数据的关键查询结果。 **已发现的异常汇总（五类规则）：** ### 规则一：超预算报销（预算管理办法第三条） | 部门 | 预算额度 | 累计金额 | 超支比例 | |------|---------|---------|---------| | D001 投资银行部 | 230,395.17 | 363,614.58 | +57.8% | | D002 固定收益部 | 107,785.42 | 164,928.12 | +53.0% | | D003 财富管理部 | 109,772.07 | 174,150.67 | ...
````

原因分析: 格式失败样例。最终文本无法抽取出符合契约的 JSON。

#### clean_but_suspicious (陷阱题)

表现: 9/15 通过, 格式失败 1, 内容错误 5, 超时 0。
代表样例: `TRAP-001` / `precise` / `通过` / `score=1.0` / `failure_layer=ok`。
题面: 请核查TRAP-001涉及的记录是否构成异常,正确时应说明无异常。

工具轨迹摘录 `runs/gate4_baseline_opencode_v1/opencode/TRAP-001/tool_calls.jsonl:1`:

````text
{"arguments": {"record_id": "TRAP-001"}, "error": null, "ok": true, "result_preview": {"approvals": [], "record": null}, "server": "expense_query_mcp", "tool": "get_expense_detail", "ts": 1783439194.885511}
````

最终轨迹摘录 `runs/gate4_baseline_opencode_v1/opencode/TRAP-001/trajectory.json:388`:

````text
"text": "```json\n{\n \"anomaly_ids\": [],\n \"answer\": \"经核查，费用报销系统与政策文件中均不存在TRAP-001对应的记录，未发现任何异常。\",\n \"citations\": []\n}\n```",
````

判卷摘录:

````text
{"anomaly_ids": [], "answer": "经核查，费用报销系统与政策文件中均不存在TRAP-001对应的记录，未发现任何异常。", "citations": []}
````

原因分析: 通过样例。轨迹显示该题型在此样本上能按要求调用工具并生成可判卷答案。

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
