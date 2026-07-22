import json, sys, os

# We'll process the data from MCP tool calls
# This script will be used to compute cumulative analysis
# Input: JSON array of all expense records
# Output: critical records per department

def compute_critical_records(records, budgets):
    """For each department, sort by reimburse_date then record_id,
    accumulate approved amounts, find first record that pushes 
    cumulative over annual budget."""
    
    # Group by department
    dept_records = {}
    for r in records:
        dept = r['department_id']
        if dept not in dept_records:
            dept_records[dept] = []
        dept_records[dept].append(r)
    
    results = {}
    for dept, recs in dept_records.items():
        # Sort by reimburse_date, then record_id
        recs.sort(key=lambda r: (r['reimburse_date'], r['record_id']))
        
        budget = budgets.get(dept, 0)
        cumulative = 0.0
        critical_record = None
        over_budget = False
        
        for r in recs:
            if cumulative <= budget:
                cumulative += r['amount']
                if cumulative > budget and critical_record is None:
                    critical_record = r['record_id']
                    over_budget = True
        
        results[dept] = {
            'department_name': recs[0]['department_name'],
            'annual_budget': budget,
            'total_spent': cumulative if cumulative > 0 else sum(r['amount'] for r in recs),
            'critical_record_id': critical_record,
            'over_budget': over_budget,
            'record_count': len(recs)
        }
    
    return results

if __name__ == '__main__':
    # This will be populated by the data-gathering phase
    pass
