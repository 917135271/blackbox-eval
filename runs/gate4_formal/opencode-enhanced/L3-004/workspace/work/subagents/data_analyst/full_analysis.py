#!/usr/bin/env python3
"""Full budget overrun analysis with complete data from both pages."""

import json
import os
import glob

# Budget data
department_budgets = {
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

tool_dir = "/home/agent/.local/share/opencode/tool-output"
tool_files = sorted(glob.glob(os.path.join(tool_dir, "tool_*")))

all_department_records = {d: [] for d in department_budgets.keys()}

# Read all tool output files
for tf in tool_files:
    try:
        with open(tf, 'r') as f:
            content = f.read()
            data = json.loads(content)
            if 'records' in data:
                for record in data['records']:
                    dept_id = record.get('department_id')
                    if dept_id and dept_id in all_department_records:
                        # Avoid duplicates
                        existing_ids = {r['record_id'] for r in all_department_records[dept_id]}
                        if record['record_id'] not in existing_ids:
                            all_department_records[dept_id].append(record)
    except Exception as e:
        print(f"Error reading {tf}: {e}")

# Now load the inline page 2 data from files I'll save separately
# Check for additional data files
extra_files = [
    "/workspace/work/subagents/data_analyst/d001_p2.json",
    "/workspace/work/subagents/data_analyst/d004_p2.json", 
    "/workspace/work/subagents/data_analyst/d005_p2.json",
]
for ef in extra_files:
    if os.path.exists(ef):
        try:
            with open(ef, 'r') as f:
                records = json.load(f)
                for record in records:
                    dept_id = record.get('department_id')
                    if dept_id and dept_id in all_department_records:
                        existing_ids = {r['record_id'] for r in all_department_records[dept_id]}
                        if record['record_id'] not in existing_ids:
                            all_department_records[dept_id].append(record)
        except Exception as e:
            print(f"Error reading {ef}: {e}")

# Print record counts
for dept_id in sorted(all_department_records.keys()):
    print(f"{dept_id}: {len(all_department_records[dept_id])} records")

# Now compute full analysis for over-budget departments
print("\n=== OVER-BUDGET ANALYSIS (sorted by reimburse_date ASC, record_id ASC) ===")

results = {}

for dept_id in ["D001", "D002", "D003", "D004", "D005", "D006"]:
    records = all_department_records[dept_id]
    budget = department_budgets[dept_id]['budget']
    
    # Sort by reimburse_date ASC, then record_id ASC
    records.sort(key=lambda r: (r['reimburse_date'], r['record_id']))
    
    cumulative = 0.0
    crossing_info = None
    
    for i, r in enumerate(records):
        cumulative += r['amount']
        if crossing_info is None and cumulative > budget:
            crossing_info = {
                'index': i,
                'record_id': r['record_id'],
                'reimburse_date': r['reimburse_date'],
                'amount': r['amount'],
                'cumulative': round(cumulative, 2),
                'budget': budget,
            }
    
    total = sum(r['amount'] for r in records)
    dept_name = department_budgets[dept_id]['name']
    
    if crossing_info:
        print(f"\n{dept_id} ({dept_name}): budget={budget:.2f}, total={total:.2f}")
        print(f"  Crosses budget at: {crossing_info['record_id']} (index {crossing_info['index']})")
        print(f"    reimburse_date={crossing_info['reimburse_date']}, amount={crossing_info['amount']:.2f}")
        print(f"    cumulative={crossing_info['cumulative']:.2f}, excess={crossing_info['cumulative']-budget:.2f}")
        
        # Show context: records around crossing point
        start = max(0, crossing_info['index'] - 3)
        end = min(len(records), crossing_info['index'] + 5)
        print(f"  Context (records {start}-{end-1}):")
        cum_before = sum(r['amount'] for r in records[:start])
        for j in range(start, end):
            r = records[j]
            cum_before += r['amount']
            marker = " <<< CROSSES BUDGET" if j == crossing_info['index'] else ""
            print(f"    [{j}] {r['record_id']} reimb={r['reimburse_date']} amt={r['amount']:.2f} cum={cum_before:.2f}{marker}")
    else:
        print(f"\n{dept_id} ({dept_name}): budget={budget:.2f}, total={total:.2f} - NEVER EXCEEDS BUDGET")
    
    results[dept_id] = {
        'department_name': dept_name,
        'budget': budget,
        'total_spent': round(total, 2),
        'crossing_info': crossing_info,
        'record_count': len(records)
    }

# Under-budget departments
print("\n=== UNDER-BUDGET DEPARTMENTS ===")
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
    dept_name = department_budgets[dept_id]['name']
    exceeds = "EXCEEDS" if max_cumulative > budget else "OK"
    print(f"{dept_id} ({dept_name}): budget={budget:.2f}, max_cumulative={max_cumulative:.2f}, total={total:.2f} [{exceeds}]")
    
    results[dept_id] = {
        'department_name': dept_name,
        'budget': budget,
        'total_spent': round(total, 2),
        'max_cumulative': round(max_cumulative, 2),
        'exceeds_budget': max_cumulative > budget,
        'record_count': len(records)
    }

# Save detailed analysis
with open('/workspace/work/subagents/data_analyst/detailed_analysis.json', 'w') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\nDetailed analysis saved to detailed_analysis.json")
