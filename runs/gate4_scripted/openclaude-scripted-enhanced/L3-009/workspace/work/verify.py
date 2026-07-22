import sqlite3
import json
from datetime import datetime

DB_PATH = "/benchmark/data/expense.db"
conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

# Check R0042xx series - these seem to be special records
r42x = conn.execute("""
    SELECT r.record_id, r.record_no, r.employee_id, e.employee_name, e.employee_level, e.position_role,
           r.department_id, r.expense_date, r.reimburse_date, r.expense_type, r.amount,
           r.city_tier, r.nights, r.days, r.special_approval
    FROM expense_records r
    JOIN employees e ON e.employee_id = r.employee_id
    WHERE r.record_id >= 'R004200'
    ORDER BY r.record_id
""").fetchall()

print("=== R0042xx RECORDS ===")
for r in r42x:
    print(f"  {r['record_id']}: {r['employee_id']} {r['employee_name']} level={r['employee_level']} role={r['position_role']} "
          f"type={r['expense_type']} amount={r['amount']} date={r['expense_date']} reim={r['reimburse_date']} "
          f"city={r['city_tier']} nights={r['nights']} special={r['special_approval']}")

# Check business_entertainment exceeding standards
be = conn.execute("""
    SELECT r.record_id, r.employee_id, e.employee_name, r.expense_date, r.amount, r.participants, r.special_approval
    FROM expense_records r
    JOIN employees e ON e.employee_id = r.employee_id
    WHERE r.expense_type = 'business_entertainment' AND r.amount > 5000
    ORDER BY r.amount DESC
""").fetchall()
print(f"\n=== BUSINESS ENTERTAINMENT > 5000: {len(be)} ===")
for r in be:
    print(f"  {r['record_id']}: {r['employee_name']} amount={r['amount']} participants={r['participants']} special={r['special_approval']}")

# Check business_entertainment per_person > 300
be2 = conn.execute("""
    SELECT r.record_id, r.employee_id, e.employee_name, r.expense_date, r.amount, r.participants, r.special_approval
    FROM expense_records r
    JOIN employees e ON e.employee_id = r.employee_id
    WHERE r.expense_type = 'business_entertainment' AND r.participants > 0 AND (r.amount * 1.0 / r.participants) > 300
    ORDER BY (r.amount * 1.0 / r.participants) DESC
""").fetchall()
print(f"\n=== BUSINESS ENTERTAINMENT per_person > 300: {len(be2)} ===")
for r in be2[:15]:
    per_person = r['amount'] / r['participants']
    print(f"  {r['record_id']}: {r['employee_name']} amount={r['amount']} participants={r['participants']} per_person={per_person:.2f} special={r['special_approval']}")

# Check training_fee > 3500
tf = conn.execute("""
    SELECT r.record_id, r.employee_id, e.employee_name, r.expense_date, r.amount, r.special_approval
    FROM expense_records r
    JOIN employees e ON e.employee_id = r.employee_id
    WHERE r.expense_type = 'training_fee' AND r.amount > 3500
    ORDER BY r.amount DESC
""").fetchall()
print(f"\n=== TRAINING_FEE > 3500: {len(tf)} ===")
for r in tf[:10]:
    print(f"  {r['record_id']}: {r['employee_name']} amount={r['amount']} special={r['special_approval']}")

# Check office_supplies > 600
os_ex = conn.execute("""
    SELECT r.record_id, r.employee_id, e.employee_name, r.expense_date, r.amount, r.special_approval
    FROM expense_records r
    JOIN employees e ON e.employee_id = r.employee_id
    WHERE r.expense_type = 'office_supplies' AND r.amount > 600
    ORDER BY r.amount DESC
""").fetchall()
print(f"\n=== OFFICE_SUPPLIES > 600: {len(os_ex)} ===")
for r in os_ex:
    print(f"  {r['record_id']}: {r['employee_name']} amount={r['amount']} special={r['special_approval']}")

# Check communication > 300
comm = conn.execute("""
    SELECT r.record_id, r.employee_id, e.employee_name, r.expense_date, r.amount, r.special_approval
    FROM expense_records r
    JOIN employees e ON e.employee_id = r.employee_id
    WHERE r.expense_type = 'communication' AND r.amount > 300
    ORDER BY r.amount DESC
""").fetchall()
print(f"\n=== COMMUNICATION > 300: {len(comm)} ===")
for r in comm[:10]:
    print(f"  {r['record_id']}: {r['employee_name']} amount={r['amount']} special={r['special_approval']}")

# Check local_transport over standard
lt = conn.execute("""
    SELECT r.record_id, r.employee_id, e.employee_name, r.expense_date, r.amount, r.city_tier, r.days, r.special_approval
    FROM expense_records r
    JOIN employees e ON e.employee_id = r.employee_id
    WHERE r.expense_type = 'local_transport' AND r.city_tier IS NOT NULL AND r.days > 0
    ORDER BY r.amount * 1.0 / r.days DESC
    LIMIT 15
""").fetchall()
print(f"\n=== LOCAL_TRANSPORT highest per_day ===")
for r in lt:
    per_day = r['amount'] / r['days']
    print(f"  {r['record_id']}: {r['employee_name']} amount={r['amount']} days={r['days']} per_day={per_day:.2f} city={r['city_tier']} special={r['special_approval']}")

# Check split pattern for R004207-R004208
print("\n=== SPLIT VERIFICATION: R004207-R004208 ===")
for rid in ['R004207', 'R004208']:
    r = conn.execute("""
        SELECT r.*, e.employee_name, e.employee_level, e.position_role
        FROM expense_records r
        JOIN employees e ON e.employee_id = r.employee_id
        WHERE r.record_id = ?
    """, (rid,)).fetchone()
    if r:
        print(f"  {r['record_id']}: {r['employee_id']} {r['employee_name']} level={r['employee_level']} role={r['position_role']} "
              f"type={r['expense_type']} amount={r['amount']} date={r['expense_date']} "
              f"city={r['city_tier']} nights={r['nights']} special={r['special_approval']}")

# Check if R004207+ have special approval
sp = conn.execute("""
    SELECT COUNT(*) as cnt FROM expense_records WHERE record_id >= 'R004200' AND special_approval = 1
""").fetchone()
print(f"\nR0042xx with special_approval=1: {sp['cnt']}")

# Count total records with special_approval
sp_all = conn.execute("SELECT COUNT(*) as cnt FROM expense_records WHERE special_approval = 1").fetchone()
print(f"Total records with special_approval=1: {sp_all['cnt']}")

# Check travel_lodging per_night issues more carefully
# Let's see the distribution of travel_lodging with city_tier and nights
tl = conn.execute("""
    SELECT r.record_id, r.employee_id, e.employee_name, e.position_role,
           r.amount, r.city_tier, r.nights, r.special_approval,
           CASE 
               WHEN r.city_tier = 'A' AND e.position_role = '员工' AND r.nights > 0 AND (r.amount/r.nights) > 450 THEN 'EXCEEDS'
               WHEN r.city_tier = 'B' AND e.position_role = '员工' AND r.nights > 0 AND (r.amount/r.nights) > 380 THEN 'EXCEEDS'
               WHEN r.city_tier = 'C' AND e.position_role = '员工' AND r.nights > 0 AND (r.amount/r.nights) > 300 THEN 'EXCEEDS'
               WHEN r.city_tier = 'A' AND e.position_role = '部门经理' AND r.nights > 0 AND (r.amount/r.nights) > 650 THEN 'EXCEEDS'
               WHEN r.city_tier = 'B' AND e.position_role = '部门经理' AND r.nights > 0 AND (r.amount/r.nights) > 550 THEN 'EXCEEDS'
               ELSE 'OK'
           END as exceeds
    FROM expense_records r
    JOIN employees e ON e.employee_id = r.employee_id
    WHERE r.expense_type = 'travel_lodging' AND r.city_tier IS NOT NULL AND r.nights > 0 AND r.special_approval = 0
    HAVING exceeds = 'EXCEEDS'
    ORDER BY (r.amount/r.nights) DESC
    LIMIT 20
""").fetchall()
print(f"\n=== TRAVEL_LODGING EXCEEDS (sample 20) ===")
for r in tl:
    per_night = r['amount'] / r['nights']
    print(f"  {r['record_id']}: {r['employee_name']} role={r['position_role']} amount={r['amount']} nights={r['nights']} per_night={per_night:.2f} city={r['city_tier']}")

conn.close()
