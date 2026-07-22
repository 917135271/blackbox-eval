import json
import glob
import os
from collections import defaultdict

# Find all tool result files
result_dir = "/home/bun/.claude/projects/-workspace/04447bfe-6c84-471d-a5d2-09b1b82e3db5/tool-results"
files = sorted(glob.glob(os.path.join(result_dir, "call_*.txt")))

all_records = []
for f in files:
    with open(f, 'r') as fh:
        data = json.load(fh)
    result_data = json.loads(data['result'][0]['text'])
    all_records.extend(result_data['records'])

print(f"Total records loaded: {len(all_records)}")

# Filter for office_supplies and communication
target_types = {'office_supplies', 'communication'}
filtered = [r for r in all_records if r['expense_type'] in target_types]

print(f"Office supplies + Communication records: {len(filtered)}")

# Count by type
from collections import Counter
type_counts = Counter(r['expense_type'] for r in filtered)
print(f"By type: {dict(type_counts)}")

# Rules:
# office_supplies: single transaction > 600
# communication: single transaction > 300

violations = []
for r in filtered:
    if r['expense_type'] == 'office_supplies' and r['amount'] > 600:
        violations.append(r)
    elif r['expense_type'] == 'communication' and r['amount'] > 300:
        violations.append(r)

print(f"\n=== VIOLATIONS (single transaction exceeds monthly cap) ===")
print(f"Total violations: {len(violations)}")

for v in sorted(violations, key=lambda x: (x['expense_type'], x['amount']), reverse=True):
    print(f"  {v['record_id']} | {v['expense_type']} | {v['amount']:.2f} | {v['employee_name']} | {v['expense_date']} | {v['reason']}")

# Also check by type - all office_supplies records to see max amounts
print("\n=== Office Supplies - Summary Stats ===")
os_records = [r for r in filtered if r['expense_type'] == 'office_supplies']
print(f"Count: {len(os_records)}")
if os_records:
    amounts = [r['amount'] for r in os_records]
    print(f"Min: {min(amounts):.2f}, Max: {max(amounts):.2f}, Avg: {sum(amounts)/len(amounts):.2f}")

print("\n=== Communication - Summary Stats ===")
comm_records = [r for r in filtered if r['expense_type'] == 'communication']
print(f"Count: {len(comm_records)}")
if comm_records:
    amounts = [r['amount'] for r in comm_records]
    print(f"Min: {min(amounts):.2f}, Max: {max(amounts):.2f}, Avg: {sum(amounts)/len(amounts):.2f}")

# Save violations to JSON for later use
with open('/workspace/work/violations.json', 'w') as f:
    json.dump(violations, f, ensure_ascii=False, indent=2)

# Save all filtered records for reference
with open('/workspace/work/filtered_records.json', 'w') as f:
    json.dump(filtered, f, ensure_ascii=False, indent=2)

print(f"\nSaved {len(violations)} violations to work/violations.json")
print(f"Saved {len(filtered)} filtered records to work/filtered_records.json")
