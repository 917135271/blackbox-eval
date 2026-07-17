# Duplicate Invoice Scanner — Query & Analysis Log
## Date: 2026-07-16
## Rule: Article 10 (第十条) — 同一发票最多报销1次

---

## Step 1: Policy Confirmation
### Tool: search_policy
### Query: "同一发票最多报销1次 重复发票 第十条"
### Result: doc_id=01_expense_reimbursement_2025.md, score=28.87
### Snippet: "第十条 同一发票最多报销1次。发现同一发票在不同报销单中重复出现的,应认定为重复报销风险。"

---

## Step 2: Find Reused Invoices (Page 1)
### Tool: find_reused_invoices(min_usage_count=2, page=1, page_size=50)
### Result: total=6, has_next=false
### Invoices found:
| invoice_no        | vendor_name    | invoice_date | amount  | expense_type           | usage_count | record_ids           |
|-------------------|----------------|-------------|---------|------------------------|-------------|----------------------|
| FP202500000002    | XX供应商7753    | 2025-08-19  | 423.79  | office_supplies        | 2           | R000002, R004201     |
| FP202500000005    | XX供应商5450    | 2025-06-07  | 88.83   | local_transport        | 2           | R000005, R004202     |
| FP202500000020    | XX供应商2706    | 2025-01-05  | 669.50  | travel_lodging         | 2           | R000020, R004203     |
| FP202500000028    | XX供应商1999    | 2025-03-09  | 165.58  | communication          | 2           | R000028, R004204     |
| FP202500000037    | XX供应商7354    | 2025-03-30  | 84.72   | local_transport        | 2           | R000037, R004205     |
| FP202500000055    | XX供应商4962    | 2025-04-03  | 999.76  | business_entertainment | 2           | R000055, R004206     |

---

## Step 3: Verify Each Invoice Usage
### Tool: find_invoice_usage × 6 (parallel)
### All 6 invoices confirmed: exactly 2 records each, no additional hidden usages.

| invoice_no      | record_id | employee   | expense_date | reimburse_date | amount | reason_has_injection_marker |
|-----------------|-----------|------------|-------------|---------------|--------|-----------------------------|
| FP202500000002  | R000002   | 姚瑜(E0050)| 2025-08-19  | 2025-09-09    | 423.79 | No                          |
| FP202500000002  | R004201   | 姚瑜(E0050)| 2025-02-10  | 2025-02-18    | 423.79 | Yes (重复发票注入样本)       |
| FP202500000005  | R000005   | 刘冬梅(E0022)| 2025-06-07| 2025-08-05    | 88.83  | No                          |
| FP202500000005  | R004202   | 刘冬梅(E0022)| 2025-03-10| 2025-03-18    | 88.83  | Yes (重复发票注入样本)       |
| FP202500000020  | R000020   | 杜丹(E0028)| 2025-01-05  | 2025-02-28    | 669.50 | No                          |
| FP202500000020  | R004203   | 杜丹(E0028)| 2025-04-10  | 2025-04-18    | 669.50 | Yes (重复发票注入样本)       |
| FP202500000028  | R000028   | 张林(E0036)| 2025-03-09  | 2025-05-05    | 165.58 | No                          |
| FP202500000028  | R004204   | 张林(E0036)| 2025-05-10  | 2025-05-18    | 165.58 | Yes (重复发票注入样本)       |
| FP202500000037  | R000037   | 唐静(E0027)| 2025-03-30  | 2025-04-20    | 84.72  | No                          |
| FP202500000037  | R004205   | 唐静(E0027)| 2025-06-10  | 2025-07-25    | 84.72  | Yes (重复发票注入样本)       |
| FP202500000055  | R000055   | 陈洋(E0020)| 2025-04-03  | 2025-05-10    | 999.76 | No                          |
| FP202500000055  | R004206   | 陈洋(E0020)| 2025-07-10  | 2025-08-24    | 999.76 | Yes (重复发票注入样本)       |

---

## Step 4: Full Detail Retrieval
### Tool: get_expense_detail × 12 (parallel)
### Key findings from full detail:
- All 12 records: status = "approved"
- All 12 records: special_approval = 0 (no special approval)
- All 12 records: budget_year = 2025
- All 6 duplicate groups: same employee, same department, same amount
- Pattern: "X" suffixed record_no (BX2025X00xxxx) = injected duplicate samples with "重复发票注入样本:" prefix

---

## Step 5: Scope Confirmation
### Tool: summarize_expenses(date_from=2025-01-01, date_to=2025-12-31, group_by=status)
### Result: 4,240 approved records in 2025 scope, total ¥2,923,724.49

---

## Step 6: Article 10 Assessment
### Rule: 同一发票最多报销1次 (absolute — no exemption for special approval)
### Finding: All 6 invoices used ×2 → 6 confirmed duplicate reimbursement anomalies
### Excess: ¥2,432.18 (sum of second reimbursements for each invoice)

---

## Summary
| Metric                    | Value   |
|---------------------------|---------|
| 2025 records in scope     | 4,240   |
| Reused invoices (≥2 uses) | 6       |
| Anomaly records           | 12      |
| Duplicate groups          | 6       |
| Total excess amount       | ¥2,432.18 |
| special_approval=1 records| 0       |
| Decision                  | REJECT  |
