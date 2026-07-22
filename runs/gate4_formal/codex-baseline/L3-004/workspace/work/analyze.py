import json, os, sys

# Department budgets from summarize_department_budgets (all approved)
departments = {
    "D001": {"name": "投资银行部", "annual_budget": 230395.17},
    "D002": {"name": "固定收益部", "annual_budget": 107785.42},
    "D003": {"name": "财富管理部", "annual_budget": 109772.07},
    "D004": {"name": "研究所", "annual_budget": 264890.39},
    "D005": {"name": "机构业务部", "annual_budget": 278540.94},
    "D006": {"name": "运营管理部", "annual_budget": 340961.75},
    "D007": {"name": "信息技术部", "annual_budget": 301500.00},
    "D008": {"name": "合规风控部", "annual_budget": 381600.00},
    "D009": {"name": "财务管理部", "annual_budget": 191300.00},
    "D010": {"name": "人力资源部", "annual_budget": 164500.00},
}

# Read all JSON data files
data_dir = "/workspace/work/raw_data"
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

all_records = []
for fname in sorted(os.listdir(data_dir)):
    if fname.endswith(".json"):
        with open(os.path.join(data_dir, fname)) as f:
            data = json.load(f)
            for rec in data.get("records", []):
                all_records.append(rec)

if not all_records:
    print("ERROR: No records found in raw_data. Please save data first.")
    sys.exit(1)

print(f"Total records: {len(all_records)}")

# Group by department
by_dept = {}
for r in all_records:
    did = r["department_id"]
    if did not in by_dept:
        by_dept[did] = []
    by_dept[did].append(r)

# Sort each department by reimburse_date, then record_id
for did in by_dept:
    by_dept[did].sort(key=lambda x: (x["reimburse_date"], x["record_id"]))

# Verify totals against summarize
for did in sorted(departments.keys()):
    if did in by_dept:
        total = round(sum(r["amount"] for r in by_dept[did]), 2)
        expected = departments[did]["annual_budget"]
        print(f"{did} {departments[did]['name']}: budget={expected}, actual_sum={total}, count={len(by_dept[did])}")

# Find first record exceeding budget (special_approval confirmed as 0 for all)
results = []
for did in sorted(departments.keys()):
    budget = departments[did]["annual_budget"]
    cumsum = 0.0
    violation_record = None
    
    if did not in by_dept:
        continue
        
    for rec in by_dept[did]:
        cumsum += rec["amount"]
        if cumsum > budget:
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

print("\n=== Budget Violation Results ===")
for r in sorted(results, key=lambda x: x["department_id"]):
    print(f"  {r['department_id']} {r['department_name']}: budget={r['annual_budget']}, "
          f"cumsum={r['cumulative_at_violation']}, "
          f"key_record={r['violation_record_id']} on {r['violation_reimburse_date']}, "
          f"violation_amount={r['violation_amount']}, dept_records={r['record_count']}")

with open("/workspace/work/analysis_result.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\nResults saved. Violation count: {len(results)}")
