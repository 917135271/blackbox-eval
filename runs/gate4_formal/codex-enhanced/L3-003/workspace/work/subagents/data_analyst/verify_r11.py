import csv

def load_records(csv_path):
    records = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            row['amount'] = float(row['amount'])
            row['special_approval'] = int(row['special_approval']) == 1
            row['annual_budget'] = float(row['annual_budget'])
            records.append(row)
    return records

records = load_records('/workspace/work/analysis/all_records.csv')

# Departments with budget exceeded (usage_rate > 1.0)
over_depts = ['D001', 'D002', 'D003', 'D004', 'D005', 'D006']

for dept_id in over_depts:
    dept_records = [r for r in records if r['department_id'] == dept_id]
    dept_records.sort(key=lambda r: (r['reimburse_date'], r['record_id']))
    
    budget = dept_records[0]['annual_budget']
    dept_name = dept_records[0]['department_name']
    
    cumulative = 0.0
    crossed = False
    crossing_record = None
    
    print(f"\n=== {dept_id} ({dept_name}) Budget: {budget:.2f} ===")
    
    for r in dept_records:
        cumulative += r['amount']
        if not crossed and cumulative > budget:
            crossed = True
            crossing_record = r
            print(f"  CROSSING at {r['record_id']} ({r['reimburse_date']}): amount={r['amount']:.2f} cumulative={cumulative:.2f} SP={r['special_approval']} type={r['expense_type']}")
            # Look at a few records before crossing
            # Find the index
            idx = dept_records.index(r)
            for prev in dept_records[max(0,idx-3):idx]:
                cum = cumulative - r['amount']
                # Actually need to recalc
                pass
            break
    
    # Show the pre-crossing cumulative
    cum2 = 0.0
    for r in dept_records:
        cum2 += r['amount']
        if r == crossing_record:
            print(f"  Pre-crossing cumulative: {cum2 - r['amount']:.2f}")
            break

