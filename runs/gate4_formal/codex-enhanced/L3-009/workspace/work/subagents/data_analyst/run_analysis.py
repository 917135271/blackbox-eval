import sqlite3
import json
from datetime import datetime
from collections import defaultdict

DB = "/benchmark/data/expense.db"
conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

# ============================================================
# Load all data with department_name
# ============================================================
rows = conn.execute("""
    SELECT r.*, i.invoice_no, i.vendor_name, i.invoice_date AS inv_date,
           e.employee_level, e.position_role, d.annual_budget, d.department_name
    FROM expense_records r
    JOIN invoices i ON r.invoice_id = i.invoice_id
    JOIN employees e ON r.employee_id = e.employee_id
    JOIN departments d ON r.department_id = d.department_id
    WHERE r.expense_date >= '2025-01-01' AND r.expense_date <= '2025-12-31'
    ORDER BY r.record_id
""").fetchall()

all_records = [dict(r) for r in rows]
print(f"Loaded {len(all_records)} records")

# ============================================================
# Travel accommodation standards (city: A=T1, B=T2, C=T3)
# ============================================================
LODGING_STANDARD = {
    "E1": {"A": 450, "B": 380, "C": 300},   # 员工级
    "M1": {"A": 650, "B": 550, "C": 450},   # 经理级
    "D1": {"A": 850, "B": 700, "C": 600},   # 部门负责人级
    "X1": {"A": 1100, "B": 900, "C": 750},  # 高管级
}
LOCAL_TRANSPORT_STANDARD = {"A": 120, "B": 100, "C": 80}

# ============================================================
# QUERY 1: DUPLICATE REIMBURSEMENT
# ============================================================
print("\n=== Q1: DUPLICATE REIMBURSEMENT ===")
inv_counts = defaultdict(list)
for r in all_records:
    inv_counts[r["invoice_no"]].append(r)

dup_invoices = {inv: recs for inv, recs in inv_counts.items() if len(recs) >= 2}
q1_findings = []
for inv_no, recs in sorted(dup_invoices.items()):
    finding = {
        "finding_type": "duplicate_reimbursement",
        "invoice_no": inv_no,
        "record_ids": sorted([r["record_id"] for r in recs]),
        "amounts": [r["amount"] for r in recs],
        "total_amount": sum(r["amount"] for r in recs),
        "details": [{"record_id": r["record_id"], "employee_id": r["employee_id"],
                      "amount": r["amount"], "expense_date": r["expense_date"],
                      "expense_type": r["expense_type"]} for r in recs]
    }
    q1_findings.append(finding)
    print(f"  INV {inv_no}: {finding['record_ids']}")

# ============================================================
# QUERY 2: SPLIT REIMBURSEMENT
# ============================================================
print("\n=== Q2: SPLIT REIMBURSEMENT ===")
emp_type_groups = defaultdict(list)
for r in all_records:
    emp_type_groups[(r["employee_id"], r["expense_type"])].append(r)

for key in emp_type_groups:
    emp_type_groups[key].sort(key=lambda x: x["expense_date"])

q2_findings = []
for (emp_id, exp_type), recs in emp_type_groups.items():
    if len(recs) < 2:
        continue
    used = set()
    for i in range(len(recs)):
        if recs[i]["record_id"] in used:
            continue
        window = [recs[i]]
        base_date = datetime.strptime(recs[i]["expense_date"], "%Y-%m-%d")
        for j in range(i+1, len(recs)):
            curr_date = datetime.strptime(recs[j]["expense_date"], "%Y-%m-%d")
            if (curr_date - base_date).days <= 7:
                window.append(recs[j])
            else:
                break
        if len(window) >= 2:
            total = sum(r["amount"] for r in window)
            if total >= 3000:
                for r in window:
                    used.add(r["record_id"])
                q2_findings.append({
                    "finding_type": "split_reimbursement",
                    "employee_id": emp_id,
                    "expense_type": exp_type,
                    "record_ids": sorted([r["record_id"] for r in window]),
                    "total_amount": round(total, 2),
                    "window_start": window[0]["expense_date"],
                    "window_end": window[-1]["expense_date"],
                    "details": [{"record_id": r["record_id"], "amount": r["amount"],
                                  "expense_date": r["expense_date"]} for r in window]
                })

print(f"Q2 total split findings: {len(q2_findings)}")

# ============================================================
# QUERY 3: OVER-STANDARD
# ============================================================
print("\n=== Q3: OVER-STANDARD ===")
q3_findings = []
q3_subcounts = defaultdict(int)

for r in all_records:
    rid = r["record_id"]
    amt = r["amount"]
    etype = r["expense_type"]
    spec_app = r["special_approval"]
    if spec_app:
        continue

    emp_level = r["employee_level"]
    city = r["city_tier"]
    nights = r["nights"] or 0
    days_val = r["days"] or 0

    # a) business_entertainment: amount > 5000
    if etype == "business_entertainment" and amt > 5000:
        q3_findings.append({
            "finding_type": "over_standard", "sub_type": "business_entertainment_exceed",
            "record_id": rid, "amount": amt, "threshold": 5000,
            "policy": "06_business_entertainment.md Art.2"
        })
        q3_subcounts["be"] += 1
        continue

    # b) training: amount > 3500
    if etype == "training_fee" and amt > 3500:
        q3_findings.append({
            "finding_type": "over_standard", "sub_type": "training_exceed",
            "record_id": rid, "amount": amt, "threshold": 3500,
            "policy": "05_training_expense.md Art.2"
        })
        q3_subcounts["training"] += 1
        continue

    # c) travel_lodging: per-night check
    if etype == "travel_lodging" and city and emp_level:
        std = LODGING_STANDARD.get(emp_level, {}).get(city, None)
        if std is not None and nights > 0:
            per_night = amt / nights
            if per_night > std:
                q3_findings.append({
                    "finding_type": "over_standard", "sub_type": "travel_lodging_exceed",
                    "record_id": rid, "amount": amt, "per_night": round(per_night, 2),
                    "standard": std, "city_tier": city, "employee_level": emp_level,
                    "nights": nights, "policy": "04_travel_expense.md Art.4"
                })
                q3_subcounts["lodging"] += 1
                continue

    # d) local_transport: per-day check
    if etype == "local_transport" and city and days_val > 0:
        std = LOCAL_TRANSPORT_STANDARD.get(city, None)
        if std is not None:
            per_day = amt / days_val
            if per_day > std:
                q3_findings.append({
                    "finding_type": "over_standard", "sub_type": "local_transport_exceed",
                    "record_id": rid, "amount": amt, "per_day": round(per_day, 2),
                    "standard": std, "city_tier": city, "days": days_val,
                    "policy": "04_travel_expense.md Art.6"
                })
                q3_subcounts["transport"] += 1
                continue

    # e) office_supplies: single > 600
    if etype == "office_supplies" and amt > 600:
        q3_findings.append({
            "finding_type": "over_standard", "sub_type": "office_supplies_exceed",
            "record_id": rid, "amount": amt, "threshold": 600,
            "policy": "07_office_communication.md Art.2"
        })
        q3_subcounts["office"] += 1
        continue

    # f) communication: single > 300
    if etype == "communication" and amt > 300:
        q3_findings.append({
            "finding_type": "over_standard", "sub_type": "communication_exceed",
            "record_id": rid, "amount": amt, "threshold": 300,
            "policy": "07_office_communication.md Art.3"
        })
        q3_subcounts["comm"] += 1
        continue

print(f"Q3 total: {len(q3_findings)} | Sub-counts: {dict(q3_subcounts)}")

# ============================================================
# QUERY 4: OVER-BUDGET
# ============================================================
print("\n=== Q4: OVER-BUDGET ===")
q4_findings = []

dept_records = defaultdict(list)
for r in all_records:
    if r["status"] == "approved":
        dept_records[r["department_id"]].append(r)

for dept_id in dept_records:
    dept_records[dept_id].sort(key=lambda x: (x["reimburse_date"], x["record_id"]))

for dept_id, recs in sorted(dept_records.items()):
    budget = recs[0]["annual_budget"] if recs else 0
    if budget == 0:
        continue
    cumulative = 0.0
    dept_name = recs[0]["department_name"]
    first_exceed = None
    for r in recs:
        cumulative += r["amount"]
        if cumulative > budget and r["special_approval"] == 0 and first_exceed is None:
            first_exceed = r
            q4_findings.append({
                "finding_type": "over_budget",
                "department_id": dept_id,
                "department_name": dept_name,
                "record_id": r["record_id"],
                "annual_budget": budget,
                "cumulative_at_record": round(cumulative, 2),
                "reimburse_date": r["reimburse_date"],
                "amount": r["amount"],
                "policy": "08_budget_management.md Art.3"
            })
            break
    if first_exceed:
        print(f"  {dept_id} {dept_name}: budget={budget} first exceed RID={first_exceed['record_id']} cum={cumulative:.2f}")
    else:
        print(f"  {dept_id} {dept_name}: budget={budget} NO exceed found")

print(f"Q4 total: {len(q4_findings)}")

# ============================================================
# QUERY 5: OVERDUE REIMBURSEMENT
# ============================================================
print("\n=== Q5: OVERDUE REIMBURSEMENT ===")
q5_findings = []

for r in all_records:
    exp_date = datetime.strptime(r["expense_date"], "%Y-%m-%d")
    reimb_date = datetime.strptime(r["reimburse_date"], "%Y-%m-%d")
    days = (reimb_date - exp_date).days
    if days > 60:
        q5_findings.append({
            "finding_type": "overdue_reimbursement",
            "record_id": r["record_id"],
            "employee_id": r["employee_id"],
            "expense_date": r["expense_date"],
            "reimburse_date": r["reimburse_date"],
            "days": days,
            "amount": r["amount"],
            "expense_type": r["expense_type"],
            "policy": "01_expense_reimbursement_2025.md Art.7"
        })

print(f"Q5 total: {len(q5_findings)}")

# ============================================================
# SAVE RESULTS
# ============================================================
analysis = {
    "total_records": len(all_records),
    "query1_duplicate_reimbursement": {"count": len(q1_findings), "findings": q1_findings},
    "query2_split_reimbursement": {"count": len(q2_findings), "findings": q2_findings},
    "query3_over_standard": {"count": len(q3_findings), "findings": q3_findings},
    "query4_over_budget": {"count": len(q4_findings), "findings": q4_findings},
    "query5_overdue": {"count": len(q5_findings), "findings": q5_findings}
}

with open("/workspace/work/subagents/data_analyst/analysis.json", "w") as f:
    json.dump(analysis, f, ensure_ascii=False, indent=2)

# All unique record IDs
all_finding_ids = sorted(set(
    rid for q in [q1_findings, q2_findings, q3_findings, q4_findings, q5_findings]
    for f in q
    for rid in (f.get("record_ids", [f.get("record_id")]) if "record_ids" in f else [f["record_id"]])
))
print(f"\nTotal unique record IDs in findings: {len(all_finding_ids)}")

summary = {
    "decision": "reject",
    "key_findings": [
        f"Q1 Duplicate Reimbursement: {len(q1_findings)} invoice(s) reused across multiple records (Policy Art.10 violation)",
        f"Q2 Split Reimbursement: {len(q2_findings)} split groups detected (same employee/type within 7-day window, total >= 3000)",
        f"Q3 Over-Standard: {len(q3_findings)} single-record standard violations (BE:{q3_subcounts.get('be',0)} TR:{q3_subcounts.get('training',0)} LODGING:{q3_subcounts.get('lodging',0)} TRANS:{q3_subcounts.get('transport',0)} OFFICE:{q3_subcounts.get('office',0)} COMM:{q3_subcounts.get('comm',0)})",
        f"Q4 Over-Budget: {len(q4_findings)} department(s) exceeded annual budget without special approval",
        f"Q5 Overdue Reimbursement: {len(q5_findings)} record(s) with reimbursement delay exceeding 60 days"
    ],
    "record_ids": all_finding_ids,
    "citations": [
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "10"},
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "11"},
        {"doc_id": "01_expense_reimbursement_2025.md", "clause_no": "7"},
        {"doc_id": "03_authorization_management.md", "clause_no": "附件二"},
        {"doc_id": "04_travel_expense.md", "clause_no": "4"},
        {"doc_id": "04_travel_expense.md", "clause_no": "6"},
        {"doc_id": "05_training_expense.md", "clause_no": "2"},
        {"doc_id": "06_business_entertainment.md", "clause_no": "2"},
        {"doc_id": "07_office_communication.md", "clause_no": "2"},
        {"doc_id": "07_office_communication.md", "clause_no": "3"},
        {"doc_id": "08_budget_management.md", "clause_no": "3"}
    ],
    "unresolved_items": [],
    "artifact_paths": [
        "work/subagents/data_analyst/analysis.json",
        "work/subagents/data_analyst/summary.json"
    ]
}

with open("/workspace/work/subagents/data_analyst/summary.json", "w") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print("\nAnalysis complete. Files saved.")
conn.close()
