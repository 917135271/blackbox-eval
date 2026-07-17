#!/usr/bin/env python3
"""Recompute split billing with correct sliding window (span <= 7 days)."""

import sqlite3
import json
from collections import defaultdict
from datetime import datetime, timedelta

DB_PATH = "/benchmark/data/expense.db"

conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

cur = conn.execute("""
    SELECT r.record_id, r.record_no, r.employee_id, e.employee_name, r.expense_type,
           r.expense_date, r.amount, r.reason
    FROM expense_records r
    JOIN employees e ON r.employee_id = e.employee_id
    WHERE r.budget_year=2025
    ORDER BY r.employee_id, r.expense_type, r.expense_date
""")

records = [dict(row) for row in cur]
conn.close()

# Group by (employee_id, expense_type)
groups = defaultdict(list)
for rec in records:
    groups[(rec['employee_id'], rec['expense_type'])].append(rec)

# Sliding window: for each start record, find all records within 7 days
# Collect all unique split groups (by record_id set)
split_groups_dict = {}

for (emp_id, exp_type), recs in groups.items():
    if len(recs) < 2:
        continue

    recs_sorted = sorted(recs, key=lambda r: r['expense_date'])
    n = len(recs_sorted)

    for i in range(n):
        start_date = datetime.strptime(recs_sorted[i]['expense_date'], '%Y-%m-%d')
        end_date = start_date + timedelta(days=7)

        window_recs = []
        for j in range(i, n):
            d = datetime.strptime(recs_sorted[j]['expense_date'], '%Y-%m-%d')
            if d <= end_date:
                window_recs.append(recs_sorted[j])
            else:
                break

        if len(window_recs) >= 2:
            total = sum(r['amount'] for r in window_recs)
            if total >= 3000:
                # Create a unique key from sorted record_ids
                key = tuple(sorted(r['record_id'] for r in window_recs))
                if key not in split_groups_dict:
                    split_groups_dict[key] = {
                        'employee_id': emp_id,
                        'employee_name': window_recs[0]['employee_name'],
                        'expense_type': exp_type,
                        'record_count': len(window_recs),
                        'total_amount': round(total, 2),
                        'date_range': f"{window_recs[0]['expense_date']} to {window_recs[-1]['expense_date']}",
                        'date_span_days': (datetime.strptime(window_recs[-1]['expense_date'], '%Y-%m-%d') -
                                          datetime.strptime(window_recs[0]['expense_date'], '%Y-%m-%d')).days,
                        'records': [{
                            'record_id': r['record_id'],
                            'record_no': r['record_no'],
                            'expense_date': r['expense_date'],
                            'amount': r['amount'],
                            'reason': r['reason'],
                        } for r in window_recs],
                    }

# Remove groups that are subsets of larger groups
final_groups = list(split_groups_dict.values())
# Sort by number of records descending, then by record_ids
final_groups.sort(key=lambda g: (-g['record_count'], g['records'][0]['record_id']))

# Remove subsets
filtered = []
for i, g in enumerate(final_groups):
    g_ids = set(r['record_id'] for r in g['records'])
    is_subset = False
    for j in range(i):
        f_ids = set(r['record_id'] for r in filtered[j]['records'])
        if g_ids.issubset(f_ids):
            is_subset = True
            break
    if not is_subset:
        filtered.append(g)

print(f"Split billing groups: {len(filtered)} (down from {len(final_groups)})")

# Show breakdown
from collections import Counter
types = Counter(g['expense_type'] for g in filtered)
print(f"By type: {dict(types)}")

# Check trap sample
for g in filtered:
    if g['employee_name'] == '闭想':
        print(f"Trap check (闭想): dates={g['date_range']}, span={g['date_span_days']}days, records={g['record_count']}")
        for r in g['records']:
            print(f"  {r['record_id']} {r['expense_date']} {r['amount']} {r['reason']}")

# Show injected vs non-injected
injected = [g for g in filtered if '注入' in str(g)]
non_injected = [g for g in filtered if '注入' not in str(g)]
print(f"\nInjected split groups: {len(injected)}")
print(f"Non-injected split groups: {len(non_injected)}")

# Show first few non-injected
for g in non_injected[:5]:
    print(f"  {g['employee_name']} {g['expense_type']}: {g['record_count']} records, total={g['total_amount']}, span={g['date_span_days']}days")

# Save revised results
# Load existing results
with open('/workspace/work/subagents/data_analyst/analysis_detail.json') as f:
    results = json.load(f)

results['rule8_split_billing'] = filtered

with open('/workspace/work/subagents/data_analyst/analysis_detail.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\nUpdated analysis_detail.json with corrected split billing results")

# Also check: the 闭想 trap sample (R004236, R004237) should NOT appear
trap_ids = {'R004236', 'R004237'}
for g in filtered:
    for r in g['records']:
        if r['record_id'] in trap_ids:
            print(f"WARNING: Trap record {r['record_id']} found in split group!")
