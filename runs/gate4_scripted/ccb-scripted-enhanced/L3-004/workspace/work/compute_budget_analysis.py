import json
import os
import re
import glob

# Department budgets from the summarize_department_budgets API call
dept_budgets = {
    "D001": {"name": "投资银行部", "budget": 230395.17},
    "D002": {"name": "固定收益部", "budget": 107785.42},
    "D003": {"name": "财富管理部", "budget": 109772.07},
    "D004": {"name": "研究所", "budget": 264890.39},
    "D005": {"name": "机构业务部", "budget": 278540.94},
    "D006": {"name": "运营管理部", "budget": 340961.75},
    "D007": {"name": "信息技术部", "budget": 301500.00},
    "D008": {"name": "合规风控部", "budget": 381600.00},
    "D009": {"name": "财务管理部", "budget": 191300.00},
    "D010": {"name": "人力资源部", "budget": 164500.00},
}

# Read all persisted output files
base_dir = "/home/bun/.claude/projects/-workspace/8a4d93f4-31f9-4aaa-85d9-b241a6a6be54/tool-results/"
all_records = []

for f in sorted(glob.glob(os.path.join(base_dir, "*.txt"))):
    with open(f, 'r') as fh:
        content = fh.read()
    # Find JSON objects in the content - look for {\"page\":
    # First approach: extract JSON from the text content
    # Each file has lines like: {"result":[{"type":"text","text":"{\"page\": ...
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            if isinstance(data, dict) and 'result' in data:
                for result_item in data['result']:
                    if result_item.get('type') == 'text':
                        text_content = result_item.get('text', '')
                        try:
                            parsed = json.loads(text_content)
                            if 'records' in parsed:
                                all_records.extend(parsed['records'])
                                print(f"Added {len(parsed['records'])} records from file, page {parsed.get('page')}")
                        except json.JSONDecodeError:
                            pass
        except json.JSONDecodeError:
            continue

print(f"\nTotal records loaded: {len(all_records)}")

# Remove duplicates based on record_id
seen = set()
unique_records = []
for r in all_records:
    if r['record_id'] not in seen:
        seen.add(r['record_id'])
        unique_records.append(r)

print(f"Unique records: {len(unique_records)}")

# Group by department
dept_records = {}
for r in unique_records:
    did = r['department_id']
    if did not in dept_records:
        dept_records[did] = []
    dept_records[did].append(r)

# For each department, sort by reimburse_date then record_id
# and compute running cumulative sum
for did in sorted(dept_records.keys()):
    records = dept_records[did]
    records.sort(key=lambda x: (x['reimburse_date'], x['record_id']))
    
    budget = dept_budgets[did]['budget']
    dept_name = dept_budgets[did]['name']
    cumulative = 0.0
    breaking_record = None
    total_amount = 0.0
    
    for r in records:
        cumulative += r['amount']
        total_amount += r['amount']
        if breaking_record is None and cumulative > budget:
            breaking_record = r
            # Don't break - continue to compute full cumulative
    
    status = "OVER BUDGET" if cumulative > budget else "WITHIN BUDGET"
    print(f"\n{did} {dept_name}: budget={budget:.2f}, cumulative={cumulative:.2f}, count={len(records)}")
    print(f"  Status: {status}")
    if breaking_record:
        print(f"  Breaking record: {breaking_record['record_id']} (reimburse_date={breaking_record['reimburse_date']}, amount={breaking_record['amount']:.2f})")
        print(f"  Cumulative at break: {sum(r['amount'] for r in records if (r['reimburse_date'], r['record_id']) <= (breaking_record['reimburse_date'], breaking_record['record_id'])):.2f}")

# Output the breaking records for further investigation
print("\n=== KEY BREAKING RECORDS (need special_approval check) ===")
for did in sorted(dept_records.keys()):
    records = dept_records[did]
    records.sort(key=lambda x: (x['reimburse_date'], x['record_id']))
    budget = dept_budgets[did]['budget']
    cumulative = 0.0
    for r in records:
        cumulative += r['amount']
        if cumulative > budget:
            print(f"{did} ({dept_budgets[did]['name']}): {r['record_id']} - budget={budget:.2f}, amount={r['amount']:.2f}, cumulative={cumulative:.2f}, reimburse_date={r['reimburse_date']}")
            break
