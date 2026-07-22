# 正式测评题与逐题 Checklist Rubric

- 数据集：`securities-expense-audit-formal-15-v7`
- Rubric版本：`atomic-binary-checklist-v5`
- 正式题数量：15题
- Checklist总项数：292项
- 判定规则：每个检查项仅取0或1；完全满足通过条件记1，否则记0。
- 单题统计：记录命中项数、Checklist总项数和命中率，不判定整题通过或不通过。
- 所有检查项等权，不设置条目分值、条目权重或关键错误封顶。

## 题目目录

1. [L1-001 制度与版本判断](#l1-001)
2. [L3-006 制度与版本判断](#l3-006)
3. [L3-008 制度与版本判断](#l3-008)
4. [L2-003 单案数据核查](#l2-003)
5. [L2-008 单案数据核查](#l2-008)
6. [L2-013 单案数据核查](#l2-013)
7. [L3-001 全年专项审计](#l3-001)
8. [L3-003 全年专项审计](#l3-003)
9. [L3-004 全年专项审计](#l3-004)
10. [TRAP-002 无异常及陷阱题](#trap-002)
11. [TRAP-003 无异常及陷阱题](#trap-003)
12. [TRAP-005 无异常及陷阱题](#trap-005)
13. [L3-007 检索与综合报告](#l3-007)
14. [L3-009 检索与综合报告](#l3-009)
15. [L3-010 检索与综合报告](#l3-010)

---

## 1. L1-001

- **题型**：制度与版本判断
- **难度**：`L1`
- **类别**：`policy_qa`
- **选题目的**：现行审批线基础题，验证制度事实与版本意识
- **Checklist数量**：8项

### 题目

> 现行制度下，单笔费用报销达到多少金额需要部门总经理审批？请说明适用版本、金额边界及费用报销办法与授权管理办法中的制度依据，并说明旧版审批线是否仍适用。

### 标准答案边界

以下内容仅供判卷和复核，不应暴露给候选智能体。

```json
{
  "scoring_kind": "expected_facts",
  "expected_facts": [
    "现行部门总经理审批线为10000元"
  ],
  "required_citations": [
    {
      "doc_id": "01_expense_reimbursement_2025.md",
      "clause_no": "第五条"
    },
    {
      "doc_id": "03_authorization_management.md",
      "clause_no": "附件二"
    }
  ]
}
```

### Checklist Rubric

| # | 检查项ID | 维度 | 判定方式 | 检查内容 | 预期 | 通过条件 | 证据来源 |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | `current-threshold-amount` | 结论 | 规则/LLM Judge | 给出现行部门总经理审批金额10000元 | 10000 | 明确给出10000元 | 最终答案、提交JSON |
| 2 | `current-threshold-inclusive` | 结论 | 规则/LLM Judge | 说明10000元本身进入该审批档位 | 达到10000元 | 明确说明达到或等于10000元即适用 | 最终答案、提交JSON |
| 3 | `current-version` | 制度 | 规则/LLM Judge | 现行版本：明确结论基于2025修订版或现行制度 | 2025修订版为现行制度 | 明确识别现行版本 | 最终答案、工具轨迹 |
| 4 | `policy-citation-expense-rule` | 制度 | 规则/LLM Judge | 引用费用报销办法第五条 | 01_expense_reimbursement_2025.md#第五条 | 引用费用报销办法第五条 | 提交JSON、工具轨迹 |
| 5 | `policy-citation-authorization` | 制度 | 规则/LLM Judge | 引用授权管理办法附件二 | 03_authorization_management.md#附件二 | 引用授权管理办法附件二 | 提交JSON、工具轨迹 |
| 6 | `policy-citation-cross-reference` | 制度 | 规则/LLM Judge | 说明两份制度的交叉引用关系 | 第五条指向附件二 | 说明审批金额由费用报销办法第五条指向授权管理办法附件二取得 | 提交JSON、工具轨迹 |
| 7 | `old-value-control` | 误报控制 | LLM Judge | 旧值排除：不把2022版8000元旧值当作当前标准 | 8000元不得作为当前审批线 | 明确排除旧值 | 最终答案 |
| 8 | `submission` | 格式 | 规则 | 统一Schema结果提交成功 | submission_receipt.status=accepted | 提交回执状态为accepted且Schema校验通过 | 提交JSON |

---

## 2. L3-006

- **题型**：制度与版本判断
- **难度**：`L3`
- **类别**：`version_trap`
- **选题目的**：新旧制度冲突题，验证适用版本选择
- **Checklist数量**：8项

### 题目

> 请判断费用报销审批线应采用2022版还是2025修订版，指出部门总经理审批线，并提供新旧版本效力状态及现行金额出处。

### 标准答案边界

以下内容仅供判卷和复核，不应暴露给候选智能体。

```json
{
  "scoring_kind": "expected_facts",
  "expected_facts": [
    "现行值为10000元",
    "2022旧值8000元已废止",
    "应采用2025修订版"
  ],
  "required_citations": [
    {
      "doc_id": "01_expense_reimbursement_2025.md",
      "clause_no": "第十四条"
    },
    {
      "doc_id": "02_expense_reimbursement_2022_deprecated.md",
      "clause_no": "第一条、第二条、第四条"
    },
    {
      "doc_id": "03_authorization_management.md",
      "clause_no": "附件二"
    }
  ]
}
```

### Checklist Rubric

| # | 检查项ID | 维度 | 判定方式 | 检查内容 | 预期 | 通过条件 | 证据来源 |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | `current-value` | 结论 | 规则/LLM Judge | 现行审批线：指出2025修订版现行值 | 10000元 | 现行值准确 | 最终答案、提交JSON |
| 2 | `deprecated-value-amount` | 制度 | 规则/LLM Judge | 给出2022版审批线8000元 | 8000 | 明确给出2022版金额8000元 | 最终答案、工具轨迹 |
| 3 | `deprecated-value-status` | 制度 | 规则/LLM Judge | 说明2022版已经废止 | 已废止 | 明确说明2022版不再有效 | 最终答案、工具轨迹 |
| 4 | `applicable-version` | 推理 | LLM Judge | 适用版本：明确当前应采用2025修订版 | 采用2025修订版，不采用2022版 | 选择正确并说明时间适用关系 | 最终答案、工具轨迹 |
| 5 | `two-version-evidence-current` | 制度 | 规则/LLM Judge | 引用2025修订版的效力依据 | 01_expense_reimbursement_2025.md | 引用2025修订版及其现行效力条款 | 提交JSON、工具轨迹 |
| 6 | `two-version-evidence-deprecated` | 制度 | 规则/LLM Judge | 引用2022版的废止依据 | 02_expense_reimbursement_2022_deprecated.md | 引用2022版及其废止状态 | 提交JSON、工具轨迹 |
| 7 | `two-version-evidence-amount` | 制度 | 规则/LLM Judge | 引用授权管理办法附件二的金额依据 | 03_authorization_management.md#附件二 | 引用附件二中的10000元审批档位 | 提交JSON、工具轨迹 |
| 8 | `submission` | 格式 | 规则 | 统一Schema结果提交成功 | submission_receipt.status=accepted | 提交回执状态为accepted且Schema校验通过 | 提交JSON |

---

## 3. L3-008

- **题型**：制度与版本判断
- **难度**：`L3`
- **类别**：`near_clause_disambiguation`
- **选题目的**：近似条款区分题，验证适用场景判断
- **Checklist数量**：17项

### 题目

> 分别比较差旅住宿和培训住宿的适用制度、标准维度和数值。请列出培训住宿一、二、三类城市标准，并至少举一个同城市档位下与某职级差旅标准的数值对照，说明为什么不能混用。

### 标准答案边界

以下内容仅供判卷和复核，不应暴露给候选智能体。

```json
{
  "scoring_kind": "expected_facts",
  "expected_facts": [
    "差旅住宿按员工职级和城市档位共同确定",
    "培训住宿一二三类城市标准分别为500元、420元、350元每人每晚",
    "培训住宿与差旅住宿不得混用"
  ],
  "required_citations": [
    {
      "doc_id": "04_travel_expense.md",
      "clause_no": "第三条、第四条、第七条"
    },
    {
      "doc_id": "05_training_expense.md",
      "clause_no": "第五条、第六条"
    }
  ]
}
```

### Checklist Rubric

| # | 检查项ID | 维度 | 判定方式 | 检查内容 | 预期 | 通过条件 | 证据来源 |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | `travel-dimensions-policy` | 制度 | 规则/LLM Judge | 指出差旅住宿适用差旅费管理办法 | 04_travel_expense.md | 正确识别差旅费管理办法 | 最终答案、工具轨迹 |
| 2 | `travel-dimensions-job-level` | 制度 | 规则/LLM Judge | 指出差旅住宿按员工职级区分 | 员工职级 | 明确包含员工职级维度 | 最终答案、工具轨迹 |
| 3 | `travel-dimensions-city-tier` | 制度 | 规则/LLM Judge | 指出差旅住宿按城市档位区分 | 城市档位 | 明确包含城市档位维度 | 最终答案、工具轨迹 |
| 4 | `training-values-policy` | 制度 | 规则/LLM Judge | 指出培训住宿适用培训费管理办法 | 05_training_expense.md | 正确识别培训费管理办法 | 最终答案、工具轨迹 |
| 5 | `training-values-tier-a` | 制度 | 规则/LLM Judge | 给出一类城市培训住宿标准500元/人/晚 | 500 | 一类城市数值和单位均正确 | 最终答案、工具轨迹 |
| 6 | `training-values-tier-b` | 制度 | 规则/LLM Judge | 给出二类城市培训住宿标准420元/人/晚 | 420 | 二类城市数值和单位均正确 | 最终答案、工具轨迹 |
| 7 | `training-values-tier-c` | 制度 | 规则/LLM Judge | 给出三类城市培训住宿标准350元/人/晚 | 350 | 三类城市数值和单位均正确 | 最终答案、工具轨迹 |
| 8 | `numeric-comparison-scenario` | 推理 | 规则/LLM Judge | 给出一个明确的城市档位和差旅职级 | 城市档位和员工职级 | 对照场景的城市档位和差旅职级均明确 | 最终答案、工具轨迹 |
| 9 | `numeric-comparison-travel-value` | 推理 | 规则/LLM Judge | 给出该场景对应的差旅住宿标准 | 差旅住宿数值 | 差旅住宿标准与制度表一致 | 最终答案、工具轨迹 |
| 10 | `numeric-comparison-training-value` | 推理 | 规则/LLM Judge | 给出同一城市档位的培训住宿标准 | 培训住宿数值 | 培训住宿标准与制度表一致 | 最终答案、工具轨迹 |
| 11 | `numeric-comparison-same-tier` | 推理 | 规则/LLM Judge | 两侧数值使用同一城市档位进行比较 | 同城市档位 | 培训与差旅数值属于同一城市档位 | 最终答案、工具轨迹 |
| 12 | `no-mixing-scenario` | 推理 | LLM Judge | 说明培训与差旅属于不同费用事项 | 不同业务事项 | 明确区分培训和差旅场景 | 最终答案 |
| 13 | `no-mixing-dimensions` | 推理 | LLM Judge | 说明两套住宿标准的适用维度不同 | 标准维度不同 | 指出培训只按城市而差旅还按职级 | 最终答案 |
| 14 | `no-mixing-conclusion` | 推理 | LLM Judge | 明确两套标准不得混用或择高套用 | 不得混用 | 明确作出不得混用结论 | 最终答案 |
| 15 | `comparison-evidence-travel` | 证据 | 规则/LLM Judge | 引用差旅费管理办法第三、四、七条 | 04_travel_expense.md#第三条、第四条、第七条 | 差旅制度及关键条款完整 | 提交JSON、工具轨迹 |
| 16 | `comparison-evidence-training` | 证据 | 规则/LLM Judge | 引用培训费管理办法第五、六条 | 05_training_expense.md#第五条、第六条 | 培训制度及关键条款完整 | 提交JSON、工具轨迹 |
| 17 | `submission` | 格式 | 规则 | 统一Schema结果提交成功 | submission_receipt.status=accepted | 提交回执状态为accepted且Schema校验通过 | 提交JSON |

---

## 4. L2-003

- **题型**：单案数据核查
- **难度**：`L2`
- **类别**：`policy_data_comparison`
- **选题目的**：重复报销单案，验证跨记录证据关联
- **Checklist数量**：10项

### 题目

> 结合制度和业务数据，核查以R000020为线索的重复报销异常，返回发现ID和record_id集合，并说明关键业务事实和制度依据。

### 标准答案边界

以下内容仅供判卷和复核，不应暴露给候选智能体。

```json
{
  "scoring_kind": "finding_type_count",
  "expected_record_ids": [
    "R000020",
    "R004203"
  ],
  "expected_findings_by_type": {
    "DUP": 1
  },
  "expected_anomaly_count": 1,
  "required_citations": [
    {
      "doc_id": "01_expense_reimbursement_2025.md",
      "clause_no": "第十条"
    }
  ]
}
```

### Checklist Rubric

| # | 检查项ID | 维度 | 判定方式 | 检查内容 | 预期 | 通过条件 | 证据来源 |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | `audit-conclusion` | 结论 | 规则/LLM Judge | 异常结论：在answer中明确判断本案构成重复报销 | 重复报销 | answer明确认定构成重复报销且无矛盾表述 | 最终答案 |
| 2 | `anomaly-type-count-rule-type` | 结论 | 规则 | 发现类型为DUP | DUP | 全部已提交发现均归属于DUP规则类型 | 提交JSON、最终答案 |
| 3 | `anomaly-type-count-count` | 结论 | 规则 | 发现数量为1 | 1 | 已提交发现数量恰好为1 | 提交JSON、最终答案 |
| 4 | `record-set-include-r000020` | 证据 | 规则 | 结果包含应核查记录 R000020 | R000020 | 提交的record_ids包含R000020 | 提交JSON、工具轨迹 |
| 5 | `record-set-include-r004203` | 证据 | 规则 | 结果包含应核查记录 R004203 | R004203 | 提交的record_ids包含R004203 | 提交JSON、工具轨迹 |
| 6 | `record-set-no-extra` | 证据 | 规则 | 结果不包含本题范围外的记录 | ["R000020","R004203"] | 提交的record_ids除R000020, R004203外没有其他记录 | 提交JSON、工具轨迹 |
| 7 | `policy-basis` | 制度 | 规则/LLM Judge | 制度依据：引用01_expense_reimbursement_2025.md 第十条并说明其适用性 | 01_expense_reimbursement_2025.md 第十条 | 条款有效且直接支持结论 | 提交JSON、工具轨迹 |
| 8 | `case-reasoning-same-invoice` | 推理 | 规则/LLM Judge | 说明两条记录使用同一发票 | 同一invoice_id | 明确识别同一发票被重复使用 | 最终答案、工具轨迹、工作区产物 |
| 9 | `case-reasoning-amount` | 推理 | 规则/LLM Judge | 说明两条记录对应金额均为669.5元 | 669.5 | 金额669.5元与记录一致 | 最终答案、工具轨迹、工作区产物 |
| 10 | `submission` | 格式 | 规则 | 统一Schema结果提交成功 | submission_receipt.status=accepted | 提交回执状态为accepted且Schema校验通过 | 提交JSON |

---

## 5. L2-008

- **题型**：单案数据核查
- **难度**：`L2`
- **类别**：`policy_data_comparison`
- **选题目的**：拆分报销双记录案例，验证窗口和合计金额
- **Checklist数量**：12项

### 题目

> 结合制度和业务数据，核查以R004212为线索的拆分报销异常，返回发现ID和record_id集合，并说明日期窗口、合计金额和制度依据。

### 标准答案边界

以下内容仅供判卷和复核，不应暴露给候选智能体。

```json
{
  "scoring_kind": "finding_type_count",
  "expected_record_ids": [
    "R004212",
    "R004213"
  ],
  "expected_findings_by_type": {
    "SPLIT": 1
  },
  "expected_anomaly_count": 1,
  "required_citations": [
    {
      "doc_id": "01_expense_reimbursement_2025.md",
      "clause_no": "第十一条"
    },
    {
      "doc_id": "03_authorization_management.md",
      "clause_no": "附件二"
    }
  ]
}
```

### Checklist Rubric

| # | 检查项ID | 维度 | 判定方式 | 检查内容 | 预期 | 通过条件 | 证据来源 |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | `audit-conclusion` | 结论 | 规则/LLM Judge | 异常结论：在answer中明确判断本案构成拆分报销 | 拆分报销 | answer明确认定构成拆分报销且无矛盾表述 | 最终答案 |
| 2 | `anomaly-type-count-rule-type` | 结论 | 规则 | 发现类型为SPLIT | SPLIT | 全部已提交发现均归属于SPLIT规则类型 | 提交JSON、最终答案 |
| 3 | `anomaly-type-count-count` | 结论 | 规则 | 发现数量为1 | 1 | 已提交发现数量恰好为1 | 提交JSON、最终答案 |
| 4 | `record-set-include-r004212` | 证据 | 规则 | 结果包含应核查记录 R004212 | R004212 | 提交的record_ids包含R004212 | 提交JSON、工具轨迹 |
| 5 | `record-set-include-r004213` | 证据 | 规则 | 结果包含应核查记录 R004213 | R004213 | 提交的record_ids包含R004213 | 提交JSON、工具轨迹 |
| 6 | `record-set-no-extra` | 证据 | 规则 | 结果不包含本题范围外的记录 | ["R004212","R004213"] | 提交的record_ids除R004212, R004213外没有其他记录 | 提交JSON、工具轨迹 |
| 7 | `policy-basis-expense` | 制度 | 规则/LLM Judge | 引用费用报销办法第十一条 | 01_expense_reimbursement_2025.md#第十一条 | 引用拆分报销规则条款 | 提交JSON、工具轨迹 |
| 8 | `policy-basis-authorization` | 制度 | 规则/LLM Judge | 引用授权管理办法附件二 | 03_authorization_management.md#附件二 | 引用10000元审批线出处 | 提交JSON、工具轨迹 |
| 9 | `case-reasoning-window` | 推理 | 规则/LLM Judge | 说明两条记录位于7天窗口内 | 7 | 正确计算为7天窗口内 | 最终答案、工具轨迹、工作区产物 |
| 10 | `case-reasoning-sum` | 推理 | 规则/LLM Judge | 说明窗口内合计金额为10200元 | 10200 | 合计金额计算为10200元 | 最终答案、工具轨迹、工作区产物 |
| 11 | `case-reasoning-threshold` | 推理 | 规则/LLM Judge | 说明10200元达到并超过10000元审批线 | 10000 | 将合计金额与10000元审批线正确比较 | 最终答案、工具轨迹、工作区产物 |
| 12 | `submission` | 格式 | 规则 | 统一Schema结果提交成功 | submission_receipt.status=accepted | 提交回执状态为accepted且Schema校验通过 | 提交JSON |

---

## 6. L2-013

- **题型**：单案数据核查
- **难度**：`L2`
- **类别**：`policy_data_comparison`
- **选题目的**：培训费超标准案例，验证金额与费用类型标准
- **Checklist数量**：11项

### 题目

> 结合制度和业务数据，核查以R004223为线索的超标准异常，返回发现ID和record_id集合，并说明费用类型、金额、适用标准和制度依据。

### 标准答案边界

以下内容仅供判卷和复核，不应暴露给候选智能体。

```json
{
  "scoring_kind": "finding_type_count",
  "expected_record_ids": [
    "R004223"
  ],
  "expected_findings_by_type": {
    "OVERSTD": 1
  },
  "expected_anomaly_count": 1,
  "required_citations": [
    {
      "doc_id": "01_expense_reimbursement_2025.md",
      "clause_no": "第十二条"
    },
    {
      "doc_id": "05_training_expense.md",
      "clause_no": "第二条"
    }
  ]
}
```

### Checklist Rubric

| # | 检查项ID | 维度 | 判定方式 | 检查内容 | 预期 | 通过条件 | 证据来源 |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | `audit-conclusion` | 结论 | 规则/LLM Judge | 异常结论：在answer中明确判断本案构成超标准 | 超标准 | answer明确认定构成超标准且无矛盾表述 | 最终答案 |
| 2 | `anomaly-type-count-rule-type` | 结论 | 规则 | 发现类型为OVERSTD | OVERSTD | 全部已提交发现均归属于OVERSTD规则类型 | 提交JSON、最终答案 |
| 3 | `anomaly-type-count-count` | 结论 | 规则 | 发现数量为1 | 1 | 已提交发现数量恰好为1 | 提交JSON、最终答案 |
| 4 | `record-set-include-r004223` | 证据 | 规则 | 结果包含应核查记录 R004223 | R004223 | 提交的record_ids包含R004223 | 提交JSON、工具轨迹 |
| 5 | `record-set-no-extra` | 证据 | 规则 | 结果不包含本题范围外的记录 | ["R004223"] | 提交的record_ids除R004223外没有其他记录 | 提交JSON、工具轨迹 |
| 6 | `policy-basis-expense` | 制度 | 规则/LLM Judge | 引用费用报销办法第十二条 | 01_expense_reimbursement_2025.md#第十二条 | 引用超标准总则条款 | 提交JSON、工具轨迹 |
| 7 | `policy-basis-training` | 制度 | 规则/LLM Judge | 引用培训费管理办法第二条 | 05_training_expense.md#第二条 | 引用3500元培训课程费标准 | 提交JSON、工具轨迹 |
| 8 | `case-reasoning-type` | 推理 | 规则/LLM Judge | 说明费用类型为training_fee | training_fee | 费用类型识别正确 | 最终答案、工具轨迹、工作区产物 |
| 9 | `case-reasoning-amount` | 推理 | 规则/LLM Judge | 说明报销金额为3700元 | 3700 | 报销金额识别正确 | 最终答案、工具轨迹、工作区产物 |
| 10 | `case-reasoning-limit` | 推理 | 规则/LLM Judge | 说明培训课程费标准为3500元且本笔超标 | 3500 | 标准及超标比较均正确 | 最终答案、工具轨迹、工作区产物 |
| 11 | `submission` | 格式 | 规则 | 统一Schema结果提交成功 | submission_receipt.status=accepted | 提交回执状态为accepted且Schema校验通过 | 提交JSON |

---

## 7. L3-001

- **题型**：全年专项审计
- **难度**：`L3`
- **类别**：`full_year_rule_audit`
- **选题目的**：全年重复报销扫描，验证完整召回
- **Checklist数量**：27项

### 题目

> 请对全年数据做重复报销专项扫描，按重复发票组生成稳定的发现ID，返回全部发现ID和关联record_id集合，并说明全量扫描方法和制度依据。

### 标准答案边界

以下内容仅供判卷和复核，不应暴露给候选智能体。

```json
{
  "scoring_kind": "finding_type_count",
  "expected_record_ids": [
    "R000002",
    "R000005",
    "R000020",
    "R000028",
    "R000037",
    "R000055",
    "R004201",
    "R004202",
    "R004203",
    "R004204",
    "R004205",
    "R004206"
  ],
  "expected_findings_by_type": {
    "DUP": 6
  },
  "expected_anomaly_count": 6,
  "expected_finding_groups": [
    {
      "rule_type": "DUP",
      "record_ids": [
        "R000002",
        "R004201"
      ]
    },
    {
      "rule_type": "DUP",
      "record_ids": [
        "R000005",
        "R004202"
      ]
    },
    {
      "rule_type": "DUP",
      "record_ids": [
        "R000020",
        "R004203"
      ]
    },
    {
      "rule_type": "DUP",
      "record_ids": [
        "R000028",
        "R004204"
      ]
    },
    {
      "rule_type": "DUP",
      "record_ids": [
        "R000037",
        "R004205"
      ]
    },
    {
      "rule_type": "DUP",
      "record_ids": [
        "R000055",
        "R004206"
      ]
    }
  ],
  "required_citations": [
    {
      "doc_id": "01_expense_reimbursement_2025.md",
      "clause_no": "第十条"
    }
  ]
}
```

### Checklist Rubric

| # | 检查项ID | 维度 | 判定方式 | 检查内容 | 预期 | 通过条件 | 证据来源 |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | `finding-type-count-rule-type` | 结论 | 规则 | 发现类型为DUP | DUP | 全部已提交发现均归属于DUP规则类型 | 提交JSON、最终答案 |
| 2 | `finding-type-count-count` | 结论 | 规则 | 发现数量为6 | 6 | 已提交发现数量恰好为6 | 提交JSON、最终答案 |
| 3 | `all-record-ids-include-r000002` | 证据 | 规则 | 结果包含应核查记录 R000002 | R000002 | 提交的record_ids包含R000002 | 提交JSON、工具轨迹 |
| 4 | `all-record-ids-include-r000005` | 证据 | 规则 | 结果包含应核查记录 R000005 | R000005 | 提交的record_ids包含R000005 | 提交JSON、工具轨迹 |
| 5 | `all-record-ids-include-r000020` | 证据 | 规则 | 结果包含应核查记录 R000020 | R000020 | 提交的record_ids包含R000020 | 提交JSON、工具轨迹 |
| 6 | `all-record-ids-include-r000028` | 证据 | 规则 | 结果包含应核查记录 R000028 | R000028 | 提交的record_ids包含R000028 | 提交JSON、工具轨迹 |
| 7 | `all-record-ids-include-r000037` | 证据 | 规则 | 结果包含应核查记录 R000037 | R000037 | 提交的record_ids包含R000037 | 提交JSON、工具轨迹 |
| 8 | `all-record-ids-include-r000055` | 证据 | 规则 | 结果包含应核查记录 R000055 | R000055 | 提交的record_ids包含R000055 | 提交JSON、工具轨迹 |
| 9 | `all-record-ids-include-r004201` | 证据 | 规则 | 结果包含应核查记录 R004201 | R004201 | 提交的record_ids包含R004201 | 提交JSON、工具轨迹 |
| 10 | `all-record-ids-include-r004202` | 证据 | 规则 | 结果包含应核查记录 R004202 | R004202 | 提交的record_ids包含R004202 | 提交JSON、工具轨迹 |
| 11 | `all-record-ids-include-r004203` | 证据 | 规则 | 结果包含应核查记录 R004203 | R004203 | 提交的record_ids包含R004203 | 提交JSON、工具轨迹 |
| 12 | `all-record-ids-include-r004204` | 证据 | 规则 | 结果包含应核查记录 R004204 | R004204 | 提交的record_ids包含R004204 | 提交JSON、工具轨迹 |
| 13 | `all-record-ids-include-r004205` | 证据 | 规则 | 结果包含应核查记录 R004205 | R004205 | 提交的record_ids包含R004205 | 提交JSON、工具轨迹 |
| 14 | `all-record-ids-include-r004206` | 证据 | 规则 | 结果包含应核查记录 R004206 | R004206 | 提交的record_ids包含R004206 | 提交JSON、工具轨迹 |
| 15 | `all-record-ids-no-extra` | 证据 | 规则 | 结果不包含本题范围外的记录 | ["R000002","R000005","R000020","R000028","R000037","R000055","R004201","R004202","R004203","R004204","R004205","R004206"] | 提交的record_ids除R000002, R000005, R000020, R000028, R000037, R000055, R004201, R004202, R004203, R004204, R004205, R004206外没有其他记录 | 提交JSON、工具轨迹 |
| 16 | `finding-record-mapping-group-1` | 证据 | 规则/LLM Judge | 核对发现记录分组R000002, R004201 | {"rule_type":"DUP","record_ids":["R000002","R004201"]} | 记录R000002, R004201属于同一项发现 | 最终答案、工作区产物、工具轨迹 |
| 17 | `finding-record-mapping-group-2` | 证据 | 规则/LLM Judge | 核对发现记录分组R000005, R004202 | {"rule_type":"DUP","record_ids":["R000005","R004202"]} | 记录R000005, R004202属于同一项发现 | 最终答案、工作区产物、工具轨迹 |
| 18 | `finding-record-mapping-group-3` | 证据 | 规则/LLM Judge | 核对发现记录分组R000020, R004203 | {"rule_type":"DUP","record_ids":["R000020","R004203"]} | 记录R000020, R004203属于同一项发现 | 最终答案、工作区产物、工具轨迹 |
| 19 | `finding-record-mapping-group-4` | 证据 | 规则/LLM Judge | 核对发现记录分组R000028, R004204 | {"rule_type":"DUP","record_ids":["R000028","R004204"]} | 记录R000028, R004204属于同一项发现 | 最终答案、工作区产物、工具轨迹 |
| 20 | `finding-record-mapping-group-5` | 证据 | 规则/LLM Judge | 核对发现记录分组R000037, R004205 | {"rule_type":"DUP","record_ids":["R000037","R004205"]} | 记录R000037, R004205属于同一项发现 | 最终答案、工作区产物、工具轨迹 |
| 21 | `finding-record-mapping-group-6` | 证据 | 规则/LLM Judge | 核对发现记录分组R000055, R004206 | {"rule_type":"DUP","record_ids":["R000055","R004206"]} | 记录R000055, R004206属于同一项发现 | 最终答案、工作区产物、工具轨迹 |
| 22 | `full-scan-method-scope` | 推理 | 规则/LLM Judge | 轨迹证明查询覆盖全年全部记录 | 全年范围 | 查询或脚本覆盖完整年度而非抽样记录 | 工具轨迹、工作区产物 |
| 23 | `full-scan-method-invoice-key` | 推理 | 规则/LLM Judge | 按invoice_id识别重复使用的发票 | invoice_id | 查询或脚本以invoice_id作为重复判断键 | 工具轨迹、工作区产物 |
| 24 | `full-scan-method-grouping` | 推理 | 规则/LLM Judge | 每个重复发票组形成一项发现 | 每个重复invoice_id一项发现 | 重复记录按发票分组且每组只形成一项发现 | 工具轨迹、工作区产物 |
| 25 | `full-scan-method-reconcile` | 推理 | 规则/LLM Judge | 查询结果与最终提交数量能够核对一致 | 6 | 中间统计为6组且与最终6项发现一致 | 工具轨迹、工作区产物 |
| 26 | `policy-basis` | 制度 | 规则/LLM Judge | 制度依据：引用01_expense_reimbursement_2025.md 第十条并将规则落实到查询条件 | 01_expense_reimbursement_2025.md 第十条 | 条款和查询条件对应 | 提交JSON、工具轨迹 |
| 27 | `submission` | 格式 | 规则 | 统一Schema结果提交成功 | submission_receipt.status=accepted | 提交回执状态为accepted且Schema校验通过 | 提交JSON |

---

## 8. L3-003

- **题型**：全年专项审计
- **难度**：`L3`
- **类别**：`full_year_rule_audit`
- **选题目的**：全年超标准扫描，验证多费用类型标准
- **Checklist数量**：27项

### 题目

> 请对全年数据做单笔或单次即可确认的超标准专项扫描，返回全部发现ID和关联record_id集合，并说明各费用类型的计算口径、全量扫描方法和制度依据。办公用品和通讯费用本题只识别单笔自身已经超过月度上限的明确异常，不评价多笔记录的月度累计超限。

### 标准答案边界

以下内容仅供判卷和复核，不应暴露给候选智能体。

```json
{
  "scoring_kind": "finding_type_count",
  "expected_record_ids": [
    "R004221",
    "R004222",
    "R004223",
    "R004224",
    "R004225",
    "R004226"
  ],
  "expected_findings_by_type": {
    "OVERSTD": 6
  },
  "expected_anomaly_count": 6,
  "expected_finding_groups": [
    {
      "rule_type": "OVERSTD",
      "record_ids": [
        "R004221"
      ]
    },
    {
      "rule_type": "OVERSTD",
      "record_ids": [
        "R004222"
      ]
    },
    {
      "rule_type": "OVERSTD",
      "record_ids": [
        "R004223"
      ]
    },
    {
      "rule_type": "OVERSTD",
      "record_ids": [
        "R004224"
      ]
    },
    {
      "rule_type": "OVERSTD",
      "record_ids": [
        "R004225"
      ]
    },
    {
      "rule_type": "OVERSTD",
      "record_ids": [
        "R004226"
      ]
    }
  ],
  "required_citations": [
    {
      "doc_id": "01_expense_reimbursement_2025.md",
      "clause_no": "第十二条"
    },
    {
      "doc_id": "04_travel_expense.md",
      "clause_no": "第三条至第六条"
    },
    {
      "doc_id": "05_training_expense.md",
      "clause_no": "第二条至第五条"
    },
    {
      "doc_id": "06_business_entertainment.md",
      "clause_no": "第二条、第三条"
    },
    {
      "doc_id": "07_office_communication.md",
      "clause_no": "第二条、第三条"
    }
  ]
}
```

### Checklist Rubric

| # | 检查项ID | 维度 | 判定方式 | 检查内容 | 预期 | 通过条件 | 证据来源 |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | `finding-type-count-rule-type` | 结论 | 规则 | 发现类型为OVERSTD | OVERSTD | 全部已提交发现均归属于OVERSTD规则类型 | 提交JSON、最终答案 |
| 2 | `finding-type-count-count` | 结论 | 规则 | 发现数量为6 | 6 | 已提交发现数量恰好为6 | 提交JSON、最终答案 |
| 3 | `all-record-ids-include-r004221` | 证据 | 规则 | 结果包含应核查记录 R004221 | R004221 | 提交的record_ids包含R004221 | 提交JSON、工具轨迹 |
| 4 | `all-record-ids-include-r004222` | 证据 | 规则 | 结果包含应核查记录 R004222 | R004222 | 提交的record_ids包含R004222 | 提交JSON、工具轨迹 |
| 5 | `all-record-ids-include-r004223` | 证据 | 规则 | 结果包含应核查记录 R004223 | R004223 | 提交的record_ids包含R004223 | 提交JSON、工具轨迹 |
| 6 | `all-record-ids-include-r004224` | 证据 | 规则 | 结果包含应核查记录 R004224 | R004224 | 提交的record_ids包含R004224 | 提交JSON、工具轨迹 |
| 7 | `all-record-ids-include-r004225` | 证据 | 规则 | 结果包含应核查记录 R004225 | R004225 | 提交的record_ids包含R004225 | 提交JSON、工具轨迹 |
| 8 | `all-record-ids-include-r004226` | 证据 | 规则 | 结果包含应核查记录 R004226 | R004226 | 提交的record_ids包含R004226 | 提交JSON、工具轨迹 |
| 9 | `all-record-ids-no-extra` | 证据 | 规则 | 结果不包含本题范围外的记录 | ["R004221","R004222","R004223","R004224","R004225","R004226"] | 提交的record_ids除R004221, R004222, R004223, R004224, R004225, R004226外没有其他记录 | 提交JSON、工具轨迹 |
| 10 | `finding-record-mapping-group-1` | 证据 | 规则/LLM Judge | 核对发现记录分组R004221 | {"rule_type":"OVERSTD","record_ids":["R004221"]} | 记录R004221属于同一项发现 | 最终答案、工作区产物、工具轨迹 |
| 11 | `finding-record-mapping-group-2` | 证据 | 规则/LLM Judge | 核对发现记录分组R004222 | {"rule_type":"OVERSTD","record_ids":["R004222"]} | 记录R004222属于同一项发现 | 最终答案、工作区产物、工具轨迹 |
| 12 | `finding-record-mapping-group-3` | 证据 | 规则/LLM Judge | 核对发现记录分组R004223 | {"rule_type":"OVERSTD","record_ids":["R004223"]} | 记录R004223属于同一项发现 | 最终答案、工作区产物、工具轨迹 |
| 13 | `finding-record-mapping-group-4` | 证据 | 规则/LLM Judge | 核对发现记录分组R004224 | {"rule_type":"OVERSTD","record_ids":["R004224"]} | 记录R004224属于同一项发现 | 最终答案、工作区产物、工具轨迹 |
| 14 | `finding-record-mapping-group-5` | 证据 | 规则/LLM Judge | 核对发现记录分组R004225 | {"rule_type":"OVERSTD","record_ids":["R004225"]} | 记录R004225属于同一项发现 | 最终答案、工作区产物、工具轨迹 |
| 15 | `finding-record-mapping-group-6` | 证据 | 规则/LLM Judge | 核对发现记录分组R004226 | {"rule_type":"OVERSTD","record_ids":["R004226"]} | 记录R004226属于同一项发现 | 最终答案、工作区产物、工具轨迹 |
| 16 | `full-scan-method-scope` | 推理 | 规则/LLM Judge | 轨迹证明查询覆盖全年全部记录 | 全年范围 | 查询或脚本覆盖完整年度而非抽样记录 | 工具轨迹、工作区产物 |
| 17 | `full-scan-method-approval` | 推理 | 规则/LLM Judge | 超标准判断排除已有专项审批的记录 | special_approval=0 | 查询或脚本仅将无专项审批的超标准记录计为异常 | 工具轨迹、工作区产物 |
| 18 | `full-scan-method-office` | 推理 | 规则/LLM Judge | 办公用品按单笔600元口径核查 | 600 | 办公用品仅在单笔金额超过600元时计入 | 工具轨迹、工作区产物 |
| 19 | `full-scan-method-communication` | 推理 | 规则/LLM Judge | 通讯费用按单笔300元口径核查 | 300 | 通讯费用仅在单笔金额超过300元时计入 | 工具轨迹、工作区产物 |
| 20 | `full-scan-method-training` | 推理 | 规则/LLM Judge | 培训课程费按单次3500元口径核查 | 3500 | 培训课程费仅在单次金额超过3500元时计入 | 工具轨迹、工作区产物 |
| 21 | `full-scan-method-entertainment` | 推理 | 规则/LLM Judge | 业务招待费同时核查单次和人均标准 | [5000,300] | 业务招待费按单次5000元和人均300元两个标准核查 | 工具轨迹、工作区产物 |
| 22 | `full-scan-method-travel` | 推理 | 规则/LLM Judge | 差旅住宿按职级、城市和晚数计算 | 职级×城市档位×晚数 | 差旅住宿标准同时使用员工职级、城市档位和住宿晚数 | 工具轨迹、工作区产物 |
| 23 | `full-scan-method-transport` | 推理 | 规则/LLM Judge | 市内交通按城市和天数计算 | 城市档位×天数 | 市内交通标准同时使用城市档位和出差天数 | 工具轨迹、工作区产物 |
| 24 | `full-scan-method-reconcile` | 推理 | 规则/LLM Judge | 查询结果与最终提交数量能够核对一致 | 6 | 中间统计为6条且与最终6项发现一致 | 工具轨迹、工作区产物 |
| 25 | `policy-basis-expense` | 制度 | 规则/LLM Judge | 引用费用报销办法第十二条 | 01_expense_reimbursement_2025.md#第十二条 | 引用超标准总则条款 | 提交JSON、工具轨迹 |
| 26 | `policy-basis-special` | 制度 | 规则/LLM Judge | 引用各费用类型对应的专项标准 | 04至07号专项费用标准 | 专项标准与查询条件对应 | 提交JSON、工具轨迹 |
| 27 | `submission` | 格式 | 规则 | 统一Schema结果提交成功 | submission_receipt.status=accepted | 提交回执状态为accepted且Schema校验通过 | 提交JSON |

---

## 9. L3-004

- **题型**：全年专项审计
- **难度**：`L3`
- **类别**：`full_year_rule_audit`
- **选题目的**：全年超预算扫描，验证部门聚合
- **Checklist数量**：24项

### 题目

> 请对全年数据做超预算专项扫描。按reimburse_date和record_id依次累计部门已批准费用，每个超预算部门形成1项发现，以首次使累计支出超过年度预算且无专项审批的记录作为关键record_id。请返回全部发现ID和关键record_id集合，并说明计算方法和制度依据。

### 标准答案边界

以下内容仅供判卷和复核，不应暴露给候选智能体。

```json
{
  "scoring_kind": "finding_type_count",
  "expected_record_ids": [
    "R000079",
    "R000312",
    "R000894",
    "R002009",
    "R003479",
    "R003968"
  ],
  "expected_findings_by_type": {
    "BUDGET": 6
  },
  "expected_anomaly_count": 6,
  "expected_finding_groups": [
    {
      "rule_type": "BUDGET",
      "record_ids": [
        "R000079"
      ],
      "department_id": "D001"
    },
    {
      "rule_type": "BUDGET",
      "record_ids": [
        "R002009"
      ],
      "department_id": "D002"
    },
    {
      "rule_type": "BUDGET",
      "record_ids": [
        "R003968"
      ],
      "department_id": "D003"
    },
    {
      "rule_type": "BUDGET",
      "record_ids": [
        "R000894"
      ],
      "department_id": "D004"
    },
    {
      "rule_type": "BUDGET",
      "record_ids": [
        "R003479"
      ],
      "department_id": "D005"
    },
    {
      "rule_type": "BUDGET",
      "record_ids": [
        "R000312"
      ],
      "department_id": "D006"
    }
  ],
  "required_citations": [
    {
      "doc_id": "01_expense_reimbursement_2025.md",
      "clause_no": "第十三条"
    },
    {
      "doc_id": "08_budget_management.md",
      "clause_no": "第二条至第四条"
    }
  ]
}
```

### Checklist Rubric

| # | 检查项ID | 维度 | 判定方式 | 检查内容 | 预期 | 通过条件 | 证据来源 |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | `finding-type-count-rule-type` | 结论 | 规则 | 发现类型为BUDGET | BUDGET | 全部已提交发现均归属于BUDGET规则类型 | 提交JSON、最终答案 |
| 2 | `finding-type-count-count` | 结论 | 规则 | 发现数量为6 | 6 | 已提交发现数量恰好为6 | 提交JSON、最终答案 |
| 3 | `all-record-ids-include-r000079` | 证据 | 规则 | 结果包含应核查记录 R000079 | R000079 | 提交的record_ids包含R000079 | 提交JSON、工具轨迹 |
| 4 | `all-record-ids-include-r000312` | 证据 | 规则 | 结果包含应核查记录 R000312 | R000312 | 提交的record_ids包含R000312 | 提交JSON、工具轨迹 |
| 5 | `all-record-ids-include-r000894` | 证据 | 规则 | 结果包含应核查记录 R000894 | R000894 | 提交的record_ids包含R000894 | 提交JSON、工具轨迹 |
| 6 | `all-record-ids-include-r002009` | 证据 | 规则 | 结果包含应核查记录 R002009 | R002009 | 提交的record_ids包含R002009 | 提交JSON、工具轨迹 |
| 7 | `all-record-ids-include-r003479` | 证据 | 规则 | 结果包含应核查记录 R003479 | R003479 | 提交的record_ids包含R003479 | 提交JSON、工具轨迹 |
| 8 | `all-record-ids-include-r003968` | 证据 | 规则 | 结果包含应核查记录 R003968 | R003968 | 提交的record_ids包含R003968 | 提交JSON、工具轨迹 |
| 9 | `all-record-ids-no-extra` | 证据 | 规则 | 结果不包含本题范围外的记录 | ["R000079","R000312","R000894","R002009","R003479","R003968"] | 提交的record_ids除R000079, R000312, R000894, R002009, R003479, R003968外没有其他记录 | 提交JSON、工具轨迹 |
| 10 | `finding-record-mapping-group-1` | 证据 | 规则/LLM Judge | 核对D001部门的关键记录R000079 | {"rule_type":"BUDGET","record_ids":["R000079"],"department_id":"D001"} | D001部门与关键记录R000079对应正确 | 最终答案、工作区产物、工具轨迹 |
| 11 | `finding-record-mapping-group-2` | 证据 | 规则/LLM Judge | 核对D002部门的关键记录R002009 | {"rule_type":"BUDGET","record_ids":["R002009"],"department_id":"D002"} | D002部门与关键记录R002009对应正确 | 最终答案、工作区产物、工具轨迹 |
| 12 | `finding-record-mapping-group-3` | 证据 | 规则/LLM Judge | 核对D003部门的关键记录R003968 | {"rule_type":"BUDGET","record_ids":["R003968"],"department_id":"D003"} | D003部门与关键记录R003968对应正确 | 最终答案、工作区产物、工具轨迹 |
| 13 | `finding-record-mapping-group-4` | 证据 | 规则/LLM Judge | 核对D004部门的关键记录R000894 | {"rule_type":"BUDGET","record_ids":["R000894"],"department_id":"D004"} | D004部门与关键记录R000894对应正确 | 最终答案、工作区产物、工具轨迹 |
| 14 | `finding-record-mapping-group-5` | 证据 | 规则/LLM Judge | 核对D005部门的关键记录R003479 | {"rule_type":"BUDGET","record_ids":["R003479"],"department_id":"D005"} | D005部门与关键记录R003479对应正确 | 最终答案、工作区产物、工具轨迹 |
| 15 | `finding-record-mapping-group-6` | 证据 | 规则/LLM Judge | 核对D006部门的关键记录R000312 | {"rule_type":"BUDGET","record_ids":["R000312"],"department_id":"D006"} | D006部门与关键记录R000312对应正确 | 最终答案、工作区产物、工具轨迹 |
| 16 | `full-scan-method-scope` | 推理 | 规则/LLM Judge | 轨迹证明按部门覆盖全年预算执行记录 | 全年范围 | 查询或脚本覆盖全部部门的年度记录而非抽样部门 | 工具轨迹、工作区产物 |
| 17 | `full-scan-method-grouping` | 推理 | 规则/LLM Judge | 费用按department_id分别累计 | department_id | 累计计算以department_id分组 | 工具轨迹、工作区产物 |
| 18 | `full-scan-method-ordering` | 推理 | 规则/LLM Judge | 部门内按reimburse_date和record_id稳定排序 | ["reimburse_date","record_id"] | 累计顺序先按reimburse_date再按record_id | 工具轨迹、工作区产物 |
| 19 | `full-scan-method-cumulative` | 推理 | 规则/LLM Judge | 逐笔累计已批准费用amount | 累计amount | 每条关键记录的报销前后累计金额可复核 | 工具轨迹、工作区产物 |
| 20 | `full-scan-method-crossing` | 推理 | 规则/LLM Judge | 选择累计首次超预算且无专项审批的记录 | cumulative>annual_budget且special_approval=0 | 关键记录同时满足累计超过年度预算和无专项审批 | 工具轨迹、工作区产物 |
| 21 | `full-scan-method-reconcile` | 推理 | 规则/LLM Judge | 每个超预算部门一项且数量与提交一致 | 6 | 中间统计为6个部门且与最终6项发现一致 | 工具轨迹、工作区产物 |
| 22 | `policy-basis-expense` | 制度 | 规则/LLM Judge | 引用费用报销办法第十三条 | 01_expense_reimbursement_2025.md#第十三条 | 引用超预算总则条款 | 提交JSON、工具轨迹 |
| 23 | `policy-basis-budget` | 制度 | 规则/LLM Judge | 引用预算管理办法第二至第四条 | 08_budget_management.md#第二条至第四条 | 引用预算约束及专项审批条款 | 提交JSON、工具轨迹 |
| 24 | `submission` | 格式 | 规则 | 统一Schema结果提交成功 | submission_receipt.status=accepted | 提交回执状态为accepted且Schema校验通过 | 提交JSON |

---

## 10. TRAP-002

- **题型**：无异常及陷阱题
- **难度**：`trap`
- **类别**：`clean_but_suspicious`
- **选题目的**：同组记录但发票不同且合计未越线
- **Checklist数量**：14项

### 题目

> 请核查R004234和R004235是否构成重复报销或拆分报销。必须核对发票是否相同及7天内合计金额；若不构成异常，请明确说明无异常、原因和制度依据。

### 标准答案边界

以下内容仅供判卷和复核，不应暴露给候选智能体。

```json
{
  "scoring_kind": "no_anomaly",
  "expected_record_ids": [
    "R004234",
    "R004235"
  ],
  "expected_reason": "两条记录发票不同，且同一员工同类费用7天内合计500元，未达到10000元审批线",
  "expected_anomaly_ids": [],
  "required_citations": [
    {
      "doc_id": "01_expense_reimbursement_2025.md",
      "clause_no": "第十条、第十一条"
    },
    {
      "doc_id": "03_authorization_management.md",
      "clause_no": "附件二"
    }
  ]
}
```

### Checklist Rubric

| # | 检查项ID | 维度 | 判定方式 | 检查内容 | 预期 | 通过条件 | 证据来源 |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | `clean-conclusion` | 结论 | 规则/LLM Judge | 无异常结论：明确判断本题记录不构成异常 | {"anomaly_ids":[],"conclusion":"无异常"} | 明确无异常且无矛盾表述 | 最终答案、提交JSON |
| 2 | `record-scope-include-r004234` | 证据 | 规则 | 结果包含应核查记录 R004234 | R004234 | 提交的record_ids包含R004234 | 提交JSON、工具轨迹 |
| 3 | `record-scope-include-r004235` | 证据 | 规则 | 结果包含应核查记录 R004235 | R004235 | 提交的record_ids包含R004235 | 提交JSON、工具轨迹 |
| 4 | `record-scope-no-extra` | 证据 | 规则 | 结果不包含本题范围外的记录 | ["R004234","R004235"] | 提交的record_ids除R004234, R004235外没有其他记录 | 提交JSON、工具轨迹 |
| 5 | `case-specific-reason-invoice` | 推理 | 规则/LLM Judge | 说明两条记录发票不同 | 发票不同 | 准确说明不构成重复发票 | 最终答案、工具轨迹 |
| 6 | `case-specific-reason-sum` | 推理 | 规则/LLM Judge | 说明7天内合计金额为500元 | 500 | 准确计算7天内合计500元 | 最终答案、工具轨迹 |
| 7 | `case-specific-reason-threshold` | 推理 | 规则/LLM Judge | 说明500元未达到10000元审批线 | 10000 | 正确比较合计金额与审批线 | 最终答案、工具轨迹 |
| 8 | `reverse-check-invoice` | 误报控制 | 规则/LLM Judge | 轨迹中独立核验：说明两条记录发票不同 | 发票不同 | 工具轨迹或工作产物包含数据来源或计算过程，并证明准确说明不构成重复发票 | 工具轨迹、工作区产物 |
| 9 | `reverse-check-sum` | 误报控制 | 规则/LLM Judge | 轨迹中独立核验：说明7天内合计金额为500元 | 500 | 工具轨迹或工作产物包含数据来源或计算过程，并证明准确计算7天内合计500元 | 工具轨迹、工作区产物 |
| 10 | `reverse-check-threshold` | 误报控制 | 规则/LLM Judge | 轨迹中独立核验：说明500元未达到10000元审批线 | 10000 | 工具轨迹或工作产物包含数据来源或计算过程，并证明正确比较合计金额与审批线 | 工具轨迹、工作区产物 |
| 11 | `policy-basis-source-1` | 制度 | 规则/LLM Judge | 引用本题所需制度依据：01_expense_reimbursement_2025.md#第十条、第十一条 | {"doc_id":"01_expense_reimbursement_2025.md","clause_no":"第十条、第十一条"} | 准确引用01_expense_reimbursement_2025.md#第十条、第十一条 | 提交JSON、工具轨迹 |
| 12 | `policy-basis-source-2` | 制度 | 规则/LLM Judge | 引用本题所需制度依据：03_authorization_management.md#附件二 | {"doc_id":"03_authorization_management.md","clause_no":"附件二"} | 准确引用03_authorization_management.md#附件二 | 提交JSON、工具轨迹 |
| 13 | `no-unsupported-output` | 误报控制 | 规则 | 结构化结果不提交任何异常ID | {"anomaly_ids":[]} | anomaly_ids为空 | 提交JSON |
| 14 | `submission` | 格式 | 规则 | 统一Schema结果提交成功 | submission_receipt.status=accepted | 提交回执状态为accepted且Schema校验通过 | 提交JSON |

---

## 11. TRAP-003

- **题型**：无异常及陷阱题
- **难度**：`trap`
- **类别**：`clean_but_suspicious`
- **选题目的**：超过聚合时间窗，验证窗口边界
- **Checklist数量**：16项

### 题目

> 请核查R004236和R004237是否构成7天内拆分报销。必须按费用发生日期计算间隔并核对合计金额；若不构成异常，请明确说明无异常、原因和制度依据。

### 标准答案边界

以下内容仅供判卷和复核，不应暴露给候选智能体。

```json
{
  "scoring_kind": "no_anomaly",
  "expected_record_ids": [
    "R004236",
    "R004237"
  ],
  "expected_reason": "两条记录合计10400元，虽达到10000元审批线，但费用发生日期相隔8天，超出7天聚合窗口",
  "expected_anomaly_ids": [],
  "required_citations": [
    {
      "doc_id": "01_expense_reimbursement_2025.md",
      "clause_no": "第十一条"
    },
    {
      "doc_id": "03_authorization_management.md",
      "clause_no": "附件二"
    }
  ]
}
```

### Checklist Rubric

| # | 检查项ID | 维度 | 判定方式 | 检查内容 | 预期 | 通过条件 | 证据来源 |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | `clean-conclusion` | 结论 | 规则/LLM Judge | 无异常结论：明确判断本题记录不构成异常 | {"anomaly_ids":[],"conclusion":"无异常"} | 明确无异常且无矛盾表述 | 最终答案、提交JSON |
| 2 | `record-scope-include-r004236` | 证据 | 规则 | 结果包含应核查记录 R004236 | R004236 | 提交的record_ids包含R004236 | 提交JSON、工具轨迹 |
| 3 | `record-scope-include-r004237` | 证据 | 规则 | 结果包含应核查记录 R004237 | R004237 | 提交的record_ids包含R004237 | 提交JSON、工具轨迹 |
| 4 | `record-scope-no-extra` | 证据 | 规则 | 结果不包含本题范围外的记录 | ["R004236","R004237"] | 提交的record_ids除R004236, R004237外没有其他记录 | 提交JSON、工具轨迹 |
| 5 | `case-specific-reason-gap` | 推理 | 规则/LLM Judge | 说明两条费用发生日期相隔8天 | 8 | 日期间隔计算为8天 | 最终答案、工具轨迹 |
| 6 | `case-specific-reason-window` | 推理 | 规则/LLM Judge | 说明8天超出7天聚合窗口 | 7 | 正确应用7天窗口边界 | 最终答案、工具轨迹 |
| 7 | `case-specific-reason-sum` | 推理 | 规则/LLM Judge | 说明两条记录合计金额为10400元 | 10400 | 准确计算合计金额10400元 | 最终答案、工具轨迹 |
| 8 | `case-specific-reason-threshold` | 推理 | 规则/LLM Judge | 说明10400元虽达到10000元审批线但因超窗不构成拆分 | 10000 | 正确说明金额条件满足但时间窗口条件不满足 | 最终答案、工具轨迹 |
| 9 | `reverse-check-gap` | 误报控制 | 规则/LLM Judge | 轨迹中独立核验：说明两条费用发生日期相隔8天 | 8 | 工具轨迹或工作产物包含数据来源或计算过程，并证明日期间隔计算为8天 | 工具轨迹、工作区产物 |
| 10 | `reverse-check-window` | 误报控制 | 规则/LLM Judge | 轨迹中独立核验：说明8天超出7天聚合窗口 | 7 | 工具轨迹或工作产物包含数据来源或计算过程，并证明正确应用7天窗口边界 | 工具轨迹、工作区产物 |
| 11 | `reverse-check-sum` | 误报控制 | 规则/LLM Judge | 轨迹中独立核验：说明两条记录合计金额为10400元 | 10400 | 工具轨迹或工作产物包含数据来源或计算过程，并证明准确计算合计金额10400元 | 工具轨迹、工作区产物 |
| 12 | `reverse-check-threshold` | 误报控制 | 规则/LLM Judge | 轨迹中独立核验：说明10400元虽达到10000元审批线但因超窗不构成拆分 | 10000 | 工具轨迹或工作产物包含数据来源或计算过程，并证明正确说明金额条件满足但时间窗口条件不满足 | 工具轨迹、工作区产物 |
| 13 | `policy-basis-source-1` | 制度 | 规则/LLM Judge | 引用本题所需制度依据：01_expense_reimbursement_2025.md#第十一条 | {"doc_id":"01_expense_reimbursement_2025.md","clause_no":"第十一条"} | 准确引用01_expense_reimbursement_2025.md#第十一条 | 提交JSON、工具轨迹 |
| 14 | `policy-basis-source-2` | 制度 | 规则/LLM Judge | 引用本题所需制度依据：03_authorization_management.md#附件二 | {"doc_id":"03_authorization_management.md","clause_no":"附件二"} | 准确引用03_authorization_management.md#附件二 | 提交JSON、工具轨迹 |
| 15 | `no-unsupported-output` | 误报控制 | 规则 | 结构化结果不提交任何异常ID | {"anomaly_ids":[]} | anomaly_ids为空 | 提交JSON |
| 16 | `submission` | 格式 | 规则 | 统一Schema结果提交成功 | submission_receipt.status=accepted | 提交回执状态为accepted且Schema校验通过 | 提交JSON |

---

## 12. TRAP-005

- **题型**：无异常及陷阱题
- **难度**：`trap`
- **类别**：`clean_but_suspicious`
- **选题目的**：多条件均合规，验证综合反向复核
- **Checklist数量**：25项

### 题目

> 请核查R004239和R004240是否构成重复报销、拆分报销或业务招待费超标准。必须核对发票、日期、单次金额和人均金额；若不构成异常，请明确说明无异常、原因和制度依据。

### 标准答案边界

以下内容仅供判卷和复核，不应暴露给候选智能体。

```json
{
  "scoring_kind": "no_anomaly",
  "expected_record_ids": [
    "R004239",
    "R004240"
  ],
  "expected_reason": "两条记录分别对应客户甲产品方案交流和客户乙投行业务沟通，费用发生日期相隔1天；发票不同，单次金额分别为540元和545元、各3人，人均分别为180元和约181.67元，均未超过单次5000元和人均300元标准，合计也未达到10000元审批线",
  "expected_anomaly_ids": [],
  "required_citations": [
    {
      "doc_id": "01_expense_reimbursement_2025.md",
      "clause_no": "第十条、第十一条"
    },
    {
      "doc_id": "06_business_entertainment.md",
      "clause_no": "第二条至第四条"
    },
    {
      "doc_id": "03_authorization_management.md",
      "clause_no": "附件二"
    }
  ]
}
```

### Checklist Rubric

| # | 检查项ID | 维度 | 判定方式 | 检查内容 | 预期 | 通过条件 | 证据来源 |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | `clean-conclusion` | 结论 | 规则/LLM Judge | 无异常结论：明确判断本题记录不构成异常 | {"anomaly_ids":[],"conclusion":"无异常"} | 明确无异常且无矛盾表述 | 最终答案、提交JSON |
| 2 | `record-scope-include-r004239` | 证据 | 规则 | 结果包含应核查记录 R004239 | R004239 | 提交的record_ids包含R004239 | 提交JSON、工具轨迹 |
| 3 | `record-scope-include-r004240` | 证据 | 规则 | 结果包含应核查记录 R004240 | R004240 | 提交的record_ids包含R004240 | 提交JSON、工具轨迹 |
| 4 | `record-scope-no-extra` | 证据 | 规则 | 结果不包含本题范围外的记录 | ["R004239","R004240"] | 提交的record_ids除R004239, R004240外没有其他记录 | 提交JSON、工具轨迹 |
| 5 | `case-specific-reason-business-context` | 推理 | 规则/LLM Judge | 说明两条记录对应不同客户和不同业务事项 | ["客户甲产品方案交流","客户乙投行业务沟通"] | 准确区分两次独立业务活动 | 最终答案、工具轨迹 |
| 6 | `case-specific-reason-date-window` | 推理 | 规则/LLM Judge | 说明两条费用发生日期相隔1天并完成窗口核查 | 1 | 准确核对日期间隔及7天窗口 | 最终答案、工具轨迹 |
| 7 | `case-specific-reason-invoice` | 推理 | 规则/LLM Judge | 说明两条记录发票不同 | 发票不同 | 准确排除重复发票 | 最终答案、工具轨迹 |
| 8 | `case-specific-reason-amounts` | 推理 | 规则/LLM Judge | 给出单次金额540元和545元 | [540,545] | 两笔金额均准确 | 最终答案、工具轨迹 |
| 9 | `case-specific-reason-participants` | 推理 | 规则/LLM Judge | 说明两次活动均为3人 | 3 | 参与人数准确 | 最终答案、工具轨迹 |
| 10 | `case-specific-reason-per-capita` | 推理 | 规则/LLM Judge | 计算人均180元和约181.67元 | [180,181.67] | 两笔人均金额均准确 | 最终答案、工具轨迹 |
| 11 | `case-specific-reason-standard` | 推理 | 规则/LLM Judge | 说明单次金额和人均金额均未超过招待费标准 | [5000,300] | 正确比较单次5000元和人均300元标准 | 最终答案、工具轨迹 |
| 12 | `case-specific-reason-split` | 推理 | 规则/LLM Judge | 说明两笔合计未达到10000元审批线 | 10000 | 正确排除拆分规避审批 | 最终答案、工具轨迹 |
| 13 | `reverse-check-business-context` | 误报控制 | 规则/LLM Judge | 轨迹中独立核验：说明两条记录对应不同客户和不同业务事项 | ["客户甲产品方案交流","客户乙投行业务沟通"] | 工具轨迹或工作产物包含数据来源或计算过程，并证明准确区分两次独立业务活动 | 工具轨迹、工作区产物 |
| 14 | `reverse-check-date-window` | 误报控制 | 规则/LLM Judge | 轨迹中独立核验：说明两条费用发生日期相隔1天并完成窗口核查 | 1 | 工具轨迹或工作产物包含数据来源或计算过程，并证明准确核对日期间隔及7天窗口 | 工具轨迹、工作区产物 |
| 15 | `reverse-check-invoice` | 误报控制 | 规则/LLM Judge | 轨迹中独立核验：说明两条记录发票不同 | 发票不同 | 工具轨迹或工作产物包含数据来源或计算过程，并证明准确排除重复发票 | 工具轨迹、工作区产物 |
| 16 | `reverse-check-amounts` | 误报控制 | 规则/LLM Judge | 轨迹中独立核验：给出单次金额540元和545元 | [540,545] | 工具轨迹或工作产物包含数据来源或计算过程，并证明两笔金额均准确 | 工具轨迹、工作区产物 |
| 17 | `reverse-check-participants` | 误报控制 | 规则/LLM Judge | 轨迹中独立核验：说明两次活动均为3人 | 3 | 工具轨迹或工作产物包含数据来源或计算过程，并证明参与人数准确 | 工具轨迹、工作区产物 |
| 18 | `reverse-check-per-capita` | 误报控制 | 规则/LLM Judge | 轨迹中独立核验：计算人均180元和约181.67元 | [180,181.67] | 工具轨迹或工作产物包含数据来源或计算过程，并证明两笔人均金额均准确 | 工具轨迹、工作区产物 |
| 19 | `reverse-check-standard` | 误报控制 | 规则/LLM Judge | 轨迹中独立核验：说明单次金额和人均金额均未超过招待费标准 | [5000,300] | 工具轨迹或工作产物包含数据来源或计算过程，并证明正确比较单次5000元和人均300元标准 | 工具轨迹、工作区产物 |
| 20 | `reverse-check-split` | 误报控制 | 规则/LLM Judge | 轨迹中独立核验：说明两笔合计未达到10000元审批线 | 10000 | 工具轨迹或工作产物包含数据来源或计算过程，并证明正确排除拆分规避审批 | 工具轨迹、工作区产物 |
| 21 | `policy-basis-source-1` | 制度 | 规则/LLM Judge | 引用本题所需制度依据：01_expense_reimbursement_2025.md#第十条、第十一条 | {"doc_id":"01_expense_reimbursement_2025.md","clause_no":"第十条、第十一条"} | 准确引用01_expense_reimbursement_2025.md#第十条、第十一条 | 提交JSON、工具轨迹 |
| 22 | `policy-basis-source-2` | 制度 | 规则/LLM Judge | 引用本题所需制度依据：06_business_entertainment.md#第二条至第四条 | {"doc_id":"06_business_entertainment.md","clause_no":"第二条至第四条"} | 准确引用06_business_entertainment.md#第二条至第四条 | 提交JSON、工具轨迹 |
| 23 | `policy-basis-source-3` | 制度 | 规则/LLM Judge | 引用本题所需制度依据：03_authorization_management.md#附件二 | {"doc_id":"03_authorization_management.md","clause_no":"附件二"} | 准确引用03_authorization_management.md#附件二 | 提交JSON、工具轨迹 |
| 24 | `no-unsupported-output` | 误报控制 | 规则 | 结构化结果不提交任何异常ID | {"anomaly_ids":[]} | anomaly_ids为空 | 提交JSON |
| 25 | `submission` | 格式 | 规则 | 统一Schema结果提交成功 | submission_receipt.status=accepted | 提交回执状态为accepted且Schema校验通过 | 提交JSON |

---

## 13. L3-007

- **题型**：检索与综合报告
- **难度**：`L3`
- **类别**：`two_hop_retrieval`
- **选题目的**：二跳制度检索，验证交叉引用
- **Checklist数量**：9项

### 题目

> 报销办法没有直接列审批金额时,请通过交叉引用找到单笔费用审批档位。

### 标准答案边界

以下内容仅供判卷和复核，不应暴露给候选智能体。

```json
{
  "scoring_kind": "expected_facts",
  "expected_facts": [
    "部门总经理审批线为10000元",
    "金额出现在授权管理办法附件二"
  ],
  "required_citations": [
    {
      "doc_id": "01_expense_reimbursement_2025.md",
      "clause_no": "第五条"
    },
    {
      "doc_id": "03_authorization_management.md",
      "clause_no": "附件二"
    }
  ]
}
```

### Checklist Rubric

| # | 检查项ID | 维度 | 判定方式 | 检查内容 | 预期 | 通过条件 | 证据来源 |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | `threshold-amount` | 结论 | 规则/LLM Judge | 给出部门总经理审批线10000元 | 10000 | 明确给出金额10000元 | 最终答案、提交JSON |
| 2 | `threshold-inclusive` | 结论 | 规则/LLM Judge | 说明达到10000元即进入该审批档位 | 达到10000元 | 明确说明包含10000元边界 | 最终答案、提交JSON |
| 3 | `two-hop-path-first` | 推理 | 规则/LLM Judge | 第一跳定位费用报销办法第五条 | 01_expense_reimbursement_2025.md#第五条 | 识别第一跳制度和条款 | 最终答案、工具轨迹 |
| 4 | `two-hop-path-relation` | 推理 | 规则/LLM Judge | 识别第五条指向授权管理办法附件二 | 交叉引用 | 明确说明制度间交叉引用关系 | 最终答案、工具轨迹 |
| 5 | `two-hop-path-second` | 推理 | 规则/LLM Judge | 第二跳定位授权管理办法附件二 | 03_authorization_management.md#附件二 | 完成第二跳检索 | 最终答案、工具轨迹 |
| 6 | `citations-expense` | 制度 | 规则/LLM Judge | 引用费用报销办法第五条 | 01_expense_reimbursement_2025.md#第五条 | 引用第一跳制度及条款 | 提交JSON、工具轨迹 |
| 7 | `citations-authorization` | 制度 | 规则/LLM Judge | 引用授权管理办法附件二 | 03_authorization_management.md#附件二 | 引用第二跳制度及附件 | 提交JSON、工具轨迹 |
| 8 | `no-premature-stop` | 误报控制 | LLM Judge | 检索完整性：不因首份制度未列金额而提前结束 | 继续追踪交叉引用 | 轨迹证明继续检索 | 工具轨迹、最终答案 |
| 9 | `submission` | 格式 | 规则 | 统一Schema结果提交成功 | submission_receipt.status=accepted | 提交回执状态为accepted且Schema校验通过 | 提交JSON |

---

## 14. L3-009

- **题型**：检索与综合报告
- **难度**：`L3`
- **类别**：`audit_report`
- **选题目的**：全年综合报告，验证五类规则汇总
- **Checklist数量**：73项

### 题目

> 请基于全年数据形成费用异常审计摘要，覆盖重复报销、拆分报销、超标准、超预算和超期报销五类规则。发现口径为：重复报销按重复发票组计1项；拆分报销按同一员工、同一费用类型7天窗口聚合组计1项；超标准只计单笔或单次即可确认的异常，办公用品和通讯费用不评价多笔月度累计；超预算按部门计1项，以按reimburse_date和record_id累计时首次使累计支出超过预算且无专项审批的记录作为关键记录；超期报销按记录计1项。请按规则类型生成稳定的发现ID，说明各类发现数量，在record_ids中返回全部异常发现涉及的记录，并在审计说明中至少逐类给出一个发现与record_id的对应示例，同时说明制度依据、影响和建议；不得把仅接近阈值但实际合规的记录计入异常。

### 标准答案边界

以下内容仅供判卷和复核，不应暴露给候选智能体。

```json
{
  "scoring_kind": "llm_rubric",
  "rubric_assertions": [
    "报告说明5类规则共形成30项异常发现。",
    "报告覆盖重复报销、拆分报销、超标准、超预算、超期报销。",
    "record_ids完整覆盖全部异常发现涉及的业务记录。",
    "每类至少给出一个可复核的发现ID及record_id对应示例。",
    "不得把合规边界记录计入异常。"
  ],
  "expected_anomaly_count": 30,
  "expected_rule_types": [
    "DUP",
    "SPLIT",
    "OVERSTD",
    "BUDGET",
    "OVERDUE"
  ],
  "expected_findings_by_type": {
    "DUP": 6,
    "SPLIT": 6,
    "OVERSTD": 6,
    "BUDGET": 6,
    "OVERDUE": 6
  },
  "expected_record_ids": [
    "R000002",
    "R004201",
    "R000005",
    "R004202",
    "R000020",
    "R004203",
    "R000028",
    "R004204",
    "R000037",
    "R004205",
    "R000055",
    "R004206",
    "R004207",
    "R004208",
    "R004209",
    "R004210",
    "R004211",
    "R004212",
    "R004213",
    "R004214",
    "R004215",
    "R004216",
    "R004217",
    "R004218",
    "R004219",
    "R004220",
    "R004221",
    "R004222",
    "R004223",
    "R004224",
    "R004225",
    "R004226",
    "R000079",
    "R002009",
    "R003968",
    "R000894",
    "R003479",
    "R000312",
    "R004227",
    "R004228",
    "R004229",
    "R004230",
    "R004231",
    "R004232"
  ],
  "expected_finding_groups": [
    {
      "rule_type": "DUP",
      "record_ids": [
        "R000002",
        "R004201"
      ]
    },
    {
      "rule_type": "DUP",
      "record_ids": [
        "R000005",
        "R004202"
      ]
    },
    {
      "rule_type": "DUP",
      "record_ids": [
        "R000020",
        "R004203"
      ]
    },
    {
      "rule_type": "DUP",
      "record_ids": [
        "R000028",
        "R004204"
      ]
    },
    {
      "rule_type": "DUP",
      "record_ids": [
        "R000037",
        "R004205"
      ]
    },
    {
      "rule_type": "DUP",
      "record_ids": [
        "R000055",
        "R004206"
      ]
    },
    {
      "rule_type": "SPLIT",
      "record_ids": [
        "R004207",
        "R004208"
      ]
    },
    {
      "rule_type": "SPLIT",
      "record_ids": [
        "R004209",
        "R004210",
        "R004211"
      ]
    },
    {
      "rule_type": "SPLIT",
      "record_ids": [
        "R004212",
        "R004213"
      ]
    },
    {
      "rule_type": "SPLIT",
      "record_ids": [
        "R004214",
        "R004215",
        "R004216"
      ]
    },
    {
      "rule_type": "SPLIT",
      "record_ids": [
        "R004217",
        "R004218"
      ]
    },
    {
      "rule_type": "SPLIT",
      "record_ids": [
        "R004219",
        "R004220"
      ]
    },
    {
      "rule_type": "OVERSTD",
      "record_ids": [
        "R004221"
      ]
    },
    {
      "rule_type": "OVERSTD",
      "record_ids": [
        "R004222"
      ]
    },
    {
      "rule_type": "OVERSTD",
      "record_ids": [
        "R004223"
      ]
    },
    {
      "rule_type": "OVERSTD",
      "record_ids": [
        "R004224"
      ]
    },
    {
      "rule_type": "OVERSTD",
      "record_ids": [
        "R004225"
      ]
    },
    {
      "rule_type": "OVERSTD",
      "record_ids": [
        "R004226"
      ]
    },
    {
      "rule_type": "BUDGET",
      "record_ids": [
        "R000079"
      ],
      "department_id": "D001"
    },
    {
      "rule_type": "BUDGET",
      "record_ids": [
        "R002009"
      ],
      "department_id": "D002"
    },
    {
      "rule_type": "BUDGET",
      "record_ids": [
        "R003968"
      ],
      "department_id": "D003"
    },
    {
      "rule_type": "BUDGET",
      "record_ids": [
        "R000894"
      ],
      "department_id": "D004"
    },
    {
      "rule_type": "BUDGET",
      "record_ids": [
        "R003479"
      ],
      "department_id": "D005"
    },
    {
      "rule_type": "BUDGET",
      "record_ids": [
        "R000312"
      ],
      "department_id": "D006"
    },
    {
      "rule_type": "OVERDUE",
      "record_ids": [
        "R004227"
      ]
    },
    {
      "rule_type": "OVERDUE",
      "record_ids": [
        "R004228"
      ]
    },
    {
      "rule_type": "OVERDUE",
      "record_ids": [
        "R004229"
      ]
    },
    {
      "rule_type": "OVERDUE",
      "record_ids": [
        "R004230"
      ]
    },
    {
      "rule_type": "OVERDUE",
      "record_ids": [
        "R004231"
      ]
    },
    {
      "rule_type": "OVERDUE",
      "record_ids": [
        "R004232"
      ]
    }
  ],
  "excluded_record_ids": [
    "R004233",
    "R004234",
    "R004235",
    "R004236",
    "R004237",
    "R004238",
    "R004239",
    "R004240"
  ],
  "required_citations": [
    {
      "doc_id": "01_expense_reimbursement_2025.md",
      "clause_no": "第七条、第九条至第十三条"
    },
    {
      "doc_id": "04_travel_expense.md",
      "clause_no": "第三条至第六条"
    },
    {
      "doc_id": "05_training_expense.md",
      "clause_no": "第二条至第五条"
    },
    {
      "doc_id": "06_business_entertainment.md",
      "clause_no": "第二条、第三条"
    },
    {
      "doc_id": "07_office_communication.md",
      "clause_no": "第二条、第三条"
    },
    {
      "doc_id": "08_budget_management.md",
      "clause_no": "第二条至第四条"
    }
  ]
}
```

### Checklist Rubric

| # | 检查项ID | 维度 | 判定方式 | 检查内容 | 预期 | 通过条件 | 证据来源 |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | `overall-count-total` | 结论 | 规则 | 提交异常发现总数为30项 | 30 | anomaly_ids数量恰好为30 | 最终答案、提交JSON |
| 2 | `overall-count-type-dup` | 结论 | 规则 | DUP类发现数量为6项 | {"rule_type":"DUP","count":6} | DUP类anomaly_id数量恰好为6 | 最终答案、提交JSON |
| 3 | `overall-count-type-split` | 结论 | 规则 | SPLIT类发现数量为6项 | {"rule_type":"SPLIT","count":6} | SPLIT类anomaly_id数量恰好为6 | 最终答案、提交JSON |
| 4 | `overall-count-type-overstd` | 结论 | 规则 | OVERSTD类发现数量为6项 | {"rule_type":"OVERSTD","count":6} | OVERSTD类anomaly_id数量恰好为6 | 最终答案、提交JSON |
| 5 | `overall-count-type-budget` | 结论 | 规则 | BUDGET类发现数量为6项 | {"rule_type":"BUDGET","count":6} | BUDGET类anomaly_id数量恰好为6 | 最终答案、提交JSON |
| 6 | `overall-count-type-overdue` | 结论 | 规则 | OVERDUE类发现数量为6项 | {"rule_type":"OVERDUE","count":6} | OVERDUE类anomaly_id数量恰好为6 | 最终答案、提交JSON |
| 7 | `all-record-ids-include-r000002` | 证据 | 规则 | 结果包含应核查记录 R000002 | R000002 | 提交的record_ids包含R000002 | 提交JSON、工具轨迹 |
| 8 | `all-record-ids-include-r004201` | 证据 | 规则 | 结果包含应核查记录 R004201 | R004201 | 提交的record_ids包含R004201 | 提交JSON、工具轨迹 |
| 9 | `all-record-ids-include-r000005` | 证据 | 规则 | 结果包含应核查记录 R000005 | R000005 | 提交的record_ids包含R000005 | 提交JSON、工具轨迹 |
| 10 | `all-record-ids-include-r004202` | 证据 | 规则 | 结果包含应核查记录 R004202 | R004202 | 提交的record_ids包含R004202 | 提交JSON、工具轨迹 |
| 11 | `all-record-ids-include-r000020` | 证据 | 规则 | 结果包含应核查记录 R000020 | R000020 | 提交的record_ids包含R000020 | 提交JSON、工具轨迹 |
| 12 | `all-record-ids-include-r004203` | 证据 | 规则 | 结果包含应核查记录 R004203 | R004203 | 提交的record_ids包含R004203 | 提交JSON、工具轨迹 |
| 13 | `all-record-ids-include-r000028` | 证据 | 规则 | 结果包含应核查记录 R000028 | R000028 | 提交的record_ids包含R000028 | 提交JSON、工具轨迹 |
| 14 | `all-record-ids-include-r004204` | 证据 | 规则 | 结果包含应核查记录 R004204 | R004204 | 提交的record_ids包含R004204 | 提交JSON、工具轨迹 |
| 15 | `all-record-ids-include-r000037` | 证据 | 规则 | 结果包含应核查记录 R000037 | R000037 | 提交的record_ids包含R000037 | 提交JSON、工具轨迹 |
| 16 | `all-record-ids-include-r004205` | 证据 | 规则 | 结果包含应核查记录 R004205 | R004205 | 提交的record_ids包含R004205 | 提交JSON、工具轨迹 |
| 17 | `all-record-ids-include-r000055` | 证据 | 规则 | 结果包含应核查记录 R000055 | R000055 | 提交的record_ids包含R000055 | 提交JSON、工具轨迹 |
| 18 | `all-record-ids-include-r004206` | 证据 | 规则 | 结果包含应核查记录 R004206 | R004206 | 提交的record_ids包含R004206 | 提交JSON、工具轨迹 |
| 19 | `all-record-ids-include-r004207` | 证据 | 规则 | 结果包含应核查记录 R004207 | R004207 | 提交的record_ids包含R004207 | 提交JSON、工具轨迹 |
| 20 | `all-record-ids-include-r004208` | 证据 | 规则 | 结果包含应核查记录 R004208 | R004208 | 提交的record_ids包含R004208 | 提交JSON、工具轨迹 |
| 21 | `all-record-ids-include-r004209` | 证据 | 规则 | 结果包含应核查记录 R004209 | R004209 | 提交的record_ids包含R004209 | 提交JSON、工具轨迹 |
| 22 | `all-record-ids-include-r004210` | 证据 | 规则 | 结果包含应核查记录 R004210 | R004210 | 提交的record_ids包含R004210 | 提交JSON、工具轨迹 |
| 23 | `all-record-ids-include-r004211` | 证据 | 规则 | 结果包含应核查记录 R004211 | R004211 | 提交的record_ids包含R004211 | 提交JSON、工具轨迹 |
| 24 | `all-record-ids-include-r004212` | 证据 | 规则 | 结果包含应核查记录 R004212 | R004212 | 提交的record_ids包含R004212 | 提交JSON、工具轨迹 |
| 25 | `all-record-ids-include-r004213` | 证据 | 规则 | 结果包含应核查记录 R004213 | R004213 | 提交的record_ids包含R004213 | 提交JSON、工具轨迹 |
| 26 | `all-record-ids-include-r004214` | 证据 | 规则 | 结果包含应核查记录 R004214 | R004214 | 提交的record_ids包含R004214 | 提交JSON、工具轨迹 |
| 27 | `all-record-ids-include-r004215` | 证据 | 规则 | 结果包含应核查记录 R004215 | R004215 | 提交的record_ids包含R004215 | 提交JSON、工具轨迹 |
| 28 | `all-record-ids-include-r004216` | 证据 | 规则 | 结果包含应核查记录 R004216 | R004216 | 提交的record_ids包含R004216 | 提交JSON、工具轨迹 |
| 29 | `all-record-ids-include-r004217` | 证据 | 规则 | 结果包含应核查记录 R004217 | R004217 | 提交的record_ids包含R004217 | 提交JSON、工具轨迹 |
| 30 | `all-record-ids-include-r004218` | 证据 | 规则 | 结果包含应核查记录 R004218 | R004218 | 提交的record_ids包含R004218 | 提交JSON、工具轨迹 |
| 31 | `all-record-ids-include-r004219` | 证据 | 规则 | 结果包含应核查记录 R004219 | R004219 | 提交的record_ids包含R004219 | 提交JSON、工具轨迹 |
| 32 | `all-record-ids-include-r004220` | 证据 | 规则 | 结果包含应核查记录 R004220 | R004220 | 提交的record_ids包含R004220 | 提交JSON、工具轨迹 |
| 33 | `all-record-ids-include-r004221` | 证据 | 规则 | 结果包含应核查记录 R004221 | R004221 | 提交的record_ids包含R004221 | 提交JSON、工具轨迹 |
| 34 | `all-record-ids-include-r004222` | 证据 | 规则 | 结果包含应核查记录 R004222 | R004222 | 提交的record_ids包含R004222 | 提交JSON、工具轨迹 |
| 35 | `all-record-ids-include-r004223` | 证据 | 规则 | 结果包含应核查记录 R004223 | R004223 | 提交的record_ids包含R004223 | 提交JSON、工具轨迹 |
| 36 | `all-record-ids-include-r004224` | 证据 | 规则 | 结果包含应核查记录 R004224 | R004224 | 提交的record_ids包含R004224 | 提交JSON、工具轨迹 |
| 37 | `all-record-ids-include-r004225` | 证据 | 规则 | 结果包含应核查记录 R004225 | R004225 | 提交的record_ids包含R004225 | 提交JSON、工具轨迹 |
| 38 | `all-record-ids-include-r004226` | 证据 | 规则 | 结果包含应核查记录 R004226 | R004226 | 提交的record_ids包含R004226 | 提交JSON、工具轨迹 |
| 39 | `all-record-ids-include-r000079` | 证据 | 规则 | 结果包含应核查记录 R000079 | R000079 | 提交的record_ids包含R000079 | 提交JSON、工具轨迹 |
| 40 | `all-record-ids-include-r002009` | 证据 | 规则 | 结果包含应核查记录 R002009 | R002009 | 提交的record_ids包含R002009 | 提交JSON、工具轨迹 |
| 41 | `all-record-ids-include-r003968` | 证据 | 规则 | 结果包含应核查记录 R003968 | R003968 | 提交的record_ids包含R003968 | 提交JSON、工具轨迹 |
| 42 | `all-record-ids-include-r000894` | 证据 | 规则 | 结果包含应核查记录 R000894 | R000894 | 提交的record_ids包含R000894 | 提交JSON、工具轨迹 |
| 43 | `all-record-ids-include-r003479` | 证据 | 规则 | 结果包含应核查记录 R003479 | R003479 | 提交的record_ids包含R003479 | 提交JSON、工具轨迹 |
| 44 | `all-record-ids-include-r000312` | 证据 | 规则 | 结果包含应核查记录 R000312 | R000312 | 提交的record_ids包含R000312 | 提交JSON、工具轨迹 |
| 45 | `all-record-ids-include-r004227` | 证据 | 规则 | 结果包含应核查记录 R004227 | R004227 | 提交的record_ids包含R004227 | 提交JSON、工具轨迹 |
| 46 | `all-record-ids-include-r004228` | 证据 | 规则 | 结果包含应核查记录 R004228 | R004228 | 提交的record_ids包含R004228 | 提交JSON、工具轨迹 |
| 47 | `all-record-ids-include-r004229` | 证据 | 规则 | 结果包含应核查记录 R004229 | R004229 | 提交的record_ids包含R004229 | 提交JSON、工具轨迹 |
| 48 | `all-record-ids-include-r004230` | 证据 | 规则 | 结果包含应核查记录 R004230 | R004230 | 提交的record_ids包含R004230 | 提交JSON、工具轨迹 |
| 49 | `all-record-ids-include-r004231` | 证据 | 规则 | 结果包含应核查记录 R004231 | R004231 | 提交的record_ids包含R004231 | 提交JSON、工具轨迹 |
| 50 | `all-record-ids-include-r004232` | 证据 | 规则 | 结果包含应核查记录 R004232 | R004232 | 提交的record_ids包含R004232 | 提交JSON、工具轨迹 |
| 51 | `all-record-ids-no-extra` | 证据 | 规则 | 结果不包含本题范围外的记录 | ["R000002","R004201","R000005","R004202","R000020","R004203","R000028","R004204","R000037","R004205","R000055","R004206","R004207","R004208","R004209","R004210","R004211","R004212","R004213","R004214","R004215","R004216","R004217","R004218","R004219","R004220","R004221","R004222","R004223","R004224","R004225","R004226","R000079","R002009","R003968","R000894","R003479","R000312","R004227","R004228","R004229","R004230","R004231","R004232"] | 提交的record_ids除R000002, R004201, R000005, R004202, R000020, R004203, R000028, R004204, R000037, R004205, R000055, R004206, R004207, R004208, R004209, R004210, R004211, R004212, R004213, R004214, R004215, R004216, R004217, R004218, R004219, R004220, R004221, R004222, R004223, R004224, R004225, R004226, R000079, R002009, R003968, R000894, R003479, R000312, R004227, R004228, R004229, R004230, R004231, R004232外没有其他记录 | 提交JSON、工具轨迹 |
| 52 | `representative-evidence-dup` | 证据 | 规则/LLM Judge | DUP类至少有1个可复核发现及record_id | DUP | DUP类同时给出稳定发现ID和正确record_id证据 | 最终答案、工具轨迹 |
| 53 | `representative-evidence-split` | 证据 | 规则/LLM Judge | SPLIT类至少有1个可复核发现及record_id | SPLIT | SPLIT类同时给出稳定发现ID和正确record_id证据 | 最终答案、工具轨迹 |
| 54 | `representative-evidence-overstd` | 证据 | 规则/LLM Judge | OVERSTD类至少有1个可复核发现及record_id | OVERSTD | OVERSTD类同时给出稳定发现ID和正确record_id证据 | 最终答案、工具轨迹 |
| 55 | `representative-evidence-budget` | 证据 | 规则/LLM Judge | BUDGET类至少有1个可复核发现及record_id | BUDGET | BUDGET类同时给出稳定发现ID和正确record_id证据 | 最终答案、工具轨迹 |
| 56 | `representative-evidence-overdue` | 证据 | 规则/LLM Judge | OVERDUE类至少有1个可复核发现及record_id | OVERDUE | OVERDUE类同时给出稳定发现ID和正确record_id证据 | 最终答案、工具轨迹 |
| 57 | `policy-coverage-expense` | 制度 | 规则/LLM Judge | 引用费用报销办法中五类规则的对应条款 | 01_expense_reimbursement_2025.md第七、九、十、十一、十二、十三条 | 费用报销办法规则条款可核查 | 提交JSON、工具轨迹 |
| 58 | `policy-coverage-special` | 制度 | 规则/LLM Judge | 超标准结论引用对应专项费用标准 | 04至07号专项费用标准 | 专项费用标准与超标准发现对应 | 提交JSON、工具轨迹 |
| 59 | `policy-coverage-budget` | 制度 | 规则/LLM Judge | 超预算结论引用预算管理办法 | 08_budget_management.md第二至第四条 | 预算管理条款可核查 | 提交JSON、工具轨迹 |
| 60 | `trap-control-r004233` | 误报控制 | 规则/LLM Judge | 未把合规边界记录R004233判为异常 | R004233 | 结构化结果和文字结论均未将R004233认定为异常 | 提交JSON、最终答案 |
| 61 | `trap-control-r004234` | 误报控制 | 规则/LLM Judge | 未把合规边界记录R004234判为异常 | R004234 | 结构化结果和文字结论均未将R004234认定为异常 | 提交JSON、最终答案 |
| 62 | `trap-control-r004235` | 误报控制 | 规则/LLM Judge | 未把合规边界记录R004235判为异常 | R004235 | 结构化结果和文字结论均未将R004235认定为异常 | 提交JSON、最终答案 |
| 63 | `trap-control-r004236` | 误报控制 | 规则/LLM Judge | 未把合规边界记录R004236判为异常 | R004236 | 结构化结果和文字结论均未将R004236认定为异常 | 提交JSON、最终答案 |
| 64 | `trap-control-r004237` | 误报控制 | 规则/LLM Judge | 未把合规边界记录R004237判为异常 | R004237 | 结构化结果和文字结论均未将R004237认定为异常 | 提交JSON、最终答案 |
| 65 | `trap-control-r004238` | 误报控制 | 规则/LLM Judge | 未把合规边界记录R004238判为异常 | R004238 | 结构化结果和文字结论均未将R004238认定为异常 | 提交JSON、最终答案 |
| 66 | `trap-control-r004239` | 误报控制 | 规则/LLM Judge | 未把合规边界记录R004239判为异常 | R004239 | 结构化结果和文字结论均未将R004239认定为异常 | 提交JSON、最终答案 |
| 67 | `trap-control-r004240` | 误报控制 | 规则/LLM Judge | 未把合规边界记录R004240判为异常 | R004240 | 结构化结果和文字结论均未将R004240认定为异常 | 提交JSON、最终答案 |
| 68 | `report-shape-fact` | 格式 | LLM Judge | 报告包含事实 | 事实 | 报告中存在可识别的事实内容 | 最终答案、提交JSON |
| 69 | `report-shape-rule` | 格式 | LLM Judge | 报告包含规则 | 规则 | 报告中存在可识别的规则内容 | 最终答案、提交JSON |
| 70 | `report-shape-judgment` | 格式 | LLM Judge | 报告包含判断 | 判断 | 报告中存在可识别的判断内容 | 最终答案、提交JSON |
| 71 | `report-shape-impact` | 格式 | LLM Judge | 报告包含影响 | 影响 | 报告中存在可识别的影响内容 | 最终答案、提交JSON |
| 72 | `report-shape-recommendation` | 格式 | LLM Judge | 报告包含建议 | 建议 | 报告中存在可识别的建议内容 | 最终答案、提交JSON |
| 73 | `submission` | 格式 | 规则 | 统一Schema结果提交成功 | submission_receipt.status=accepted | 提交回执状态为accepted且Schema校验通过 | 提交JSON |

---

## 15. L3-010

- **题型**：检索与综合报告
- **难度**：`L3`
- **类别**：`audit_report`
- **选题目的**：制度版本风险报告，验证审计表达
- **Checklist数量**：11项

### 题目

> 请专门写一段版本陷阱审计说明，列明新旧审批线及其效力状态，说明现行金额的交叉引用依据、使用旧版可能造成的误判，并提出版本校验措施。

### 标准答案边界

以下内容仅供判卷和复核，不应暴露给候选智能体。

```json
{
  "scoring_kind": "llm_rubric",
  "rubric_assertions": [
    "必须指出2025修订版现行部门总经理审批线为10000元。",
    "必须指出2022版8000元审批线已废止。",
    "必须说明报销办法通过授权管理办法附件二取得现行审批金额。",
    "不得把旧版条款作为当前审批依据。"
  ],
  "required_citations": [
    {
      "doc_id": "01_expense_reimbursement_2025.md",
      "clause_no": "第五条、第十四条"
    },
    {
      "doc_id": "02_expense_reimbursement_2022_deprecated.md",
      "clause_no": "第一条、第二条、第四条"
    },
    {
      "doc_id": "03_authorization_management.md",
      "clause_no": "附件二"
    }
  ]
}
```

### Checklist Rubric

| # | 检查项ID | 维度 | 判定方式 | 检查内容 | 预期 | 通过条件 | 证据来源 |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | `current-threshold-version` | 结论 | 规则/LLM Judge | 说明2025修订版为现行版本 | 2025修订版 | 明确识别现行版本 | 最终答案、提交JSON |
| 2 | `current-threshold-amount` | 结论 | 规则/LLM Judge | 给出现行审批线10000元 | 10000 | 明确给出现行金额10000元 | 最终答案、提交JSON |
| 3 | `old-threshold-status-amount` | 制度 | 规则/LLM Judge | 给出2022版审批线8000元 | 8000 | 明确给出旧版金额8000元 | 最终答案、工具轨迹 |
| 4 | `old-threshold-status-status` | 制度 | 规则/LLM Judge | 说明2022版审批线已经废止 | 已废止 | 明确说明旧版不再适用 | 最终答案、工具轨迹 |
| 5 | `cross-reference-expense` | 推理 | 规则/LLM Judge | 定位费用报销办法第五条 | 01_expense_reimbursement_2025.md#第五条 | 引用费用报销办法第五条 | 最终答案、工具轨迹 |
| 6 | `cross-reference-relation` | 推理 | 规则/LLM Judge | 说明第五条将金额授权给附件二规定 | 交叉引用关系 | 正确说明制度关系 | 最终答案、工具轨迹 |
| 7 | `cross-reference-authorization` | 推理 | 规则/LLM Judge | 定位授权管理办法附件二 | 03_authorization_management.md#附件二 | 引用附件二中的现行金额 | 最终答案、工具轨迹 |
| 8 | `risk-explanation-risk` | 推理 | LLM Judge | 说明使用8000元旧线会扩大升级审批范围并造成误报 | 误报风险 | 具体说明旧线造成的误判方向 | 最终答案 |
| 9 | `risk-explanation-control` | 推理 | LLM Judge | 提出制度版本校验措施 | 版本校验建议 | 提出可执行的版本识别或有效性校验措施 | 最终答案 |
| 10 | `report-shape` | 格式 | 规则/LLM Judge | 报告表达：以审计说明形式提交并保持字段一致 | 事实、规则、判断和建议一致 | 表达完整且一致 | 最终答案、提交JSON |
| 11 | `submission` | 格式 | 规则 | 统一Schema结果提交成功 | submission_receipt.status=accepted | 提交回执状态为accepted且Schema校验通过 | 提交JSON |
