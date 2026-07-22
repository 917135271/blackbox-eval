import json
import sys
from datetime import datetime, timedelta
from collections import defaultdict

# Employee level mapping
LEVEL_MAP = {
    'E1': '员工级',
    'M1': '经理级',
    'D1': '部门负责人级',
    'X1': '高管级'
}

# City tier mapping
TIER_MAP = {
    'A': '一类城市',
    'B': '二类城市',
    'C': '三类城市'
}

# Travel lodging standards: (level, city_tier) -> per_night
TRAVEL_LODGING_STD = {
    ('员工级', '一类城市'): 450,
    ('员工级', '二类城市'): 380,
    ('员工级', '三类城市'): 300,
    ('经理级', '一类城市'): 650,
    ('经理级', '二类城市'): 550,
    ('经理级', '三类城市'): 450,
    ('部门负责人级', '一类城市'): 850,
    ('部门负责人级', '二类城市'): 700,
    ('部门负责人级', '三类城市'): 600,
    ('高管级', '一类城市'): 1100,
    ('高管级', '二类城市'): 900,
    ('高管级', '三类城市'): 750,
}

# City transport standards
CITY_TRANSPORT_STD = {
    '一类城市': 120,
    '二类城市': 100,
    '三类城市': 80,
}

# Training lodging standards
TRAINING_LODGING_STD = {
    '一类城市': 500,
    '二类城市': 420,
    '三类城市': 350,
}

# Approval tiers
APPROVAL_TIERS = [
    ('AR-01', 0, 3000),
    ('AR-02', 3000, 10000),
    ('AR-03', 10000, 50000),
    ('AR-04', 50000, 200000),
    ('AR-05', 200000, float('inf')),
]

# Department budgets
DEPT_BUDGETS = {
    'D001': 230395.17,
    'D002': 107785.42,
    'D003': 109772.07,
    'D004': 264890.39,
    'D005': 278540.94,
    'D006': 340961.75,
    'D007': 301500.0,
    'D008': 381600.0,
    'D009': 191300.0,
    'D010': 164500.0,
}

# Employee data
EMPLOYEES = {}
def load_employees():
    return EMPLOYEES

print("Analysis module loaded successfully")
