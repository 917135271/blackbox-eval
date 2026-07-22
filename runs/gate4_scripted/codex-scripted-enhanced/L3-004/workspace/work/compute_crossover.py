import json
import sys

# Budget amounts
budgets = {
    "D001": 230395.17,
    "D002": 107785.42,
    "D003": 109772.07,
    "D004": 264890.39,
    "D005": 278540.94,
    "D006": 340961.75,
}

dept_names = {
    "D001": "投资银行部",
    "D002": "固定收益部",
    "D003": "财富管理部",
    "D004": "研究所",
    "D005": "机构业务部",
    "D006": "运营管理部",
}

# Read all department data from stdin (JSON lines)
all_records = []
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        data = json.loads(line)
        if "records" in data:
            all_records.extend(data["records"])
    except:
        pass

# Group by department
dept_records = {}
for r in all_records:
    did = r["department_id"]
    if did not in dept_records:
        dept_records[did] = []
    dept_records[did].append(r)

results = {}
for did in ["D001", "D002", "D003", "D004", "D005", "D006"]:
    if did not in dept_records:
        continue
    records = dept_records[did]
    # Sort by (reimburse_date, record_id)
    records.sort(key=lambda r: (r["reimburse_date"], r["record_id"]))
    
    budget = budgets[did]
    cumulative = 0.0
    crossover_record = None
    
    for r in records:
        cumulative += r["amount"]
        if crossover_record is None and cumulative > budget:
            crossover_record = r
    
    results[did] = {
        "name": dept_names[did],
        "budget": budget,
        "total": round(cumulative, 2),
        "crossover_record_id": crossover_record["record_id"] if crossover_record else None,
        "crossover_date": crossover_record["reimburse_date"] if crossover_record else None,
        "crossover_amount": round(crossover_record["amount"], 2) if crossover_record else None,
        "record_count": len(records),
    }

print(json.dumps(results, indent=2, ensure_ascii=False))
