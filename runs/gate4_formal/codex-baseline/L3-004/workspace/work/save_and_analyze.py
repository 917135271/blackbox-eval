import json, os

# Department budgets
budgets = {
    "D001": 230395.17, "D002": 107785.42, "D003": 109772.07,
    "D004": 264890.39, "D005": 278540.94, "D006": 340961.75,
}

data_dir = "/workspace/work/dept_data"
os.makedirs(data_dir, exist_ok=True)

# This script assumes data files exist in dept_data/ as D00X.json
# Each file contains a list of records with record_id, reimburse_date, amount

results = {}
for did in ["D001","D002","D003","D004","D005","D006"]:
    fpath = os.path.join(data_dir, f"{did}.json")
    if not os.path.exists(fpath):
        print(f"MISSING: {fpath}")
        continue
    with open(fpath) as f:
        records = json.load(f)
    # Sort by reimburse_date then record_id
    records.sort(key=lambda r: (r["reimburse_date"], r["record_id"]))
    budget = budgets[did]
    cum = 0.0
    found = None
    for r in records:
        cum += r["amount"]
        if cum > budget and found is None:
            found = {"record_id": r["record_id"], "reimburse_date": r["reimburse_date"], 
                     "cumulative": round(cum,2), "record_amount": r["amount"]}
    if found:
        results[did] = found
        print(f"{did}: key_record={found['record_id']} on {found['reimburse_date']}, cum={found['cumulative']}")
    else:
        print(f"{did}: NO VIOLATION FOUND (total={round(cum,2)}, budget={budget})")

with open("/workspace/work/violation_results.json","w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print("\nDone. Results saved.")
