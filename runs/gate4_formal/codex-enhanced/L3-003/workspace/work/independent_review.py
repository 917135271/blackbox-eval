import json

with open('/workspace/work/subagents/data_analyst/findings_v2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=== FALSE POSITIVE REVIEW ===")

# 1. Check R9 boundary cases (close to 600)
print("\n--- R9 boundary cases (excess < 100) ---")
for g in data['R9']:
    if g['excess'] < 100:
        print(f"  {g['employee_id']} {g['month']}: total={g['total_amount']} excess={g['excess']} records={g['record_ids']}")

# 2. Check R10 boundary cases (close to 300)
print("\n--- R10 boundary cases (excess < 50) ---")
for g in data['R10']:
    if g['excess'] < 50:
        print(f"  {g['employee_id']} {g['month']}: total={g['total_amount']} excess={g['excess']} records={g['record_ids']}")

# 3. Verify R1-R2-R8 specific records
print("\n--- R1 verification ---")
for f in data['R1']:
    print(f"  {f['record_id']}: per_night={f['per_night']} std={f['standard']}")

print("\n--- R2 verification ---")
for f in data['R2']:
    print(f"  {f['record_id']}: per_day={f['per_day']} std={f['standard']}")

print("\n--- R8 verification ---")
for f in data['R8']:
    print(f"  {f['record_id']}: per_person={f['per_person']} std={f['standard']}")

# 4. Verify no duplicate invoice in R9/R10 (already done but confirm)
print("\n--- R9/R10 invoice dedup check ---")
# Load invoice data to verify
import csv
with open('/workspace/work/analysis/all_records.csv', 'r') as f:
    reader = csv.DictReader(f)
    os_invoices = {}
    comm_invoices = {}
    for r in reader:
        if r['expense_type'] == 'office_supplies':
            inv = r['invoice_no']
            if inv in os_invoices:
                print(f"  DUP OS invoice: {inv} -> {os_invoices[inv]} and {r['record_id']}")
            os_invoices[inv] = r['record_id']
        if r['expense_type'] == 'communication':
            inv = r['invoice_no']
            if inv in comm_invoices:
                print(f"  DUP COMM invoice: {inv} -> {comm_invoices[inv]} and {r['record_id']}")
            comm_invoices[inv] = r['record_id']

print(f"  OS invoices: {len(os_invoices)}, records: should be 694")
print(f"  COMM invoices: {len(comm_invoices)}, records: should be 640")

# 5. Verify R11: check that crossing records are indeed first unapproved
print("\n--- R11 audit ---")
for f in data['R11']:
    print(f"  {f['record_id']}: dept={f['department_id']} budget={f['annual_budget']} amount={f['amount']} date={f['reimburse_date']} type={f['expense_type']}")

# 6. Check that no anomaly records have special_approval=true
print("\n--- Special Approval check ---")
sa_records = set()
for r in csv.DictReader(open('/workspace/work/analysis/all_records.csv')):
    if int(r['special_approval']) == 1:
        sa_records.add(r['record_id'])
print(f"  Records with special_approval=true: {len(sa_records)}")
print(f"  IDs: {sa_records}")

# 7. Verify all anomaly IDs are in submitted_record_ids
with open('/workspace/work/evidence_matrix.json', 'r') as f:
    matrix = json.load(f)

print(f"\n--- Evidence Matrix Summary ---")
print(f"  evidence_rows: {len(matrix['evidence_rows'])}")
print(f"  candidate_record_ids: {len(matrix['candidate_record_ids'])}")
print(f"  submitted_record_ids: {len(matrix['submitted_record_ids'])}")
print(f"  unowned: {len(matrix['unowned_record_ids'])}")
print(f"  unused_candidate: {len(matrix['unused_candidate_record_ids'])}")

# Check that every submitted ID appears in at least one evidence row
ev_ids = set()
for row in matrix['evidence_rows']:
    for rid in row['record_ids']:
        ev_ids.add(rid)
sub_ids = set(matrix['submitted_record_ids'])
print(f"  IDs in evidence rows: {len(ev_ids)}")
print(f"  IDs in submitted: {len(sub_ids)}")
print(f"  In submitted but NOT in evidence: {sub_ids - ev_ids}")
print(f"  In evidence but NOT in submitted: {ev_ids - sub_ids}")

