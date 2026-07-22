import json
from datetime import datetime, date
from collections import defaultdict

# Load all records
records = []
with open('/workspace/work/data/all_records_sorted.jsonl') as f:
    for line in f:
        line = line.strip()
        if line:
            records.append(json.loads(line))

# Filter for approved records
records = [r for r in records if r.get('status') == 'approved']
print(f"Total approved records: {len(records)}")

# Employee level mapping
LEVEL_MAP = {'E1': '员工级', 'M1': '经理级', 'D1': '部门负责人级', 'X1': '高管级'}
TIER_MAP = {'A': '一类城市', 'B': '二类城市', 'C': '三类城市'}

# Travel lodging standards
TRAVEL_LODGING_STD = {
    ('员工级', '一类城市'): 450, ('员工级', '二类城市'): 380, ('员工级', '三类城市'): 300,
    ('经理级', '一类城市'): 650, ('经理级', '二类城市'): 550, ('经理级', '三类城市'): 450,
    ('部门负责人级', '一类城市'): 850, ('部门负责人级', '二类城市'): 700, ('部门负责人级', '三类城市'): 600,
    ('高管级', '一类城市'): 1100, ('高管级', '二类城市'): 900, ('高管级', '三类城市'): 750,
}

CITY_TRANSPORT_STD = {'一类城市': 120, '二类城市': 100, '三类城市': 80}
TRAINING_LODGING_STD = {'一类城市': 500, '二类城市': 420, '三类城市': 350}

# Approval tiers
APPROVAL_TIERS = [(0, 3000), (3000, 10000), (10000, 50000), (50000, 200000), (200000, float('inf'))]

# Dept budgets
DEPT_BUDGETS = {
    'D001': 230395.17, 'D002': 107785.42, 'D003': 109772.07,
    'D004': 264890.39, 'D005': 278540.94, 'D006': 340961.75,
    'D007': 301500.0, 'D008': 381600.0, 'D009': 191300.0, 'D010': 164500.0,
}

def parse_date(s):
    return datetime.strptime(s, '%Y-%m-%d').date()

def get_level(emp_level):
    return LEVEL_MAP.get(emp_level, '员工级')

# ============================================================
# 1. DUPLICATE REIMBURSEMENT (reused invoices)
# ============================================================
print("\n=== DUPLICATE REIMBURSEMENT ===")
# Build invoice -> record_ids mapping
invoice_to_records = defaultdict(list)
for r in records:
    inv = r.get('invoice_no', '')
    if inv:
        invoice_to_records[inv].append(r['record_id'])

dup_groups = []
for inv, rids in invoice_to_records.items():
    if len(rids) > 1:
        dup_groups.append((inv, sorted(rids)))

dup_groups.sort(key=lambda x: x[0])
print(f"Duplicate invoice groups: {len(dup_groups)}")
dup_anomalies = []
dup_all_rids = set()
for i, (inv, rids) in enumerate(dup_groups, 1):
    aid = f"ANOM-DUP-{i:03d}"
    dup_anomalies.append((aid, rids, inv))
    dup_all_rids.update(rids)
    print(f"  {aid}: invoice={inv}, records={rids}")

# ============================================================
# 2. LATE REIMBURSEMENT (>60 days)
# ============================================================
print("\n=== LATE REIMBURSEMENT ===")
late_records = []
for r in records:
    exp_date = parse_date(r['expense_date'])
    reim_date = parse_date(r['reimburse_date'])
    delay = (reim_date - exp_date).days
    if delay > 60:
        late_records.append((r['record_id'], delay, r))

late_records.sort(key=lambda x: x[1], reverse=True)
print(f"Late records (>60 days): {len(late_records)}")
late_anomalies = []
late_all_rids = set()
for i, (rid, delay, rec) in enumerate(late_records, 1):
    aid = f"ANOM-LATE-{i:03d}"
    late_anomalies.append((aid, [rid], rec))
    late_all_rids.add(rid)
    print(f"  {aid}: record={rid}, delay={delay} days, employee={rec['employee_id']}, type={rec['expense_type']}")

# ============================================================
# 3. EXCEEDING STANDARDS (single transaction)
# ============================================================
print("\n=== EXCEEDING STANDARDS ===")
over_std_records = []

for r in records:
    rid = r['record_id']
    etype = r['expense_type']
    amount = r['amount']
    emp_level = r.get('employee_level', 'E1')
    emp_name = r.get('employee_name', '')
    level_cn = get_level(emp_level)
    city_tier = r.get('city_tier', '')
    tier_cn = TIER_MAP.get(city_tier, '')
    nights = r.get('nights') or 0
    days = r.get('days') or 0
    participants = r.get('participants') or 0
    reason = r.get('reason', '')

    if etype == 'travel_lodging':
        if tier_cn and nights > 0:
            std_per_night = TRAVEL_LODGING_STD.get((level_cn, tier_cn))
            if std_per_night:
                per_night = amount / nights
                if per_night > std_per_night:
                    over_std_records.append((rid, etype, amount, std_per_night * nights, 
                                           f"{level_cn}/{tier_cn}/{nights}晚 per_night={per_night:.2f}>std={std_per_night}", r))

    elif etype == 'local_transport':
        if tier_cn and days > 0:
            std_per_day = CITY_TRANSPORT_STD.get(tier_cn)
            if std_per_day:
                per_day = amount / days
                if per_day > std_per_day:
                    over_std_records.append((rid, etype, amount, std_per_day * days,
                                           f"{tier_cn}/{days}天 per_day={per_day:.2f}>std={std_per_day}", r))

    elif etype == 'training_fee':
        # Training course fee: 3500/person/period
        # Training comprehensive: internal 800/day, external 1200/day
        if '课程' in reason or '培训' in reason:
            if amount > 3500:
                over_std_records.append((rid, etype, amount, 3500, f"培训课程费>{3500}", r))
        elif '内部' in reason:
            if days > 0 and amount / days > 800:
                over_std_records.append((rid, etype, amount, 800 * days, f"内部培训>{800*max(days,1)}", r))
        elif '外部' in reason:
            if days > 0 and amount / days > 1200:
                over_std_records.append((rid, etype, amount, 1200 * days, f"外部培训>{1200*max(days,1)}", r))
        else:
            # Check both course fee and day rate
            if amount > 3500:
                over_std_records.append((rid, etype, amount, 3500, f"培训费>{3500}", r))

    elif etype == 'business_entertainment':
        if amount > 5000:
            over_std_records.append((rid, etype, amount, 5000, f"招待费>{5000}", r))
        elif participants > 0 and amount / participants > 300:
            over_std_records.append((rid, etype, amount, 300 * participants, 
                                   f"招待费人均{amount/participants:.2f}>{300}", r))

    elif etype == 'office_supplies':
        # Single transaction: 600/month/person
        if amount > 600:
            over_std_records.append((rid, etype, amount, 600, f"办公用品>{600}", r))

    elif etype == 'communication':
        # Single transaction: 300/month/person
        if amount > 300:
            over_std_records.append((rid, etype, amount, 300, f"通讯费>{300}", r))

over_std_records.sort(key=lambda x: x[2], reverse=True)
print(f"Over-standard records: {len(over_std_records)}")
std_anomalies = []
std_all_rids = set()
for i, (rid, etype, amount, std_limit, detail, rec) in enumerate(over_std_records, 1):
    aid = f"ANOM-STD-{i:03d}"
    std_anomalies.append((aid, [rid], etype, amount, std_limit, detail, rec))
    std_all_rids.add(rid)
    print(f"  {aid}: record={rid}, type={etype}, amount={amount}, std={std_limit}, {detail}")

# ============================================================
# 4. EXCEEDING BUDGET (by department, cumulative)
# ============================================================
print("\n=== EXCEEDING BUDGET ===")
# Sort by reimburse_date then record_id (already sorted)
dept_cumulative = defaultdict(float)
dept_budget_records = {}  # dept -> list of (cumulative_before, record, cumulative_after)

for r in records:
    dept = r['department_id']
    amount = r['amount']
    budget = DEPT_BUDGETS.get(dept, float('inf'))
    before = dept_cumulative[dept]
    dept_cumulative[dept] += amount
    after = dept_cumulative[dept]
    
    if dept not in dept_budget_records:
        dept_budget_records[dept] = []
    dept_budget_records[dept].append((before, after, r))

budget_anomalies = []
budget_all_rids = set()

for dept in sorted(dept_budget_records.keys()):
    budget = DEPT_BUDGETS.get(dept, float('inf'))
    if dept_cumulative[dept] <= budget:
        continue  # Not over budget
    
    # Find first record where cumulative exceeds budget AND no special approval
    # Actually: "以按reimburse_date和record_id累计时首次使累计支出超过预算且无专项审批的记录作为关键记录"
    key_record = None
    for i, (before, after, r) in enumerate(dept_budget_records[dept]):
        if after > budget and r.get('special_approval', 0) == 0:
            key_record = r
            break
    
    if key_record is None:
        # All over-budget records have special approval? No - there are no special approvals
        # Find the first record that pushes cumulative over budget
        for i, (before, after, r) in enumerate(dept_budget_records[dept]):
            if after > budget:
                key_record = r
                break
    
    if key_record:
        aid = f"ANOM-BUD-{dept}"
        budget_anomalies.append((aid, dept, budget, key_record))
        budget_all_rids.add(key_record['record_id'])
        cum_after = dept_cumulative[dept]
        print(f"  {aid}: dept={dept}, budget={budget:.2f}, exceeded={cum_after:.2f}, key_record={key_record['record_id']}, amount={key_record['amount']}")

# ============================================================
# 5. SPLIT REIMBURSEMENT
# ============================================================
print("\n=== SPLIT REIMBURSEMENT ===")
# Group by (employee_id, expense_type)
emp_type_groups = defaultdict(list)
for r in records:
    key = (r['employee_id'], r['expense_type'])
    emp_type_groups[key].append(r)

# For each group, sort by expense_date, find clusters within 7 days
split_anomalies = []
split_all_rids = set()
already_covered = set()  # (emp_id, type, cluster_start_date)

for (emp_id, etype), recs in emp_type_groups.items():
    if len(recs) < 2:
        continue
    
    recs_sorted = sorted(recs, key=lambda r: parse_date(r['expense_date']))
    
    # Sliding window: for each starting record, find consecutive records within 7 days
    n = len(recs_sorted)
    i = 0
    while i < n:
        start_date = parse_date(recs_sorted[i]['expense_date'])
        cluster = [recs_sorted[i]]
        j = i + 1
        while j < n:
            curr_date = parse_date(recs_sorted[j]['expense_date'])
            if (curr_date - start_date).days <= 7:
                cluster.append(recs_sorted[j])
                j += 1
            else:
                break
        
        if len(cluster) >= 2:
            total = sum(r['amount'] for r in cluster)
            
            # Check if total reaches a higher approval tier
            individual_max_tier = 0
            for r in cluster:
                amt = r['amount']
                for t_idx, (lo, hi) in enumerate(APPROVAL_TIERS):
                    if lo <= amt < hi:
                        individual_max_tier = max(individual_max_tier, t_idx)
                        break
            
            total_tier = 0
            for t_idx, (lo, hi) in enumerate(APPROVAL_TIERS):
                if lo <= total < hi:
                    total_tier = t_idx
                    break
            
            if total_tier > individual_max_tier:
                # This is a split!
                cluster_rids = [r['record_id'] for r in cluster]
                cluster_key = (emp_id, etype, str(start_date))
                
                # Check if this cluster overlaps with already covered
                if cluster_key not in already_covered:
                    aid = f"ANOM-SPLIT-{len(split_anomalies)+1:03d}"
                    split_anomalies.append((aid, emp_id, etype, cluster_rids, total, individual_max_tier, total_tier, cluster))
                    split_all_rids.update(cluster_rids)
                    already_covered.add(cluster_key)
                    print(f"  {aid}: employee={emp_id}, type={etype}, start={start_date}, "
                          f"records={cluster_rids}, total={total:.2f}, "
                          f"indiv_tier=AR-{individual_max_tier+1:02d}, total_tier=AR-{total_tier+1:02d}")
        
        i = max(j, i + 1)

print(f"\nSplit anomaly groups: {len(split_anomalies)}")

# ============================================================
# SUMMARY
# ============================================================
print("\n=== SUMMARY ===")
print(f"Duplicate groups: {len(dup_anomalies)}, records: {len(dup_all_rids)}")
print(f"Late records: {len(late_anomalies)}, records: {len(late_all_rids)}")
print(f"Over-standard: {len(std_anomalies)}, records: {len(std_all_rids)}")
print(f"Over-budget: {len(budget_anomalies)}, records: {len(budget_all_rids)}")
print(f"Split groups: {len(split_anomalies)}, records: {len(split_all_rids)}")

total_anomalies = len(dup_anomalies) + len(late_anomalies) + len(std_anomalies) + len(budget_anomalies) + len(split_anomalies)
all_rids = dup_all_rids | late_all_rids | std_all_rids | budget_all_rids | split_all_rids
print(f"Total anomaly instances: {total_anomalies}")
print(f"Total unique records: {len(all_rids)}")

# Save for later
import pickle
with open('/workspace/work/data/analysis_results.pkl', 'wb') as f:
    pickle.dump({
        'dup_anomalies': dup_anomalies,
        'late_anomalies': late_anomalies,
        'std_anomalies': std_anomalies,
        'budget_anomalies': budget_anomalies,
        'split_anomalies': split_anomalies,
        'dup_all_rids': dup_all_rids,
        'late_all_rids': late_all_rids,
        'std_all_rids': std_all_rids,
        'budget_all_rids': budget_all_rids,
        'split_all_rids': split_all_rids,
        'all_rids': all_rids,
        'total_anomalies': total_anomalies,
    }, f)

print("\nAnalysis complete. Results saved.")
