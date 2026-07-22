import json
import os

base = "/home/agent/.local/share/opencode/tool-output"
workspace = "/workspace/work"

dept_budgets = {
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

page1_files = {
    "D001": "tool_f83a12159001Sy7hwj5xYCmP5B",
    "D002": "tool_f83a124ed001svbwalAQkZzqlC",
    "D003": "tool_f83a128930010bDDrPMExEpbfw",
    "D004": "tool_f83a12bd8001EsOlJOqCpNwp3D",
    "D005": "tool_f83a12f4d001f76jHRW3vkUr1f",
    "D006": "tool_f83a1331f0015CGIScJbSjvc2m",
}

# Load all data
dept_records = {}
for dept, fname in page1_files.items():
    with open(os.path.join(base, fname)) as f:
        data = json.load(f)
    dept_records[dept] = data['records']
    print(f"{dept} (page1): {len(data['records'])} records")

# Add D006 page 2
with open(os.path.join(base, "tool_f83a1c693001ifDtWri06MS12M")) as f:
    d6p2 = json.load(f)
dept_records["D006"].extend(d6p2['records'])
print(f"D006 (page2): +{len(d6p2['records'])} records = {len(dept_records['D006'])} total")

# Add D001 page 2
with open(os.path.join(workspace, "d001_p2.json")) as f:
    d1p2 = json.load(f)
# The p2 records are simplified - need to get them from the full query result
# Wait, I saved only partial fields. Let me use the full D001 page 2 from the MCP response.
# Actually, D001's threshold is in page 1, so I don't strictly need page 2 for the computation
# but I should have complete data for verification.
print(f"D001 (page2): {len(d1p2['records'])} partial records")

# For D004 and D005, thresholds are in page1, so I have what I need.
# But for completeness, let me note the gaps.
print(f"\nD004: have 500/611 records")
print(f"D005: have 500/616 records")

# Now process each department to find threshold records
results = {}

for dept in ["D001", "D002", "D003", "D004", "D005", "D006"]:
    records = dept_records[dept]
    budget = dept_budgets[dept]
    
    # Sort by reimburse_date ASC, record_id ASC
    records.sort(key=lambda r: (r['reimburse_date'], r['record_id']))
    
    cum = 0.0
    threshold_id = None
    threshold_cum_before = 0.0
    all_ids = []
    
    for r in records:
        cum += r['amount']
        all_ids.append(r['record_id'])
        if threshold_id is None and cum > budget:
            threshold_id = r['record_id']
            threshold_cum_before = cum - r['amount']
    
    total_spent = cum
    results[dept] = {
        'budget': budget,
        'total_spent': total_spent,
        'threshold_id': threshold_id,
        'cum_before_threshold': threshold_cum_before,
        'record_count': len(records),
    }
    
    print(f"\n{dept} ({dept_names[dept]}):")
    print(f"  Budget: {budget:.2f}")
    print(f"  Total approved (available records): {total_spent:.2f}")
    print(f"  Records: {len(records)}")
    print(f"  Cumulative before threshold: {threshold_cum_before:.2f}")
    print(f"  Threshold record_id: {threshold_id}")
    
# Now also check - for all records without special_approval
# Since list_expenses with special_approval=true returned 0 records,
# all records lack special approval.
print("\n=== ALL RECORDS LACK SPECIAL APPROVAL ===")

PYEOF