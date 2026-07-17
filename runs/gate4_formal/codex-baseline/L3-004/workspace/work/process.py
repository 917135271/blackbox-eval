import json

# Budget data from summarize_department_budgets
budgets = {
    "D001": 230395.17,
    "D002": 107785.42,
    "D003": 109772.07,
    "D004": 264890.39,
    "D005": 278540.94,
    "D006": 340961.75,
}

# Load all records
with open("/workspace/work/all_records.json") as f:
    all_records = json.load(f)

# Group by department
dept_records = {}
for r in all_records:
    dept = r["department_id"]
    if dept not in dept_records:
        dept_records[dept] = []
    dept_records[dept].append(r)

# Sort each department by expense_date
for dept in dept_records:
    dept_records[dept].sort(key=lambda r: r["expense_date"])

# Compute violations: first record where cumulative exceeds budget, and all after
violations = {}
for dept in sorted(dept_records.keys()):
    if dept not in budgets:
        continue
    budget = budgets[dept]
    cum = 0.0
    viol_ids = []
    for r in dept_records[dept]:
        cum += r["amount"]
        if cum > budget:
            viol_ids.append(r["record_id"])
    violations[dept] = viol_ids
    print(f"{dept}: budget={budget:.2f}, total_records={len(dept_records[dept])}, cum={cum:.2f}, violations={len(viol_ids)}")
    # Print first and last violation for verification
    if viol_ids:
        first_r = next(r for r in dept_records[dept] if r["record_id"] == viol_ids[0])
        last_r = next(r for r in dept_records[dept] if r["record_id"] == viol_ids[-1])
        # Find cum before first violation
        cum_before = 0.0
        for r in dept_records[dept]:
            if r["record_id"] == viol_ids[0]:
                break
            cum_before += r["amount"]
        cum_at_first = cum_before + first_r["amount"]
        print(f"  First violation: {viol_ids[0]} date={first_r['expense_date']} cum_before={cum_before:.2f} cum_at={cum_at_first:.2f}")

# Build all_record_ids
all_record_ids = []
for dept in sorted(violations.keys()):
    all_record_ids.extend(violations[dept])

print(f"\nTotal violation records: {len(all_record_ids)}")
print(f"Unique violation records: {len(set(all_record_ids))}")

# Save violations for later use
with open("/workspace/work/violations.json", "w") as f:
    json.dump(violations, f, indent=2)

with open("/workspace/work/all_violation_ids.json", "w") as f:
    json.dump(all_record_ids, f)

print("\nViolations saved to /workspace/work/violations.json")
