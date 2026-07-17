# Expense Audit Analysis Notes
## Data Analyst Subagent — Invocation 43ff5975-5ace-4af7-9d1f-b31037116e3e

---

## Scope

- **21 records**: R900001 through R900021
- **4 employees**: E9001(员工甲/员工级), E9002(经理乙/经理级), E9003(员工丙/员工级), E9004(经理丁/部门负责人级)
- **2 departments**: D901(开发审计一部, budget=200000), D902(开发审计二部, budget=50000)
- **5 rules**: Duplicate(Art.10), Split(Art.11), Over-Standard(Art.12), Overdue(Art.7/9), Over-Budget(Art.13/08.Art.3)

---

## Methodology

1. Retrieved all 21 records via `get_expense_detail`, each with embedded approvals
2. Found reused invoices via `find_reused_invoices` → only INV900001 (FPDEV900001) used 2x
3. Verified policy clauses by reading full policy MD files from `/benchmark/data/corpus/`
4. Computed all figures via Python reconciliation script
5. Applied special_approval=1 as exemption under Art.12 and Art.13

---

## Rule-by-Rule Analysis

### Rule 1: Duplicate Reimbursement (Art.10)
- **Invoice INV900001** used by both R900001 and R900002
- Both records are anomalous
- No other reused invoices found

### Rule 2: Split Reimbursement (Art.11)
- **E9001 + travel_transport**: R900003(Feb 3, 5200) & R900004(Feb 6, 5200) → 3 days gap, 10400 total ≥ AR-03(10000)
- R900010+R900011: 8 days gap → NOT within 7 days
- R900014+R900015: 17 days gap → NOT within 7 days
- No other employee-type groups have qualifying pairs

### Rule 3: Over-Standard (Art.12)

**3a. Office Supplies (07 Art.2: ≤600/mo/employee)**:
- E9001 Jan: R900001+R900002=960 BUT duplicate invoices → primary violation is Rule-1, not separately flagged here
- E9001 Apr: R900007=650 > 600 → ANOMALY
- E9001 May: R900008=590 ≤ 600 → OK
- E9002 May: R900009=590 ≤ 600 → OK

**3b. Communication (07 Art.3: ≤300/mo/employee)**:
- E9001 Mar: R900006=200 ≤ 300 → OK
- E9001 Sep: R900014(180)+R900015(160)=340 > 300 → ANOMALY

**3c. Travel Lodging (04 Art.4)**:
- R900013: E9002(经理级), 一类城市, 2晚, 1400 → 700/晚 > 650×1.0 → ANOMALY

**3d. Training Fee (05 Art.3)**:
- R900016: Internal training 1 day 850 > 800 → ANOMALY

**3e. Training Lodging (05 Art.5)**:
- R900021: 一类城市 1晚 480 ≤ 500 → OK

**3f. Business Entertainment (06 Art.2, Art.3)**:
- R900005: 3600 ≤ 5000(event OK), 3600/10=360 > 300(person OVER) → ANOMALY
- R900017: 5200 > 5000(event OVER), 5200/20=260 ≤ 300(person OK) → ANOMALY

### Rule 4: Overdue (Art.7, Art.9)
- R900006: 2025-03-01 → 2025-05-05 = 65 days > 60 → ANOMALY
- R900012: 2025-12-20 → 2026-01-10 = 21 days, year-end Art.9 exempt (≤Jan 15) → CLEAR
- All other records ≤ 10 days → OK

### Rule 5: Over-Budget (Art.13, 08 Art.3)
- D902 budget=50000:
  - R900018(45000, Jan 15): cum=45000, rate=0.90 → OK
  - R900019(6000, Feb 15): cum=51000, rate=1.02 → BREACH, special_approval=0 → ANOMALY
  - R900020(5000, Mar 15): cum=56000, rate=1.12 → BREACH, special_approval=1 → CLEARED
- D901 budget=200000, used=36760 → far under budget

---

## Exemptions Applied

| Record | Rule | Exemption |
|--------|------|-----------|
| R900020 | Rule-5 | special_approval=1 → Art.12/Art.13 exempt |
| R900012 | Rule-4 | Year-end Art.9: Dec expense, submitted Jan 10 ≤ Jan 15 |
| R900001,R900002 | Rule-3a | Duplicate invoice caught under Rule-1; overage is consequential, not separately flagged |

---

## Anomalous Records (13)
R900001, R900002, R900003, R900004, R900005, R900006, R900007, R900013, R900014, R900015, R900016, R900017, R900019

## Non-Anomalous (8)
R900008, R900009, R900010, R900011, R900012, R900018, R900020, R900021

---

## Citations Used
- 01_expense_reimbursement_2025.md: 第七条, 第九条, 第十条, 第十一条, 第十二条, 第十三条
- 03_authorization_management.md: 附件二 (AR-03 ≥10000)
- 04_travel_expense.md: 第四条 (住宿标准表: 经理级一类城市650)
- 05_training_expense.md: 第三条 (内部培训≤800/日), 第五条 (培训住宿一类城市500)
- 06_business_entertainment.md: 第二条 (≤5000/次), 第三条 (≤300/人)
- 07_office_communication.md: 第二条 (≤600/月), 第三条 (≤300/月)
- 08_budget_management.md: 第三条 (1.0倍后不得继续报销)

---

## Unresolved Items
- None. All 21 records fully analyzed. All figures reconciled with database data. No missing data.
