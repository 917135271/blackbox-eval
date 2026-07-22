import json, sys

# Department budgets from summarize_department_budgets
departments = {
    "D001": {"name": "投资银行部", "annual_budget": 230395.17},
    "D002": {"name": "固定收益部", "annual_budget": 107785.42},
    "D003": {"name": "财富管理部", "annual_budget": 109772.07},
    "D004": {"name": "研究所", "annual_budget": 264890.39},
    "D005": {"name": "机构业务部", "annual_budget": 278540.94},
    "D006": {"name": "运营管理部", "annual_budget": 340961.75},
}

# Collect all records into one list
all_records = []

# Read all JSON files from data collection
import os
data_dir = "/workspace/work/raw_data"
for fname in sorted(os.listdir(data_dir)):
    if fname.endswith(".json"):
        with open(os.path.join(data_dir, fname)) as f:
            data = json.load(f)
            for rec in data.get("records", []):
                all_records.append(rec)

print(f"Total records loaded: {len(all_records)}")

# Group by department
by_dept = {}
for r in all_records:
    did = r["department_id"]
    if did not in by_dept:
        by_dept[did] = []
    by_dept[did].append(r)

# Sort each department by reimburse_date then record_id
for did in by_dept:
    by_dept[did].sort(key=lambda x: (x["reimburse_date"], x["record_id"]))

# Find first record exceeding budget without special_approval
results = []
for did in departments:
    budget = departments[did]["annual_budget"]
    cumsum = 0.0
    violation_record = None
    
    for rec in by_dept[did]:
        cumsum += rec["amount"]
        if cumsum > budget and rec["special_approval"] == 0:
            violation_record = rec
            break
    
    if violation_record:
        results.append({
            "department_id": did,
            "department_name": departments[did]["name"],
            "annual_budget": budget,
            "cumulative_at_violation": round(cumsum, 2),
            "violation_record_id": violation_record["record_id"],
            "violation_reimburse_date": violation_record["reimburse_date"],
            "violation_amount": violation_record["amount"],
            "record_count": len(by_dept[did])
        })

print("\nBudget violation summary:")
for r in sorted(results, key=lambda x: x["department_id"]):
    print(f"  {r['department_id']} {r['department_name']}: budget={r['annual_budget']}, "
          f"cumsum={r['cumulative_at_violation']}, "
          f"violation_record={r['violation_record_id']} on {r['violation_reimburse_date']}, "
          f"amount={r['violation_amount']}, total_records={r['record_count']}")

# Save results
with open("/workspace/work/analysis_result.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print("\nResults saved to work/analysis_result.json")
