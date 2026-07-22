#!/usr/bin/env python3
"""Process expense data from tool outputs to find budget overrun key records."""

import json
import os
import glob

# Budget data from summarize_department_budgets
department_budgets = {
    "D001": {"name": "投资银行部", "budget": 230395.17, "used": 363614.58, "record_count": 525},
    "D002": {"name": "固定收益部", "budget": 107785.42, "used": 164928.12, "record_count": 254},
    "D003": {"name": "财富管理部", "budget": 109772.07, "used": 174150.67, "record_count": 249},
    "D004": {"name": "研究所", "budget": 264890.39, "used": 408832.95, "record_count": 611},
    "D005": {"name": "机构业务部", "budget": 278540.94, "used": 433442.76, "record_count": 616},
    "D006": {"name": "运营管理部", "budget": 340961.75, "used": 530241.29, "record_count": 833},
    "D007": {"name": "信息技术部", "budget": 301500.00, "used": 252588.38, "record_count": 342},
    "D008": {"name": "合规风控部", "budget": 381600.00, "used": 297095.29, "record_count": 376},
    "D009": {"name": "财务管理部", "budget": 191300.00, "used": 159294.06, "record_count": 253},
    "D010": {"name": "人力资源部", "budget": 164500.00, "used": 139536.39, "record_count": 181},
}

# Map tool output files to queries
# Based on the order of our queries
tool_dir = "/home/agent/.local/share/opencode/tool-output"

# Read all tool output files
tool_files = sorted(glob.glob(os.path.join(tool_dir, "tool_*")))
print(f"Found {len(tool_files)} tool output files")

# Let's read each and figure out which department it belongs to
all_department_records = {d: [] for d in department_budgets.keys()}

for tf in tool_files:
    try:
        with open(tf, 'r') as f:
            content = f.read()
            # The file is a single JSON line
            data = json.loads(content)
            if 'records' in data:
                for record in data['records']:
                    dept_id = record.get('department_id')
                    if dept_id and dept_id in all_department_records:
                        all_department_records[dept_id].append(record)
    except Exception as e:
        print(f"Error reading {tf}: {e}")

# Print record counts per department
for dept_id in sorted(all_department_records.keys()):
    records = all_department_records[dept_id]
    expected = department_budgets[dept_id]['record_count']
    print(f"{dept_id} ({department_budgets[dept_id]['name']}): {len(records)} records (expected {expected})")

# For each over-budget department, sort and compute cumulative
print("\n=== OVER-BUDGET DEPARTMENTS: Cumulative Analysis ===")
over_budget_depts = ["D001", "D002", "D003", "D004", "D005", "D006"]

budget_crossing_records = {}

for dept_id in over_budget_depts:
    records = all_department_records[dept_id]
    budget = department_budgets[dept_id]['budget']
    
    # Sort by reimburse_date ASC, then record_id ASC
    records.sort(key=lambda r: (r['reimburse_date'], r['record_id']))
    
    cumulative = 0.0
    crossing_index = None
    crossing_record = None
    
    for i, r in enumerate(records):
        cumulative += r['amount']
        if crossing_index is None and cumulative > budget:
            crossing_index = i
            crossing_record = r
    
    print(f"\n{dept_id} ({department_budgets[dept_id]['name']}): budget={budget:.2f}")
    
    if crossing_record:
        print(f"  Budget crossed at record index {crossing_index} (0-based)")
        print(f"  Record: {crossing_record['record_id']}, reimburse_date={crossing_record['reimburse_date']}, amount={crossing_record['amount']:.2f}, cumulative={cumulative:.2f}")
        print(f"  Need to check special_approval for this record and records after it")
        
        # Collect records that are candidates for the key (from crossing point onwards)
        budget_crossing_records[dept_id] = {
            'crossing_index': crossing_index,
            'crossing_record_id': crossing_record['record_id'],
            'budget': budget,
            'records_around_crossing': [
                {'record_id': r['record_id'], 'reimburse_date': r['reimburse_date'], 
                 'amount': r['amount']}
                for r in records[max(0,crossing_index-3):crossing_index+10]
            ]
        }
    else:
        print(f"  NEVER exceeds budget (max cumulative would need all records)")
    
    # Verify total
    total = sum(r['amount'] for r in records)
    expected = department_budgets[dept_id]['used']
    print(f"  Computed total: {total:.2f} (expected {expected:.2f}), diff: {abs(total-expected):.2f}")

# Save intermediate results
output = {
    'budget_crossing_records': budget_crossing_records,
    'department_record_counts': {d: len(all_department_records[d]) for d in all_department_records}
}

with open('/workspace/work/subagents/data_analyst/intermediate.json', 'w') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("\n\n=== UNDER-BUDGET DEPARTMENTS ===")
for dept_id in ["D007", "D008", "D009", "D010"]:
    records = all_department_records[dept_id]
    budget = department_budgets[dept_id]['budget']
    records.sort(key=lambda r: (r['reimburse_date'], r['record_id']))
    cumulative = 0.0
    max_cumulative = 0.0
    for r in records:
        cumulative += r['amount']
        if cumulative > max_cumulative:
            max_cumulative = cumulative
    total = sum(r['amount'] for r in records)
    expected = department_budgets[dept_id]['used']
    print(f"{dept_id} ({department_budgets[dept_id]['name']}): budget={budget:.2f}, max_cumulative={max_cumulative:.2f}, total={total:.2f} (expected {expected:.2f})")
    if max_cumulative > budget:
        print(f"  WARNING: Exceeds budget!")
    else:
        print(f"  OK: Never exceeds budget")

print("\nDone. Intermediate saved.")
