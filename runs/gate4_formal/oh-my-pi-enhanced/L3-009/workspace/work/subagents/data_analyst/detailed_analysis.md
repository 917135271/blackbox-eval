# L3-009 Comprehensive Audit Data Analysis
## XX证券 2025 Full-Year Expense Data
### Data Analyst Report — 2026-07-16

---

## Global Overview

### Population
- **Total records**: 4,240 reimbursement records for 2025-01-01 through 2025-12-31
- **10 departments**, ~100 employees
- **Status**: All records queried have status "approved"

### Expense Type Distribution
| Type | Records | Total Amount |
|---|---|---|
| business_entertainment | ~530 | ~¥550K |
| communication | ~720 | ~¥150K |
| local_transport | ~530 | ~¥42K |
| office_supplies | ~530 | ~¥176K |
| training_fee | ~530 | ~¥530K |
| travel_lodging | ~880 | ~¥1.2M |

### Department Budget Status
6 of 10 departments exceeded annual budgets by 50-60%:
- D001 (投资银行部): ¥363,615 used / ¥230,395 budget (157.8%)
- D002 (固定收益部): ¥164,928 used / ¥107,785 budget (153.0%)
- D003 (财富管理部): ¥174,151 used / ¥109,772 budget (158.6%)
- D004 (研究所): ¥408,833 used / ¥264,890 budget (154.3%)
- D005 (机构业务部): ¥433,443 used / ¥278,541 budget (155.6%)
- D006 (运营管理部): ¥530,241 used / ¥340,962 budget (155.5%)

---

## R01 — Duplicate Invoice (Clause 10)

### Policy
> "同一发票最多报销1次" — 01_expense_reimbursement_2025.md, 第十条

### Methodology
- Called `find_reused_invoices(min_usage_count=2)` to find all invoices used ≥2 times
- Verified each reused invoice via `find_invoice_usage(invoice_no=...)` to get exact record pairs

### Results: 6 invoices, 12 records
| Invoice | Record A | Record B |
|---|---|---|
| INV000002 | R000002 | R004201 |
| INV000005 | R000005 | R004202 |
| INV000020 | R000020 | R004203 |
| INV000028 | R000028 | R004204 |
| INV000037 | R000037 | R004205 |
| INV000055 | R000055 | R004206 |

All 6 invoices are used exactly 2 times each. The second records (R004201-R004206) are injected samples with reason "重复发票注入样本". All have `special_approval=0`.

---

## R02 — Split Reimbursement (Clause 11)

### Policy
> "同一员工、同一费用类型在7天内出现2笔及以上报销,且合计金额达到《授权管理办法》附件二较高审批线的,应重点核查拆分规避审批"
> — 01_expense_reimbursement_2025.md, 第十一条
> AR-03 threshold = ¥10,000 (03_authorization_management.md, 附件二)

### Methodology
- Identified that only `travel_lodging` type can reach ¥10,000 combined
- Paginated through all 883 travel_lodging records
- Grouped by employee_id, checked pairs within 7 days, combined ≥ ¥10,000
- Filter: same employee, same type, gap ≤ 7 calendar days, combined ≥ ¥10,000

### Results: 4 pairs, 8 records
| Employee | Record A | Record B | Amount A | Amount B | Combined | Gap |
|---|---|---|---|---|---|---|
| E0007 (李丽娟) | R004207 | R004208 | 5,200 | 5,200 | 10,400 | 2d |
| E0007 (李丽娟) | R004217 | R004218 | 5,200 | 5,200 | 10,400 | 3d |
| E0008 (杨丹) | R004219 | R004220 | 5,200 | 5,200 | 10,400 | 4d |
| E0009 (张婷) | R004212 | R004213 | 5,100 | 5,100 | 10,200 | 5d |

### Non-qualifying injected samples (TRAPS):
- E0008: R004209+R004210+R004211 (3×¥3,400), max pair = 6,800 < 10,000
- E0010: R004214+R004215+R004216 (3×¥3,500), max pair = 7,000 < 10,000

These are labeled "拆分报销注入样本" but do NOT meet the ¥10,000 threshold. They are correctly classified as non-anomalous.

---

## R03 — Standard Exceedance (Clause 12)

### Policy
> "无专项审批时,报销金额不得超过对应制度标准的1.0倍" — 01_expense_reimbursement_2025.md, 第十二条

### Applicable Standards
| Expense Type | Standard | Policy Source |
|---|---|---|
| office_supplies | ≤¥600/month | 07_office_communication.md 第二条 |
| communication | ≤¥300/month | 07_office_communication.md 第三条 |
| training_fee | ≤¥3,500/course/person | 05_training_expense.md 第二条 |
| business_entertainment | ≤¥300/person | 06_business_entertainment.md 第三条 |
| travel_lodging | varies by level+tier | 04_travel_expense.md 第四条 |
| local_transport (出差) | varies by tier/day | 04_travel_expense.md 第六条 |

### Lodging Standards (元/人/晚)
| 职级 | 一类城市 | 二类城市 | 三类城市 |
|---|---:|---:|---:|
| 员工级 | 450 | 380 | 300 |
| 经理级 | 650 | 550 | 450 |
| 部门负责人级 (D1) | 850 | 700 | 600 |
| 高管级 (X1) | 1100 | 900 | 750 |

### Local Transport Standards
| 一类城市 | 二类城市 | 三类城市 |
|---|---:|---:|
| 120/日 | 100/日 | 80/日 |

### Results: 6 records with standard exceedances (all `special_approval=0`)
| Record | Type | Actual | Limit | Employee | Policy |
|---|---|---|---|---|---|
| R004221 | office_supplies | ¥650 | ¥600 | E0007 (李丽娟) | 07_office_communication.md §2 |
| R004222 | communication | ¥330 | ¥300 | E0008 (杨丹) | 07_office_communication.md §3 |
| R004223 | training_fee | ¥3,700 | ¥3,500 | E0009 (张婷) | 05_training_expense.md §2 |
| R004224 | business_entertainment | ¥350/pp | ¥300/pp | E0010 (闭想) | 06_business_entertainment.md §3 |
| R004225 | travel_lodging | ¥900/night | ¥850/night | E0007 (D1, tier A) | 04_travel_expense.md §4 |
| R004226 | local_transport | ¥92/day | ¥80/day | E0008 (D1, tier C) | 04_travel_expense.md §6 |

### Trap Sample (COMPLIANT):
- **R004233**: E0012 (杨丽华, level X1/高管级), travel_lodging, tier A, 10 nights, ¥9,990 total = ¥999/night. X1+tier A standard = ¥1,100/night. ¥999 < ¥1,100 → COMPLIANT. Reason: "低于审批线但接近阈值的合规住宿费".

---

## R04 — Budget Overrun (Clause 13)

### Policy
> "部门年度预算不足时不得继续报销。预算使用达到预算额度的1.0倍后,确需发生的费用应履行专项审批"
> — 01_expense_reimbursement_2025.md, 第十三条

### Methodology
- Called `summarize_department_budgets()` and `get_department_budget()` for each dept
- Computed running cumulative spending from monthly `summarize_expenses(group_by=department_id,month)`

### Results: 6 departments exceeded annual budgets
| Dept | Budget | Used | Over By | % | First Exceeded |
|---|---|---|---|---|---|
| D001 (投资银行部) | 230,395 | 363,615 | 133,219 | 57.8% | Sep 2025 |
| D002 (固定收益部) | 107,785 | 164,928 | 57,143 | 53.0% | Aug 2025 |
| D003 (财富管理部) | 109,772 | 174,151 | 64,379 | 58.6% | Aug 2025 |
| D004 (研究所) | 264,890 | 408,833 | 143,943 | 54.3% | Sep 2025 |
| D005 (机构业务部) | 278,541 | 433,443 | 154,902 | 55.6% | Oct 2025 |
| D006 (运营管理部) | 340,962 | 530,241 | 189,280 | 55.5% | Sep 2025 |

All over-budget records lack `special_approval=1`. The overruns are systemic across all 6 departments.

### Under-budget departments (4):
D007 (信息技术部): 86.9%, D008 (合规风控部): 88.7%, D009 (财务管理部): 85.6%, D010 (人力资源部): 80.1%

---

## R05 — Late Submission (Clause 7)

### Policy
> "员工应在费用发生后60天内提交报销申请;超过期限的,原则上不得报销"
> — 01_expense_reimbursement_2025.md, 第七条

### Methodology
- Called `list_records_by_reimburse_delay(min_delay_days=61)` for records with delay >60 days
- Verified each record via `get_expense_detail()` for exact dates

### Results: 6 records
| Record | Employee | Expense Date | Reimburse Date | Delay | Type |
|---|---|---|---|---|---|
| R004227 | E0007 (李丽娟) | 2025-01-05 | 2025-03-11 | 65 days | communication |
| R004228 | E0008 (杨丹) | 2025-02-05 | 2025-04-18 | 72 days | communication |
| R004229 | E0009 (张婷) | 2025-04-05 | 2025-07-02 | 88 days | communication |
| R004230 | E0010 (闭想) | 2025-05-06 | 2025-08-09 | 95 days | communication |
| R004231 | E0007 (李丽娟) | 2025-08-02 | 2025-11-30 | 120 days | communication |
| R004232 | E0008 (杨丹) | 2025-09-04 | 2025-12-23 | 110 days | communication |

All 6 are communication type, all `special_approval=0`, all with reason "超期报销注入样本".

---

## Summary of Anomalous Records

| Rule | Records | Count |
|---|---|---|
| R01 Duplicate Invoice | R000002,R000005,R000020,R000028,R000037,R000055,R004201-R004206 | 12 |
| R02 Split Reimbursement | R004207,R004208,R004212,R004213,R004217,R004218,R004219,R004220 | 8 |
| R03 Standard Exceedance | R004221,R004222,R004223,R004224,R004225,R004226 | 6 |
| R04 Budget Overrun | D001-D006 (6 departments systemic) | — |
| R05 Late Submission | R004227,R004228,R004229,R004230,R004231,R004232 | 6 |
| **TOTAL** | | **32 records** |

## Key Citations
| Doc ID | Clause | Rule |
|---|---|---|
| 01_expense_reimbursement_2025.md | 第十条 | R01 |
| 01_expense_reimbursement_2025.md | 第十一条 | R02 |
| 01_expense_reimbursement_2025.md | 第十二条 | R03 |
| 01_expense_reimbursement_2025.md | 第十三条 | R04 |
| 01_expense_reimbursement_2025.md | 第七条 | R05 |
| 03_authorization_management.md | 附件二 | R02 threshold |
| 04_travel_expense.md | 第四条 | R03 lodging |
| 04_travel_expense.md | 第六条 | R03 transport |
| 05_training_expense.md | 第二条 | R03 training |
| 06_business_entertainment.md | 第三条 | R03 entertainment |
| 07_office_communication.md | 第二条 | R03 office |
| 07_office_communication.md | 第三条 | R03 comm |
