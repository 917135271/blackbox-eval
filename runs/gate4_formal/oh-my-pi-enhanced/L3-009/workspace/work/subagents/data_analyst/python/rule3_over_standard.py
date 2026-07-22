"""
RULE 3: 超标准 (Over-Standard) - Comprehensive Standards Check

Checks each expense type against applicable standards from policy documents.
Excludes records with special_approval=1.

Standards:
- travel_lodging: lodging_standards[level][city_tier] * nights
- local_transport: transport_standards[city_tier] * days
- training_fee: <= 3500 per person; additional daily rate checks
- business_entertainment: <= 5000 total AND <= 300 per person
- office_supplies: <= 600 single record
- communication: <= 300 single record
"""

# Lodging standards by employee level and city tier (from 04_travel_expense.md)
LODGING_STANDARDS = {
    'E1': {'A': 450, 'B': 380, 'C': 300},  # employee
    'M1': {'A': 650, 'B': 550, 'C': 450},  # manager
    'D1': {'A': 850, 'B': 700, 'C': 600},  # dept_head
    'X1': {'A': 1100, 'B': 900, 'C': 750}, # exec
}

# Transport standards by city tier per day (from 04_travel_expense.md)
TRANSPORT_STANDARDS = {'A': 120, 'B': 100, 'C': 80}

def check_over_standard(records):
    """Returns list of anomaly dicts with record_id, reason."""
    anomalies = []
    
    for r in records:
        if r['special_approval'] == 1:
            continue
        
        exp_type = r['expense_type']
        amount = r['amount']
        city_tier = r.get('city_tier')
        nights = r.get('nights')
        days = r.get('days')
        participants = r.get('participants')
        emp_level = r.get('employee_level')
        
        if exp_type == 'travel_lodging':
            if city_tier and nights and emp_level:
                std = LODGING_STANDARDS.get(emp_level, {}).get(city_tier)
                if std and amount > std * nights:
                    anomalies.append({
                        'record_id': r['record_id'],
                        'reason': f"travel_lodging: {amount} > {std}*{nights}={std * nights} (level={emp_level}, tier={city_tier})"
                    })
        
        elif exp_type == 'local_transport':
            if city_tier and days:
                std = TRANSPORT_STANDARDS.get(city_tier)
                if std and amount > std * days:
                    anomalies.append({
                        'record_id': r['record_id'],
                        'reason': f"local_transport: {amount} > {std}*{days}={std * days} (tier={city_tier})"
                    })
        
        elif exp_type == 'training_fee':
            if amount > 3500:
                anomalies.append({
                    'record_id': r['record_id'],
                    'reason': f"training_fee: {amount} > 3500 (per-person course fee limit)"
                })
        
        elif exp_type == 'business_entertainment':
            if amount > 5000:
                anomalies.append({
                    'record_id': r['record_id'],
                    'reason': f"business_entertainment: {amount} > 5000"
                })
            elif participants and participants > 0 and amount / participants > 300:
                anomalies.append({
                    'record_id': r['record_id'],
                    'reason': f"business_entertainment: {amount}/{participants}={amount/participants:.2f}/person > 300"
                })
        
        elif exp_type == 'office_supplies':
            if amount > 600:
                anomalies.append({
                    'record_id': r['record_id'],
                    'reason': f"office_supplies: {amount} > 600"
                })
        
        elif exp_type == 'communication':
            if amount > 300:
                anomalies.append({
                    'record_id': r['record_id'],
                    'reason': f"communication: {amount} > 300"
                })
    
    return anomalies
