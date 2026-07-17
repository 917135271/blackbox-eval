# Policy Researcher — Detailed Analysis

## Audit: L3-009 XX证券 2025 Full-Year Comprehensive Audit

---

## 1. Policy Applicability Determination

### 1.1 Applicable Policy: 01_expense_reimbursement_2025.md

**Doc ID**: `01_expense_reimbursement_2025.md`
**Title**: XX证券费用报销管理办法(2025修订版)
**Document Reference**: XX证财规〔2025〕甲号

**Effective Date**: 2025-01-01 (per 第十四条: "本办法自二〇二五年一月一日起施行")

**Scope**: Applies to all XX证券 departments, branches, and employees for travel, training, entertainment, office, and communication expense reimbursements (第二条).

**Repeal of Prior Version**: 第十四条 explicitly states: "原《XX证券费用报销管理办法(2022版)》同时废止。" — the 2022 version is repealed concurrently.

**Conclusion**: 01_expense_reimbursement_2025.md is the sole applicable expense reimbursement policy for the entire audit period 2025-01-01 to 2025-12-31.

### 1.2 Deprecated Policy: 02_expense_reimbursement_2022_deprecated.md

**Doc ID**: `02_expense_reimbursement_2022_deprecated.md`
**Title**: XX证券费用报销管理办法(2022版)
**Document Reference**: XX证财规〔2022〕乙号

**Status**: Deprecated. The document self-identifies as archival only: "仅作为制度沿革留档" (第一条).

**Key outdated provisions**:
- Single reimbursement at 8000元 required 部门总经理 approval (第二条)
- Single reimbursement at 30000元 required 分管副总 approval (第三条)

**Explicit prohibition**: 第四条 states "本办法的审批金额已被后续制度替代,不得作为现行审批依据。" — the approval amounts have been superseded and must not be used as current approval basis.

**Conclusion**: 02_expense_reimbursement_2022_deprecated.md is NOT applicable to any 2025 expense. All rules must reference only 01 and its supporting policies.

---

## 2. Rule-by-Rule Clause Extraction

### 2.1 R01 — Duplicate Invoice Reimbursement

**Governing Clause**: 01_expense_reimbursement_2025.md, **第十条**

**Exact Text**: "同一发票最多报销1次。发现同一发票在不同报销单中重复出现的,应认定为重复报销风险。"

**Interpretation**:
- Each invoice may be reimbursed at most once.
- If the same invoice appears in multiple reimbursement records, it must be flagged as duplicate reimbursement risk.
- No exemptions apply — this is an absolute prohibition.

**Citation**: `{doc_id: "01_expense_reimbursement_2025.md", clause_no: "第十条"}`

---

### 2.2 R02 — Split Claim (规避审批)

**Governing Clause**: 01_expense_reimbursement_2025.md, **第十一条**

**Exact Text**: "不得将同一事项或同类事项拆分为多笔报销以规避审批权限。同一员工、同一费用类型在7天内出现2笔及以上报销,且合计金额达到《授权管理办法》附件二较高审批线的,应重点核查拆分规避审批。"

**Interpretation**:
- Splitting the same or similar expense item into multiple reimbursements to evade approval thresholds is prohibited.
- **Detection criteria** (all must be satisfied):
  1. Same employee (`employee_id`)
  2. Same expense type (`expense_type`)
  3. Within 7 calendar days
  4. 2 or more reimbursement records
  5. Combined amount reaches the "higher approval line" from 03_authorization_management.md 附件二

**Higher Approval Line**: The "较高审批线" in 附件二 refers to the threshold that triggers a higher-level approver. Per 03_authorization_management.md:
- AR-03: ≥10,000元, requiring 部门总经理 (department general manager)
- This is the line above AR-01/AR-02 (部门经理 level).
- **Effective threshold for R02: ≥10,000元 (AR-03 line)**

**Citations**:
- `{doc_id: "01_expense_reimbursement_2025.md", clause_no: "第十一条"}`
- `{doc_id: "03_authorization_management.md", clause_no: "附件二"}`

---

### 2.3 R03 — Excess Over Standard

**Governing Clause**: 01_expense_reimbursement_2025.md, **第十二条**

**Exact Text**: "无专项审批时,报销金额不得超过对应制度标准的1.0倍。"

**Interpretation**:
- Without special approval (`special_approval=false` or absent), the reimbursement amount must not exceed 1.0× the applicable standard.
- **Exemption**: `special_approval=true` exempts the record from R03 violation.
- Standards are defined in the expense-type-specific policies below.

**Expense Standards by Type**:

#### 2.3.1 Travel — Lodging (04_travel_expense.md)

| Level | 一类城市 | 二类城市 | 三类城市 |
|---|---:|---:|---:|
| 员工级 (Employee) | 450元/晚 | 380元/晚 | 300元/晚 |
| 经理级 (Manager) | 650元/晚 | 550元/晚 | 450元/晚 |
| 部门负责人级 (Dept Head) | 850元/晚 | 700元/晚 | 600元/晚 |
| 高管级 (Executive) | 1100元/晚 | 900元/晚 | 750元/晚 |

Authority: 04_travel_expense.md 第四条; excess without special approval → 第五条 prohibits reimbursement of excess.

#### 2.3.2 Training (05_training_expense.md)

| Item | Standard |
|---|---:|
| Course fee | ≤3,500元/人/期 (第二条) |
| Internal training | ≤800元/天 (第三条) |
| External training | ≤1,200元/天 (第四条) |
| Lodging — 一类城市 | 500元/晚 (第五条) |
| Lodging — 二类城市 | 420元/晚 (第五条) |
| Lodging — 三类城市 | 350元/晚 (第五条) |

Note: Training lodging standards (05) override travel lodging standards (04) during training — per 04_travel_expense.md 第七条.

#### 2.3.3 Business Entertainment (06_business_entertainment.md)

| Item | Standard |
|---|---:|
| Single event | ≤5,000元 (第二条) |
| Per person | ≤300元 (第三条) |

#### 2.3.4 Office & Communication (07_office_communication.md)

| Item | Standard |
|---|---:|
| Office supplies | ≤600元/人/月 (第二条) |
| Communication | ≤300元/人/月 (第三条) |

**Citations for R03**:
- `{doc_id: "01_expense_reimbursement_2025.md", clause_no: "第十二条"}`
- `{doc_id: "04_travel_expense.md", clause_no: "第四条"}`
- `{doc_id: "04_travel_expense.md", clause_no: "第五条"}`
- `{doc_id: "05_training_expense.md", clause_no: "第二条"}`
- `{doc_id: "05_training_expense.md", clause_no: "第三条"}`
- `{doc_id: "05_training_expense.md", clause_no: "第四条"}`
- `{doc_id: "05_training_expense.md", clause_no: "第五条"}`
- `{doc_id: "06_business_entertainment.md", clause_no: "第二条"}`
- `{doc_id: "06_business_entertainment.md", clause_no: "第三条"}`
- `{doc_id: "07_office_communication.md", clause_no: "第二条"}`
- `{doc_id: "07_office_communication.md", clause_no: "第三条"}`

---

### 2.4 R04 — Budget Exceeded

**Governing Clauses**:
1. 01_expense_reimbursement_2025.md, **第十三条**: "部门年度预算不足时不得继续报销。预算使用达到预算额度的1.0倍后,确需发生的费用应履行专项审批。"
2. 08_budget_management.md, **第三条**: "部门费用累计使用达到年度预算额度的1.0倍后,原则上不得继续报销。"
3. 08_budget_management.md, **第四条**: "因监管要求、客户服务或经营连续性确需超预算支出的,应履行专项审批。"

**Interpretation**:
- When cumulative department usage reaches ≥1.0× the annual budget, further reimbursement is prohibited.
- **Detection**: Compare `cumulative_approved_amount` for a department against its `annual_budget`.
- **Exemption**: `special_approval=true` exempts the record from R04 violation (第十三条 explicitly allows: "确需发生的费用应履行专项审批").

**Citations**:
- `{doc_id: "01_expense_reimbursement_2025.md", clause_no: "第十三条"}`
- `{doc_id: "08_budget_management.md", clause_no: "第三条"}`
- `{doc_id: "08_budget_management.md", clause_no: "第四条"}`

---

### 2.5 R05 — Late Reimbursement

**Governing Clause**: 01_expense_reimbursement_2025.md, **第七条**

**Exact Text**: "员工应在费用发生后60天内提交报销申请;超过期限的,原则上不得报销。"

**Interpretation**:
- The gap between `expense_date` and `reimburse_date` must not exceed 60 calendar days.
- **Detection**: `(reimburse_date - expense_date) > 60 days`
- The language "原则上不得报销" (in principle shall not be reimbursed) establishes a firm rule, not a guideline.
- No special_approval exemption is specified for this rule.

**Note**: 第九条 provides a year-end extension: expenses from the fiscal year-end may be submitted within 15 days after the fiscal year ends. This means December 2025 expenses could be submitted by 2026-01-15. However, the 60-day rule still applies — the extension only adjusts the latest possible submission date for year-end expenses; it does not override 第七条's 60-day limit.

**Citation**: `{doc_id: "01_expense_reimbursement_2025.md", clause_no: "第七条"}`

---

## 3. Approval Authority Matrix

Extracted from 03_authorization_management.md 附件二 (费用报销审批权限表):

| Tier | Amount Range | Required Approver(s) |
|---|---:|---|
| AR-01 | 0元 ≤ amount < 3,000元 | 部门经理 (Department Manager) |
| AR-02 | 3,000元 ≤ amount < 10,000元 | 部门经理 + 财务复核 (Dept Manager + Financial Review) |
| AR-03 | 10,000元 ≤ amount < 50,000元 | 部门总经理 (Department General Manager) |
| AR-04 | 50,000元 ≤ amount < 200,000元 | 分管副总 (VP in Charge) |
| AR-05 | amount ≥ 200,000元 | 总经理办公会 (General Manager Office Meeting) |

**Key**: 01_expense_reimbursement_2025.md 第五条 delegates approval authority to this table: "单笔费用报销的审批权限,不在本办法正文列示具体金额,统一按《XX证券授权管理办法》附件二执行。"

---

## 4. Special Approval Exemption Summary

`special_approval=true` provides exemption from:

| Rule | Clause | Exempted? | Basis |
|---|---:|---:|---|
| R01 Duplicate | 第十条 | **NO** | No exception language in clause |
| R02 Split | 第十一条 | **NO** | No exception language in clause |
| R03 Excess | 第十二条 | **YES** | "无专项审批时" — implies with special approval, exceeding standard is permitted |
| R04 Budget | 第十三条 | **YES** | "确需发生的费用应履行专项审批" — budget overrun permitted with special approval |
| R05 Late | 第七条 | **NO** | No exception language in clause; "原则上不得报销" is absolute |

---

## 5. Policy Hierarchy

```
01_expense_reimbursement_2025.md (umbrella, effective 2025-01-01)
├── 第三条 → 03_authorization_management.md (approval tiers, 附件二)
├── 第十二条 → 04_travel_expense.md (lodging standards)
├── 第十二条 → 05_training_expense.md (training standards)
├── 第十二条 → 06_business_entertainment.md (entertainment standards)
├── 第十二条 → 07_office_communication.md (office/comm standards)
└── 第十三条 → 08_budget_management.md (budget enforcement)
```

---

## 6. Documents Reviewed

| # | Doc ID | Title | Status |
|---:|---|---|---|
| 1 | 01_expense_reimbursement_2025.md | XX证券费用报销管理办法(2025修订版) | **APPLICABLE** |
| 2 | 02_expense_reimbursement_2022_deprecated.md | XX证券费用报销管理办法(2022版) | DEPRECATED |
| 3 | 03_authorization_management.md | XX证券授权管理办法 | APPLICABLE (approval tiers) |
| 4 | 04_travel_expense.md | XX证券差旅费管理办法 | APPLICABLE (lodging standards) |
| 5 | 05_training_expense.md | XX证券培训费管理办法 | APPLICABLE (training standards) |
| 6 | 06_business_entertainment.md | XX证券业务招待费管理办法 | APPLICABLE (entertainment standards) |
| 7 | 07_office_communication.md | XX证券办公与通讯费用管理办法 | APPLICABLE (office/comm standards) |
| 8 | 08_budget_management.md | XX证券预算管理办法 | APPLICABLE (budget enforcement) |

Documents 09–20 (information security, seal, attendance, archive, procurement, HR transfer, meeting, contract, confidentiality, IT asset, office environment, customer complaint) were reviewed and confirmed NOT relevant to expense reimbursement audit rules.
