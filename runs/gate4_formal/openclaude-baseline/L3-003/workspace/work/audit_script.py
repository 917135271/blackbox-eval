import json

# Known single-transaction certainties from queries:
# office_supplies > 600: R004221 (650.00)
# communication > 300: R004222 (330.00)
# training_fee > 3500: R004223 (3700.00)

# Let's load the persisted output files to analyze travel_lodging > 1100 and local_transport

# For travel_lodging, we need to check per-night rate against standard
# Standards per policy 04_travel_expense Article 4:
# Level mapping (from detail: D1=员工级):
#   员工级 (D1): A=450, B=380, C=300
#   经理级 (D2): A=650, B=550, C=450
#   部门负责人级 (D3): A=850, B=700, C=600
#   高管级 (D4): A=1100, B=900, C=750

lodging_std = {
    '员工级': {'A': 450, 'B': 380, 'C': 300},
    '经理级': {'A': 650, 'B': 550, 'C': 450},
    '部门负责人级': {'A': 850, 'B': 700, 'C': 600},
    '高管级': {'A': 1100, 'B': 900, 'C': 750},
}

# For local_transport per policy 04_travel_expense Article 6:
# 一类城市 120/day, 二类城市 100/day, 三类城市 80/day
transport_std = {'A': 120, 'B': 100, 'C': 80}

print("Script loaded with standards")
