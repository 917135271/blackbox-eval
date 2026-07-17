import json, subprocess, sys

DEPT_IDS = ["D001", "D002", "D003", "D004", "D005", "D006"]
BUDGETS = {
    "D001": 230395.17, "D002": 107785.42, "D003": 109772.07,
    "D004": 264890.39, "D005": 278540.94, "D006": 340961.75
}

def fetch_all(dept_id, page_size=100):
    records = []
    page = 1
    while True:
        cmd = [
            "python3", "-c", f"""
import json, subprocess
r = subprocess.run(["mcp__expense_query__list_expenses", json.dumps({{"department_id":"{dept_id}","date_from":"2025-01-01","date_to":"2025-12-31","page":{page},"page_size":{page_size},"sort_desc":False,"order_by":"expense_date"}})], capture_output=True, text=True)
print(r.stdout)
"""
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        try:
            data = json.loads(result.stdout)
        except:
            print(f"FAILED parsing page {page} for {dept_id}: {result.stdout[:200]}", file=sys.stderr)
            break
        recs = data.get("records", [])
        records.extend(recs)
        if not data.get("has_next", False):
            break
        page += 1
    return records

# Just test with one department first
recs = fetch_all("D001", page_size=100)
print(f"D001: fetched {len(recs)} records")
if recs:
    print(f"  First: {recs[0].get('record_id')} date={recs[0].get('expense_date')} amount={recs[0].get('amount')} sa={recs[0].get('special_approval')}")
    print(f"  Last: {recs[-1].get('record_id')} date={recs[-1].get('expense_date')} amount={recs[-1].get('amount')} sa={recs[-1].get('special_approval')}")
