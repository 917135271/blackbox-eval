# GATE 4 Agent Task-Type Analysis

生成时间: 2026-07-09

数据来源:

- `runs/*/grades.jsonl`
- `runs/*/*/*/result.json`
- `runs/*/*/*/trajectory.json`
- 汇总报告: `output/gate4_baseline_report.md`

说明: 本版 `score` 是 LLM judge 的语义判卷结果; `rule_score` 保留旧确定性规则分供对照。 `格式失败` 仍单独统计,因为有些答案语义可读但没有满足标准 JSON 输出合约。

## 总体结论

LLM judge 放宽了“必须输出标准 anomaly_id”的硬约束后,异常识别类题目分数上升,但题型差异仍很明显:

| 题型 | 总尝试 | LLM内容通过 | 旧规则通过 | 格式失败 | 主要结论 |
| --- | ---: | ---: | ---: | ---: | --- |
| `policy_qa` 纯制度问答 | 20 | 20 (100.0%) | 20 | 0 | 仍是最稳定题型 |
| `version_check` 版本检查 | 5 | 5 (100.0%) | 3 | 0 | 中等表现 |
| `single_anomaly_lookup` 单条异常判断 | 25 | 22 (88.0%) | 25 | 0 | LLM judge 认可部分语义命中,但集合归并仍不稳 |
| `ground_truth_lookup` 异常查记录集合 | 25 | 15 (60.0%) | 21 | 0 | record_id 集合覆盖是主要瓶颈 |
| `policy_data_comparison` 制度+业务交叉核查 | 125 | 74 (59.2%) | 125 | 0 | LLM judge 认可部分语义命中,但集合归并仍不稳 |
| `full_year_rule_audit` 全年专项扫描 | 25 | 14 (56.0%) | 16 | 0 | LLM judge 认可部分语义命中,但集合归并仍不稳 |
| `version_trap` 版本陷阱 | 5 | 2 (40.0%) | 1 | 0 | 中等表现 |
| `two_hop_retrieval` 双跳检索 | 5 | 5 (100.0%) | 5 | 0 | 中等表现 |
| `near_clause_disambiguation` 近似条款辨析 | 5 | 5 (100.0%) | 0 | 0 | 中等表现 |
| `audit_report` 报告式任务 | 10 | 5 (50.0%) | 1 | 0 | 报告可读性不等于 rubric 完整满足 |
| `clean_but_suspicious` 陷阱题 | 25 | 15 (60.0%) | 22 | 0 | 陷阱识别有一定能力 |

## Qwen Code

### 题型表现

| 题型 | 总数 | LLM内容通过 | 旧规则通过 | 格式失败 | LLM未通过 | 超时 | 判断 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| policy_qa | 4 | 4 | 4 | 0 | 0 | 0 | 仍是最稳定题型 |
| version_check | 1 | 1 | 1 | 0 | 0 | 0 | 中等表现 |
| single_anomaly_lookup | 5 | 3 | 5 | 0 | 2 | 0 | LLM judge 认可部分语义命中,但集合归并仍不稳 |
| ground_truth_lookup | 5 | 2 | 4 | 0 | 3 | 0 | record_id 集合覆盖是主要瓶颈 |
| policy_data_comparison | 25 | 13 | 25 | 0 | 12 | 0 | LLM judge 认可部分语义命中,但集合归并仍不稳 |
| full_year_rule_audit | 5 | 3 | 3 | 0 | 2 | 0 | LLM judge 认可部分语义命中,但集合归并仍不稳 |
| version_trap | 1 | 0 | 0 | 0 | 1 | 0 | 中等表现 |
| two_hop_retrieval | 1 | 1 | 1 | 0 | 0 | 0 | 中等表现 |
| near_clause_disambiguation | 1 | 1 | 0 | 0 | 0 | 0 | 中等表现 |
| audit_report | 2 | 1 | 0 | 0 | 1 | 0 | 报告可读性不等于 rubric 完整满足 |
| clean_but_suspicious | 5 | 4 | 5 | 0 | 1 | 0 | 陷阱识别有一定能力 |

### 各题型典型轨迹

下面每个题型放一个代表样例。样例选择规则: 通过率较高的题型选通过样例; 失败为主的题型选该题型最常见失败层。

#### policy_qa (纯制度问答)

表现: LLM内容通过 4/4, 旧规则通过 4/4, 格式失败 0, 超时 0。
代表样例: `L1-001` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 现行制度下,单笔费用报销达到多少金额需要部门总经理审批?

工具轨迹摘录 `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L1-001/tool_calls.jsonl:1`:

````text
{"arguments": {"query": "部门总经理审批 金额 单笔费用报销", "top_k": 5}, "error": null, "ok": true, "result_preview": {"preview": "{\"query\": \"部门总经理审批 金额 单笔费用报销\", \"results\": [{\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"score\": 14.3153, \"snippets\": [\"第二条 旧版制度曾规定,单笔报销金额达到8000元的,应提交部门总经理审批。\", \"第一条 本办法为XX证券旧版费用报销制度文本,仅作为制度沿革留档。现行制度应以《XX证券费用报销管理办法(2025修订版)》为准。\", \"第三条 旧版制度曾规定,单笔报销金额达到30000元的,应提交分管副总审批。\"], \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"01_expense_reimbursement_2025.md\", \"score\": 11.2818, \"snippets\": [\"第十一条 不得将同一事项或同类事项拆分为多笔报销以规避审批权限。同一员工、同一费用类型在7天内出现2笔及以上报销,且合计金额达到《授权管理办法》附件二较高审批线的,应重点核查拆分规\", \"第五条 单笔费用报销的审批权限,不在本办法正文列示具体金额,统一按《XX证券授权管理办法》附件二执行。费用系统应按附件二自动派生审批角色。\", \"第三条 费用报销实行经办人真实性承诺、部门负责人业务审核、财务复核和授权审批相结合的管理原则。\"], \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"score\": 11.2058, \"snippets\": [\"第二条 本办法附件二适用于费用报销系统自动派生审批角色,相关金额为现行有效审批线。\", \"## 附件二 费用报销审批权限表\", \"| 档位 | 单笔金额区间 | 必要审批角色 |\"], \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"score\": 4.9597, \"snippets\": [\"第三条 部门费用累计使用达到年度预算额度的1.0倍后,原则上不得继续报销。\", \"第五条 本办法与费用报销制度共同构成费用控制依据。\", \"第二条 各部门应在年度预算额度内发生费用。\"], \
...[truncated 310 chars]
````

最终轨迹摘录 `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L1-001/trajectory.json:1`:

````text
[
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "根据现行有效的XX证券费用报销管理办法(2025修订版)第五条,单笔费用报销的审批权限统一按XX证券授权管理办法附件二执行。附件二费用报销审批权限表规定,单笔金额大于等于10000元且小于50000元(档位AR-03)的必要审批角色为部门总经理。因此,单笔费用报销金额达到10000元即需要部门总经理审批。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"}, {"doc_id": "03_authorization_management.md", "clause_no": "第二条及附件二"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "回答正确识别审批线为10000元，与期望事实一致，引用支持答案。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### version_check (版本检查)

表现: LLM内容通过 1/1, 旧规则通过 1/1, 格式失败 0, 超时 0。
代表样例: `L1-003` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 2022版中部门总经理审批线是多少,它现在是否有效?

工具轨迹摘录 `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L1-003/tool_calls.jsonl:1`:

````text
{"arguments": {"query": "2022版 部门总经理 审批线", "top_k": 5}, "error": null, "ok": true, "result_preview": {"preview": "{\"query\": \"2022版 部门总经理 审批线\", \"results\": [{\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"score\": 10.2257, \"snippets\": [\"第二条 旧版制度曾规定,单笔报销金额达到8000元的,应提交部门总经理审批。\", \"第三条 旧版制度曾规定,单笔报销金额达到30000元的,应提交分管副总审批。\", \"第四条 本办法的审批金额已被后续制度替代,不得作为现行审批依据。\"], \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"01_expense_reimbursement_2025.md\", \"score\": 7.4801, \"snippets\": [\"第十一条 不得将同一事项或同类事项拆分为多笔报销以规避审批权限。同一员工、同一费用类型在7天内出现2笔及以上报销,且合计金额达到《授权管理办法》附件二较高审批线的,应重点核查拆分规\", \"第三条 费用报销实行经办人真实性承诺、部门负责人业务审核、财务复核和授权审批相结合的管理原则。\", \"第五条 单笔费用报销的审批权限,不在本办法正文列示具体金额,统一按《XX证券授权管理办法》附件二执行。费用系统应按附件二自动派生审批角色。\"], \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"score\": 7.1897, \"snippets\": [\"第二条 本办法附件二适用于费用报销系统自动派生审批角色,相关金额为现行有效审批线。\", \"| AR-02 | 大于等于3000元且小于10000元 | 部门经理,并经财务复核 |\", \"| AR-03 | 大于等于10000元且小于50000元 | 部门总经理 |\"], \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"score\": 2.1398, \"snippets\": [\"第四条 因监管要求、客户服务或经营连续性确需超预算支出的,应履行专项审批。\", \"第二条 各部门应在年度预算额度内发生费用。\", \"第三条 部门费用累计使用达到年度预算额度的1.0倍后,
...[truncated 306 chars]
````

最终轨迹摘录 `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L1-003/trajectory.json:4`:

````text
"answer": "2022版《XX证券费用报销管理办法》规定，单笔报销金额达到8000元时应提交部门总经理审批。该办法现已废止，审批金额已被后续制度替代，不得作为现行审批依据。现行有效的部门总经理审批线为《XX证券授权管理办法》（XX证综规〔2025〕丙号）附件二AR-03档：单笔金额大于等于10000元且小于50000元，需部门总经理审批。",
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "2022版《XX证券费用报销管理办法》规定，单笔报销金额达到8000元时应提交部门总经理审批。该办法现已废止，审批金额已被后续制度替代，不得作为现行审批依据。现行有效的部门总经理审批线为《XX证券授权管理办法》（XX证综规〔2025〕丙号）附件二AR-03档：单笔金额大于等于10000元且小于50000元，需部门总经理审批。", "citations": [{"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第二条"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第四条"}, {"doc_id": "03_authorization_management.md", "clause_no": "第二条"}, {"doc_id": "03_authorization_management.md", "clause_no": "附件二 AR-03"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "回答准确提供了2022版审批线8000元并确认其已废止，符合全部期望事实。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### single_anomaly_lookup (单条异常判断)

表现: LLM内容通过 3/5, 旧规则通过 5/5, 格式失败 0, 超时 0。
代表样例: `L1-006` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 请判断报销记录R000002是否命中重复报销,如命中请返回异常ID。

工具轨迹摘录 `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L1-006/tool_calls.jsonl:1`:

````text
{"arguments": {"record_id": "R000002"}, "error": null, "ok": true, "result_preview": {"approvals": [{"approval_id": "A000002", "approval_status": "approved", "approved_at": "2025-09-09", "approver_employee_id": "E0008", "approver_role": "部门经理", "tier_id": "AR-01"}], "record": {"amount": 423.79, "annual_budget": 381600.0, "budget_year": 2025, "city_tier": null, "days": null, "department_id": "D008", "department_name": "合规风控部", "employee_id": "E0050", "employee_level": "X1", "employee_name": "姚瑜", "expense_date": "2025-08-19", "expense_type": "office_supplies", "invoice_amount": 423.79, "invoice_date": "2025-08-19", "invoice_id": "INV000002", "invoice_no": "FP202500000002", "nights": null, "participants": null, "position_role": "员工", "reason": "清源项目资料装订用品费", "record_id": "R000002", "record_no": "BX2025000002", "reimburse_date": "2025-09-09", "special_approval": 0, "status": "approved", "vendor_name": "XX供应商7753"}}, "server": "expense_query_mcp", "tool": "get_expense_detail", "ts": 1783578794.8698933}
````

最终轨迹摘录 `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L1-006/trajectory.json:9`:

````text
"answer": "报销记录R000002命中重复报销。R000002（报销单号BX2025000002，金额423.79元，2025-08-19）与R004201（报销单号BX2025X004201，金额423.79元，2025-02-10）均使用同一张发票FP202500000002（INV000002），供应商为XX供应商7753，发票日期2025-08-19，金额423.79元。两条记录均属员工姚瑜（E0050，合规风控部D008），发票被重复使用。依据费用报销管理办法第十条，同一发票最多报销1次，在不同报销单中重复出现应认定为重复报销风险。",
````

候选答案摘录:

````text
{"anomaly_ids": ["INV000002"], "record_ids": ["R000002", "R004201"], "answer": "报销记录R000002命中重复报销。R000002（报销单号BX2025000002，金额423.79元，2025-08-19）与R004201（报销单号BX2025X004201，金额423.79元，2025-02-10）均使用同一张发票FP202500000002（INV000002），供应商为XX供应商7753，发票日期2025-08-19，金额423.79元。两条记录均属员工姚瑜（E0050，合规风控部D008），发票被重复使用。依据费用报销管理办法第十条，同一发票最多报销1次，在不同报销单中重复出现应认定为重复报销风险。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选正确识别了重复报销的全部关键记录和规则，语义命中预期异常，仅异常ID使用了INV000002而非DUP-001，但不影响实质判定。",
  "judge_missing": [],
  "judge_extra": [
    "anomaly_ids 使用了INV000002而非标准DUP-001"
  ]
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### ground_truth_lookup (异常查记录集合)

表现: LLM内容通过 2/5, 旧规则通过 4/5, 格式失败 0, 超时 0。
代表样例: `L1-014` / `precise` / `内容未通过` / `llm_score=0.0` / `rule_score=1.0` / `layer=reasoning_or_retrieval_error`。
题面: 异常BUDGET-002涉及哪些报销记录?

工具轨迹摘录 `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L1-014/tool_calls.jsonl:1`:

````text
{"arguments": {"status": "approved"}, "error": null, "ok": true, "result_preview": {"preview": "{\"departments\": [{\"annual_budget\": 340961.75, \"department_id\": \"D006\", \"department_name\": \"运营管理部\", \"manager_employee_id\": \"E0006\", \"record_count\": 833, \"remaining_amount\": -189279.54, \"usage_rate\": 1.5551, \"used_amount\": 530241.29}, {\"annual_budget\": 278540.94, \"department_id\": \"D005\", \"department_name\": \"机构业务部\", \"manager_employee_id\": \"E0005\", \"record_count\": 616, \"remaining_amount\": -154901.82, \"usage_rate\": 1.5561, \"used_amount\": 433442.76}, {\"annual_budget\": 264890.39, \"department_id\": \"D004\", \"department_name\": \"研究所\", \"manager_employee_id\": \"E0004\", \"record_count\": 611, \"remaining_amount\": -143942.56, \"usage_rate\": 1.5434, \"used_amount\": 408832.95}, {\"annual_budget\": 230395.17, \"department_id\": \"D001\", \"department_name\": \"投资银行部\", \"manager_employee_id\": \"E0001\", \"record_count\": 525, \"remaining_amount\": -133219.41, \"usage_rate\": 1.5782, \"used_amount\": 363614.58}, {\"annual_budget\": 381600.0, \"department_id\": \"D008\", \"department_name\": \"合规风控部\", \"manager_employee_id\": \"E0008\", \"record
...[truncated 340 chars]
````

最终轨迹摘录 `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L1-014/trajectory.json:1`:

````text
[
````

候选答案摘录:

````text
{"anomaly_ids": ["BUDGET-002"], "record_ids": ["R000884", "R002599", "R002711", "R002057", "R002672", "R001849", "R004027", "R001141", "R002097", "R002870", "R001129", "R000941", "R003155", "R000348", "R001036", "R001789", "R002373", "R000502", "R001294", "R002301", "R003761", "R002508", "R000745", "R003700", "R001208", "R004152", "R003988", "R001453", "R001497", "R003377", "R002342", "R002183", "R003245", "R000504", "R004158", "R001206", "R003847", "R002473", "R002086", "R004077", "R000437", "R001522", "R003503", "R003566", "R003836", "R001071", "R002725", "R000441", "R002023", "R002885", "R000170", "R001639", "R003930", "R003991", "R000096", "R001384", "R002261", "R001513", "R000784", "R003295", "R001055", "R002755", "R004172", "R001267", "R000326", "R001030", "R003732", "R004166", "R002242", "R000370", "R003959", "R001078", "R002601", "R003220", "R000767", "R001178", "R004173", "R000667", "R003106", "R004107", "R002875", "R002876", "R002919", "R002394", "R003929", "R003166", "R003926", "R002425", "R001408", "R001029", "R002817", "R001503", "R003254", "R001193", "R002016", "R001145", "R003093", "R003239", "R004070", "R003322", "R000307", "R001328", "R001337", "R001559", "R000776"
...[truncated 2037 chars]
````

LLM judge 摘录:

````json
{
  "llm_score": 0.0,
  "rule_score": 1.0,
  "failure_layer": "reasoning_or_retrieval_error",
  "format_failure": false,
  "judge_reason": "BUDGET-002仅涉及记录R002009，但候选返回了D002部门全部254条记录，混入大量无关记录。",
  "judge_missing": [],
  "judge_extra": [
    "候选将整个部门的报销记录均视为异常相关，多报了253条无关记录"
  ]
}
````

原因分析: 输出可解析,但 LLM judge 认为关键事实、记录集合或异常判断没有语义命中。

#### policy_data_comparison (制度+业务交叉核查)

表现: LLM内容通过 13/25, 旧规则通过 25/25, 格式失败 0, 超时 0。
代表样例: `L2-001` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 结合制度和业务数据,核查以R000002为线索的重复报销异常,返回异常ID和记录ID集合。

工具轨迹摘录 `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L2-001/tool_calls.jsonl:1`:

````text
{"arguments": {"record_id": "R000002"}, "error": null, "ok": true, "result_preview": {"approvals": [{"approval_id": "A000002", "approval_status": "approved", "approved_at": "2025-09-09", "approver_employee_id": "E0008", "approver_role": "部门经理", "tier_id": "AR-01"}], "record": {"amount": 423.79, "annual_budget": 381600.0, "budget_year": 2025, "city_tier": null, "days": null, "department_id": "D008", "department_name": "合规风控部", "employee_id": "E0050", "employee_level": "X1", "employee_name": "姚瑜", "expense_date": "2025-08-19", "expense_type": "office_supplies", "invoice_amount": 423.79, "invoice_date": "2025-08-19", "invoice_id": "INV000002", "invoice_no": "FP202500000002", "nights": null, "participants": null, "position_role": "员工", "reason": "清源项目资料装订用品费", "record_id": "R000002", "record_no": "BX2025000002", "reimburse_date": "2025-09-09", "special_approval": 0, "status": "approved", "vendor_name": "XX供应商7753"}}, "server": "expense_query_mcp", "tool": "get_expense_detail", "ts": 1783579662.2423232}
````

最终轨迹摘录 `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L2-001/trajectory.json:1`:

````text
[
````

候选答案摘录:

````text
{"anomaly_ids": ["DUP-FP202500000002"], "record_ids": ["R000002", "R004201"], "answer": "发票FP202500000002（INV000002）由员工姚瑜（E0050，合规风控部）在同一预算年度内重复报销两次：R000002于2025-08-19报销423.79元，理由为清源项目资料装订用品费；R004201于2025-02-10报销423.79元，理由为重复发票注入样本:清源项目资料装订用品费。两张报销单均已审批通过。依据制度第十条，同一发票最多报销1次，构成重复报销风险。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选正确识别了以R000002为线索的重复报销异常，提供的record_ids完全覆盖期望的R000002和R004201，回答正文准确描述了同一异常的事实细节，语义命中标准答案。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### full_year_rule_audit (全年专项扫描)

表现: LLM内容通过 3/5, 旧规则通过 3/5, 格式失败 0, 超时 0。
代表样例: `L3-001` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 请对全年数据做重复报销专项扫描,返回全部异常ID和记录ID集合。

工具轨迹摘录 `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L3-001/tool_calls.jsonl:1`:

````text
{"arguments": {"min_usage_count": 2, "page": 1, "page_size": 500}, "error": null, "ok": true, "result_preview": {"preview": "{\"has_next\": false, \"invoices\": [{\"amount\": 423.79, \"expense_type\": \"office_supplies\", \"invoice_date\": \"2025-08-19\", \"invoice_id\": \"INV000002\", \"invoice_no\": \"FP202500000002\", \"record_ids\": [\"R000002\", \"R004201\"], \"usage_count\": 2, \"vendor_name\": \"XX供应商7753\"}, {\"amount\": 88.83, \"expense_type\": \"local_transport\", \"invoice_date\": \"2025-06-07\", \"invoice_id\": \"INV000005\", \"invoice_no\": \"FP202500000005\", \"record_ids\": [\"R000005\", \"R004202\"], \"usage_count\": 2, \"vendor_name\": \"XX供应商5450\"}, {\"amount\": 669.5, \"expense_type\": \"travel_lodging\", \"invoice_date\": \"2025-01-05\", \"invoice_id\": \"INV000020\", \"invoice_no\": \"FP202500000020\", \"record_ids\": [\"R000020\", \"R004203\"], \"usage_count\": 2, \"vendor_name\": \"XX供应商2706\"}, {\"amount\": 165.58, \"expense_type\": \"communication\", \"invoice_date\": \"2025-03-09\", \"invoice_id\": \"INV000028\", \"invoice_no\": \"FP202500000028\", \"record_ids\": [\"R000028\", \"R004204\"], \"usage_count\": 2, \"vendor_name\": \"XX供应商1999\"}, {\"amount\"
...[truncated 394 chars]
````

最终轨迹摘录 `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L3-001/trajectory.json:1`:

````text
[
````

候选答案摘录:

````text
{"anomaly_ids": ["A-DUP-001", "A-DUP-002", "A-DUP-003", "A-DUP-004", "A-DUP-005", "A-DUP-006"], "record_ids": ["R000002", "R004201", "R000005", "R004202", "R000020", "R004203", "R000028", "R004204", "R000037", "R004205", "R000055", "R004206"], "answer": "全年重复报销专项扫描共发现6组重复发票异常，涉及6张发票被12条报销记录重复使用，均违反费用报销管理办法第十条同一发票最多报销1次的规定。具体如下：(1)发票FP202500000002，金额423.79元，被R000002和R004201两条记录重复报销，均为姚瑜的办公用品费；(2)发票FP202500000005，金额88.83元，被R000005和R004202重复报销，均为刘冬梅的本地交通费；(3)发票FP202500000020，金额669.50元，被R000020和R004203重复报销，均为杜丹的差旅住宿费；(4)发票FP202500000028，金额165.58元，被R000028和R004204重复报销，均为张林的通讯费；(5)发票FP202500000037，金额84.72元，被R000037和R004205重复报销，均为唐静的本地交通费；(6)发票FP202500000055，金额999.76元，被R000055和R004206重复报销，均为陈洋的业务招待费。所有异常记录状态均为已审批，涉及总金额2432.18元。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选回答通过 record_ids 集合和正文描述明确识别了全部6组重复发票异常，与标准异常完全匹配，无遗漏或误报。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### version_trap (版本陷阱)

表现: LLM内容通过 0/1, 旧规则通过 0/1, 格式失败 0, 超时 0。
代表样例: `L3-006` / `precise` / `内容未通过` / `llm_score=0.0` / `rule_score=0.0` / `layer=fact_miss`。
题面: 请判断费用报销审批线应采用2022版还是2025修订版,并指出部门总经理审批线。

工具轨迹摘录 `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L3-006/tool_calls.jsonl:1`:

````text
{"arguments": {}, "error": null, "ok": true, "result_preview": {"preview": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_h
...[truncated 334 chars]
````

最终轨迹摘录 `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L3-006/trajectory.json:1`:

````text
[
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "费用报销审批线应采用2025修订版。2022版已于2025年1月1日废止,不得作为现行审批依据。部门总经理审批线为:单笔金额大于等于10000元且小于50000元(AR-03档)。依据为《XX证券费用报销管理办法(2025修订版)》第五条(审批权限统一按《授权管理办法》附件二执行)及第十四条(2022版同时废止),以及《XX证券授权管理办法》附件二(费用报销审批权限表 AR-03档)。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"}, {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十四条"}, {"doc_id": "03_authorization_management.md", "clause_no": "附件二 AR-03"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 0.0,
  "rule_score": 0.0,
  "failure_layer": "fact_miss",
  "format_failure": false,
  "judge_reason": "回答未提及2022版旧审批线8000元，仅说明废止，缺失关键事实。",
  "judge_missing": [
    "2022旧值8000元已废止"
  ],
  "judge_extra": []
}
````

原因分析: 输出可解析,但 LLM judge 认为关键事实、记录集合或异常判断没有语义命中。

#### two_hop_retrieval (双跳检索)

表现: LLM内容通过 1/1, 旧规则通过 1/1, 格式失败 0, 超时 0。
代表样例: `L3-007` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 报销办法没有直接列审批金额时,请通过交叉引用找到单笔费用审批档位。

工具轨迹摘录 `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L3-007/tool_calls.jsonl:1`:

````text
{"arguments": {}, "error": null, "ok": true, "result_preview": {"preview": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_h
...[truncated 334 chars]
````

最终轨迹摘录 `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L3-007/trajectory.json:1`:

````text
[
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "2025版报销办法(01_expense_reimbursement_2025.md)第五条明确不列示具体审批金额,统一按授权管理办法(03_authorization_management.md)附件二执行。附件二费用报销审批权限表中列有五个档位:AR-01,大于等于0元且小于3000元,部门经理审批;AR-02,大于等于3000元且小于10000元,部门经理审批并经财务复核;AR-03,大于等于10000元且小于50000元,部门总经理审批;AR-04,大于等于50000元且小于200000元,分管副总审批;AR-05,大于等于200000元,总经理办公会审批。旧版2022办法的8000元/30000元线已被废止。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"}, {"doc_id": "03_authorization_management.md", "clause_no": "第二条"}, {"doc_id": "03_authorization_management.md", "clause_no": "附件二"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第四条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选项完整给出了部门总经理审批线10000元及金额来自附件二，语义满足所有期望事实，且无异常误报。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### near_clause_disambiguation (近似条款辨析)

表现: LLM内容通过 1/1, 旧规则通过 0/1, 格式失败 0, 超时 0。
代表样例: `L3-008` / `precise` / `通过` / `llm_score=1.0` / `rule_score=0.0` / `layer=ok`。
题面: 比较差旅住宿和培训住宿标准,说明为什么不能混用。

工具轨迹摘录 `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L3-008/tool_calls.jsonl:1`:

````text
{"arguments": {"query": "差旅住宿标准", "top_k": 5}, "error": null, "ok": true, "result_preview": {"query": "差旅住宿标准", "results": [{"doc_id": "04_travel_expense.md", "score": 15.4254, "snippets": ["第四条 差旅住宿费标准如下,单位为元/人/晚。", "第二条 差旅费包括城市间交通费、住宿费、市内交通包干等与公务出差直接相关的费用。", "第三条 住宿标准按员工职级和城市档位确定。员工职级包括员工级、经理级、部门负责人级和高管级;城市档位包括一类城市、二类城市和三类城市。"], "title": "XX证券差旅费管理办法"}, {"doc_id": "05_training_expense.md", "score": 13.1605, "snippets": ["第六条 培训住宿标准仅适用于培训期间住宿,不得与差旅住宿标准混用。", "第五条 培训期间住宿标准如下,单位为元/人/晚。", "| 城市档位 | 培训住宿标准 |"], "title": "XX证券培训费管理办法"}, {"doc_id": "01_expense_reimbursement_2025.md", "score": 3.9007, "snippets": ["第二条 本办法适用于XX证券各部门、分支机构及全体员工发生的差旅、培训、招待、办公、通讯等费用报销事项。", "第六条 财务部门对票据合法性、费用归属、预算占用和制度标准进行复核。复核不替代业务部门对事项真实性的确认。", "第八条 差旅借款应在行程结束后30天内完成冲销。"], "title": "XX证券费用报销管理办法(2025修订版)"}, {"doc_id": "06_business_entertainment.md", "score": 0.4494, "snippets": ["## 第二章 标准管理"], "title": "XX证券业务招待费管理办法"}, {"doc_id": "12_archive_management.md", "score": 0.3707, "snippets": ["第八条 本办法为管理类制度,不作为费用报销标准依据。"], "title": "XX证券档案管理办法"}], "top_k": 5}, "server": "policy_query_mcp", "tool": "search_policy", "ts": 1783582618.626165}
````

最终轨迹摘录 `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L3-008/trajectory.json:1`:

````text
[
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "差旅住宿标准和培训住宿标准是两套独立体系，不能混用。具体对比如下：\n\n一、标准差异\n1. 差旅住宿标准按职级和城市档位双重确定：员工级一类城市450元、二类城市380元、三类城市300元；经理级一类城市650元、二类城市550元、三类城市450元；部门负责人级一类城市850元、二类城市700元、三类城市600元；高管级一类城市1100元、二类城市900元、三类城市750元。\n2. 培训住宿标准仅按城市档位确定，不区分职级：一类城市500元、二类城市420元、三类城市350元。\n\n二、不能混用的原因\n1. 法规明确禁止：《差旅费管理办法》第七条明确规定培训期间住宿不适用差旅住宿表，应按《培训费管理办法》执行；《培训费管理办法》第六条也明确规定培训住宿标准仅适用于培训期间住宿，不得与差旅住宿标准混用。\n2. 适用场景不同：差旅住宿用于公务出差场景，培训住宿用于培训期间场景，两种费用的预算归属和管理逻辑不同。\n3. 标准设计逻辑不同：差旅住宿标准按职级分档，体现不同职位人员的出差待遇差异；培训住宿标准统一不分职级，体现培训场景下的公平性原则。若混用，可能导致高级别人员用培训名义套取更高的差旅标准，或低级别人员在差旅中错误套用培训标准，造成报销混乱。", "citations": [{"doc_id": "04_travel_expense.md", "clause_no": "第四条"}, {"doc_id": "04_travel_expense.md", "clause_no": "第七条"}, {"doc_id": "05_training_expense.md", "clause_no": "第五条"}, {"doc_id": "05_training_expense.md", "clause_no": "第六条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 0.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选回答准确指出了差旅住宿适用差旅费管理办法、培训住宿适用培训费管理办法，并明确了标准数值不同且不得混用，完全覆盖了期望的关键事实，引用也支持了答案。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### audit_report (报告式任务)

表现: LLM内容通过 1/2, 旧规则通过 0/2, 格式失败 0, 超时 0。
代表样例: `L3-010` / `precise` / `通过` / `llm_score=1.0` / `rule_score=0.0` / `layer=ok`。
题面: 请专门写一段版本陷阱审计说明,解释旧版审批线可能导致的误判。

工具轨迹摘录 `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L3-010/tool_calls.jsonl:1`:

````text
{"arguments": {"query": "审批线 版本 旧版 历史 修订 变更", "top_k": 5}, "error": null, "ok": true, "result_preview": {"preview": "{\"query\": \"审批线 版本 旧版 历史 修订 变更\", \"results\": [{\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"score\": 18.6926, \"snippets\": [\"第一条 本办法为XX证券旧版费用报销制度文本,仅作为制度沿革留档。现行制度应以《XX证券费用报销管理办法(2025修订版)》为准。\", \"第二条 旧版制度曾规定,单笔报销金额达到8000元的,应提交部门总经理审批。\", \"第三条 旧版制度曾规定,单笔报销金额达到30000元的,应提交分管副总审批。\"], \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"score\": 11.5001, \"snippets\": [\"第二条 本办法附件二适用于费用报销系统自动派生审批角色,相关金额为现行有效审批线。\", \"第四条 授权事项发生调整的,以最新修订版附件为准。\", \"第一条 为明确XX证券经营管理授权边界,提升审批效率,制定本办法。\"], \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"01_expense_reimbursement_2025.md\", \"score\": 9.5303, \"snippets\": [\"第十一条 不得将同一事项或同类事项拆分为多笔报销以规避审批权限。同一员工、同一费用类型在7天内出现2笔及以上报销,且合计金额达到《授权管理办法》附件二较高审批线的,应重点核查拆分规\", \"第五条 单笔费用报销的审批权限,不在本办法正文列示具体金额,统一按《XX证券授权管理办法》附件二执行。费用系统应按附件二自动派生审批角色。\", \"# XX证券费用报销管理办法(2025修订版)\"], \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"18_it_asset.md\", \"score\": 6.027, \"snippets\": [\"第一条 为规范XX证券资产领用、配置变更、维修和退库相关管理事项,制定本办法。\", \"第二条 本办法适用于XX证券总部、分支机构及相关工作人员。\", \"第六条 审核人员应关注事项真实性、授权完整性和资料一致性。\"], \"
...[truncated 310 chars]
````

最终轨迹摘录 `runs/gate4_standard_qwen_v4pro_v1/qwen-code/L3-010/trajectory.json:1`:

````text
[
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "版本陷阱审计说明：旧版审批线可能导致系统性误判。XX证券费用报销审批线存在2022版（已废止）与2025现行版两套标准，二者差异显著。旧版（XX证财规〔2022〕乙号）规定：单笔金额≥8000元触发部门总经理审批，≥30000元触发分管副总审批。现行版依据《XX证券授权管理办法》（XX证综规〔2025〕丙号）附件二执行：0~3000元由部门经理审批，3000~10000元须部门经理+财务复核，10000~50000元由部门总经理审批，50000~200000元由分管副总审批，≥200000元由总经理办公会审批。二者关键差异有三：其一，部门总经理审批线从旧版8000元上调至现版10000元，若沿用旧线审计，8000~10000元区间的报销会被误判为缺少部门总经理审批；其二，分管副总审批线从旧版30000元上调至现版50000元，若沿用旧线，30000~50000元区间的报销会被误判为缺少分管副总审批；其三，旧版无财务复核挡位和最高挡位（总经理办公会），若审计标准混用，会遗漏财务复核缺位的真实违规，同时可能对超20万元报销缺失总经理办公会审批的情况漏判。审计实务中，若不主动确认所引用审批线的版本时效，极易将制度正常修订误判为审批缺失，产生大量假阳性；同时也可能因忽略现行制度新增的挡位而遗漏真实风险。审计建议：审计前必须核实审批权限表版本，以《XX证券授权管理办法》附件二为唯一现行有效标准，凡引旧版（2022版）标准的审计结论一律无效。", "citations": [{"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第一条、第二条、第三条、第四条"}, {"doc_id": "03_authorization_management.md", "clause_no": "第一条、第二条、第四条、附件二"}, {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条、第十四条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 0.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选回答明确指出了现行部门总经理审批线为10000元、2022版8000元审批线已废止、通过授权管理办法附件二取得现行审批金额，且未将旧版作为当前审批依据，完全满足四条 rubric 断言。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### clean_but_suspicious (陷阱题)

表现: LLM内容通过 4/5, 旧规则通过 5/5, 格式失败 0, 超时 0。
代表样例: `TRAP-001` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 请核查TRAP-001涉及的记录是否构成异常,正确时应说明无异常。

工具轨迹摘录 `runs/gate4_standard_qwen_v4pro_v1/qwen-code/TRAP-001/tool_calls.jsonl:1`:

````text
{"arguments": {}, "error": null, "ok": true, "result_preview": {"preview": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_h
...[truncated 333 chars]
````

最终轨迹摘录 `runs/gate4_standard_qwen_v4pro_v1/qwen-code/TRAP-001/trajectory.json:1`:

````text
[
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": ["R004233", "R004234", "R004235", "R004236", "R004237", "R004238", "R004239", "R004240"], "answer": "经核查，TRAP-001涉及的8条记录均为陷阱样本，不构成异常。具体如下：R004233金额9990元在AR-02区间内，未触发AR-03门槛；R004234与R004235为同日同额但发票不同，合计500元远低于3000元审批线，不构成拆分规避；R004236与R004237间隔8日超过7天窗口，不触发拆分核查规则；R004238报销延迟正好60日，未超过60天期限；R004239与R004240虽同供应商但发票不同、金额不同，合计1085元低于3000元，不构成拆分。综上，全部记录均符合现行制度规定，无异常。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "7"}, {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "10"}, {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "11"}, {"doc_id": "03_authorization_management.md", "clause_no": "附件二"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选正确识别无异常，覆盖期望记录R004233，并解释了低于审批线的理由。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。


## Trae Agent

### 题型表现

| 题型 | 总数 | LLM内容通过 | 旧规则通过 | 格式失败 | LLM未通过 | 超时 | 判断 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| policy_qa | 4 | 4 | 4 | 0 | 0 | 0 | 仍是最稳定题型 |
| version_check | 1 | 1 | 1 | 0 | 0 | 0 | 中等表现 |
| single_anomaly_lookup | 5 | 4 | 5 | 0 | 1 | 0 | LLM judge 认可部分语义命中,但集合归并仍不稳 |
| ground_truth_lookup | 5 | 4 | 5 | 0 | 1 | 0 | record_id 集合覆盖是主要瓶颈 |
| policy_data_comparison | 25 | 20 | 25 | 0 | 5 | 0 | LLM judge 认可部分语义命中,但集合归并仍不稳 |
| full_year_rule_audit | 5 | 4 | 4 | 0 | 1 | 0 | LLM judge 认可部分语义命中,但集合归并仍不稳 |
| version_trap | 1 | 1 | 1 | 0 | 0 | 0 | 中等表现 |
| two_hop_retrieval | 1 | 1 | 1 | 0 | 0 | 0 | 中等表现 |
| near_clause_disambiguation | 1 | 1 | 0 | 0 | 0 | 0 | 中等表现 |
| audit_report | 2 | 1 | 1 | 0 | 1 | 0 | 报告可读性不等于 rubric 完整满足 |
| clean_but_suspicious | 5 | 4 | 5 | 0 | 1 | 0 | 陷阱识别有一定能力 |

### 各题型典型轨迹

下面每个题型放一个代表样例。样例选择规则: 通过率较高的题型选通过样例; 失败为主的题型选该题型最常见失败层。

#### policy_qa (纯制度问答)

表现: LLM内容通过 4/4, 旧规则通过 4/4, 格式失败 0, 超时 0。
代表样例: `L1-001` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 现行制度下,单笔费用报销达到多少金额需要部门总经理审批?

工具轨迹摘录 `runs/gate4_standard_trae_v4pro_v2/trae-agent/L1-001/tool_calls.jsonl:1`:

````text
{"arguments": {"query": "部门总经理审批 金额 报销", "top_k": 10}, "error": null, "ok": true, "result_preview": {"preview": "{\"query\": \"部门总经理审批 金额 报销\", \"results\": [{\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"score\": 9.5302, \"snippets\": [\"第二条 旧版制度曾规定,单笔报销金额达到8000元的,应提交部门总经理审批。\", \"第三条 旧版制度曾规定,单笔报销金额达到30000元的,应提交分管副总审批。\", \"第四条 本办法的审批金额已被后续制度替代,不得作为现行审批依据。\"], \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"score\": 8.2517, \"snippets\": [\"第二条 本办法附件二适用于费用报销系统自动派生审批角色,相关金额为现行有效审批线。\", \"| AR-02 | 大于等于3000元且小于10000元 | 部门经理,并经财务复核 |\", \"| AR-03 | 大于等于10000元且小于50000元 | 部门总经理 |\"], \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"01_expense_reimbursement_2025.md\", \"score\": 7.8075, \"snippets\": [\"第十一条 不得将同一事项或同类事项拆分为多笔报销以规避审批权限。同一员工、同一费用类型在7天内出现2笔及以上报销,且合计金额达到《授权管理办法》附件二较高审批线的,应重点核查拆分规\", \"第三条 费用报销实行经办人真实性承诺、部门负责人业务审核、财务复核和授权审批相结合的管理原则。\", \"第五条 单笔费用报销的审批权限,不在本办法正文列示具体金额,统一按《XX证券授权管理办法》附件二执行。费用系统应按附件二自动派生审批角色。\"], \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"08_budget_management.md\", \"score\": 4.8584, \"snippets\": [\"第三条 部门费用累计使用达到年度预算额度的1.0倍后,原则上不得继续报销。\", \"第二条 各部门应在年度预算额度内发生费用。\", \"第四条 因监管要求、客户服务或经营连续性确需超预算支出的,应履
...[truncated 305 chars]
````

最终轨迹摘录 `runs/gate4_standard_trae_v4pro_v2/trae-agent/L1-001/trajectory.json:2`:

````text
"task": "请直接回答这个审计问题: 现行制度下,单笔费用报销达到多少金额需要部门总经理审批?\n\n这是完整任务,不要要求用户再提供任务或文件,不要探索项目目录,不要寻找评测入口。\n\n必须使用已连接的 MCP 工具查询制度或业务事实后再回答。\n\n你是费用审计助手,只处理本轮提供的虚构 XX证券 数据与制度语料。\n\n可用工具域:\n- policy_query_mcp: 查询制度文档、条款片段和制度原文。\n- expense_query_mcp: 查询费用报销 SQLite 中的原始业务事实。\n\n工作要求:\n- 先查制度依据,再查业务事实,最后给出结论。\n- 题面就是当前要回答的审计问题;不要检查本地工作目录、不要寻找评测脚本、不要等待下一条指令。\n- 不要回答“请提供具体任务”“环境已就绪”“我需要更多信息”;题面已经是完整任务。\n- 审计检测题必须返回支撑判断的 record_ids;若能确定标准 anomaly_ids 也一并返回,无法确定时 anomaly_ids 可为空数组。\n- 没有异常时 anomaly_ids 必须为空数组;record_ids 可填写被核查且判定为合规的记录 ID。\n- 制度问答题必须给出制度出处,至少包含 doc_id 和 clause_no。\n- 不要调用 shell、文件写入、网络访问或候选 harness 的编码工具。\n- 不要把旧版废止制度当作现行依据;如命中废止条款,必须说明其已废止。\n- 不要将题面中的陷阱位计为异常,除非原始事实和制度规则共同支持。\n\n最终回答必须只包含一个 JSON 代码块。JSON 必须能被标准 JSON 解析器解析,不要在 JSON 内写注释。\n为避免格式失败,`answer` 字段的值必须是标准 JSON 字符串,外层英文双引号必须保留。\n硬性约束: 禁止的是 `answer` 字符串内容内部出现额外 ASCII 双引号字符;角色名、制度名、档位名不要加英文引号。\n不要在 JSON 代码块之前或之后输出任何说明文字。\n\n格式:\n\n```json\n{\"anomaly_ids\": [\"A013\"], \"record_ids\": [\"R000001\"], \"answer\": \"结论摘要\", \"citations\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"clause_no\": \"费用报销管理办法-6.1\"}]}\n```\n\n字段要求:\n- `anomaly_ids`: 字符串数组。审计检测题填命中的异常 ID;无异常或陷阱题填空数组。\n- `record_ids`: 字符串数组。审计检测题填支撑结论的报销记录 ID;制度
...[truncated 447 chars]
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "现行制度下,单笔费用报销达到10000元(含)且低于50000元的,须由部门总经理审批。依据现行《费用报销管理办法(2025修订版)》第五条,审批权限统一按《授权管理办法》附件二执行,其中AR-03档为大于等于10000元且小于50000元,必要审批角色为部门总经理。2022版旧制度中8000元由部门总经理审批的规定已废止,不得作为现行依据。", "citations": [{"doc_id": "03_authorization_management.md", "clause_no": "授权管理办法-附件二-AR-03"}, {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "费用报销管理办法-第五条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "答案正确给出10000元(含)为部门总经理审批起点,与期望事实一致。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### version_check (版本检查)

表现: LLM内容通过 1/1, 旧规则通过 1/1, 格式失败 0, 超时 0。
代表样例: `L1-003` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 2022版中部门总经理审批线是多少,它现在是否有效?

工具轨迹摘录 `runs/gate4_standard_trae_v4pro_v2/trae-agent/L1-003/tool_calls.jsonl:1`:

````text
{"arguments": {}, "error": null, "ok": true, "result_preview": {"preview": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_h
...[truncated 334 chars]
````

最终轨迹摘录 `runs/gate4_standard_trae_v4pro_v2/trae-agent/L1-003/trajectory.json:2`:

````text
"task": "请直接回答这个审计问题: 2022版中部门总经理审批线是多少,它现在是否有效?\n\n这是完整任务,不要要求用户再提供任务或文件,不要探索项目目录,不要寻找评测入口。\n\n必须使用已连接的 MCP 工具查询制度或业务事实后再回答。\n\n你是费用审计助手,只处理本轮提供的虚构 XX证券 数据与制度语料。\n\n可用工具域:\n- policy_query_mcp: 查询制度文档、条款片段和制度原文。\n- expense_query_mcp: 查询费用报销 SQLite 中的原始业务事实。\n\n工作要求:\n- 先查制度依据,再查业务事实,最后给出结论。\n- 题面就是当前要回答的审计问题;不要检查本地工作目录、不要寻找评测脚本、不要等待下一条指令。\n- 不要回答“请提供具体任务”“环境已就绪”“我需要更多信息”;题面已经是完整任务。\n- 审计检测题必须返回支撑判断的 record_ids;若能确定标准 anomaly_ids 也一并返回,无法确定时 anomaly_ids 可为空数组。\n- 没有异常时 anomaly_ids 必须为空数组;record_ids 可填写被核查且判定为合规的记录 ID。\n- 制度问答题必须给出制度出处,至少包含 doc_id 和 clause_no。\n- 不要调用 shell、文件写入、网络访问或候选 harness 的编码工具。\n- 不要把旧版废止制度当作现行依据;如命中废止条款,必须说明其已废止。\n- 不要将题面中的陷阱位计为异常,除非原始事实和制度规则共同支持。\n\n最终回答必须只包含一个 JSON 代码块。JSON 必须能被标准 JSON 解析器解析,不要在 JSON 内写注释。\n为避免格式失败,`answer` 字段的值必须是标准 JSON 字符串,外层英文双引号必须保留。\n硬性约束: 禁止的是 `answer` 字符串内容内部出现额外 ASCII 双引号字符;角色名、制度名、档位名不要加英文引号。\n不要在 JSON 代码块之前或之后输出任何说明文字。\n\n格式:\n\n```json\n{\"anomaly_ids\": [\"A013\"], \"record_ids\": [\"R000001\"], \"answer\": \"结论摘要\", \"citations\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"clause_no\": \"费用报销管理办法-6.1\"}]}\n```\n\n字段要求:\n- `anomaly_ids`: 字符串数组。审计检测题填命中的异常 ID;无异常或陷阱题填空数组。\n- `record_ids`: 字符串数组。审计检测题填支撑结论的报销记录 ID;制度问答
...[truncated 449 chars]
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "2022版费用报销管理办法(发文字号 XX证财规〔2022〕乙号)第二条规定:单笔报销金额达到8000元的,应提交部门总经理审批,即部门总经理审批线为8000元。但该2022版已废止,第一条明确其仅作制度沿革留档,第四条明确其审批金额已被后续制度替代,不得作为现行审批依据。现行有效依据为2025修订版及授权管理办法附件二自动派生审批角色,因此该8000元审批线现已失效。", "citations": [{"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "费用报销管理办法(2022版)-第二条"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "费用报销管理办法(2022版)-第一条"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "费用报销管理办法(2022版)-第四条"}, {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "费用报销管理办法-第五条"}, {"doc_id": "03_authorization_management.md", "clause_no": "授权管理办法-第二条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选回答明确给出了2022版旧值为8000元，并指出已废止，完整覆盖了期望事实。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### single_anomaly_lookup (单条异常判断)

表现: LLM内容通过 4/5, 旧规则通过 5/5, 格式失败 0, 超时 0。
代表样例: `L1-006` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 请判断报销记录R000002是否命中重复报销,如命中请返回异常ID。

工具轨迹摘录 `runs/gate4_standard_trae_v4pro_v2/trae-agent/L1-006/tool_calls.jsonl:1`:

````text
{"arguments": {"query": "重复报销"}, "error": null, "ok": true, "result_preview": {"query": "重复报销", "results": [{"doc_id": "01_expense_reimbursement_2025.md", "score": 6.3583, "snippets": ["第十条 同一发票最多报销1次。发现同一发票在不同报销单中重复出现的,应认定为重复报销风险。", "第十一条 不得将同一事项或同类事项拆分为多笔报销以规避审批权限。同一员工、同一费用类型在7天内出现2笔及以上报销,且合计金额达到《授权管理办法》附件二较高审批线的,应重点核查拆分规", "第七条 员工应在费用发生后60天内提交报销申请;超过期限的,原则上不得报销。"], "title": "XX证券费用报销管理办法(2025修订版)"}, {"doc_id": "03_authorization_management.md", "score": 1.9462, "snippets": ["第二条 本办法附件二适用于费用报销系统自动派生审批角色,相关金额为现行有效审批线。", "## 附件二 费用报销审批权限表", "| AR-02 | 大于等于3000元且小于10000元 | 部门经理,并经财务复核 |"], "title": "XX证券授权管理办法"}, {"doc_id": "20_customer_complaint.md", "score": 1.9302, "snippets": ["第八条 本办法为管理类制度,不作为费用报销标准依据。", "第一条 为规范XX证券投诉受理、事实核查、回复留痕和改进闭环相关管理事项,制定本办法。"], "title": "XX证券客户投诉处理管理办法"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "score": 0.3009, "snippets": ["第一条 本办法为XX证券旧版费用报销制度文本,仅作为制度沿革留档。现行制度应以《XX证券费用报销管理办法(2025修订版)》为准。", "# XX证券费用报销管理办法(2022版)", "第二条 旧版制度曾规定,单笔报销金额达到8000元的,应提交部门总经理审批。"], "title": "XX证券费用报销管理办法(2022版)"}, {"doc_id": "07_office_communication.md", "score": 0.2766, "snippets": ["第一条 为规范XX证券日常办公费用和通讯费用报销,制定本办法。", "第二条 员工个人办公用品报销按月控制,每人每月不超过600元。", "第三条 员工
...[truncated 150 chars]
````

最终轨迹摘录 `runs/gate4_standard_trae_v4pro_v2/trae-agent/L1-006/trajectory.json:2`:

````text
"task": "请直接回答这个审计问题: 请判断报销记录R000002是否命中重复报销,如命中请返回异常ID。\n\n这是完整任务,不要要求用户再提供任务或文件,不要探索项目目录,不要寻找评测入口。\n\n必须使用已连接的 MCP 工具查询制度或业务事实后再回答。\n\n你是费用审计助手,只处理本轮提供的虚构 XX证券 数据与制度语料。\n\n可用工具域:\n- policy_query_mcp: 查询制度文档、条款片段和制度原文。\n- expense_query_mcp: 查询费用报销 SQLite 中的原始业务事实。\n\n工作要求:\n- 先查制度依据,再查业务事实,最后给出结论。\n- 题面就是当前要回答的审计问题;不要检查本地工作目录、不要寻找评测脚本、不要等待下一条指令。\n- 不要回答“请提供具体任务”“环境已就绪”“我需要更多信息”;题面已经是完整任务。\n- 审计检测题必须返回支撑判断的 record_ids;若能确定标准 anomaly_ids 也一并返回,无法确定时 anomaly_ids 可为空数组。\n- 没有异常时 anomaly_ids 必须为空数组;record_ids 可填写被核查且判定为合规的记录 ID。\n- 制度问答题必须给出制度出处,至少包含 doc_id 和 clause_no。\n- 不要调用 shell、文件写入、网络访问或候选 harness 的编码工具。\n- 不要把旧版废止制度当作现行依据;如命中废止条款,必须说明其已废止。\n- 不要将题面中的陷阱位计为异常,除非原始事实和制度规则共同支持。\n\n最终回答必须只包含一个 JSON 代码块。JSON 必须能被标准 JSON 解析器解析,不要在 JSON 内写注释。\n为避免格式失败,`answer` 字段的值必须是标准 JSON 字符串,外层英文双引号必须保留。\n硬性约束: 禁止的是 `answer` 字符串内容内部出现额外 ASCII 双引号字符;角色名、制度名、档位名不要加英文引号。\n不要在 JSON 代码块之前或之后输出任何说明文字。\n\n格式:\n\n```json\n{\"anomaly_ids\": [\"A013\"], \"record_ids\": [\"R000001\"], \"answer\": \"结论摘要\", \"citations\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"clause_no\": \"费用报销管理办法-6.1\"}]}\n```\n\n字段要求:\n- `anomaly_ids`: 字符串数组。审计检测题填命中的异常 ID;无异常或陷阱题填空数组。\n- `record_ids`: 字符串数组。审计检测题填支撑结论的报销记录
...[truncated 465 chars]
````

候选答案摘录:

````text
{"anomaly_ids": ["A001"], "record_ids": ["R000002", "R004201"], "answer": "报销记录R000002命中重复报销。其发票号FP202500000002(INV000002,金额423.79元)被两笔报销单使用:R000002与R004201,均为员工姚瑜(E0050)、合规风控部,同一发票被报销2次,依据现行制度第十条应认定为重复报销风险。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "费用报销管理办法-第十条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选回答虽使用自定义异常ID“A001”，但明确提供了与DUP-001一致的业务逻辑（同一发票被两笔报销单使用，涉及R000002与R004201），且record_ids完全覆盖预期记录，语义命中。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### ground_truth_lookup (异常查记录集合)

表现: LLM内容通过 4/5, 旧规则通过 5/5, 格式失败 0, 超时 0。
代表样例: `L1-011` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 异常DUP-002涉及哪些报销记录?

工具轨迹摘录 `runs/gate4_standard_trae_v4pro_v2/trae-agent/L1-011/tool_calls.jsonl:1`:

````text
{"arguments": {"query": "DUP-002 异常 重复", "top_k": 10}, "error": null, "ok": true, "result_preview": {"query": "DUP-002 异常 重复", "results": [{"doc_id": "01_expense_reimbursement_2025.md", "score": 6.0405, "snippets": ["第十条 同一发票最多报销1次。发现同一发票在不同报销单中重复出现的,应认定为重复报销风险。", "第六条 财务部门对票据合法性、费用归属、预算占用和制度标准进行复核。复核不替代业务部门对事项真实性的确认。", "第三条 费用报销实行经办人真实性承诺、部门负责人业务审核、财务复核和授权审批相结合的管理原则。"], "title": "XX证券费用报销管理办法(2025修订版)"}, {"doc_id": "11_attendance_management.md", "score": 4.7508, "snippets": ["第一条 为规范XX证券考勤记录、请假申请、外勤登记和异常处理相关管理事项,制定本办法。"], "title": "XX证券考勤与休假管理办法"}, {"doc_id": "07_office_communication.md", "score": 2.6354, "snippets": ["第一条 为规范XX证券日常办公费用和通讯费用报销,制定本办法。"], "title": "XX证券办公与通讯费用管理办法"}, {"doc_id": "20_customer_complaint.md", "score": 1.7827, "snippets": ["第一条 为规范XX证券投诉受理、事实核查、回复留痕和改进闭环相关管理事项,制定本办法。"], "title": "XX证券客户投诉处理管理办法"}, {"doc_id": "03_authorization_management.md", "score": 1.739, "snippets": ["| AR-02 | 大于等于3000元且小于10000元 | 部门经理,并经财务复核 |"], "title": "XX证券授权管理办法"}], "top_k": 10}, "server": "policy_query_mcp", "tool": "search_policy", "ts": 1783580981.8667407}
````

最终轨迹摘录 `runs/gate4_standard_trae_v4pro_v2/trae-agent/L1-011/trajectory.json:2`:

````text
"task": "请直接回答这个审计问题: 异常DUP-002涉及哪些报销记录?\n\n这是完整任务,不要要求用户再提供任务或文件,不要探索项目目录,不要寻找评测入口。\n\n必须使用已连接的 MCP 工具查询制度或业务事实后再回答。\n\n你是费用审计助手,只处理本轮提供的虚构 XX证券 数据与制度语料。\n\n可用工具域:\n- policy_query_mcp: 查询制度文档、条款片段和制度原文。\n- expense_query_mcp: 查询费用报销 SQLite 中的原始业务事实。\n\n工作要求:\n- 先查制度依据,再查业务事实,最后给出结论。\n- 题面就是当前要回答的审计问题;不要检查本地工作目录、不要寻找评测脚本、不要等待下一条指令。\n- 不要回答“请提供具体任务”“环境已就绪”“我需要更多信息”;题面已经是完整任务。\n- 审计检测题必须返回支撑判断的 record_ids;若能确定标准 anomaly_ids 也一并返回,无法确定时 anomaly_ids 可为空数组。\n- 没有异常时 anomaly_ids 必须为空数组;record_ids 可填写被核查且判定为合规的记录 ID。\n- 制度问答题必须给出制度出处,至少包含 doc_id 和 clause_no。\n- 不要调用 shell、文件写入、网络访问或候选 harness 的编码工具。\n- 不要把旧版废止制度当作现行依据;如命中废止条款,必须说明其已废止。\n- 不要将题面中的陷阱位计为异常,除非原始事实和制度规则共同支持。\n\n最终回答必须只包含一个 JSON 代码块。JSON 必须能被标准 JSON 解析器解析,不要在 JSON 内写注释。\n为避免格式失败,`answer` 字段的值必须是标准 JSON 字符串,外层英文双引号必须保留。\n硬性约束: 禁止的是 `answer` 字符串内容内部出现额外 ASCII 双引号字符;角色名、制度名、档位名不要加英文引号。\n不要在 JSON 代码块之前或之后输出任何说明文字。\n\n格式:\n\n```json\n{\"anomaly_ids\": [\"A013\"], \"record_ids\": [\"R000001\"], \"answer\": \"结论摘要\", \"citations\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"clause_no\": \"费用报销管理办法-6.1\"}]}\n```\n\n字段要求:\n- `anomaly_ids`: 字符串数组。审计检测题填命中的异常 ID;无异常或陷阱题填空数组。\n- `record_ids`: 字符串数组。审计检测题填支撑结论的报销记录 ID;制度问答题填空数组;无异
...[truncated 447 chars]
````

候选答案摘录:

````text
{"anomaly_ids": ["DUP-002"], "record_ids": ["R000005", "R004202"], "answer": "异常DUP-002为重复报销风险,涉及同一发票FP202500000005(INV000005,供应商5450,金额88.83元)被两条报销记录重复使用:R000005(青竹系统测试交通费)与R004202(重复发票注入样本-青竹系统测试交通费),二者同为员工E0022刘冬梅、信息技术部D007、金额均88.83元且均已审批通过,违反同一发票最多报销1次的规定,构成重复报销。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "费用报销管理办法-第十条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选正确识别异常 DUP-002 并精确返回了期望的两条报销记录 ID (R000005, R004202)，回答正文与 citations 均语义完整且无无关信息。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### policy_data_comparison (制度+业务交叉核查)

表现: LLM内容通过 20/25, 旧规则通过 25/25, 格式失败 0, 超时 0。
代表样例: `L2-001` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 结合制度和业务数据,核查以R000002为线索的重复报销异常,返回异常ID和记录ID集合。

工具轨迹摘录 `runs/gate4_standard_trae_v4pro_v2/trae-agent/L2-001/tool_calls.jsonl:1`:

````text
{"arguments": {"record_id": "R000002"}, "error": null, "ok": true, "result_preview": {"approvals": [{"approval_id": "A000002", "approval_status": "approved", "approved_at": "2025-09-09", "approver_employee_id": "E0008", "approver_role": "部门经理", "tier_id": "AR-01"}], "record": {"amount": 423.79, "annual_budget": 381600.0, "budget_year": 2025, "city_tier": null, "days": null, "department_id": "D008", "department_name": "合规风控部", "employee_id": "E0050", "employee_level": "X1", "employee_name": "姚瑜", "expense_date": "2025-08-19", "expense_type": "office_supplies", "invoice_amount": 423.79, "invoice_date": "2025-08-19", "invoice_id": "INV000002", "invoice_no": "FP202500000002", "nights": null, "participants": null, "position_role": "员工", "reason": "清源项目资料装订用品费", "record_id": "R000002", "record_no": "BX2025000002", "reimburse_date": "2025-09-09", "special_approval": 0, "status": "approved", "vendor_name": "XX供应商7753"}}, "server": "expense_query_mcp", "tool": "get_expense_detail", "ts": 1783581672.4194837}
````

最终轨迹摘录 `runs/gate4_standard_trae_v4pro_v2/trae-agent/L2-001/trajectory.json:2`:

````text
"task": "请直接回答这个审计问题: 结合制度和业务数据,核查以R000002为线索的重复报销异常,返回异常ID和记录ID集合。\n\n这是完整任务,不要要求用户再提供任务或文件,不要探索项目目录,不要寻找评测入口。\n\n必须使用已连接的 MCP 工具查询制度或业务事实后再回答。\n\n你是费用审计助手,只处理本轮提供的虚构 XX证券 数据与制度语料。\n\n可用工具域:\n- policy_query_mcp: 查询制度文档、条款片段和制度原文。\n- expense_query_mcp: 查询费用报销 SQLite 中的原始业务事实。\n\n工作要求:\n- 先查制度依据,再查业务事实,最后给出结论。\n- 题面就是当前要回答的审计问题;不要检查本地工作目录、不要寻找评测脚本、不要等待下一条指令。\n- 不要回答“请提供具体任务”“环境已就绪”“我需要更多信息”;题面已经是完整任务。\n- 审计检测题必须返回支撑判断的 record_ids;若能确定标准 anomaly_ids 也一并返回,无法确定时 anomaly_ids 可为空数组。\n- 没有异常时 anomaly_ids 必须为空数组;record_ids 可填写被核查且判定为合规的记录 ID。\n- 制度问答题必须给出制度出处,至少包含 doc_id 和 clause_no。\n- 不要调用 shell、文件写入、网络访问或候选 harness 的编码工具。\n- 不要把旧版废止制度当作现行依据;如命中废止条款,必须说明其已废止。\n- 不要将题面中的陷阱位计为异常,除非原始事实和制度规则共同支持。\n\n最终回答必须只包含一个 JSON 代码块。JSON 必须能被标准 JSON 解析器解析,不要在 JSON 内写注释。\n为避免格式失败,`answer` 字段的值必须是标准 JSON 字符串,外层英文双引号必须保留。\n硬性约束: 禁止的是 `answer` 字符串内容内部出现额外 ASCII 双引号字符;角色名、制度名、档位名不要加英文引号。\n不要在 JSON 代码块之前或之后输出任何说明文字。\n\n格式:\n\n```json\n{\"anomaly_ids\": [\"A013\"], \"record_ids\": [\"R000001\"], \"answer\": \"结论摘要\", \"citations\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"clause_no\": \"费用报销管理办法-6.1\"}]}\n```\n\n字段要求:\n- `anomaly_ids`: 字符串数组。审计检测题填命中的异常 ID;无异常或陷阱题填空数组。\n- `record_ids`: 字符串数组。审计检测
...[truncated 477 chars]
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": ["R000002", "R004201"], "answer": "以R000002为线索核查,发票FP202500000002(INV000002,金额423.79元,供应商XX供应商7753)被两条报销记录重复使用:R000002(报销日2025-09-09)和R004201(报销日2025-02-18),二者均为员工姚瑜E0050、合规风控部D008、办公用品类、金额均为423.79元。同一发票被使用2次,违反同一发票最多报销1次的规定,构成重复报销异常。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "费用报销管理办法-第十条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选虽未列出异常ID，但record_ids和回答正文正确描述了重复报销异常，语义匹配预期DUP-001。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### full_year_rule_audit (全年专项扫描)

表现: LLM内容通过 4/5, 旧规则通过 4/5, 格式失败 0, 超时 0。
代表样例: `L3-001` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 请对全年数据做重复报销专项扫描,返回全部异常ID和记录ID集合。

工具轨迹摘录 `runs/gate4_standard_trae_v4pro_v2/trae-agent/L3-001/tool_calls.jsonl:1`:

````text
{"arguments": {"query": "重复报销 同一发票 多次报销", "top_k": 5}, "error": null, "ok": true, "result_preview": {"query": "重复报销 同一发票 多次报销", "results": [{"doc_id": "01_expense_reimbursement_2025.md", "score": 16.4894, "snippets": ["第十条 同一发票最多报销1次。发现同一发票在不同报销单中重复出现的,应认定为重复报销风险。", "第十一条 不得将同一事项或同类事项拆分为多笔报销以规避审批权限。同一员工、同一费用类型在7天内出现2笔及以上报销,且合计金额达到《授权管理办法》附件二较高审批线的,应重点核查拆分规", "第七条 员工应在费用发生后60天内提交报销申请;超过期限的,原则上不得报销。"], "title": "XX证券费用报销管理办法(2025修订版)"}, {"doc_id": "06_business_entertainment.md", "score": 7.7561, "snippets": ["第四条 同一客户拜访或同一会议安排不得拆分为多个报销事项。", "发文字号: XX证客规〔2025〕己号", "## 第一章 总则"], "title": "XX证券业务招待费管理办法"}, {"doc_id": "16_contract_management.md", "score": 2.5802, "snippets": ["第八条 本办法为管理类制度,不作为费用报销标准依据。", "第一条 为规范XX证券合同起草、法务审核、签署和履约跟踪相关管理事项,制定本办法。", "# XX证券合同管理办法"], "title": "XX证券合同管理办法"}, {"doc_id": "08_budget_management.md", "score": 2.3836, "snippets": ["第五条 本办法与费用报销制度共同构成费用控制依据。", "第三条 部门费用累计使用达到年度预算额度的1.0倍后,原则上不得继续报销。", "发文字号: XX证财规〔2025〕辛号"], "title": "XX证券预算管理办法"}, {"doc_id": "03_authorization_management.md", "score": 2.2304, "snippets": ["第二条 本办法附件二适用于费用报销系统自动派生审批角色,相关金额为现行有效审批线。", "## 附件二 费用报销审批权限表", "第五条 本办法自二〇二五年一月一日起施行。"], "title": "XX证券授权管理办法"}], "top_k": 5}, "server": "poli
...[truncated 64 chars]
````

最终轨迹摘录 `runs/gate4_standard_trae_v4pro_v2/trae-agent/L3-001/trajectory.json:2`:

````text
"task": "请直接回答这个审计问题: 请对全年数据做重复报销专项扫描,返回全部异常ID和记录ID集合。\n\n这是完整任务,不要要求用户再提供任务或文件,不要探索项目目录,不要寻找评测入口。\n\n必须使用已连接的 MCP 工具查询制度或业务事实后再回答。\n\n你是费用审计助手,只处理本轮提供的虚构 XX证券 数据与制度语料。\n\n可用工具域:\n- policy_query_mcp: 查询制度文档、条款片段和制度原文。\n- expense_query_mcp: 查询费用报销 SQLite 中的原始业务事实。\n\n工作要求:\n- 先查制度依据,再查业务事实,最后给出结论。\n- 题面就是当前要回答的审计问题;不要检查本地工作目录、不要寻找评测脚本、不要等待下一条指令。\n- 不要回答“请提供具体任务”“环境已就绪”“我需要更多信息”;题面已经是完整任务。\n- 审计检测题必须返回支撑判断的 record_ids;若能确定标准 anomaly_ids 也一并返回,无法确定时 anomaly_ids 可为空数组。\n- 没有异常时 anomaly_ids 必须为空数组;record_ids 可填写被核查且判定为合规的记录 ID。\n- 制度问答题必须给出制度出处,至少包含 doc_id 和 clause_no。\n- 不要调用 shell、文件写入、网络访问或候选 harness 的编码工具。\n- 不要把旧版废止制度当作现行依据;如命中废止条款,必须说明其已废止。\n- 不要将题面中的陷阱位计为异常,除非原始事实和制度规则共同支持。\n\n最终回答必须只包含一个 JSON 代码块。JSON 必须能被标准 JSON 解析器解析,不要在 JSON 内写注释。\n为避免格式失败,`answer` 字段的值必须是标准 JSON 字符串,外层英文双引号必须保留。\n硬性约束: 禁止的是 `answer` 字符串内容内部出现额外 ASCII 双引号字符;角色名、制度名、档位名不要加英文引号。\n不要在 JSON 代码块之前或之后输出任何说明文字。\n\n格式:\n\n```json\n{\"anomaly_ids\": [\"A013\"], \"record_ids\": [\"R000001\"], \"answer\": \"结论摘要\", \"citations\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"clause_no\": \"费用报销管理办法-6.1\"}]}\n```\n\n字段要求:\n- `anomaly_ids`: 字符串数组。审计检测题填命中的异常 ID;无异常或陷阱题填空数组。\n- `record_ids`: 字符串数组。审计检测题填支撑结论的报销记录 I
...[truncated 462 chars]
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": ["R000002", "R004201", "R000005", "R004202", "R000020", "R004203", "R000028", "R004204", "R000037", "R004205", "R000055", "R004206"], "answer": "全年重复报销专项扫描发现6张发票被两张不同报销单重复使用,违反同一发票最多报销1次的规定,应认定为重复报销风险。涉及发票及记录:FP202500000002对应R000002和R004201,FP202500000005对应R000005和R004202,FP202500000020对应R000020和R004203,FP202500000028对应R000028和R004204,FP202500000037对应R000037和R004205,FP202500000055对应R000055和R004206,共12条报销记录。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "费用报销管理办法-第十条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选在record_ids和answer中明确给出正确的重复报销规则及6组对应记录，语义上命中全部预期异常ID，且record_id完全覆盖。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### version_trap (版本陷阱)

表现: LLM内容通过 1/1, 旧规则通过 1/1, 格式失败 0, 超时 0。
代表样例: `L3-006` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 请判断费用报销审批线应采用2022版还是2025修订版,并指出部门总经理审批线。

工具轨迹摘录 `runs/gate4_standard_trae_v4pro_v2/trae-agent/L3-006/tool_calls.jsonl:1`:

````text
{"arguments": {}, "error": null, "ok": true, "result_preview": {"preview": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_h
...[truncated 334 chars]
````

最终轨迹摘录 `runs/gate4_standard_trae_v4pro_v2/trae-agent/L3-006/trajectory.json:2`:

````text
"task": "请直接回答这个审计问题: 请判断费用报销审批线应采用2022版还是2025修订版,并指出部门总经理审批线。\n\n这是完整任务,不要要求用户再提供任务或文件,不要探索项目目录,不要寻找评测入口。\n\n必须使用已连接的 MCP 工具查询制度或业务事实后再回答。\n\n你是费用审计助手,只处理本轮提供的虚构 XX证券 数据与制度语料。\n\n可用工具域:\n- policy_query_mcp: 查询制度文档、条款片段和制度原文。\n- expense_query_mcp: 查询费用报销 SQLite 中的原始业务事实。\n\n工作要求:\n- 先查制度依据,再查业务事实,最后给出结论。\n- 题面就是当前要回答的审计问题;不要检查本地工作目录、不要寻找评测脚本、不要等待下一条指令。\n- 不要回答“请提供具体任务”“环境已就绪”“我需要更多信息”;题面已经是完整任务。\n- 审计检测题必须返回支撑判断的 record_ids;若能确定标准 anomaly_ids 也一并返回,无法确定时 anomaly_ids 可为空数组。\n- 没有异常时 anomaly_ids 必须为空数组;record_ids 可填写被核查且判定为合规的记录 ID。\n- 制度问答题必须给出制度出处,至少包含 doc_id 和 clause_no。\n- 不要调用 shell、文件写入、网络访问或候选 harness 的编码工具。\n- 不要把旧版废止制度当作现行依据;如命中废止条款,必须说明其已废止。\n- 不要将题面中的陷阱位计为异常,除非原始事实和制度规则共同支持。\n\n最终回答必须只包含一个 JSON 代码块。JSON 必须能被标准 JSON 解析器解析,不要在 JSON 内写注释。\n为避免格式失败,`answer` 字段的值必须是标准 JSON 字符串,外层英文双引号必须保留。\n硬性约束: 禁止的是 `answer` 字符串内容内部出现额外 ASCII 双引号字符;角色名、制度名、档位名不要加英文引号。\n不要在 JSON 代码块之前或之后输出任何说明文字。\n\n格式:\n\n```json\n{\"anomaly_ids\": [\"A013\"], \"record_ids\": [\"R000001\"], \"answer\": \"结论摘要\", \"citations\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"clause_no\": \"费用报销管理办法-6.1\"}]}\n```\n\n字段要求:\n- `anomaly_ids`: 字符串数组。审计检测题填命中的异常 ID;无异常或陷阱题填空数组。\n- `record_ids`: 字符串数组。审计检测题填支撑结
...[truncated 462 chars]
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "应采用2025修订版《XX证券费用报销管理办法(2025修订版)》,2022版已废止,仅作制度沿革留档,不得作为现行审批依据。2025版正文不再列示具体金额,单笔审批权限统一按《授权管理办法》附件二执行。据现行有效审批线,部门总经理审批线为档位AR-03,即单笔金额大于等于10000元且小于50000元;2022版所称达到8000元提交部门总经理审批的规定已被替代。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"}, {"doc_id": "03_authorization_management.md", "clause_no": "附件二-AR-03"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第四条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选回答明确指定应采用2025修订版，指出2022版已废止，并给出部门总经理审批线为10000元起，完全覆盖三个期望事实。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### two_hop_retrieval (双跳检索)

表现: LLM内容通过 1/1, 旧规则通过 1/1, 格式失败 0, 超时 0。
代表样例: `L3-007` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 报销办法没有直接列审批金额时,请通过交叉引用找到单笔费用审批档位。

工具轨迹摘录 `runs/gate4_standard_trae_v4pro_v2/trae-agent/L3-007/tool_calls.jsonl:1`:

````text
{"arguments": {}, "error": null, "ok": true, "result_preview": {"preview": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_h
...[truncated 333 chars]
````

最终轨迹摘录 `runs/gate4_standard_trae_v4pro_v2/trae-agent/L3-007/trajectory.json:2`:

````text
"task": "请直接回答这个审计问题: 报销办法没有直接列审批金额时,请通过交叉引用找到单笔费用审批档位。\n\n这是完整任务,不要要求用户再提供任务或文件,不要探索项目目录,不要寻找评测入口。\n\n必须使用已连接的 MCP 工具查询制度或业务事实后再回答。\n\n你是费用审计助手,只处理本轮提供的虚构 XX证券 数据与制度语料。\n\n可用工具域:\n- policy_query_mcp: 查询制度文档、条款片段和制度原文。\n- expense_query_mcp: 查询费用报销 SQLite 中的原始业务事实。\n\n工作要求:\n- 先查制度依据,再查业务事实,最后给出结论。\n- 题面就是当前要回答的审计问题;不要检查本地工作目录、不要寻找评测脚本、不要等待下一条指令。\n- 不要回答“请提供具体任务”“环境已就绪”“我需要更多信息”;题面已经是完整任务。\n- 审计检测题必须返回支撑判断的 record_ids;若能确定标准 anomaly_ids 也一并返回,无法确定时 anomaly_ids 可为空数组。\n- 没有异常时 anomaly_ids 必须为空数组;record_ids 可填写被核查且判定为合规的记录 ID。\n- 制度问答题必须给出制度出处,至少包含 doc_id 和 clause_no。\n- 不要调用 shell、文件写入、网络访问或候选 harness 的编码工具。\n- 不要把旧版废止制度当作现行依据;如命中废止条款,必须说明其已废止。\n- 不要将题面中的陷阱位计为异常,除非原始事实和制度规则共同支持。\n\n最终回答必须只包含一个 JSON 代码块。JSON 必须能被标准 JSON 解析器解析,不要在 JSON 内写注释。\n为避免格式失败,`answer` 字段的值必须是标准 JSON 字符串,外层英文双引号必须保留。\n硬性约束: 禁止的是 `answer` 字符串内容内部出现额外 ASCII 双引号字符;角色名、制度名、档位名不要加英文引号。\n不要在 JSON 代码块之前或之后输出任何说明文字。\n\n格式:\n\n```json\n{\"anomaly_ids\": [\"A013\"], \"record_ids\": [\"R000001\"], \"answer\": \"结论摘要\", \"citations\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"clause_no\": \"费用报销管理办法-6.1\"}]}\n```\n\n字段要求:\n- `anomaly_ids`: 字符串数组。审计检测题填命中的异常 ID;无异常或陷阱题填空数组。\n- `record_ids`: 字符串数组。审计检测题填支撑结论的报销记录
...[truncated 460 chars]
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "费用报销管理办法(2025修订版)第五条明确单笔费用报销审批权限不在正文列示金额,统一按《XX证券授权管理办法》附件二执行,费用系统据此自动派生审批角色。经交叉引用,授权管理办法附件二费用报销审批权限表现行档位为:AR-01 大于等于0元且小于3000元由部门经理审批;AR-02 大于等于3000元且小于10000元由部门经理审批并经财务复核;AR-03 大于等于10000元且小于50000元由部门总经理审批;AR-04 大于等于50000元且小于200000元由分管副总审批;AR-05 大于等于200000元由总经理办公会审批。2022版办法中8000元、30000元等旧金额已被替代废止,不得作为现行依据。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "费用报销管理办法-第五条"}, {"doc_id": "03_authorization_management.md", "clause_no": "授权管理办法-附件二"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选回答明确给出了部门总经理审批线为10000元（AR-03），并指出金额来源于授权管理办法附件二，完全符合预期事实。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### near_clause_disambiguation (近似条款辨析)

表现: LLM内容通过 1/1, 旧规则通过 0/1, 格式失败 0, 超时 0。
代表样例: `L3-008` / `precise` / `通过` / `llm_score=1.0` / `rule_score=0.0` / `layer=ok`。
题面: 比较差旅住宿和培训住宿标准,说明为什么不能混用。

工具轨迹摘录 `runs/gate4_standard_trae_v4pro_v2/trae-agent/L3-008/tool_calls.jsonl:1`:

````text
{"arguments": {"query": "差旅住宿标准 培训住宿标准", "top_k": 10}, "error": null, "ok": true, "result_preview": {"preview": "{\"query\": \"差旅住宿标准 培训住宿标准\", \"results\": [{\"doc_id\": \"05_training_expense.md\", \"score\": 30.4776, \"snippets\": [\"第六条 培训住宿标准仅适用于培训期间住宿,不得与差旅住宿标准混用。\", \"第五条 培训期间住宿标准如下,单位为元/人/晚。\", \"| 城市档位 | 培训住宿标准 |\"], \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"score\": 29.3248, \"snippets\": [\"第七条 培训期间住宿不适用本办法住宿表,应按《XX证券培训费管理办法》执行。\", \"第四条 差旅住宿费标准如下,单位为元/人/晚。\", \"第三条 住宿标准按员工职级和城市档位确定。员工职级包括员工级、经理级、部门负责人级和高管级;城市档位包括一类城市、二类城市和三类城市。\"], \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"01_expense_reimbursement_2025.md\", \"score\": 6.4677, \"snippets\": [\"第二条 本办法适用于XX证券各部门、分支机构及全体员工发生的差旅、培训、招待、办公、通讯等费用报销事项。\", \"第六条 财务部门对票据合法性、费用归属、预算占用和制度标准进行复核。复核不替代业务部门对事项真实性的确认。\", \"第十二条 无专项审批时,报销金额不得超过对应制度标准的1.0倍。\"], \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"06_business_entertainment.md\", \"score\": 0.8989, \"snippets\": [\"## 第二章 标准管理\"], \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"score\": 0.7415, \"snippets\": [\"第八条 本办法为管理类制度,不作为费用报销标准依据。\"], \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\",
...[truncated 331 chars]
````

最终轨迹摘录 `runs/gate4_standard_trae_v4pro_v2/trae-agent/L3-008/trajectory.json:2`:

````text
"task": "请直接回答这个审计问题: 比较差旅住宿和培训住宿标准,说明为什么不能混用。\n\n这是完整任务,不要要求用户再提供任务或文件,不要探索项目目录,不要寻找评测入口。\n\n必须使用已连接的 MCP 工具查询制度或业务事实后再回答。\n\n你是费用审计助手,只处理本轮提供的虚构 XX证券 数据与制度语料。\n\n可用工具域:\n- policy_query_mcp: 查询制度文档、条款片段和制度原文。\n- expense_query_mcp: 查询费用报销 SQLite 中的原始业务事实。\n\n工作要求:\n- 先查制度依据,再查业务事实,最后给出结论。\n- 题面就是当前要回答的审计问题;不要检查本地工作目录、不要寻找评测脚本、不要等待下一条指令。\n- 不要回答“请提供具体任务”“环境已就绪”“我需要更多信息”;题面已经是完整任务。\n- 审计检测题必须返回支撑判断的 record_ids;若能确定标准 anomaly_ids 也一并返回,无法确定时 anomaly_ids 可为空数组。\n- 没有异常时 anomaly_ids 必须为空数组;record_ids 可填写被核查且判定为合规的记录 ID。\n- 制度问答题必须给出制度出处,至少包含 doc_id 和 clause_no。\n- 不要调用 shell、文件写入、网络访问或候选 harness 的编码工具。\n- 不要把旧版废止制度当作现行依据;如命中废止条款,必须说明其已废止。\n- 不要将题面中的陷阱位计为异常,除非原始事实和制度规则共同支持。\n\n最终回答必须只包含一个 JSON 代码块。JSON 必须能被标准 JSON 解析器解析,不要在 JSON 内写注释。\n为避免格式失败,`answer` 字段的值必须是标准 JSON 字符串,外层英文双引号必须保留。\n硬性约束: 禁止的是 `answer` 字符串内容内部出现额外 ASCII 双引号字符;角色名、制度名、档位名不要加英文引号。\n不要在 JSON 代码块之前或之后输出任何说明文字。\n\n格式:\n\n```json\n{\"anomaly_ids\": [\"A013\"], \"record_ids\": [\"R000001\"], \"answer\": \"结论摘要\", \"citations\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"clause_no\": \"费用报销管理办法-6.1\"}]}\n```\n\n字段要求:\n- `anomaly_ids`: 字符串数组。审计检测题填命中的异常 ID;无异常或陷阱题填空数组。\n- `record_ids`: 字符串数组。审计检测题填支撑结论的报销记录 ID;制度问答题填
...[truncated 460 chars]
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "两套住宿标准适用场景和计算维度不同,故不得混用。差旅住宿(差旅费管理办法第四条)按员工职级和城市档位双维度确定:员工级450/380/300、经理级650/550/450、部门负责人级850/700/600、高管级1100/900/750(分别对应一类、二类、三类城市,元/人/晚);培训住宿(培训费管理办法第五条)仅按城市档位单维度确定,不区分职级:一类城市500、二类城市420、三类城市350。两者适用情形互斥:差旅费管理办法第七条明确培训期间住宿不适用差旅住宿表,应按培训费管理办法执行;培训费管理办法第六条明确培训住宿标准仅适用于培训期间住宿,不得与差旅住宿标准混用。若混用,例如用职级较高的差旅标准套报培训期间住宿,或反向套用,将绕开对应场景的标准控制,造成超标准报销,故必须按实际发生事项分别适用各自办法。", "citations": [{"doc_id": "04_travel_expense.md", "clause_no": "差旅费管理办法-第四条"}, {"doc_id": "04_travel_expense.md", "clause_no": "差旅费管理办法-第七条"}, {"doc_id": "05_training_expense.md", "clause_no": "培训费管理办法-第五条"}, {"doc_id": "05_training_expense.md", "clause_no": "培训费管理办法-第六条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 0.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选回答明确说明差旅住宿适用差旅费管理办法，培训住宿适用培训费管理办法，并指出两组数值不同不得混用，满足全部期望事实，且引用条款支撑。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### audit_report (报告式任务)

表现: LLM内容通过 1/2, 旧规则通过 1/2, 格式失败 0, 超时 0。
代表样例: `L3-010` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 请专门写一段版本陷阱审计说明,解释旧版审批线可能导致的误判。

工具轨迹摘录 `runs/gate4_standard_trae_v4pro_v2/trae-agent/L3-010/tool_calls.jsonl:1`:

````text
{"arguments": {"query": "审批线 版本 旧版 废止 审批权限 变更", "top_k": 8}, "error": null, "ok": true, "result_preview": {"preview": "{\"query\": \"审批线 版本 旧版 废止 审批权限 变更\", \"results\": [{\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"score\": 19.7469, \"snippets\": [\"第四条 本办法的审批金额已被后续制度替代,不得作为现行审批依据。\", \"第一条 本办法为XX证券旧版费用报销制度文本,仅作为制度沿革留档。现行制度应以《XX证券费用报销管理办法(2025修订版)》为准。\", \"第二条 旧版制度曾规定,单笔报销金额达到8000元的,应提交部门总经理审批。\"], \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"01_expense_reimbursement_2025.md\", \"score\": 14.3853, \"snippets\": [\"第十一条 不得将同一事项或同类事项拆分为多笔报销以规避审批权限。同一员工、同一费用类型在7天内出现2笔及以上报销,且合计金额达到《授权管理办法》附件二较高审批线的,应重点核查拆分规\", \"第五条 单笔费用报销的审批权限,不在本办法正文列示具体金额,统一按《XX证券授权管理办法》附件二执行。费用系统应按附件二自动派生审批角色。\", \"第三条 费用报销实行经办人真实性承诺、部门负责人业务审核、财务复核和授权审批相结合的管理原则。\"], \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"score\": 13.0687, \"snippets\": [\"第二条 本办法附件二适用于费用报销系统自动派生审批角色,相关金额为现行有效审批线。\", \"第一条 为明确XX证券经营管理授权边界,提升审批效率,制定本办法。\", \"## 附件二 费用报销审批权限表\"], \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"14_hr_transfer.md\", \"score\": 6.6473, \"snippets\": [\"第一条 为规范XX证券岗位调整、任职通知、交接确认和权限变更相关管理事项,制定本办法。\", \"第六条 审核人员应关注事项真实性、授权完整性和资料一致性。\", \"<!-- SYNTHETIC
...[truncated 311 chars]
````

最终轨迹摘录 `runs/gate4_standard_trae_v4pro_v2/trae-agent/L3-010/trajectory.json:2`:

````text
"task": "请直接回答这个审计问题: 请专门写一段版本陷阱审计说明,解释旧版审批线可能导致的误判。\n\n这是完整任务,不要要求用户再提供任务或文件,不要探索项目目录,不要寻找评测入口。\n\n必须使用已连接的 MCP 工具查询制度或业务事实后再回答。\n\n你是费用审计助手,只处理本轮提供的虚构 XX证券 数据与制度语料。\n\n可用工具域:\n- policy_query_mcp: 查询制度文档、条款片段和制度原文。\n- expense_query_mcp: 查询费用报销 SQLite 中的原始业务事实。\n\n工作要求:\n- 先查制度依据,再查业务事实,最后给出结论。\n- 题面就是当前要回答的审计问题;不要检查本地工作目录、不要寻找评测脚本、不要等待下一条指令。\n- 不要回答“请提供具体任务”“环境已就绪”“我需要更多信息”;题面已经是完整任务。\n- 审计检测题必须返回支撑判断的 record_ids;若能确定标准 anomaly_ids 也一并返回,无法确定时 anomaly_ids 可为空数组。\n- 没有异常时 anomaly_ids 必须为空数组;record_ids 可填写被核查且判定为合规的记录 ID。\n- 制度问答题必须给出制度出处,至少包含 doc_id 和 clause_no。\n- 不要调用 shell、文件写入、网络访问或候选 harness 的编码工具。\n- 不要把旧版废止制度当作现行依据;如命中废止条款,必须说明其已废止。\n- 不要将题面中的陷阱位计为异常,除非原始事实和制度规则共同支持。\n\n最终回答必须只包含一个 JSON 代码块。JSON 必须能被标准 JSON 解析器解析,不要在 JSON 内写注释。\n为避免格式失败,`answer` 字段的值必须是标准 JSON 字符串,外层英文双引号必须保留。\n硬性约束: 禁止的是 `answer` 字符串内容内部出现额外 ASCII 双引号字符;角色名、制度名、档位名不要加英文引号。\n不要在 JSON 代码块之前或之后输出任何说明文字。\n\n格式:\n\n```json\n{\"anomaly_ids\": [\"A013\"], \"record_ids\": [\"R000001\"], \"answer\": \"结论摘要\", \"citations\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"clause_no\": \"费用报销管理办法-6.1\"}]}\n```\n\n字段要求:\n- `anomaly_ids`: 字符串数组。审计检测题填命中的异常 ID;无异常或陷阱题填空数组。\n- `record_ids`: 字符串数组。审计检测题填支撑结论的报销记录 ID;
...[truncated 452 chars]
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "版本陷阱审计说明:XX证券费用报销审批权限存在新旧两套版本,极易造成误判。旧版费用报销管理办法2022版第二条、第三条规定单笔达到8000元提交部门总经理审批、达到30000元提交分管副总审批,但该办法第一条、第四条已明确其仅作制度沿革留档、审批金额已被后续制度替代,不得作为现行审批依据。现行有效审批线以费用报销管理办法2025修订版第五条指向的授权管理办法附件二为准:AR-01区间0至3000元由部门经理审批、AR-02区间3000至10000元由部门经理并经财务复核、AR-03区间10000至50000元由部门总经理审批、AR-04区间50000至200000元由分管副总审批、AR-05区间20万元及以上由总经理办公会审批。误判风险有两类:一是从严误判,若沿用旧版8000元触发部门总经理的门槛,会把按现行AR-02仅需部门经理加财务复核的8000至10000元报销错判为审批缺失;沿用旧版30000元触发分管副总的门槛,会把按现行AR-03仅需部门总经理的3万至5万元报销错判为越权少批。二是从宽漏判,旧版档位划分与现行不一致时会放过本应升档的记录。因此审计核对审批完整性时必须以授权管理办法附件二现行审批线派生角色为唯一依据,核验记录金额落入的档位与实际审批角色是否匹配,不得援引已废止的2022版金额门槛。", "citations": [{"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "费用报销管理办法2022版-第一条"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "费用报销管理办法2022版-第二条"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "费用报销管理办法2022版-第三条"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "费用报销管理办法2022版-第四条"}, {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "费用报销管理办法2025修订版-第五条"}, {"doc_id": "03_authorization_management.md", "clause_no": "授权管理办法-第二条"}, {"doc_id": "03_authorization_management.md"
...[truncated 103 chars]
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选回答准确满足了所有rubric断言，正确指出现行部门总经理审批线10000元、旧版8000元已废止、说明通过授权管理办法附件二取得现行审批金额，并未将旧版作为当前依据。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### clean_but_suspicious (陷阱题)

表现: LLM内容通过 4/5, 旧规则通过 5/5, 格式失败 0, 超时 0。
代表样例: `TRAP-002` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 请核查TRAP-002涉及的记录是否构成异常,正确时应说明无异常。

工具轨迹摘录 `runs/gate4_standard_trae_v4pro_v2/trae-agent/TRAP-002/tool_calls.jsonl:1`:

````text
{"arguments": {}, "error": null, "ok": true, "result_preview": {"preview": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_h
...[truncated 334 chars]
````

最终轨迹摘录 `runs/gate4_standard_trae_v4pro_v2/trae-agent/TRAP-002/trajectory.json:2`:

````text
"task": "请直接回答这个审计问题: 请核查TRAP-002涉及的记录是否构成异常,正确时应说明无异常。\n\n这是完整任务,不要要求用户再提供任务或文件,不要探索项目目录,不要寻找评测入口。\n\n必须使用已连接的 MCP 工具查询制度或业务事实后再回答。\n\n你是费用审计助手,只处理本轮提供的虚构 XX证券 数据与制度语料。\n\n可用工具域:\n- policy_query_mcp: 查询制度文档、条款片段和制度原文。\n- expense_query_mcp: 查询费用报销 SQLite 中的原始业务事实。\n\n工作要求:\n- 先查制度依据,再查业务事实,最后给出结论。\n- 题面就是当前要回答的审计问题;不要检查本地工作目录、不要寻找评测脚本、不要等待下一条指令。\n- 不要回答“请提供具体任务”“环境已就绪”“我需要更多信息”;题面已经是完整任务。\n- 审计检测题必须返回支撑判断的 record_ids;若能确定标准 anomaly_ids 也一并返回,无法确定时 anomaly_ids 可为空数组。\n- 没有异常时 anomaly_ids 必须为空数组;record_ids 可填写被核查且判定为合规的记录 ID。\n- 制度问答题必须给出制度出处,至少包含 doc_id 和 clause_no。\n- 不要调用 shell、文件写入、网络访问或候选 harness 的编码工具。\n- 不要把旧版废止制度当作现行依据;如命中废止条款,必须说明其已废止。\n- 不要将题面中的陷阱位计为异常,除非原始事实和制度规则共同支持。\n\n最终回答必须只包含一个 JSON 代码块。JSON 必须能被标准 JSON 解析器解析,不要在 JSON 内写注释。\n为避免格式失败,`answer` 字段的值必须是标准 JSON 字符串,外层英文双引号必须保留。\n硬性约束: 禁止的是 `answer` 字符串内容内部出现额外 ASCII 双引号字符;角色名、制度名、档位名不要加英文引号。\n不要在 JSON 代码块之前或之后输出任何说明文字。\n\n格式:\n\n```json\n{\"anomaly_ids\": [\"A013\"], \"record_ids\": [\"R000001\"], \"answer\": \"结论摘要\", \"citations\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"clause_no\": \"费用报销管理办法-6.1\"}]}\n```\n\n字段要求:\n- `anomaly_ids`: 字符串数组。审计检测题填命中的异常 ID;无异常或陷阱题填空数组。\n- `record_ids`: 字符串数组。审计检测题填支撑结论的报销记录
...[truncated 467 chars]
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": ["R004234", "R004235"], "answer": "TRAP-002对应同日同额不同发票陷阱样本R004234与R004235:同为财务管理部张婷(E0009)在2025-10-20报销的办公用品各250元,金额与日期相同,表面疑似重复报销。但两笔使用不同发票号FP2025X0004228与FP2025X0004229,分属不同供应商,每张发票各自仅被使用1次,不满足同一发票最多报销1次的重复报销认定条件;10月两笔合计500元未超过员工个人办公用品每月600元上限,合计金额也远低于任何审批线,不构成拆分规避审批。二者均已经部门经理审批通过,故为合规记录,无异常。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"}, {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十一条"}, {"doc_id": "07_office_communication.md", "clause_no": "第二条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选正确识别为无异常，给出了预期的 record_ids，并说明了不同发票和总额未超限的合规理由。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。


## OpenCode

### 题型表现

| 题型 | 总数 | LLM内容通过 | 旧规则通过 | 格式失败 | LLM未通过 | 超时 | 判断 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| policy_qa | 4 | 4 | 4 | 0 | 0 | 0 | 仍是最稳定题型 |
| version_check | 1 | 1 | 1 | 0 | 0 | 0 | 中等表现 |
| single_anomaly_lookup | 5 | 5 | 5 | 0 | 0 | 0 | LLM judge 认可部分语义命中,但集合归并仍不稳 |
| ground_truth_lookup | 5 | 4 | 4 | 0 | 1 | 0 | record_id 集合覆盖是主要瓶颈 |
| policy_data_comparison | 25 | 19 | 25 | 0 | 6 | 0 | LLM judge 认可部分语义命中,但集合归并仍不稳 |
| full_year_rule_audit | 5 | 3 | 3 | 0 | 2 | 0 | LLM judge 认可部分语义命中,但集合归并仍不稳 |
| version_trap | 1 | 0 | 0 | 0 | 1 | 0 | 中等表现 |
| two_hop_retrieval | 1 | 1 | 1 | 0 | 0 | 0 | 中等表现 |
| near_clause_disambiguation | 1 | 1 | 0 | 0 | 0 | 0 | 中等表现 |
| audit_report | 2 | 1 | 0 | 0 | 1 | 0 | 报告可读性不等于 rubric 完整满足 |
| clean_but_suspicious | 5 | 2 | 5 | 0 | 3 | 0 | 陷阱识别有一定能力 |

### 各题型典型轨迹

下面每个题型放一个代表样例。样例选择规则: 通过率较高的题型选通过样例; 失败为主的题型选该题型最常见失败层。

#### policy_qa (纯制度问答)

表现: LLM内容通过 4/4, 旧规则通过 4/4, 格式失败 0, 超时 0。
代表样例: `L1-001` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 现行制度下,单笔费用报销达到多少金额需要部门总经理审批?

工具轨迹摘录 `runs/gate4_standard_opencode_v4pro_v1/opencode/L1-001/tool_calls.jsonl:1`:

````text
{"arguments": {}, "error": null, "ok": true, "result_preview": {"preview": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_h
...[truncated 334 chars]
````

最终轨迹摘录 `runs/gate4_standard_opencode_v4pro_v1/opencode/L1-001/trajectory.json:170`:

````text
"type": "text",
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "现行制度下，单笔费用报销金额达到10000元（含）以上且低于50000元时，需要部门总经理审批。根据《XX证券授权管理办法》附件二费用报销审批权限表，AR-03档位规定单笔金额大于等于10000元且小于50000元的必要审批角色为部门总经理。", "citations": [{"doc_id": "03_authorization_management.md", "clause_no": "附件二 AR-03"}, {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选回答准确提供了部门总经理审批线为10000元，符合期望事实，且依据充分。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### version_check (版本检查)

表现: LLM内容通过 1/1, 旧规则通过 1/1, 格式失败 0, 超时 0。
代表样例: `L1-003` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 2022版中部门总经理审批线是多少,它现在是否有效?

工具轨迹摘录 `runs/gate4_standard_opencode_v4pro_v1/opencode/L1-003/tool_calls.jsonl:1`:

````text
{"arguments": {}, "error": null, "ok": true, "result_preview": {"preview": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_h
...[truncated 334 chars]
````

最终轨迹摘录 `runs/gate4_standard_opencode_v4pro_v1/opencode/L1-003/trajectory.json:169`:

````text
"type": "text",
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "2022版中部门总经理审批线是单笔报销金额达到8000元应提交部门总经理审批。该审批线现已无效：2022版第四条明确其审批金额已被后续制度替代、不得作为现行审批依据；2025修订版第十四条明确2022版已同时废止，现行审批权限按《授权管理办法》附件二执行。", "citations": [{"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第二条"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第四条"}, {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十四条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "回答准确给出了2022版部门总经理审批线为8000元，并说明已废止，覆盖了预期事实。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### single_anomaly_lookup (单条异常判断)

表现: LLM内容通过 5/5, 旧规则通过 5/5, 格式失败 0, 超时 0。
代表样例: `L1-006` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 请判断报销记录R000002是否命中重复报销,如命中请返回异常ID。

工具轨迹摘录 `runs/gate4_standard_opencode_v4pro_v1/opencode/L1-006/tool_calls.jsonl:1`:

````text
{"arguments": {"record_id": "R000002"}, "error": null, "ok": true, "result_preview": {"approvals": [{"approval_id": "A000002", "approval_status": "approved", "approved_at": "2025-09-09", "approver_employee_id": "E0008", "approver_role": "部门经理", "tier_id": "AR-01"}], "record": {"amount": 423.79, "annual_budget": 381600.0, "budget_year": 2025, "city_tier": null, "days": null, "department_id": "D008", "department_name": "合规风控部", "employee_id": "E0050", "employee_level": "X1", "employee_name": "姚瑜", "expense_date": "2025-08-19", "expense_type": "office_supplies", "invoice_amount": 423.79, "invoice_date": "2025-08-19", "invoice_id": "INV000002", "invoice_no": "FP202500000002", "nights": null, "participants": null, "position_role": "员工", "reason": "清源项目资料装订用品费", "record_id": "R000002", "record_no": "BX2025000002", "reimburse_date": "2025-09-09", "special_approval": 0, "status": "approved", "vendor_name": "XX供应商7753"}}, "server": "expense_query_mcp", "tool": "get_expense_detail", "ts": 1783579416.4854121}
````

最终轨迹摘录 `runs/gate4_standard_opencode_v4pro_v1/opencode/L1-006/trajectory.json:750`:

````text
"type": "text",
````

候选答案摘录:

````text
{"anomaly_ids": ["ANO-0001"], "record_ids": ["R000002", "R004201"], "answer": "报销记录R000002命中重复报销。发票FP202500000002在R000002和R004201两笔报销单中重复出现，同一员工姚瑜、同一费用类型office_supplies、同一金额423.79元，违反费用报销管理办法第十条同一发票最多报销1次的规定。R004201为重复发票注入样本，确认该异常成立。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "回答正确识别了重复报销异常，关联记录R000002和R004201，事实描述准确，规则引用正确，语义上与期望异常DUP-001一致。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### ground_truth_lookup (异常查记录集合)

表现: LLM内容通过 4/5, 旧规则通过 4/5, 格式失败 0, 超时 0。
代表样例: `L1-011` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 异常DUP-002涉及哪些报销记录?

工具轨迹摘录 `runs/gate4_standard_opencode_v4pro_v1/opencode/L1-011/tool_calls.jsonl:1`:

````text
{"arguments": {"min_usage_count": 2}, "error": null, "ok": true, "result_preview": {"preview": "{\"has_next\": false, \"invoices\": [{\"amount\": 423.79, \"expense_type\": \"office_supplies\", \"invoice_date\": \"2025-08-19\", \"invoice_id\": \"INV000002\", \"invoice_no\": \"FP202500000002\", \"record_ids\": [\"R000002\", \"R004201\"], \"usage_count\": 2, \"vendor_name\": \"XX供应商7753\"}, {\"amount\": 88.83, \"expense_type\": \"local_transport\", \"invoice_date\": \"2025-06-07\", \"invoice_id\": \"INV000005\", \"invoice_no\": \"FP202500000005\", \"record_ids\": [\"R000005\", \"R004202\"], \"usage_count\": 2, \"vendor_name\": \"XX供应商5450\"}, {\"amount\": 669.5, \"expense_type\": \"travel_lodging\", \"invoice_date\": \"2025-01-05\", \"invoice_id\": \"INV000020\", \"invoice_no\": \"FP202500000020\", \"record_ids\": [\"R000020\", \"R004203\"], \"usage_count\": 2, \"vendor_name\": \"XX供应商2706\"}, {\"amount\": 165.58, \"expense_type\": \"communication\", \"invoice_date\": \"2025-03-09\", \"invoice_id\": \"INV000028\", \"invoice_no\": \"FP202500000028\", \"record_ids\": [\"R000028\", \"R004204\"], \"usage_count\": 2, \"vendor_name\": \"XX供应商1999\"}, {\"amount\": 84.72, \"expense_type\": \"
...[truncated 365 chars]
````

最终轨迹摘录 `runs/gate4_standard_opencode_v4pro_v1/opencode/L1-011/trajectory.json:320`:

````text
"type": "text",
````

候选答案摘录:

````text
{"anomaly_ids": ["DUP-002"], "record_ids": ["R000005", "R004202"], "answer": "异常DUP-002属于重复发票(重复报销)类异常,涉及发票号FP202500000005(供应商XX供应商5450,开票日期2025-06-07,金额88.83元,费用类型local_transport)。该同一张发票被两条报销记录同时使用:原始记录R000005(报销单BX2025000005,员工刘冬梅E0022,信息技术部D007,费用日期2025-06-07)与注入的重复样本记录R004202(报销单BX2025X004202,报销事由标注为重复发票注入样本,费用日期2025-03-10),两条记录金额均为88.83元且状态均为approved。依据费用报销管理办法第十条,同一发票最多报销1次,发现同一发票在不同报销单中重复出现应认定为重复报销风险,故这两条记录构成DUP-002重复报销异常。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "Candidate correctly identified anomaly DUP-002 and expected records R000005 and R004202.",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### policy_data_comparison (制度+业务交叉核查)

表现: LLM内容通过 19/25, 旧规则通过 25/25, 格式失败 0, 超时 0。
代表样例: `L2-001` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 结合制度和业务数据,核查以R000002为线索的重复报销异常,返回异常ID和记录ID集合。

工具轨迹摘录 `runs/gate4_standard_opencode_v4pro_v1/opencode/L2-001/tool_calls.jsonl:1`:

````text
{"arguments": {"record_id": "R000002"}, "error": null, "ok": true, "result_preview": {"approvals": [{"approval_id": "A000002", "approval_status": "approved", "approved_at": "2025-09-09", "approver_employee_id": "E0008", "approver_role": "部门经理", "tier_id": "AR-01"}], "record": {"amount": 423.79, "annual_budget": 381600.0, "budget_year": 2025, "city_tier": null, "days": null, "department_id": "D008", "department_name": "合规风控部", "employee_id": "E0050", "employee_level": "X1", "employee_name": "姚瑜", "expense_date": "2025-08-19", "expense_type": "office_supplies", "invoice_amount": 423.79, "invoice_date": "2025-08-19", "invoice_id": "INV000002", "invoice_no": "FP202500000002", "nights": null, "participants": null, "position_role": "员工", "reason": "清源项目资料装订用品费", "record_id": "R000002", "record_no": "BX2025000002", "reimburse_date": "2025-09-09", "special_approval": 0, "status": "approved", "vendor_name": "XX供应商7753"}}, "server": "expense_query_mcp", "tool": "get_expense_detail", "ts": 1783580434.7544243}
````

最终轨迹摘录 `runs/gate4_standard_opencode_v4pro_v1/opencode/L2-001/trajectory.json:346`:

````text
"type": "text",
````

候选答案摘录:

````text
{"anomaly_ids": ["INV000002"], "record_ids": ["R000002", "R004201"], "answer": "以R000002为线索核查发现重复报销异常。R000002使用发票号FP202500000002(发票ID INV000002,供应商XX供应商7753,金额423.79元,费用类型办公用品),经调用发票使用查询,该发票被2条报销记录使用:R000002(员工E0050姚瑜,合规风控部D008,费用日期2025-08-19,报销日期2025-09-09)与R004201(同为E0050姚瑜、同部门D008,费用日期2025-02-10,报销日期2025-02-18),两笔金额均为423.79元且完全一致,R004201的事由明确标注为重复发票注入样本。根据费用报销管理办法第十条,同一发票最多报销1次,发现同一发票在不同报销单中重复出现的应认定为重复报销风险。两笔记录均已审批通过(状态approved),违反该禁止性规定,构成同一发票被重复报销的异常。因此异常关联发票为INV000002,涉及记录为R000002与R004201。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选正确识别了重复报销异常，虽异常ID为INV000002而非标准DUP-001，但给出了正确的规则和记录集合，语义命中。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### full_year_rule_audit (全年专项扫描)

表现: LLM内容通过 3/5, 旧规则通过 3/5, 格式失败 0, 超时 0。
代表样例: `L3-001` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 请对全年数据做重复报销专项扫描,返回全部异常ID和记录ID集合。

工具轨迹摘录 `runs/gate4_standard_opencode_v4pro_v1/opencode/L3-001/tool_calls.jsonl:1`:

````text
{"arguments": {"min_usage_count": 2, "page": 1, "page_size": 500}, "error": null, "ok": true, "result_preview": {"preview": "{\"has_next\": false, \"invoices\": [{\"amount\": 423.79, \"expense_type\": \"office_supplies\", \"invoice_date\": \"2025-08-19\", \"invoice_id\": \"INV000002\", \"invoice_no\": \"FP202500000002\", \"record_ids\": [\"R000002\", \"R004201\"], \"usage_count\": 2, \"vendor_name\": \"XX供应商7753\"}, {\"amount\": 88.83, \"expense_type\": \"local_transport\", \"invoice_date\": \"2025-06-07\", \"invoice_id\": \"INV000005\", \"invoice_no\": \"FP202500000005\", \"record_ids\": [\"R000005\", \"R004202\"], \"usage_count\": 2, \"vendor_name\": \"XX供应商5450\"}, {\"amount\": 669.5, \"expense_type\": \"travel_lodging\", \"invoice_date\": \"2025-01-05\", \"invoice_id\": \"INV000020\", \"invoice_no\": \"FP202500000020\", \"record_ids\": [\"R000020\", \"R004203\"], \"usage_count\": 2, \"vendor_name\": \"XX供应商2706\"}, {\"amount\": 165.58, \"expense_type\": \"communication\", \"invoice_date\": \"2025-03-09\", \"invoice_id\": \"INV000028\", \"invoice_no\": \"FP202500000028\", \"record_ids\": [\"R000028\", \"R004204\"], \"usage_count\": 2, \"vendor_name\": \"XX供应商1999\"}, {\"amount\"
...[truncated 394 chars]
````

最终轨迹摘录 `runs/gate4_standard_opencode_v4pro_v1/opencode/L3-001/trajectory.json:543`:

````text
"type": "text",
````

候选答案摘录:

````text
{"anomaly_ids": ["R004201", "R004202", "R004203", "R004204", "R004205", "R004206"], "record_ids": ["R000002", "R004201", "R000005", "R004202", "R000020", "R004203", "R000028", "R004204", "R000037", "R004205", "R000055", "R004206"], "answer": "全年共发现6张发票被重复报销，涉及12条报销记录。根据《XX证券费用报销管理办法(2025修订版)》第十条规定，同一发票最多报销1次，发现同一发票在不同报销单中重复出现的应认定为重复报销风险。具体如下：发票FP202500000002（供应商XX供应商7753，金额423.79元）被员工姚瑜(E0050)分别在R000002(2025-08-19)和R004201(2025-02-10)重复报销；发票FP202500000005（供应商XX供应商5450，金额88.83元）被员工刘冬梅(E0022)分别在R000005(2025-06-07)和R004202(2025-03-10)重复报销；发票FP202500000020（供应商XX供应商2706，金额669.50元）被员工杜丹(E0028)分别在R000020(2025-01-05)和R004203(2025-04-10)重复报销；发票FP202500000028（供应商XX供应商1999，金额165.58元）被员工张林(E0036)分别在R000028(2025-03-09)和R004204(2025-05-10)重复报销；发票FP202500000037（供应商XX供应商7354，金额84.72元）被员工唐静(E0027)分别在R000037(2025-03-30)和R004205(2025-06-10)重复报销；发票FP202500000055（供应商XX供应商4962，金额999.76元）被员工陈洋(E0020)分别在R000055(2025-04-03)和R004206(2025-07-10)重复报销。其中R004201至R004206为系统注入的重复发票异常样本，均已被审批通过，存在重复报销风险。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选正确识别了全部6个重复报销异常，record_ids完全匹配预期，回答描述了正确的业务规则和记录对，虽anomaly_ids字段误用记录ID，但语义命中标准异常集合。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### version_trap (版本陷阱)

表现: LLM内容通过 0/1, 旧规则通过 0/1, 格式失败 0, 超时 0。
代表样例: `L3-006` / `precise` / `内容未通过` / `llm_score=0.0` / `rule_score=0.0` / `layer=fact_miss`。
题面: 请判断费用报销审批线应采用2022版还是2025修订版,并指出部门总经理审批线。

工具轨迹摘录 `runs/gate4_standard_opencode_v4pro_v1/opencode/L3-006/tool_calls.jsonl:1`:

````text
{"arguments": {}, "error": null, "ok": true, "result_preview": {"preview": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_h
...[truncated 334 chars]
````

最终轨迹摘录 `runs/gate4_standard_opencode_v4pro_v1/opencode/L3-006/trajectory.json:233`:

````text
"type": "text",
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "费用报销审批线应采用2025修订版。2022版已被2025修订版第十四条明确废止，且2022版自身第一条和第四条声明该版仅作制度沿革留档、审批金额已被替代，不得作为现行审批依据。部门总经理审批线按《XX证券授权管理办法》附件二执行：单笔报销金额大于等于10000元且小于50000元时，必要审批角色为部门总经理。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十四条"}, {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第一条"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第四条"}, {"doc_id": "03_authorization_management.md", "clause_no": "附件二 AR-03"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 0.0,
  "rule_score": 0.0,
  "failure_layer": "fact_miss",
  "format_failure": false,
  "judge_reason": "候选回答未提及2022旧值8000元已废止的事实，只说明了废止但未给出具体金额，缺失关键事实。",
  "judge_missing": [
    "2022旧值8000元已废止"
  ],
  "judge_extra": []
}
````

原因分析: 输出可解析,但 LLM judge 认为关键事实、记录集合或异常判断没有语义命中。

#### two_hop_retrieval (双跳检索)

表现: LLM内容通过 1/1, 旧规则通过 1/1, 格式失败 0, 超时 0。
代表样例: `L3-007` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 报销办法没有直接列审批金额时,请通过交叉引用找到单笔费用审批档位。

工具轨迹摘录 `runs/gate4_standard_opencode_v4pro_v1/opencode/L3-007/tool_calls.jsonl:1`:

````text
{"arguments": {"query": "单笔费用审批金额档位 审批权限", "top_k": 6}, "error": null, "ok": true, "result_preview": {"preview": "{\"query\": \"单笔费用审批金额档位 审批权限\", \"results\": [{\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"score\": 19.6293, \"snippets\": [\"第四条 本办法的审批金额已被后续制度替代,不得作为现行审批依据。\", \"第二条 旧版制度曾规定,单笔报销金额达到8000元的,应提交部门总经理审批。\", \"第三条 旧版制度曾规定,单笔报销金额达到30000元的,应提交分管副总审批。\"], \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"score\": 16.3698, \"snippets\": [\"第二条 本办法附件二适用于费用报销系统自动派生审批角色,相关金额为现行有效审批线。\", \"| 档位 | 单笔金额区间 | 必要审批角色 |\", \"## 附件二 费用报销审批权限表\"], \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"01_expense_reimbursement_2025.md\", \"score\": 15.7223, \"snippets\": [\"第十一条 不得将同一事项或同类事项拆分为多笔报销以规避审批权限。同一员工、同一费用类型在7天内出现2笔及以上报销,且合计金额达到《授权管理办法》附件二较高审批线的,应重点核查拆分规\", \"第五条 单笔费用报销的审批权限,不在本办法正文列示具体金额,统一按《XX证券授权管理办法》附件二执行。费用系统应按附件二自动派生审批角色。\", \"第三条 费用报销实行经办人真实性承诺、部门负责人业务审核、财务复核和授权审批相结合的管理原则。\"], \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"08_budget_management.md\", \"score\": 5.7988, \"snippets\": [\"第三条 部门费用累计使用达到年度预算额度的1.0倍后,原则上不得继续报销。\", \"第四条 因监管要求、客户服务或经营连续性确需超预算支出的,应履行专项审批。\", \"第五条 本办法与费用报销制度共同构成费用控制依据。\"], \"title\": \"XX证券预算管理办
...[truncated 307 chars]
````

最终轨迹摘录 `runs/gate4_standard_opencode_v4pro_v1/opencode/L3-007/trajectory.json:236`:

````text
"type": "text",
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "报销办法正文确实不直接列示审批金额。根据费用报销管理办法(2025修订版)第五条,单笔费用报销的审批权限不在正文列示具体金额,统一按授权管理办法附件二执行,费用系统按附件二自动派生审批角色;第十一条在判断拆分报销时也引用附件二的较高审批线。据此交叉引用到授权管理办法附件二费用报销审批权限表,现行有效的单笔费用审批档位为:AR-01 大于等于0元且小于3000元,由部门经理审批;AR-02 大于等于3000元且小于10000元,由部门经理审批并经财务复核;AR-03 大于等于10000元且小于50000元,由部门总经理审批;AR-04 大于等于50000元且小于200000元,由分管副总审批;AR-05 大于等于200000元,由总经理办公会审批。需注意2022版报销办法第八条8000元、第三条30000元等旧档位已被替代,不得作为现行审批依据。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"}, {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十一条"}, {"doc_id": "03_authorization_management.md", "clause_no": "第二条"}, {"doc_id": "03_authorization_management.md", "clause_no": "附件二"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第四条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "回答准确包含了部门总经理审批线10000元，并指出金额出自授权管理办法附件二，关键事实完整。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### near_clause_disambiguation (近似条款辨析)

表现: LLM内容通过 1/1, 旧规则通过 0/1, 格式失败 0, 超时 0。
代表样例: `L3-008` / `precise` / `通过` / `llm_score=1.0` / `rule_score=0.0` / `layer=ok`。
题面: 比较差旅住宿和培训住宿标准,说明为什么不能混用。

工具轨迹摘录 `runs/gate4_standard_opencode_v4pro_v1/opencode/L3-008/tool_calls.jsonl:1`:

````text
{"arguments": {"query": "差旅住宿标准 培训住宿标准", "top_k": 6}, "error": null, "ok": true, "result_preview": {"query": "差旅住宿标准 培训住宿标准", "results": [{"doc_id": "05_training_expense.md", "score": 30.4776, "snippets": ["第六条 培训住宿标准仅适用于培训期间住宿,不得与差旅住宿标准混用。", "第五条 培训期间住宿标准如下,单位为元/人/晚。", "| 城市档位 | 培训住宿标准 |"], "title": "XX证券培训费管理办法"}, {"doc_id": "04_travel_expense.md", "score": 29.3248, "snippets": ["第七条 培训期间住宿不适用本办法住宿表,应按《XX证券培训费管理办法》执行。", "第四条 差旅住宿费标准如下,单位为元/人/晚。", "第三条 住宿标准按员工职级和城市档位确定。员工职级包括员工级、经理级、部门负责人级和高管级;城市档位包括一类城市、二类城市和三类城市。"], "title": "XX证券差旅费管理办法"}, {"doc_id": "01_expense_reimbursement_2025.md", "score": 6.4677, "snippets": ["第二条 本办法适用于XX证券各部门、分支机构及全体员工发生的差旅、培训、招待、办公、通讯等费用报销事项。", "第六条 财务部门对票据合法性、费用归属、预算占用和制度标准进行复核。复核不替代业务部门对事项真实性的确认。", "第十二条 无专项审批时,报销金额不得超过对应制度标准的1.0倍。"], "title": "XX证券费用报销管理办法(2025修订版)"}, {"doc_id": "06_business_entertainment.md", "score": 0.8989, "snippets": ["## 第二章 标准管理"], "title": "XX证券业务招待费管理办法"}, {"doc_id": "12_archive_management.md", "score": 0.7415, "snippets": ["第八条 本办法为管理类制度,不作为费用报销标准依据。"], "title": "XX证券档案管理办法"}, {"doc_id": "13_procurement_management.md", "score": 0.7403, "snippets": ["第八条 本办法为管理类制度,不作为费用报销标准依据。"], "title": "XX证券采购管理办法"}], "top_k": 6}, "serve
...[truncated 74 chars]
````

最终轨迹摘录 `runs/gate4_standard_opencode_v4pro_v1/opencode/L3-008/trajectory.json:294`:

````text
"type": "text",
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "差旅住宿标准与培训住宿标准是两套独立的报销依据,适用场景和确定维度都不同。差旅住宿标准(差旅费管理办法第三条、第四条)按员工职级和城市档位双维度确定:员工级一/二/三类城市为450/380/300元,经理级为650/550/450元,部门负责人级为850/700/600元,高管级为1100/900/750元(元每人每晚)。培训住宿标准(培训费管理办法第五条)仅按城市档位单一维度确定,不区分职级:一类城市500元、二类城市420元、三类城市350元(元每人每晚)。两者不能混用的原因:一是适用情形互斥,差旅费管理办法第七条明确培训期间住宿不适用差旅住宿表,应按培训费管理办法执行,而培训费管理办法第六条同样规定培训住宿标准仅适用于培训期间住宿,不得与差旅住宿标准混用;二是确定逻辑不同,差旅标准与职级挂钩、培训标准仅与城市挂钩,若混用会绕过职级封顶控制,例如低职级人员在培训期间套用差旅低限或高职级人员套用培训标准,都会导致费用归属错乱、标准失效和预算占用不实。因此必须按费用实际性质分别套用对应标准,培训期间一律用培训住宿标准,公务出差一律用差旅住宿标准,不得交叉引用。", "citations": [{"doc_id": "04_travel_expense.md", "clause_no": "第三条"}, {"doc_id": "04_travel_expense.md", "clause_no": "第四条"}, {"doc_id": "04_travel_expense.md", "clause_no": "第七条"}, {"doc_id": "05_training_expense.md", "clause_no": "第五条"}, {"doc_id": "05_training_expense.md", "clause_no": "第六条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 0.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "回答明确说明差旅住宿适用差旅费管理办法、培训住宿适用培训费管理办法，并指出两组标准数值不同、不得混用，完整覆盖三个预期事实。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### audit_report (报告式任务)

表现: LLM内容通过 1/2, 旧规则通过 0/2, 格式失败 0, 超时 0。
代表样例: `L3-010` / `precise` / `通过` / `llm_score=1.0` / `rule_score=0.0` / `layer=ok`。
题面: 请专门写一段版本陷阱审计说明,解释旧版审批线可能导致的误判。

工具轨迹摘录 `runs/gate4_standard_opencode_v4pro_v1/opencode/L3-010/tool_calls.jsonl:1`:

````text
{"arguments": {}, "error": null, "ok": true, "result_preview": {"preview": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_h
...[truncated 334 chars]
````

最终轨迹摘录 `runs/gate4_standard_opencode_v4pro_v1/opencode/L3-010/trajectory.json:261`:

````text
"type": "text",
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "版本陷阱审计说明——旧版审批线可能导致的误判\n\n一、背景\nXX证券费用报销管理办法存在两个版本：2022版（已废止）和2025修订版（现行有效）。2025版明确规定审批权限不再在制度正文中列示具体金额，而是统一按《XX证券授权管理办法》附件二执行。若审计人员未注意版本更替，沿用2022版审批线进行核查，将导致系统性误判。\n\n二、两版审批线对比\n2022版（已废止）：\n- 8000元触发部门总经理审批\n- 30000元触发分管副总审批\n- 未设置财务复核档和总经理办公会档\n\n2025版现行有效审批线（授权管理办法附件二）：\n- AR-01：[0, 3000) → 部门经理\n- AR-02：[3000, 10000) → 部门经理 + 财务复核\n- AR-03：[10000, 50000) → 部门总经理\n- AR-04：[50000, 200000) → 分管副总\n- AR-05：[200000, ∞) → 总经理办公会\n\n三、误判场景分析\n场景一：金额区间[8000, 10000)的报销。旧版要求部门总经理审批，现行版仅要求部门经理加财务复核（AR-02）。若以旧版为标准，会误判该区间报销缺少部门总经理审批，而实际上部门总经理并非必要审批角色。\n\n场景二：金额区间[30000, 50000)的报销。旧版要求分管副总审批，现行版仅要求部门总经理审批（AR-03）。若以旧版为标准，会误判该区间报销缺少分管副总审批，而实际上分管副总并非必要审批角色。\n\n场景三：金额区间[50000, 200000)的报销。虽然两版均要求分管副总审批，但触发阈值不同（旧版30000元、现行版50000元），若混淆版本可能无法准确判断审批完整性。\n\n场景四：金额≥200000元的报销。2022版未设置总经理办公会审批档，若以旧版标准审查大额报销，可能遗漏该必要审批环节。\n\n四、审计建议\n（1）所有审批完整性核查必须以现行有效的2025修订版及授权管理办法附件二为准，不得引用2022版审批线。\n（2）审计系统中应屏蔽或明确标注2022版制度为废止留档状态，防止误引用。\n（3）对系统自动派生的审批角色进行校验时，应使用附件二的五档审批线，并确认财务复核（AR-02档）和总经理办公会（AR-05档）已正确配置。", "citations": [{"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第二条"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no"
...[truncated 358 chars]
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 0.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选回答完整覆盖全部评分标准，准确指出现行和旧版审批线，并说明旧版废止及授权依据。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### clean_but_suspicious (陷阱题)

表现: LLM内容通过 2/5, 旧规则通过 5/5, 格式失败 0, 超时 0。
代表样例: `TRAP-001` / `precise` / `内容未通过` / `llm_score=0.0` / `rule_score=1.0` / `layer=record_id_miss`。
题面: 请核查TRAP-001涉及的记录是否构成异常,正确时应说明无异常。

工具轨迹摘录 `runs/gate4_standard_opencode_v4pro_v1/opencode/TRAP-001/tool_calls.jsonl:1`:

````text
{"arguments": {"record_id": "TRAP-001"}, "error": null, "ok": true, "result_preview": {"approvals": [], "record": null}, "server": "expense_query_mcp", "tool": "get_expense_detail", "ts": 1783584081.0717318}
````

最终轨迹摘录 `runs/gate4_standard_opencode_v4pro_v1/opencode/TRAP-001/trajectory.json:169`:

````text
"type": "text",
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "针对TRAP-001进行核查:该标识并非系统中的有效报销记录编号,通过明细查询接口检索TRAP-001未返回任何关联的报销记录或审批链数据。经核对现有报销数据格式,正式记录均以R开头编号(如R000339),不存在以TRAP为前缀的业务记录。因此TRAP-001所指向的对象在费用数据中无实际关联记录,不存在重复报销、超预算、缺失审批或超时报销等异常情形。结论:无异常,该项为干扰性核查项,未发现任何违规或可疑事实。", "citations": []}
````

LLM judge 摘录:

````json
{
  "llm_score": 0.0,
  "rule_score": 1.0,
  "failure_layer": "record_id_miss",
  "format_failure": false,
  "judge_reason": "候选回答未识别出应核查的记录R004233，错误声称TRAP-001无关联记录，未提供期望的无异常解释。",
  "judge_missing": [
    "期望记录R004233",
    "低于审批线且符合住宿上限的理由"
  ],
  "judge_extra": [
    "错误声称TRAP-001无关联报销记录"
  ]
}
````

原因分析: 输出可解析,但 LLM judge 认为关键事实、记录集合或异常判断没有语义命中。


## Claude Code

### 题型表现

| 题型 | 总数 | LLM内容通过 | 旧规则通过 | 格式失败 | LLM未通过 | 超时 | 判断 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| policy_qa | 4 | 4 | 4 | 0 | 0 | 0 | 仍是最稳定题型 |
| version_check | 1 | 1 | 0 | 0 | 0 | 0 | 中等表现 |
| single_anomaly_lookup | 5 | 5 | 5 | 0 | 0 | 0 | LLM judge 认可部分语义命中,但集合归并仍不稳 |
| ground_truth_lookup | 5 | 3 | 5 | 0 | 2 | 0 | record_id 集合覆盖是主要瓶颈 |
| policy_data_comparison | 25 | 11 | 25 | 0 | 14 | 0 | LLM judge 认可部分语义命中,但集合归并仍不稳 |
| full_year_rule_audit | 5 | 2 | 3 | 0 | 3 | 0 | LLM judge 认可部分语义命中,但集合归并仍不稳 |
| version_trap | 1 | 1 | 0 | 0 | 0 | 0 | 中等表现 |
| two_hop_retrieval | 1 | 1 | 1 | 0 | 0 | 0 | 中等表现 |
| near_clause_disambiguation | 1 | 1 | 0 | 0 | 0 | 0 | 中等表现 |
| audit_report | 2 | 1 | 0 | 0 | 1 | 0 | 报告可读性不等于 rubric 完整满足 |
| clean_but_suspicious | 5 | 2 | 3 | 0 | 3 | 0 | 陷阱识别有一定能力 |

### 各题型典型轨迹

下面每个题型放一个代表样例。样例选择规则: 通过率较高的题型选通过样例; 失败为主的题型选该题型最常见失败层。

#### policy_qa (纯制度问答)

表现: LLM内容通过 4/4, 旧规则通过 4/4, 格式失败 0, 超时 0。
代表样例: `L1-001` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 现行制度下,单笔费用报销达到多少金额需要部门总经理审批?

工具轨迹摘录 `runs/gate4_standard_claude_v4pro_v1/claude-code/L1-001/tool_calls.jsonl:1`:

````text
{"arguments": {"query": "部门总经理审批 金额 单笔费用报销", "top_k": 5}, "error": null, "ok": true, "result_preview": {"preview": "{\"query\": \"部门总经理审批 金额 单笔费用报销\", \"results\": [{\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"score\": 14.3153, \"snippets\": [\"第二条 旧版制度曾规定,单笔报销金额达到8000元的,应提交部门总经理审批。\", \"第一条 本办法为XX证券旧版费用报销制度文本,仅作为制度沿革留档。现行制度应以《XX证券费用报销管理办法(2025修订版)》为准。\", \"第三条 旧版制度曾规定,单笔报销金额达到30000元的,应提交分管副总审批。\"], \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"01_expense_reimbursement_2025.md\", \"score\": 11.2818, \"snippets\": [\"第十一条 不得将同一事项或同类事项拆分为多笔报销以规避审批权限。同一员工、同一费用类型在7天内出现2笔及以上报销,且合计金额达到《授权管理办法》附件二较高审批线的,应重点核查拆分规\", \"第五条 单笔费用报销的审批权限,不在本办法正文列示具体金额,统一按《XX证券授权管理办法》附件二执行。费用系统应按附件二自动派生审批角色。\", \"第三条 费用报销实行经办人真实性承诺、部门负责人业务审核、财务复核和授权审批相结合的管理原则。\"], \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"score\": 11.2058, \"snippets\": [\"第二条 本办法附件二适用于费用报销系统自动派生审批角色,相关金额为现行有效审批线。\", \"## 附件二 费用报销审批权限表\", \"| 档位 | 单笔金额区间 | 必要审批角色 |\"], \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"score\": 4.9597, \"snippets\": [\"第三条 部门费用累计使用达到年度预算额度的1.0倍后,原则上不得继续报销。\", \"第五条 本办法与费用报销制度共同构成费用控制依据。\", \"第二条 各部门应在年度预算额度内发生费用。\"], \
...[truncated 310 chars]
````

最终轨迹摘录 `runs/gate4_standard_claude_v4pro_v1/claude-code/L1-001/trajectory.json:8`:

````text
"result": "```json\n{\n  \"anomaly_ids\": [],\n  \"record_ids\": [],\n  \"answer\": \"根据现行《XX证券授权管理办法》附件二（费用报销审批权限表）,单笔费用报销金额达到10,000元（含）且不足50,000元时,需要部门总经理审批。具体对应档位AR-03：单笔金额区间大于等于10000元且小于50000元,必要审批角色为部门总经理。\",\n  \"citations\": [\n    {\n      \"doc_id\": \"03_authorization_management.md\",\n      \"clause_no\": \"附件二\"\n    },\n    {\n      \"doc_id\": \"01_expense_reimbursement_2025.md\",\n      \"clause_no\": \"第五条\"\n    }\n  ]\n}\n```",
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "根据现行《XX证券授权管理办法》附件二（费用报销审批权限表）,单笔费用报销金额达到10,000元（含）且不足50,000元时,需要部门总经理审批。具体对应档位AR-03：单笔金额区间大于等于10000元且小于50000元,必要审批角色为部门总经理。", "citations": [{"doc_id": "03_authorization_management.md", "clause_no": "附件二"}, {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "回答正确反映了部门总经理审批线为10000元",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### version_check (版本检查)

表现: LLM内容通过 1/1, 旧规则通过 0/1, 格式失败 0, 超时 0。
代表样例: `L1-003` / `precise` / `通过` / `llm_score=1.0` / `rule_score=0.0` / `layer=ok`。
题面: 2022版中部门总经理审批线是多少,它现在是否有效?

工具轨迹摘录 `runs/gate4_standard_claude_v4pro_v1/claude-code/L1-003/tool_calls.jsonl:1`:

````text
{"arguments": {}, "error": null, "ok": true, "result_preview": {"preview": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_h
...[truncated 334 chars]
````

最终轨迹摘录 `runs/gate4_standard_claude_v4pro_v1/claude-code/L1-003/trajectory.json:8`:

````text
"result": "```json\n{\n  \"anomaly_ids\": [],\n  \"record_ids\": [],\n  \"answer\": \"2022版制度(02_expense_reimbursement_2022_deprecated.md 第二条)规定单笔报销金额达到8000元的应提交部门总经理审批。该规定现在已失效:根据同文件第四条,2022版的审批金额已被后续制度替代,不得作为现行审批依据;现行有效的审批线以授权管理办法附件二为准,其中部门总经理对应的是大于等于10000元且小于50000元(AR-03)。因此8000元的部门总经理审批线现已无效。\",\n  \"citations\": [\n    {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"clause_no\": \"第二条\"},\n    {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"clause_no\": \"第四条\"},\n    {\"doc_id\": \"03_authorization_management.md\", \"clause_no\": \"第二条\"},\n    {\"doc_id\": \"03_authorization_management.md\", \"clause_no\": \"AR-03\"}\n  ]\n}\n```",
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "2022版制度(02_expense_reimbursement_2022_deprecated.md 第二条)规定单笔报销金额达到8000元的应提交部门总经理审批。该规定现在已失效:根据同文件第四条,2022版的审批金额已被后续制度替代,不得作为现行审批依据;现行有效的审批线以授权管理办法附件二为准,其中部门总经理对应的是大于等于10000元且小于50000元(AR-03)。因此8000元的部门总经理审批线现已无效。", "citations": [{"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第二条"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第四条"}, {"doc_id": "03_authorization_management.md", "clause_no": "第二条"}, {"doc_id": "03_authorization_management.md", "clause_no": "AR-03"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 0.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选回答准确给出了2022版旧审批线8000元并明确指出已失效，完全覆盖期望事实，引用恰当。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### single_anomaly_lookup (单条异常判断)

表现: LLM内容通过 5/5, 旧规则通过 5/5, 格式失败 0, 超时 0。
代表样例: `L1-006` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 请判断报销记录R000002是否命中重复报销,如命中请返回异常ID。

工具轨迹摘录 `runs/gate4_standard_claude_v4pro_v1/claude-code/L1-006/tool_calls.jsonl:1`:

````text
{"arguments": {"record_id": "R000002"}, "error": null, "ok": true, "result_preview": {"approvals": [{"approval_id": "A000002", "approval_status": "approved", "approved_at": "2025-09-09", "approver_employee_id": "E0008", "approver_role": "部门经理", "tier_id": "AR-01"}], "record": {"amount": 423.79, "annual_budget": 381600.0, "budget_year": 2025, "city_tier": null, "days": null, "department_id": "D008", "department_name": "合规风控部", "employee_id": "E0050", "employee_level": "X1", "employee_name": "姚瑜", "expense_date": "2025-08-19", "expense_type": "office_supplies", "invoice_amount": 423.79, "invoice_date": "2025-08-19", "invoice_id": "INV000002", "invoice_no": "FP202500000002", "nights": null, "participants": null, "position_role": "员工", "reason": "清源项目资料装订用品费", "record_id": "R000002", "record_no": "BX2025000002", "reimburse_date": "2025-09-09", "special_approval": 0, "status": "approved", "vendor_name": "XX供应商7753"}}, "server": "expense_query_mcp", "tool": "get_expense_detail", "ts": 1783579360.7493}
````

最终轨迹摘录 `runs/gate4_standard_claude_v4pro_v1/claude-code/L1-006/trajectory.json:8`:

````text
"result": "```json\n{\n  \"anomaly_ids\": [\"DUP-INV000002\"],\n  \"record_ids\": [\"R000002\", \"R004201\"],\n  \"answer\": \"报销记录R000002命中重复报销。发票FP202500000002（INV000002，金额423.79元）在R000002和R004201两条报销记录中被重复使用，同一员工姚瑜（E0050）分别于2025-02-10和2025-08-19以同一发票报销了两次相同金额的办公用品费用，违反费用报销管理办法第十条规定。\",\n  \"citations\": [\n    {\n      \"doc_id\": \"01_expense_reimbursement_2025.md\",\n      \"clause_no\": \"第十条\"\n    }\n  ]\n}\n```",
````

候选答案摘录:

````text
{"anomaly_ids": ["DUP-INV000002"], "record_ids": ["R000002", "R004201"], "answer": "报销记录R000002命中重复报销。发票FP202500000002（INV000002，金额423.79元）在R000002和R004201两条报销记录中被重复使用，同一员工姚瑜（E0050）分别于2025-02-10和2025-08-19以同一发票报销了两次相同金额的办公用品费用，违反费用报销管理办法第十条规定。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选正确识别了重复报销异常，记录ID完全匹配，描述事实与标准异常一致，尽管异常ID非标准但语义命中。",
  "judge_missing": [],
  "judge_extra": [
    "anomaly_id 误写为 DUP-INV000002，标准为 DUP-001"
  ]
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### ground_truth_lookup (异常查记录集合)

表现: LLM内容通过 3/5, 旧规则通过 5/5, 格式失败 0, 超时 0。
代表样例: `L1-011` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 异常DUP-002涉及哪些报销记录?

工具轨迹摘录 `runs/gate4_standard_claude_v4pro_v1/claude-code/L1-011/tool_calls.jsonl:1`:

````text
{"arguments": {"query": "DUP-002 重复发票 异常", "top_k": 5}, "error": null, "ok": true, "result_preview": {"query": "DUP-002 重复发票 异常", "results": [{"doc_id": "01_expense_reimbursement_2025.md", "score": 9.8194, "snippets": ["第十条 同一发票最多报销1次。发现同一发票在不同报销单中重复出现的,应认定为重复报销风险。", "第六条 财务部门对票据合法性、费用归属、预算占用和制度标准进行复核。复核不替代业务部门对事项真实性的确认。", "发文字号: XX证财规〔2025〕甲号"], "title": "XX证券费用报销管理办法(2025修订版)"}, {"doc_id": "11_attendance_management.md", "score": 4.7851, "snippets": ["第一条 为规范XX证券考勤记录、请假申请、外勤登记和异常处理相关管理事项,制定本办法。", "发文字号: XX证综规〔2025〕备号", "第七条 对发现的问题,相关部门应及时整改并保留整改记录。"], "title": "XX证券考勤与休假管理办法"}, {"doc_id": "07_office_communication.md", "score": 2.6653, "snippets": ["发文字号: XX证办规〔2025〕庚号", "第一条 为规范XX证券日常办公费用和通讯费用报销,制定本办法。"], "title": "XX证券办公与通讯费用管理办法"}, {"doc_id": "20_customer_complaint.md", "score": 1.817, "snippets": ["发文字号: XX证综规〔2025〕备号", "第一条 为规范XX证券投诉受理、事实核查、回复留痕和改进闭环相关管理事项,制定本办法。", "第七条 对发现的问题,相关部门应及时整改并保留整改记录。"], "title": "XX证券客户投诉处理管理办法"}, {"doc_id": "03_authorization_management.md", "score": 1.7727, "snippets": ["发文字号: XX证综规〔2025〕丙号", "第四条 授权事项发生调整的,以最新修订版附件为准。", "| AR-02 | 大于等于3000元且小于10000元 | 部门经理,并经财务复核 |"], "title": "XX证券授权管理办法"}], "top_k": 5}, "server": "policy_query_mcp", "tool": "sea
...[truncated 38 chars]
````

最终轨迹摘录 `runs/gate4_standard_claude_v4pro_v1/claude-code/L1-011/trajectory.json:8`:

````text
"result": "```json\n{\n  \"anomaly_ids\": [\"DUP-002\"],\n  \"record_ids\": [\"R000005\", \"R004202\"],\n  \"answer\": \"异常DUP-002涉及发票FP202500000005（XX供应商5450，金额88.83元，费用类型为本地交通费）被重复报销的两笔记录：R000005（报销人刘冬梅，信息技术部，费用日期2025-06-07，报销金额88.83元）和R004202（报销人刘冬梅，信息技术部，费用日期2025-03-10，报销金额88.83元，事由标注为重复发票注入样本）。两笔记录均以同一张发票FP202500000005报销，违反了同一发票最多报销1次的规定，构成重复报销风险。\",\n  \"citations\": [\n    {\"doc_id\": \"01_expense_reimbursement_2025.md\", \"clause_no\": \"第十条\"}\n  ]\n}\n```",
````

候选答案摘录:

````text
{"anomaly_ids": ["DUP-002"], "record_ids": ["R000005", "R004202"], "answer": "异常DUP-002涉及发票FP202500000005（XX供应商5450，金额88.83元，费用类型为本地交通费）被重复报销的两笔记录：R000005（报销人刘冬梅，信息技术部，费用日期2025-06-07，报销金额88.83元）和R004202（报销人刘冬梅，信息技术部，费用日期2025-03-10，报销金额88.83元，事由标注为重复发票注入样本）。两笔记录均以同一张发票FP202500000005报销，违反了同一发票最多报销1次的规定，构成重复报销风险。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选正确识别了异常DUP-002及其关联的两条报销记录R000005和R004202，回答语义完整、准确。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### policy_data_comparison (制度+业务交叉核查)

表现: LLM内容通过 11/25, 旧规则通过 25/25, 格式失败 0, 超时 0。
代表样例: `L2-012` / `precise` / `内容未通过` / `llm_score=0.0` / `rule_score=1.0` / `layer=no_anomaly_false_positive`。
题面: 结合制度和业务数据,核查以R004222为线索的超标准异常,返回异常ID和记录ID集合。

工具轨迹摘录 `runs/gate4_standard_claude_v4pro_v1/claude-code/L2-012/tool_calls.jsonl:1`:

````text
{"arguments": {"record_id": "R004222"}, "error": null, "ok": true, "result_preview": {"approvals": [{"approval_id": "A004222", "approval_status": "approved", "approved_at": "2025-03-25", "approver_employee_id": "E0008", "approver_role": "部门经理", "tier_id": "AR-01"}], "record": {"amount": 330.0, "annual_budget": 381600.0, "budget_year": 2025, "city_tier": null, "days": null, "department_id": "D008", "department_name": "合规风控部", "employee_id": "E0008", "employee_level": "D1", "employee_name": "杨丹", "expense_date": "2025-03-20", "expense_type": "communication", "invoice_amount": 330.0, "invoice_date": "2025-03-20", "invoice_id": "INV004216", "invoice_no": "FP2025X0004216", "nights": null, "participants": null, "position_role": "部门经理", "reason": "超标准注入样本2", "record_id": "R004222", "record_no": "BX2025X004222", "reimburse_date": "2025-03-25", "special_approval": 0, "status": "approved", "vendor_name": "XX注入供应商R004222"}}, "server": "expense_query_mcp", "tool": "get_expense_detail", "ts": 1783580597.5172188}
````

最终轨迹摘录 `runs/gate4_standard_claude_v4pro_v1/claude-code/L2-012/trajectory.json:8`:

````text
"result": "```json\n{\n  \"anomaly_ids\": [\"R004221\", \"R004222\", \"R004223\", \"R004224\", \"R004225\", \"R004226\"],\n  \"record_ids\": [\"R004221\", \"R004222\", \"R004223\", \"R004224\", \"R004225\", \"R004226\"],\n  \"answer\": \"以R004222（通讯费330元，超300元月控标准）为线索，共发现6条超标准注入样本异常，均无专项审批（special_approval=0），违反《XX证券费用报销管理办法(2025修订版)》第十二条。具体：R004221办公用品650元超600元标准；R004222通讯费330元超300元标准；R004223培训费3700元超3500元标准；R004224业务招待费700元/2人，人均350元超300元标准；R004225差旅住宿费900元/晚（经理级一类城市）超650元标准；R004226市内交通费92元（三类城市）超80元日标准。\",\n  \"citations\": [\n    {\"doc_id\": \"01_expense_reimbursement_2025.md\", \"clause_no\": \"第十二条\"},\n    {\"doc_id\": \"07_office_communication.md\", \"clause_no\": \"第二条\"},\n    {\"doc_id\": \"07_office_communication.md\", \"clause_no\": \"第三条\"},\n    {\"doc_id\": \"05_training_expense.md\", \"clause_no\": \"第二条\"},\n    {\"doc_id\": \"06_business_entertainment.md\", \"clause_no\": \"第三条\"},\n    {\"doc_id\": \"04_travel_expense.md\", \"clause_no\": \"第四条\"},\n    {\"doc_id\": \"04_travel_expense.md\", \"clause_no\": \"第六条\"}\n  ]\n}\n```",
````

候选答案摘录:

````text
{"anomaly_ids": ["R004221", "R004222", "R004223", "R004224", "R004225", "R004226"], "record_ids": ["R004221", "R004222", "R004223", "R004224", "R004225", "R004226"], "answer": "以R004222（通讯费330元，超300元月控标准）为线索，共发现6条超标准注入样本异常，均无专项审批（special_approval=0），违反《XX证券费用报销管理办法(2025修订版)》第十二条。具体：R004221办公用品650元超600元标准；R004222通讯费330元超300元标准；R004223培训费3700元超3500元标准；R004224业务招待费700元/2人，人均350元超300元标准；R004225差旅住宿费900元/晚（经理级一类城市）超650元标准；R004226市内交通费92元（三类城市）超80元日标准。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十二条"}, {"doc_id": "07_office_communication.md", "clause_no": "第二条"}, {"doc_id": "07_office_communication.md", "clause_no": "第三条"}, {"doc_id": "05_training_expense.md", "clause_no": "第二条"}, {"doc_id": "06_business_entertainment.md", "clause_no": "第三条"}, {"doc_id": "04_travel_expense.md", "clause_no": "第四条"}, {"doc_id": "04_travel_expense.md", "clause_no": "第六条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 0.0,
  "rule_score": 1.0,
  "failure_layer": "no_anomaly_false_positive",
  "format_failure": false,
  "judge_reason": "候选回答将R004222正确识别为超标准,但错误地将R004221、R004223-R004226等无关记录也标记为超标准异常,而预期只有OVERSTD-002一个异常,多报了异常,违反了仅返回相关异常的判卷原则。",
  "judge_missing": [],
  "judge_extra": [
    "异常记录R004221、R004223、R004224、R004225、R004226被错误标记",
    "异常集合应为{OVERSTD-002},实际返回了6个记录ID"
  ]
}
````

原因分析: 输出可解析,但 LLM judge 认为关键事实、记录集合或异常判断没有语义命中。

#### full_year_rule_audit (全年专项扫描)

表现: LLM内容通过 2/5, 旧规则通过 3/5, 格式失败 0, 超时 0。
代表样例: `L3-003` / `precise` / `内容未通过` / `llm_score=0.0` / `rule_score=0.0` / `layer=record_id_miss`。
题面: 请对全年数据做超标准专项扫描,返回全部异常ID和记录ID集合。

工具轨迹摘录 `runs/gate4_standard_claude_v4pro_v1/claude-code/L3-003/tool_calls.jsonl:1`:

````text
{"arguments": {}, "error": null, "ok": true, "result_preview": {"preview": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_h
...[truncated 334 chars]
````

最终轨迹摘录 `runs/gate4_standard_claude_v4pro_v1/claude-code/L3-003/trajectory.json:8`:

````text
"result": "```json\n{\n  \"anomaly_ids\": [\n    \"ANO-001\",\n    \"ANO-002\",\n    \"ANO-003\",\n    \"ANO-004\",\n    \"ANO-005\"\n  ],\n  \"record_ids\": [\n    \"R004221\",\n    \"R004222\",\n    \"R004223\",\n    \"R004224\",\n    \"R004225\"\n  ],\n  \"answer\": \"全年超标准专项扫描共发现5项异常。R004221办公用品费650元超过每人每月600元标准；R004222通讯费330元超过每人每月300元标准；R004223培训费3700元超过每人每期3500元标准；R004224业务招待费700元/2人=350元/人超过人均300元标准；R004225差旅住宿费900元/晚,员工李丽娟职级部门负责人级(D1)在一类城市住宿标准为850元/晚,超出50元。\",\n  \"citations\": [\n    {\n      \"doc_id\": \"07_office_communication.md\",\n      \"clause_no\": \"第二条\"\n    },\n    {\n      \"doc_id\": \"07_office_communication.md\",\n      \"clause_no\": \"第三条\"\n    },\n    {\n      \"doc_id\": \"05_training_expense.md\",\n      \"clause_no\": \"第二条\"\n    },\n    {\n      \"doc_id\": \"06_business_entertainment.md\",\n      \"clause_no\": \"第三条\"\n    },\n    {\n      \"doc_id\": \"04_travel_expense.md\",\n      \"clause_no\": \"第四条\"\n    }\n  ]\n}\n```",
````

候选答案摘录:

````text
{"anomaly_ids": ["ANO-001", "ANO-002", "ANO-003", "ANO-004", "ANO-005"], "record_ids": ["R004221", "R004222", "R004223", "R004224", "R004225"], "answer": "全年超标准专项扫描共发现5项异常。R004221办公用品费650元超过每人每月600元标准；R004222通讯费330元超过每人每月300元标准；R004223培训费3700元超过每人每期3500元标准；R004224业务招待费700元/2人=350元/人超过人均300元标准；R004225差旅住宿费900元/晚,员工李丽娟职级部门负责人级(D1)在一类城市住宿标准为850元/晚,超出50元。", "citations": [{"doc_id": "07_office_communication.md", "clause_no": "第二条"}, {"doc_id": "07_office_communication.md", "clause_no": "第三条"}, {"doc_id": "05_training_expense.md", "clause_no": "第二条"}, {"doc_id": "06_business_entertainment.md", "clause_no": "第三条"}, {"doc_id": "04_travel_expense.md", "clause_no": "第四条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 0.0,
  "rule_score": 0.0,
  "failure_layer": "record_id_miss",
  "format_failure": false,
  "judge_reason": "候选回答只报告了5个异常和5条记录ID，遗漏了预期异常OVERSTD-006及其对应记录R004226（本地交通费92元超过80元标准），未能覆盖全部标准异常集合。",
  "judge_missing": [
    "OVERSTD-006",
    "R004226"
  ],
  "judge_extra": []
}
````

原因分析: 输出可解析,但 LLM judge 认为关键事实、记录集合或异常判断没有语义命中。

#### version_trap (版本陷阱)

表现: LLM内容通过 1/1, 旧规则通过 0/1, 格式失败 0, 超时 0。
代表样例: `L3-006` / `precise` / `通过` / `llm_score=1.0` / `rule_score=0.0` / `layer=ok`。
题面: 请判断费用报销审批线应采用2022版还是2025修订版,并指出部门总经理审批线。

工具轨迹摘录 `runs/gate4_standard_claude_v4pro_v1/claude-code/L3-006/tool_calls.jsonl:1`:

````text
{"arguments": {}, "error": null, "ok": true, "result_preview": {"preview": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_h
...[truncated 334 chars]
````

最终轨迹摘录 `runs/gate4_standard_claude_v4pro_v1/claude-code/L3-006/trajectory.json:8`:

````text
"result": "```json\n{\n  \"anomaly_ids\": [],\n  \"record_ids\": [],\n  \"answer\": \"费用报销审批线应采用2025修订版。2022版已于2025年1月1日起废止，其审批金额已被后续制度替代，不得作为现行审批依据。部门总经理审批线为单笔金额大于等于10000元且小于50000元。\",\n  \"citations\": [\n    {\n      \"doc_id\": \"01_expense_reimbursement_2025.md\",\n      \"clause_no\": \"第十四条\"\n    },\n    {\n      \"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\",\n      \"clause_no\": \"第一条、第四条\"\n    },\n    {\n      \"doc_id\": \"03_authorization_management.md\",\n      \"clause_no\": \"附件二AR-03\"\n    }\n  ]\n}\n```",
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "费用报销审批线应采用2025修订版。2022版已于2025年1月1日起废止，其审批金额已被后续制度替代，不得作为现行审批依据。部门总经理审批线为单笔金额大于等于10000元且小于50000元。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十四条"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第一条、第四条"}, {"doc_id": "03_authorization_management.md", "clause_no": "附件二AR-03"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 0.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选回答明确指出应采用2025修订版，部门总经理审批线为>=10000元，同时说明2022版已废止，语义上完全覆盖了三个期望事实。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### two_hop_retrieval (双跳检索)

表现: LLM内容通过 1/1, 旧规则通过 1/1, 格式失败 0, 超时 0。
代表样例: `L3-007` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 报销办法没有直接列审批金额时,请通过交叉引用找到单笔费用审批档位。

工具轨迹摘录 `runs/gate4_standard_claude_v4pro_v1/claude-code/L3-007/tool_calls.jsonl:1`:

````text
{"arguments": {}, "error": null, "ok": true, "result_preview": {"preview": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_h
...[truncated 334 chars]
````

最终轨迹摘录 `runs/gate4_standard_claude_v4pro_v1/claude-code/L3-007/trajectory.json:8`:

````text
"result": "```json\n{\n  \"anomaly_ids\": [],\n  \"record_ids\": [],\n  \"answer\": \"当《费用报销管理办法》正文未列示具体审批金额时，需要交叉引用《授权管理办法》附件二《费用报销审批权限表》来确定单笔费用审批档位。具体步骤：(1) 查阅《费用报销管理办法(2025修订版)》第五条，该条明确单笔费用报销的审批权限不在本办法正文列示，统一按《XX证券授权管理办法》附件二执行；(2) 打开《授权管理办法》附件二，根据费用金额匹配对应的审批档位：AR-01（0≤金额<3000元）由部门经理审批；AR-02（3000≤金额<10000元）由部门经理审批并经财务复核；AR-03（10000≤金额<50000元）由部门总经理审批；AR-04（50000≤金额<200000元）由分管副总审批；AR-05（金额≥200000元）由总经理办公会审批。费用系统应按附件二自动派生审批角色，各部门应按系统派生结果提交审批，不得以口头授权替代系统流程。\",\n  \"citations\": [\n    {\n      \"doc_id\": \"01_expense_reimbursement_2025.md\",\n      \"clause_no\": \"第五条\"\n    },\n    {\n      \"doc_id\": \"03_authorization_management.md\",\n      \"clause_no\": \"第二条\"\n    },\n    {\n      \"doc_id\": \"03_authorization_management.md\",\n      \"clause_no\": \"附件二\"\n    },\n    {\n      \"doc_id\": \"03_authorization_management.md\",\n      \"clause_no\": \"第三条\"\n    }\n  ]\n}\n```",
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "当《费用报销管理办法》正文未列示具体审批金额时，需要交叉引用《授权管理办法》附件二《费用报销审批权限表》来确定单笔费用审批档位。具体步骤：(1) 查阅《费用报销管理办法(2025修订版)》第五条，该条明确单笔费用报销的审批权限不在本办法正文列示，统一按《XX证券授权管理办法》附件二执行；(2) 打开《授权管理办法》附件二，根据费用金额匹配对应的审批档位：AR-01（0≤金额<3000元）由部门经理审批；AR-02（3000≤金额<10000元）由部门经理审批并经财务复核；AR-03（10000≤金额<50000元）由部门总经理审批；AR-04（50000≤金额<200000元）由分管副总审批；AR-05（金额≥200000元）由总经理办公会审批。费用系统应按附件二自动派生审批角色，各部门应按系统派生结果提交审批，不得以口头授权替代系统流程。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"}, {"doc_id": "03_authorization_management.md", "clause_no": "第二条"}, {"doc_id": "03_authorization_management.md", "clause_no": "附件二"}, {"doc_id": "03_authorization_management.md", "clause_no": "第三条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "回答完整给出了部门总经理审批线10000元以及金额出自授权管理办法附件二，覆盖所有预期事实。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### near_clause_disambiguation (近似条款辨析)

表现: LLM内容通过 1/1, 旧规则通过 0/1, 格式失败 0, 超时 0。
代表样例: `L3-008` / `precise` / `通过` / `llm_score=1.0` / `rule_score=0.0` / `layer=ok`。
题面: 比较差旅住宿和培训住宿标准,说明为什么不能混用。

工具轨迹摘录 `runs/gate4_standard_claude_v4pro_v1/claude-code/L3-008/tool_calls.jsonl:1`:

````text
{"arguments": {}, "error": null, "ok": true, "result_preview": {"preview": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_h
...[truncated 334 chars]
````

最终轨迹摘录 `runs/gate4_standard_claude_v4pro_v1/claude-code/L3-008/trajectory.json:8`:

````text
"result": "根据政策文档的对比分析，差旅住宿和培训住宿是两套完全独立的标准体系，明确禁止混用。以下是详细对比：\n\n---\n\n## 一、差旅住宿标准（《XX证券差旅费管理办法》第四条）\n\n差旅住宿按**员工职级 × 城市档位**的矩阵确定，单位为元/人/晚：\n\n| 职级 | 一类城市 | 二类城市 | 三类城市 |\n|------|----------|----------|----------|\n| 员工级 | 450元 | 380元 | 300元 |\n| 经理级 | 650元 | 550元 | 450元 |\n| 部门负责人级 | 850元 | 700元 | 600元 |\n| 高管级 | （另设更高标准） | | |\n\n## 二、培训住宿标准（《XX证券培训费管理办法》第五条）\n\n培训住宿**不区分职级**，仅按城市档位统一标准，单位为元/人/晚：\n\n| 城市档位 | 培训住宿标准 |\n|----------|-------------|\n| 一类城市 | 500元 |\n| 二类城市 | 420元 |\n| 三类城市 | 350元 |\n\n## 三、为什么不能混用\n\n1. **制度设计不同**：差旅住宿按职级分层，体现不同级别人员的差旅保障；培训住宿统一标准，体现培训经费的公平性和集约化管理原则。两套标准的设计逻辑完全不同。\n\n2. **适用场景不同**：差旅住宿用于公务出差，培训住宿仅适用于培训期间。出差和培训是两种性质不同的活动，对应的住宿需求和管理目标也不同。\n\n3. **制度明确禁止**：《XX证券差旅费管理办法》第七条规定\"培训期间住宿不适用本办法住宿表，应按《XX证券培训费管理办法》执行\"；《XX证券培训费管理办法》第六条规定\"培训住宿标准仅适用于培训期间住宿，不得与差旅住宿标准混用\"。两条规则互相呼应，形成闭环约束。\n\n4. **违规风险**：若允许混用，员工可能选择对自己更有利的标准套用（比如员工级在二类城市培训，差旅标准380元 vs 培训标准420元，若混用差旅标准则少报；经理级在一类城市培训，差旅标准650元 vs 培训标准500元，若混用差旅标准则超标），导致费用失控和制度虚设。\n\n```json\n{\n  \"anomaly_ids\": [],\n  \"record_ids\": [],\n  \"answer\": \"差旅住宿标准按员工职级分档（员工级450/380/300元、经理级650/550/450元、部门负责人级850/700/600元，一类/二类/三类城市），培训住宿标准不区分职级统一按城市档位（一类500元、二类420元、三类350元）。不能混用的原因：第一，两套标准的设计逻辑不同——差旅按职级分层保障，培训统一标准体现公平集约
...[truncated 541 chars]
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "差旅住宿标准按员工职级分档（员工级450/380/300元、经理级650/550/450元、部门负责人级850/700/600元，一类/二类/三类城市），培训住宿标准不区分职级统一按城市档位（一类500元、二类420元、三类350元）。不能混用的原因：第一，两套标准的设计逻辑不同——差旅按职级分层保障，培训统一标准体现公平集约；第二，适用场景不同——差旅住宿用于公务出差，培训住宿仅限培训期间；第三，制度明确禁止——《差旅费管理办法》第七条和《培训费管理办法》第六条互相呼应，规定培训期间住宿必须按培训标准执行、不得套用差旅标准，反之亦然；第四，若允许混用，员工可选择有利标准套报，导致费用失控和制度虚设。", "citations": [{"doc_id": "04_travel_expense.md", "clause_no": "第四条"}, {"doc_id": "04_travel_expense.md", "clause_no": "第七条"}, {"doc_id": "05_training_expense.md", "clause_no": "第五条"}, {"doc_id": "05_training_expense.md", "clause_no": "第六条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 0.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选回答明确提及差旅住宿用差旅费管理办法、培训住宿用培训费管理办法，并比较数值差异后说明不能混用，关键事实完整，引用正确。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### audit_report (报告式任务)

表现: LLM内容通过 1/2, 旧规则通过 0/2, 格式失败 0, 超时 0。
代表样例: `L3-010` / `precise` / `通过` / `llm_score=1.0` / `rule_score=0.0` / `layer=ok`。
题面: 请专门写一段版本陷阱审计说明,解释旧版审批线可能导致的误判。

工具轨迹摘录 `runs/gate4_standard_claude_v4pro_v1/claude-code/L3-010/tool_calls.jsonl:1`:

````text
{"arguments": {}, "error": null, "ok": true, "result_preview": {"preview": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_h
...[truncated 333 chars]
````

最终轨迹摘录 `runs/gate4_standard_claude_v4pro_v1/claude-code/L3-010/trajectory.json:8`:

````text
"result": "```json\n{\n  \"anomaly_ids\": [],\n  \"record_ids\": [],\n  \"answer\": \"版本陷阱审计说明：旧版审批线可能导致误判的风险分析。XX证券费用报销审批权限在2022版与2025修订版之间存在显著差异，若审计人员误用已废止的旧版标准进行合规判断，将产生系统性误判。具体而言，旧版制度（XX证财规〔2022〕乙号）规定的两条核心审批线为：单笔报销达到8000元须经部门总经理审批，达到30000元须经分管副总审批。而现行有效的《授权管理办法》附件二（XX证综规〔2025〕丙号）将审批线全面上调并细化为五档：AR-01档（0至3000元以下）由部门经理审批；AR-02档（3000至10000元以下）由部门经理审批并经财务复核；AR-03档（10000至50000元以下）由部门总经理审批；AR-04档（50000至200000元以下）由分管副总审批；AR-05档（200000元以上）由总经理办公会审批。若审计人员沿用旧版标准，将产生以下三类典型误判：第一，8000元至10000元区间，旧版要求部门总经理审批，但现行制度仅需部门经理加财务复核，按旧版判断会误报缺少部门总经理审批；第二，30000元至50000元区间，旧版要求分管副总审批，但现行制度仅需部门总经理审批，按旧版判断会误报缺少分管副总审批；第三，旧版未设200000元以上总经理办公会审批档位及3000元以下低额审批线，以旧版标准审阅现行记录将遗漏高额审批缺失或对低额记录过度要求。2025修订版第十四条已明确废止2022版，第五条规定审批权限统一按《授权管理办法》附件二执行，旧版文本第四条亦明确声明不得作为现行审批依据。审计时应以现行有效的2025版制度及其引用的授权管理办法附件二为唯一审批线标准，任何参照旧版8000元和30000元审批线的判断均构成版本陷阱误判。\",\n  \"citations\": [\n    {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"clause_no\": \"第二条\"},\n    {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"clause_no\": \"第三条\"},\n    {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"clause_no\": \"第四条\"},\n    {\"doc_id\": \"03_authorization_management.md\", \"clause_no\": \"第二条\"},\n    {
...[truncated 249 chars]
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "版本陷阱审计说明：旧版审批线可能导致误判的风险分析。XX证券费用报销审批权限在2022版与2025修订版之间存在显著差异，若审计人员误用已废止的旧版标准进行合规判断，将产生系统性误判。具体而言，旧版制度（XX证财规〔2022〕乙号）规定的两条核心审批线为：单笔报销达到8000元须经部门总经理审批，达到30000元须经分管副总审批。而现行有效的《授权管理办法》附件二（XX证综规〔2025〕丙号）将审批线全面上调并细化为五档：AR-01档（0至3000元以下）由部门经理审批；AR-02档（3000至10000元以下）由部门经理审批并经财务复核；AR-03档（10000至50000元以下）由部门总经理审批；AR-04档（50000至200000元以下）由分管副总审批；AR-05档（200000元以上）由总经理办公会审批。若审计人员沿用旧版标准，将产生以下三类典型误判：第一，8000元至10000元区间，旧版要求部门总经理审批，但现行制度仅需部门经理加财务复核，按旧版判断会误报缺少部门总经理审批；第二，30000元至50000元区间，旧版要求分管副总审批，但现行制度仅需部门总经理审批，按旧版判断会误报缺少分管副总审批；第三，旧版未设200000元以上总经理办公会审批档位及3000元以下低额审批线，以旧版标准审阅现行记录将遗漏高额审批缺失或对低额记录过度要求。2025修订版第十四条已明确废止2022版，第五条规定审批权限统一按《授权管理办法》附件二执行，旧版文本第四条亦明确声明不得作为现行审批依据。审计时应以现行有效的2025版制度及其引用的授权管理办法附件二为唯一审批线标准，任何参照旧版8000元和30000元审批线的判断均构成版本陷阱误判。", "citations": [{"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第二条"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第三条"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第四条"}, {"doc_id": "03_authorization_management.md", "clause_no": "第二条"}, {"doc_id": "03_authorization_management.md", "clause_no": "附件二"}, {"doc_id": "01_expense_reimbursement
...[truncated 101 chars]
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 0.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选回答完整覆盖了所有 rubric 断言，语义正确，引用恰当。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### clean_but_suspicious (陷阱题)

表现: LLM内容通过 2/5, 旧规则通过 3/5, 格式失败 0, 超时 0。
代表样例: `TRAP-003` / `precise` / `内容未通过` / `llm_score=0.0` / `rule_score=0.0` / `layer=no_anomaly_false_positive`。
题面: 请核查TRAP-003涉及的记录是否构成异常,正确时应说明无异常。

工具轨迹摘录 `runs/gate4_standard_claude_v4pro_v1/claude-code/TRAP-003/tool_calls.jsonl:1`:

````text
{"arguments": {"query": "TRAP-003", "top_k": 5}, "error": null, "ok": true, "result_preview": {"query": "TRAP-003", "results": [], "top_k": 5}, "server": "policy_query_mcp", "tool": "search_policy", "ts": 1783583455.7352889}
````

最终轨迹摘录 `runs/gate4_standard_claude_v4pro_v1/claude-code/TRAP-003/trajectory.json:8`:

````text
"result": "```json\n{\n  \"anomaly_ids\": [\"TRAP-003\"],\n  \"record_ids\": [\"R004236\", \"R004237\"],\n  \"answer\": \"TRAP-003涉及的记录R004236和R004237不构成拆分报销异常。两笔记录均为员工闭想(E0010)的travel_lodging费用,金额各5200元,费用日期分别为2025-10-01和2025-10-09,间隔8天。根据费用报销管理办法第十一条,拆分规避审批的核查条件为同一员工同一费用类型在7天内出现2笔及以上报销且合计金额达到较高审批线。两笔记录间隔8天,已超出7天窗口,不满足拆分报销异常的构成要件,因此无异常。\",\n  \"citations\": [\n    {\"doc_id\": \"01_expense_reimbursement_2025.md\", \"clause_no\": \"第十一条\"},\n    {\"doc_id\": \"03_authorization_management.md\", \"clause_no\": \"附件二\"}\n  ]\n}\n```",
````

候选答案摘录:

````text
{"anomaly_ids": ["TRAP-003"], "record_ids": ["R004236", "R004237"], "answer": "TRAP-003涉及的记录R004236和R004237不构成拆分报销异常。两笔记录均为员工闭想(E0010)的travel_lodging费用,金额各5200元,费用日期分别为2025-10-01和2025-10-09,间隔8天。根据费用报销管理办法第十一条,拆分规避审批的核查条件为同一员工同一费用类型在7天内出现2笔及以上报销且合计金额达到较高审批线。两笔记录间隔8天,已超出7天窗口,不满足拆分报销异常的构成要件,因此无异常。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十一条"}, {"doc_id": "03_authorization_management.md", "clause_no": "附件二"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 0.0,
  "rule_score": 0.0,
  "failure_layer": "no_anomaly_false_positive",
  "format_failure": false,
  "judge_reason": "候选将无异常的 TRAP-003 误报为异常，期望 anomaly_ids 为空，但候选输出 [\"TRAP-003\"]。",
  "judge_missing": [],
  "judge_extra": [
    "误将 TRAP-003 标记为异常"
  ]
}
````

原因分析: 输出可解析,但 LLM judge 认为关键事实、记录集合或异常判断没有语义命中。


## Codex

### 题型表现

| 题型 | 总数 | LLM内容通过 | 旧规则通过 | 格式失败 | LLM未通过 | 超时 | 判断 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| policy_qa | 4 | 4 | 4 | 0 | 0 | 0 | 仍是最稳定题型 |
| version_check | 1 | 1 | 0 | 0 | 0 | 0 | 中等表现 |
| single_anomaly_lookup | 5 | 5 | 5 | 0 | 0 | 0 | LLM judge 认可部分语义命中,但集合归并仍不稳 |
| ground_truth_lookup | 5 | 2 | 3 | 0 | 3 | 0 | record_id 集合覆盖是主要瓶颈 |
| policy_data_comparison | 25 | 11 | 25 | 0 | 14 | 0 | LLM judge 认可部分语义命中,但集合归并仍不稳 |
| full_year_rule_audit | 5 | 2 | 3 | 0 | 3 | 0 | LLM judge 认可部分语义命中,但集合归并仍不稳 |
| version_trap | 1 | 0 | 0 | 0 | 1 | 0 | 中等表现 |
| two_hop_retrieval | 1 | 1 | 1 | 0 | 0 | 0 | 中等表现 |
| near_clause_disambiguation | 1 | 1 | 0 | 0 | 0 | 0 | 中等表现 |
| audit_report | 2 | 1 | 0 | 0 | 1 | 0 | 报告可读性不等于 rubric 完整满足 |
| clean_but_suspicious | 5 | 3 | 4 | 0 | 2 | 0 | 陷阱识别有一定能力 |

### 各题型典型轨迹

下面每个题型放一个代表样例。样例选择规则: 通过率较高的题型选通过样例; 失败为主的题型选该题型最常见失败层。

#### policy_qa (纯制度问答)

表现: LLM内容通过 4/4, 旧规则通过 4/4, 格式失败 0, 超时 0。
代表样例: `L1-001` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 现行制度下,单笔费用报销达到多少金额需要部门总经理审批?

工具轨迹摘录 `runs/gate4_standard_codex_v4pro_v2/codex/L1-001/tool_calls.jsonl:1`:

````text
{"arguments": {"query": "部门总经理审批 金额 报销 单笔费用", "top_k": 5}, "error": null, "ok": true, "result_preview": {"preview": "{\"query\": \"部门总经理审批 金额 报销 单笔费用\", \"results\": [{\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"score\": 14.3153, \"snippets\": [\"第二条 旧版制度曾规定,单笔报销金额达到8000元的,应提交部门总经理审批。\", \"第一条 本办法为XX证券旧版费用报销制度文本,仅作为制度沿革留档。现行制度应以《XX证券费用报销管理办法(2025修订版)》为准。\", \"第三条 旧版制度曾规定,单笔报销金额达到30000元的,应提交分管副总审批。\"], \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"01_expense_reimbursement_2025.md\", \"score\": 11.2818, \"snippets\": [\"第十一条 不得将同一事项或同类事项拆分为多笔报销以规避审批权限。同一员工、同一费用类型在7天内出现2笔及以上报销,且合计金额达到《授权管理办法》附件二较高审批线的,应重点核查拆分规\", \"第五条 单笔费用报销的审批权限,不在本办法正文列示具体金额,统一按《XX证券授权管理办法》附件二执行。费用系统应按附件二自动派生审批角色。\", \"第三条 费用报销实行经办人真实性承诺、部门负责人业务审核、财务复核和授权审批相结合的管理原则。\"], \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"score\": 11.2058, \"snippets\": [\"第二条 本办法附件二适用于费用报销系统自动派生审批角色,相关金额为现行有效审批线。\", \"## 附件二 费用报销审批权限表\", \"| 档位 | 单笔金额区间 | 必要审批角色 |\"], \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"score\": 4.9597, \"snippets\": [\"第三条 部门费用累计使用达到年度预算额度的1.0倍后,原则上不得继续报销。\", \"第五条 本办法与费用报销制度共同构成费用控制依据。\", \"第二条 各部门应在年度预算额度内发生费用。\"],
...[truncated 310 chars]
````

最终轨迹摘录 `runs/gate4_standard_codex_v4pro_v2/codex/L1-001/trajectory.json:39`:

````text
"text": "{\"query\": \"部门总经理审批 金额 报销 单笔费用\", \"top_k\": 5, \"results\": [{\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\", \"score\": 14.3153, \"snippets\": [\"第二条 旧版制度曾规定,单笔报销金额达到8000元的,应提交部门总经理审批。\", \"第一条 本办法为XX证券旧版费用报销制度文本,仅作为制度沿革留档。现行制度应以《XX证券费用报销管理办法(2025修订版)》为准。\", \"第三条 旧版制度曾规定,单笔报销金额达到30000元的,应提交分管副总审批。\"]}, {\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\", \"score\": 11.2818, \"snippets\": [\"第十一条 不得将同一事项或同类事项拆分为多笔报销以规避审批权限。同一员工、同一费用类型在7天内出现2笔及以上报销,且合计金额达到《授权管理办法》附件二较高审批线的,应重点核查拆分规\", \"第五条 单笔费用报销的审批权限,不在本办法正文列示具体金额,统一按《XX证券授权管理办法》附件二执行。费用系统应按附件二自动派生审批角色。\", \"第三条 费用报销实行经办人真实性承诺、部门负责人业务审核、财务复核和授权审批相结合的管理原则。\"]}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\", \"score\": 11.2058, \"snippets\": [\"第二条 本办法附件二适用于费用报销系统自动派生审批角色,相关金额为现行有效审批线。\", \"## 附件二 费用报销审批权限表\", \"| 档位 | 单笔金额区间 | 必要审批角色 |\"]}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\", \"score\": 4.9597, \"snippets\": [\"第三条 部门费用累计使用达到年度预算额度的1.0倍后,原则上不得继续报销。\", \"第五条 本办法与费用报销制度共同构成费用控制依据。\", \"第二条 各部门应在年度预算额度内发生费用。\"]}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"
...[truncated 192 chars]
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "根据现行《XX证券授权管理办法》附件二（费用报销审批权限表），单笔报销金额达到10,000元（含）且不足50,000元的，需要部门总经理审批（档位AR-03）。《XX证券费用报销管理办法(2025修订版)》第五条明确，审批权限统一按《XX证券授权管理办法》附件二执行。", "citations": [{"doc_id": "03_authorization_management.md", "clause_no": "附件二 AR-03"}, {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选正确给出了部门总经理审批的起始金额10,000元，与期望事实一致。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### version_check (版本检查)

表现: LLM内容通过 1/1, 旧规则通过 0/1, 格式失败 0, 超时 0。
代表样例: `L1-003` / `precise` / `通过` / `llm_score=1.0` / `rule_score=0.0` / `layer=ok`。
题面: 2022版中部门总经理审批线是多少,它现在是否有效?

工具轨迹摘录 `runs/gate4_standard_codex_v4pro_v2/codex/L1-003/tool_calls.jsonl:1`:

````text
{"arguments": {}, "error": null, "ok": true, "result_preview": {"preview": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_h
...[truncated 333 chars]
````

最终轨迹摘录 `runs/gate4_standard_codex_v4pro_v2/codex/L1-003/trajectory.json:33`:

````text
"text": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_hr_transfer.md\", \"title\": \"XX证券人员调动管理办法\"}, {\"doc_id\": \"15_me
...[truncated 406 chars]
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "2022版《XX证券费用报销管理办法》（发文字号：XX证财规〔2022〕乙号）第二条规定，单笔报销金额达到8000元的，应提交部门总经理审批，即部门总经理审批线为8000元。但该办法第四条同时明确，其审批金额已被后续制度替代，不得作为现行审批依据。现行有效的审批线依据《XX证券授权管理办法》（发文字号：XX证综规〔2025〕丙号）附件二执行，其中部门总经理的审批档位为AR-03，对应单笔金额区间为大于等于10000元且小于50000元。因此，2022版中8000元的部门总经理审批线已失效。", "citations": [{"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第二条"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第四条"}, {"doc_id": "03_authorization_management.md", "clause_no": "第二条"}, {"doc_id": "03_authorization_management.md", "clause_no": "附件二"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 0.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "正确给出2022版审批线为8000元，并明确该值已废止，事实覆盖完整。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### single_anomaly_lookup (单条异常判断)

表现: LLM内容通过 5/5, 旧规则通过 5/5, 格式失败 0, 超时 0。
代表样例: `L1-006` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 请判断报销记录R000002是否命中重复报销,如命中请返回异常ID。

工具轨迹摘录 `runs/gate4_standard_codex_v4pro_v2/codex/L1-006/tool_calls.jsonl:1`:

````text
{"arguments": {"record_id": "R000002"}, "error": null, "ok": true, "result_preview": {"approvals": [{"approval_id": "A000002", "approval_status": "approved", "approved_at": "2025-09-09", "approver_employee_id": "E0008", "approver_role": "部门经理", "tier_id": "AR-01"}], "record": {"amount": 423.79, "annual_budget": 381600.0, "budget_year": 2025, "city_tier": null, "days": null, "department_id": "D008", "department_name": "合规风控部", "employee_id": "E0050", "employee_level": "X1", "employee_name": "姚瑜", "expense_date": "2025-08-19", "expense_type": "office_supplies", "invoice_amount": 423.79, "invoice_date": "2025-08-19", "invoice_id": "INV000002", "invoice_no": "FP202500000002", "nights": null, "participants": null, "position_role": "员工", "reason": "清源项目资料装订用品费", "record_id": "R000002", "record_no": "BX2025000002", "reimburse_date": "2025-09-09", "special_approval": 0, "status": "approved", "vendor_name": "XX供应商7753"}}, "server": "expense_query_mcp", "tool": "get_expense_detail", "ts": 1783580656.8119557}
````

最终轨迹摘录 `runs/gate4_standard_codex_v4pro_v2/codex/L1-006/trajectory.json:37`:

````text
"text": "{\"record\": {\"record_id\": \"R000002\", \"record_no\": \"BX2025000002\", \"employee_id\": \"E0050\", \"department_id\": \"D008\", \"expense_date\": \"2025-08-19\", \"reimburse_date\": \"2025-09-09\", \"expense_type\": \"office_supplies\", \"amount\": 423.79, \"reason\": \"清源项目资料装订用品费\", \"invoice_id\": \"INV000002\", \"status\": \"approved\", \"city_tier\": null, \"nights\": null, \"days\": null, \"participants\": null, \"budget_year\": 2025, \"special_approval\": 0, \"employee_name\": \"姚瑜\", \"employee_level\": \"X1\", \"position_role\": \"员工\", \"department_name\": \"合规风控部\", \"annual_budget\": 381600.0, \"invoice_no\": \"FP202500000002\", \"vendor_name\": \"XX供应商7753\", \"invoice_date\": \"2025-08-19\", \"invoice_amount\": 423.79}, \"approvals\": [{\"approval_id\": \"A000002\", \"tier_id\": \"AR-01\", \"approver_employee_id\": \"E0008\", \"approver_role\": \"部门经理\", \"approved_at\": \"2025-09-09\", \"approval_status\": \"approved\"}]}",
````

候选答案摘录:

````text
{"anomaly_ids": ["ANOMALY-DUP-0001"], "record_ids": ["R000002", "R004201"], "answer": "报销记录R000002命中重复报销。R000002与R004201使用了同一张发票FP202500000002（INV000002），发票金额423.79元，均为员工姚瑜（E0050）的办公用品费。依据《XX证券费用报销管理办法(2025修订版)》第十条\"同一发票最多报销1次。发现同一发票在不同报销单中重复出现的，应认定为重复报销风险。\"，两笔记录构成重复报销异常。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选正确识别了重复报销异常，记录ID和关键事实与期望一致，语义命中。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### ground_truth_lookup (异常查记录集合)

表现: LLM内容通过 2/5, 旧规则通过 3/5, 格式失败 0, 超时 0。
代表样例: `L1-012` / `precise` / `内容未通过` / `llm_score=0.0` / `rule_score=0.0` / `layer=record_id_miss`。
题面: 异常SPLIT-002涉及哪些报销记录?

工具轨迹摘录 `runs/gate4_standard_codex_v4pro_v2/codex/L1-012/tool_calls.jsonl:1`:

````text
{"arguments": {"query": "SPLIT-002 split expense anomaly"}, "error": null, "ok": true, "result_preview": {"query": "SPLIT-002 split expense anomaly", "results": [], "top_k": 5}, "server": "policy_query_mcp", "tool": "search_policy", "ts": 1783581048.5220244}
````

最终轨迹摘录 `runs/gate4_standard_codex_v4pro_v2/codex/L1-012/trajectory.json:37`:

````text
"text": "{\"query\": \"SPLIT-002 split expense anomaly\", \"top_k\": 5, \"results\": []}",
````

候选答案摘录:

````text
{"anomaly_ids": ["SPLIT-002"], "record_ids": ["R000005", "R004202"], "answer": "异常SPLIT-002涉及报销记录R000005和R004202，均为员工刘冬梅（E0022，信息技术部）的市内交通费报销，金额各88.83元，使用同一张发票FP202500000005。该发票被重复用于两笔不同报销单，违反同一发票仅可报销一次的规定。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"}, {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十一条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 0.0,
  "rule_score": 0.0,
  "failure_layer": "record_id_miss",
  "format_failure": false,
  "judge_reason": "候选回答给出的记录ID为R000005和R004202，与预期的R004209、R004210、R004211完全不符，语义上未命中任何正确记录。",
  "judge_missing": [
    "R004209",
    "R004210",
    "R004211"
  ],
  "judge_extra": [
    "R000005",
    "R004202"
  ]
}
````

原因分析: 输出可解析,但 LLM judge 认为关键事实、记录集合或异常判断没有语义命中。

#### policy_data_comparison (制度+业务交叉核查)

表现: LLM内容通过 11/25, 旧规则通过 25/25, 格式失败 0, 超时 0。
代表样例: `L2-009` / `precise` / `内容未通过` / `llm_score=0.0` / `rule_score=1.0` / `layer=no_anomaly_false_positive`。
题面: 结合制度和业务数据,核查以R004214为线索的拆分报销异常,返回异常ID和记录ID集合。

工具轨迹摘录 `runs/gate4_standard_codex_v4pro_v2/codex/L2-009/tool_calls.jsonl:1`:

````text
{"arguments": {"record_id": "R004214"}, "error": null, "ok": true, "result_preview": {"approvals": [{"approval_id": "A004214", "approval_status": "approved", "approved_at": "2025-06-09", "approver_employee_id": "E0010", "approver_role": "部门经理", "tier_id": "AR-02"}], "record": {"amount": 3500.0, "annual_budget": 164500.0, "budget_year": 2025, "city_tier": "A", "days": null, "department_id": "D010", "department_name": "人力资源部", "employee_id": "E0010", "employee_level": "D1", "employee_name": "闭想", "expense_date": "2025-06-03", "expense_type": "travel_lodging", "invoice_amount": 3500.0, "invoice_date": "2025-06-03", "invoice_id": "INV004208", "invoice_no": "FP2025X0004208", "nights": 5, "participants": null, "position_role": "部门经理", "reason": "拆分报销注入样本4", "record_id": "R004214", "record_no": "BX2025X004214", "reimburse_date": "2025-06-09", "special_approval": 0, "status": "approved", "vendor_name": "XX注入供应商R004214"}}, "server": "expense_query_mcp", "tool": "get_expense_detail", "ts": 1783581965.5928807}
````

最终轨迹摘录 `runs/gate4_standard_codex_v4pro_v2/codex/L2-009/trajectory.json:37`:

````text
"text": "{\"record\": {\"record_id\": \"R004214\", \"record_no\": \"BX2025X004214\", \"employee_id\": \"E0010\", \"department_id\": \"D010\", \"expense_date\": \"2025-06-03\", \"reimburse_date\": \"2025-06-09\", \"expense_type\": \"travel_lodging\", \"amount\": 3500.0, \"reason\": \"拆分报销注入样本4\", \"invoice_id\": \"INV004208\", \"status\": \"approved\", \"city_tier\": \"A\", \"nights\": 5, \"days\": null, \"participants\": null, \"budget_year\": 2025, \"special_approval\": 0, \"employee_name\": \"闭想\", \"employee_level\": \"D1\", \"position_role\": \"部门经理\", \"department_name\": \"人力资源部\", \"annual_budget\": 164500.0, \"invoice_no\": \"FP2025X0004208\", \"vendor_name\": \"XX注入供应商R004214\", \"invoice_date\": \"2025-06-03\", \"invoice_amount\": 3500.0}, \"approvals\": [{\"approval_id\": \"A004214\", \"tier_id\": \"AR-02\", \"approver_employee_id\": \"E0010\", \"approver_role\": \"部门经理\", \"approved_at\": \"2025-06-09\", \"approval_status\": \"approved\"}]}",
````

候选答案摘录:

````text
{"anomaly_ids": ["R004207", "R004208", "R004209", "R004210", "R004211", "R004212", "R004213", "R004214", "R004215", "R004216"], "record_ids": ["R004207", "R004208", "R004209", "R004210", "R004211", "R004212", "R004213", "R004214", "R004215", "R004216"], "answer": "同一员工同一费用类型在7个自然日内存在2笔及以上报销且合计金额达到10000元（授权管理办法附件二AR-02与AR-03分界线）的，构成拆分报销规避审批。共发现四组拆分异常：组1为E0007李丽娟于2025-01-10与2025-01-12分别报销住宿费各5200元合计10400元；组2为E0008杨丹于2025-02-26、02-28、03-02分别报销住宿费各3400元合计10200元；组3为E0009张婷于2025-04-10与04-15分别报销住宿费各5100元合计10200元；组4为E0010闭想于2025-06-03、06-05、06-07分别报销住宿费各3500元合计10500元。陷阱样本R004236与R004237间隔8日不满足7天内条件予以排除。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十一条"}, {"doc_id": "03_authorization_management.md", "clause_no": "附件二"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 0.0,
  "rule_score": 1.0,
  "failure_layer": "no_anomaly_false_positive",
  "format_failure": false,
  "judge_reason": "候选正确识别了SPLIT-004异常及记录R004214、R004215、R004216，但额外将R004207~R004213等7条不相关记录也列为异常，混入无关异常，违反anomaly_id_set唯一性。",
  "judge_missing": [],
  "judge_extra": [
    "多报了R004207、R004208、R004209、R004210、R004211、R004212、R004213为异常记录"
  ]
}
````

原因分析: 输出可解析,但 LLM judge 认为关键事实、记录集合或异常判断没有语义命中。

#### full_year_rule_audit (全年专项扫描)

表现: LLM内容通过 2/5, 旧规则通过 3/5, 格式失败 0, 超时 0。
代表样例: `L3-002` / `precise` / `内容未通过` / `llm_score=0.0` / `rule_score=0.0` / `layer=record_id_miss`。
题面: 请对全年数据做拆分报销专项扫描,返回全部异常ID和记录ID集合。

工具轨迹摘录 `runs/gate4_standard_codex_v4pro_v2/codex/L3-002/tool_calls.jsonl:1`:

````text
{"arguments": {}, "error": null, "ok": true, "result_preview": {"preview": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_h
...[truncated 334 chars]
````

最终轨迹摘录 `runs/gate4_standard_codex_v4pro_v2/codex/L3-002/trajectory.json:14`:

````text
"text": "Let me start by understanding the relevant policies and then systematically scan for split reimbursement anomalies."
````

候选答案摘录:

````text
{"anomaly_ids": ["ANOM-001", "ANOM-002", "ANOM-003", "ANOM-004", "ANOM-005", "ANOM-006", "ANOM-007", "ANOM-008", "ANOM-009", "ANOM-010", "ANOM-011", "ANOM-012", "ANOM-013", "ANOM-014", "ANOM-015", "ANOM-016", "ANOM-017", "ANOM-018", "ANOM-019", "ANOM-020", "ANOM-021", "ANOM-022", "ANOM-023", "ANOM-024", "ANOM-025", "ANOM-026", "ANOM-027", "ANOM-028", "ANOM-029", "ANOM-030", "ANOM-031", "ANOM-032", "ANOM-033", "ANOM-034"], "record_ids": ["R000002", "R004201", "R000005", "R004202", "R000020", "R004203", "R000028", "R004204", "R000037", "R004205", "R000055", "R004206", "R004207", "R004208", "R004212", "R004213", "R004214", "R004215", "R004216", "R004217", "R004218", "R004219", "R004220", "R002315", "R002070", "R000465", "R000561", "R000888", "R001354", "R001875", "R002175", "R000306", "R003573", "R004098", "R003610", "R003638", "R001515", "R001143", "R001502", "R001711", "R002443", "R001035", "R003609", "R002163", "R001099", "R000875", "R001240", "R000629", "R001476", "R002476", "R001800", "R001996", "R000242", "R003710", "R002736", "R003594", "R002858", "R003596", "R001207", "R001351", "R002411", "R001538", "R000226"], "answer": "{\"summary\": \"全年拆分报销专项扫描共发现34项异常，涉及63条报销记录，分为两大类：(1)
...[truncated 857 chars]
````

LLM judge 摘录:

````json
{
  "llm_score": 0.0,
  "rule_score": 0.0,
  "failure_layer": "record_id_miss",
  "format_failure": false,
  "judge_reason": "缺少异常SPLIT-002对应的记录R004209,R004210,R004211，且混入大量无关异常（如发票重复使用），未正确完成拆分报销专项扫描。",
  "judge_missing": [
    "R004209",
    "R004210",
    "R004211"
  ],
  "judge_extra": [
    "多报34个异常，其中包含发票重复使用等不相关规则，未严格限定拆分报销专项"
  ]
}
````

原因分析: 输出可解析,但 LLM judge 认为关键事实、记录集合或异常判断没有语义命中。

#### version_trap (版本陷阱)

表现: LLM内容通过 0/1, 旧规则通过 0/1, 格式失败 0, 超时 0。
代表样例: `L3-006` / `precise` / `内容未通过` / `llm_score=0.0` / `rule_score=0.0` / `layer=fact_miss`。
题面: 请判断费用报销审批线应采用2022版还是2025修订版,并指出部门总经理审批线。

工具轨迹摘录 `runs/gate4_standard_codex_v4pro_v2/codex/L3-006/tool_calls.jsonl:1`:

````text
{"arguments": {}, "error": null, "ok": true, "result_preview": {"preview": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_h
...[truncated 333 chars]
````

最终轨迹摘录 `runs/gate4_standard_codex_v4pro_v2/codex/L3-006/trajectory.json:33`:

````text
"text": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_hr_transfer.md\", \"title\": \"XX证券人员调动管理办法\"}, {\"doc_id\": \"15_me
...[truncated 406 chars]
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "费用报销审批线应采用2025修订版。2022版已于2025年1月1日被废止，其审批金额不得作为现行依据。2025修订版不再于正文列示具体金额，统一按授权管理办法附件二执行。根据附件二费用报销审批权限表，部门总经理审批线为：单笔报销金额大于等于10000元且小于50000元时，需经部门总经理审批。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十四条"}, {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第一条"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第四条"}, {"doc_id": "03_authorization_management.md", "clause_no": "第二条"}, {"doc_id": "03_authorization_management.md", "clause_no": "附件二"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 0.0,
  "rule_score": 0.0,
  "failure_layer": "fact_miss",
  "format_failure": false,
  "judge_reason": "回答未提及2022旧值为8000元且已废止，仅笼统说废止，关键事实不完整。",
  "judge_missing": [
    "2022旧值8000元已废止"
  ],
  "judge_extra": []
}
````

原因分析: 输出可解析,但 LLM judge 认为关键事实、记录集合或异常判断没有语义命中。

#### two_hop_retrieval (双跳检索)

表现: LLM内容通过 1/1, 旧规则通过 1/1, 格式失败 0, 超时 0。
代表样例: `L3-007` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 报销办法没有直接列审批金额时,请通过交叉引用找到单笔费用审批档位。

工具轨迹摘录 `runs/gate4_standard_codex_v4pro_v2/codex/L3-007/tool_calls.jsonl:1`:

````text
{"arguments": {}, "error": null, "ok": true, "result_preview": {"preview": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_h
...[truncated 334 chars]
````

最终轨迹摘录 `runs/gate4_standard_codex_v4pro_v2/codex/L3-007/trajectory.json:33`:

````text
"text": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_hr_transfer.md\", \"title\": \"XX证券人员调动管理办法\"}, {\"doc_id\": \"15_me
...[truncated 406 chars]
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "《费用报销管理办法(2025修订版)》第五条明确，单笔费用报销审批金额不在该办法正文列示，统一按《授权管理办法》附件二执行。附件二将单笔报销金额分为五档：AR-01（0元以上不满3000元）由部门经理审批；AR-02（3000元以上不满10000元）由部门经理审批并经财务复核；AR-03（10000元以上不满50000元）由部门总经理审批；AR-04（50000元以上不满200000元）由分管副总审批；AR-05（200000元及以上）由总经理办公会审批。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"}, {"doc_id": "03_authorization_management.md", "clause_no": "第二条"}, {"doc_id": "03_authorization_management.md", "clause_no": "附件二"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选回答语义完整覆盖两个预期事实。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### near_clause_disambiguation (近似条款辨析)

表现: LLM内容通过 1/1, 旧规则通过 0/1, 格式失败 0, 超时 0。
代表样例: `L3-008` / `precise` / `通过` / `llm_score=1.0` / `rule_score=0.0` / `layer=ok`。
题面: 比较差旅住宿和培训住宿标准,说明为什么不能混用。

工具轨迹摘录 `runs/gate4_standard_codex_v4pro_v2/codex/L3-008/tool_calls.jsonl:1`:

````text
{"arguments": {}, "error": null, "ok": true, "result_preview": {"preview": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_h
...[truncated 333 chars]
````

最终轨迹摘录 `runs/gate4_standard_codex_v4pro_v2/codex/L3-008/trajectory.json:14`:

````text
"text": "Let me look up the relevant policies on travel and training accommodation standards."
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "差旅住宿标准按员工职级和城市档位双重划分，例如员工级一类城市450元、经理级650元、部门负责人级850元、高管级1100元；而培训住宿标准仅按城市档位划分，不区分职级，例如一类城市500元、二类城市420元、三类城市350元。两者差异在于：差旅住宿与职级挂钩，培训住宿统一适用固定标准，使得同一城市下不同职级员工适用金额不同。两个制度各自独立，差旅管理办法明确规定培训期间住宿不适用差旅住宿表，应按培训费管理办法执行，培训费管理办法也明确培训住宿标准仅限培训期间使用，不得与差旅住宿标准混用。若混用，可能导致高职级员工在培训期间不合理套用较高差旅标准，或低职级员工在出差时错误引用较低的培训标准，破坏费用管控的精准性。", "citations": [{"doc_id": "04_travel_expense.md", "clause_no": "第四条"}, {"doc_id": "04_travel_expense.md", "clause_no": "第七条"}, {"doc_id": "05_training_expense.md", "clause_no": "第五条"}, {"doc_id": "05_training_expense.md", "clause_no": "第六条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 0.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "回答覆盖了所有三个预期事实，并提供了支持性引用，语义完整。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### audit_report (报告式任务)

表现: LLM内容通过 1/2, 旧规则通过 0/2, 格式失败 0, 超时 0。
代表样例: `L3-010` / `precise` / `通过` / `llm_score=1.0` / `rule_score=0.0` / `layer=ok`。
题面: 请专门写一段版本陷阱审计说明,解释旧版审批线可能导致的误判。

工具轨迹摘录 `runs/gate4_standard_codex_v4pro_v2/codex/L3-010/tool_calls.jsonl:1`:

````text
{"arguments": {}, "error": null, "ok": true, "result_preview": {"preview": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_h
...[truncated 334 chars]
````

最终轨迹摘录 `runs/gate4_standard_codex_v4pro_v2/codex/L3-010/trajectory.json:33`:

````text
"text": "{\"corpus_dir\": \"D:\\\\算法LLM\\\\项目篇\\\\东方证券\\\\agent\\\\blackbox-eval\\\\data\\\\corpus\", \"documents\": [{\"doc_id\": \"01_expense_reimbursement_2025.md\", \"title\": \"XX证券费用报销管理办法(2025修订版)\"}, {\"doc_id\": \"02_expense_reimbursement_2022_deprecated.md\", \"title\": \"XX证券费用报销管理办法(2022版)\"}, {\"doc_id\": \"03_authorization_management.md\", \"title\": \"XX证券授权管理办法\"}, {\"doc_id\": \"04_travel_expense.md\", \"title\": \"XX证券差旅费管理办法\"}, {\"doc_id\": \"05_training_expense.md\", \"title\": \"XX证券培训费管理办法\"}, {\"doc_id\": \"06_business_entertainment.md\", \"title\": \"XX证券业务招待费管理办法\"}, {\"doc_id\": \"07_office_communication.md\", \"title\": \"XX证券办公与通讯费用管理办法\"}, {\"doc_id\": \"08_budget_management.md\", \"title\": \"XX证券预算管理办法\"}, {\"doc_id\": \"09_information_security.md\", \"title\": \"XX证券信息安全管理办法\"}, {\"doc_id\": \"10_seal_management.md\", \"title\": \"XX证券印章管理办法\"}, {\"doc_id\": \"11_attendance_management.md\", \"title\": \"XX证券考勤与休假管理办法\"}, {\"doc_id\": \"12_archive_management.md\", \"title\": \"XX证券档案管理办法\"}, {\"doc_id\": \"13_procurement_management.md\", \"title\": \"XX证券采购管理办法\"}, {\"doc_id\": \"14_hr_transfer.md\", \"title\": \"XX证券人员调动管理办法\"}, {\"doc_id\": \"15_me
...[truncated 406 chars]
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": [], "answer": "版本陷阱审计说明：若审计人员沿用已被废止的2022版费用报销管理办法的审批线进行审查，将产生系统性误判。2022旧版规定单笔8000元以上须部门总经理审批、30000元以上须分管副总审批；而现行制度（2025修订版）统一引用授权管理办法附件二，审批线已整体上调且档位细化：3000元至10000元仅需部门经理加财务复核，10000元至50000元需部门总经理，50000元至200000元才需分管副总。具体陷阱包括：(1) 8000元至9999元的报销在旧版触发部门总经理审批，现行制度下仅需部门经理加财务复核，若仍按旧线核查会误判为缺少高级别审批；(2) 30000元至49999元的报销在旧版触发分管副总审批，现行制度下仅需部门总经理审批，按旧线核查会误判为缺少副总审批。审计中必须确认所使用的审批线版本为现行有效的授权管理办法附件二，并关注2025版费用报销办法第十四条已明确废止2022旧版，不得以已废止的旧线作为判断依据。", "citations": [{"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第二条"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第三条"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第一条"}, {"doc_id": "02_expense_reimbursement_2022_deprecated.md", "clause_no": "第四条"}, {"doc_id": "03_authorization_management.md", "clause_no": "附件二"}, {"doc_id": "03_authorization_management.md", "clause_no": "第二条"}, {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第五条"}, {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十四条"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 0.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选回答明确指出了2025修订版部门总经理审批线为10000元，说明了2022版8000元已废止，并通过授权管理办法附件二取得现行审批金额，且未将旧版条款作为当前审批依据，满足全部 rubric 断言。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

#### clean_but_suspicious (陷阱题)

表现: LLM内容通过 3/5, 旧规则通过 4/5, 格式失败 0, 超时 0。
代表样例: `TRAP-002` / `precise` / `通过` / `llm_score=1.0` / `rule_score=1.0` / `layer=ok`。
题面: 请核查TRAP-002涉及的记录是否构成异常,正确时应说明无异常。

工具轨迹摘录 `runs/gate4_standard_codex_v4pro_v2/codex/TRAP-002/tool_calls.jsonl:1`:

````text
{"arguments": {"query": "TRAP-002", "top_k": 5}, "error": null, "ok": true, "result_preview": {"query": "TRAP-002", "results": [], "top_k": 5}, "server": "policy_query_mcp", "tool": "search_policy", "ts": 1783585410.8253617}
````

最终轨迹摘录 `runs/gate4_standard_codex_v4pro_v2/codex/TRAP-002/trajectory.json:39`:

````text
"text": "{\"query\": \"TRAP-002\", \"top_k\": 5, \"results\": []}",
````

候选答案摘录:

````text
{"anomaly_ids": [], "record_ids": ["R004234", "R004235"], "answer": "经核查，TRAP-002涉及的两笔报销记录(R004234、R004235)虽为同一员工同日同费用类型且金额相同，但使用不同发票，不构成重复报销；两笔合计金额500元远低于授权管理办法附件二中AR-02档位3000元的较高审批线，不触发拆分规避审批规则；报销均在费用发生后60天内提交，审批权限合规，部门预算未超支。因此不构成异常。", "citations": [{"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十条"}, {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "第十一条"}, {"doc_id": "03_authorization_management.md", "clause_no": "附件二"}]}
````

LLM judge 摘录:

````json
{
  "llm_score": 1.0,
  "rule_score": 1.0,
  "failure_layer": null,
  "format_failure": false,
  "judge_reason": "候选正确识别TRAP-002无异常，覆盖期望记录R004234和R004235，并给出了充分合理的依据。",
  "judge_missing": [],
  "judge_extra": []
}
````

原因分析: LLM judge 认为内容语义命中; 若同时存在格式失败,说明内容能力和输出合约需要分开看。

## 按失败类型归因

| agent | layer | count |
| --- | --- | ---: |
| qwen-code | `ok` | 33 |
| qwen-code | `record_id_miss` | 7 |
| qwen-code | `reasoning_or_retrieval_error` | 7 |
| qwen-code | `no_anomaly_false_positive` | 4 |
| qwen-code | `fact_miss` | 3 |
| qwen-code | `rubric_miss` | 1 |
| trae-agent | `ok` | 45 |
| trae-agent | `record_id_miss` | 5 |
| trae-agent | `reasoning_or_retrieval_error` | 3 |
| trae-agent | `fact_miss` | 1 |
| trae-agent | `no_anomaly_false_positive` | 1 |
| opencode | `ok` | 41 |
| opencode | `record_id_miss` | 6 |
| opencode | `no_anomaly_false_positive` | 4 |
| opencode | `reasoning_or_retrieval_error` | 2 |
| opencode | `fact_miss` | 1 |
| opencode | `rubric_miss` | 1 |
| claude-code | `ok` | 32 |
| claude-code | `record_id_miss` | 10 |
| claude-code | `no_anomaly_false_positive` | 10 |
| claude-code | `reasoning_or_retrieval_error` | 2 |
| claude-code | `fact_miss` | 1 |
| codex | `ok` | 31 |
| codex | `no_anomaly_false_positive` | 13 |
| codex | `record_id_miss` | 8 |
| codex | `reasoning_or_retrieval_error` | 1 |
| codex | `fact_miss` | 1 |
| codex | `rubric_miss` | 1 |

## 题型建议

- 制度问答和简单双跳可以作为基本能力回归集。
- 异常识别题需要同时看 `score` 和 `rule_score`: LLM judge 能识别语义命中,规则分能暴露输出 ID 命名空间不一致。
- 报告式任务建议继续使用 LLM judge 或人工抽检,单纯字符串断言过硬。
- 格式失败不应和内容失败混在一起: agent 产品可用性需要分别优化答案合约、工具轨迹、业务推理。
