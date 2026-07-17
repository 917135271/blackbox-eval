import json, sqlite3, os

# Connect to the database
db_path = "/benchmark/data/expense.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check approval table structure
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

# Check if any approval has approver_role = '财务复核'
cursor.execute("SELECT COUNT(*) FROM approvals WHERE approver_role = '财务复核'")
count = cursor.fetchone()[0]
print(f"Total approvals with role '财务复核': {count}")

# Check all distinct approver_roles
cursor.execute("SELECT DISTINCT approver_role FROM approvals")
roles = cursor.fetchall()
print(f"All approval roles: {[r[0] for r in roles]}")

# Check all distinct tier_ids
cursor.execute("SELECT DISTINCT tier_id FROM approvals")
tiers = cursor.fetchall()
print(f"All tier IDs: {[t[0] for t in tiers]}")

# Check AR-02 records: how many approvals per record?
cursor.execute("""
    SELECT a.record_id, COUNT(*) as approval_count, GROUP_CONCAT(a.approver_role) as roles
    FROM approvals a
    WHERE a.tier_id = 'AR-02'
    GROUP BY a.record_id
    ORDER BY approval_count DESC
    LIMIT 10
""")
print("\nAR-02 approval patterns (top 10):")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} approvals - roles: {row[2]}")

# Check total AR-02 records
cursor.execute("SELECT COUNT(*) FROM approvals WHERE tier_id = 'AR-02'")
ar02_count = cursor.fetchone()[0]
print(f"\nTotal AR-02 approval entries: {ar02_count}")

# Check if any AR-02 record has more than 1 approval
cursor.execute("""
    SELECT COUNT(*) FROM (
        SELECT a.record_id, COUNT(*) as cnt
        FROM approvals a
        WHERE a.tier_id = 'AR-02'
        GROUP BY a.record_id
        HAVING cnt > 1
    )
""")
multi_approval_count = cursor.fetchone()[0]
print(f"AR-02 records with >1 approval: {multi_approval_count}")

conn.close()
