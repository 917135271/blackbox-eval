"""
RULE 2: 拆分报销 (Split Reimbursement) - Python Window Detection

Finds groups where same employee + same expense_type + expense_date within 7 days
AND >= 2 records AND SUM(amount) >= 3000 (AR-02 threshold from 03_authorization_management)
"""

import csv
from collections import defaultdict
from datetime import datetime, timedelta

# Load all records with employee info
def load_records(csv_path):
    records = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['amount'] = float(row['amount'])
            row['special_approval'] = int(row['special_approval'])
            records.append(row)
    return records

def detect_split_anomalies(records):
    # Group by (employee_id, expense_type)
    groups = defaultdict(list)
    for r in records:
        key = (r['employee_id'], r['expense_type'])
        groups[key].append(r)
    
    anomalies = []
    
    for (emp_id, exp_type), group in groups.items():
        group_sorted = sorted(group, key=lambda x: x['expense_date'])
        
        i = 0
        while i < len(group_sorted):
            window_start = datetime.strptime(group_sorted[i]['expense_date'], '%Y-%m-%d')
            window_records = [group_sorted[i]]
            
            j = i + 1
            while j < len(group_sorted):
                curr_date = datetime.strptime(group_sorted[j]['expense_date'], '%Y-%m-%d')
                if (curr_date - window_start).days <= 7:
                    window_records.append(group_sorted[j])
                    j += 1
                else:
                    break
            
            if len(window_records) >= 2:
                total_amount = sum(r['amount'] for r in window_records)
                if total_amount >= 3000:
                    anomalies.append({
                        'employee_id': emp_id,
                        'expense_type': exp_type,
                        'window_start': window_start.strftime('%Y-%m-%d'),
                        'record_ids': [r['record_id'] for r in window_records],
                        'total_amount': total_amount,
                        'record_count': len(window_records)
                    })
            
            i = j
    
    return anomalies

# Usage:
# records = load_records('/tmp/all_records.csv')
# anomalies = detect_split_anomalies(records)
