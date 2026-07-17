import json, sys, os
from collections import defaultdict

# Employee data
employees = [
    {"employee_id":"E0001","employee_name":"何英","employee_level":"D1","department_id":"D001","position_role":"部门经理"},
    {"employee_id":"E0002","employee_name":"赖红霞","employee_level":"D1","department_id":"D002","position_role":"部门经理"},
    {"employee_id":"E0003","employee_name":"曾桂香","employee_level":"D1","department_id":"D003","position_role":"部门经理"},
    {"employee_id":"E0004","employee_name":"杨秀兰","employee_level":"D1","department_id":"D004","position_role":"部门经理"},
    {"employee_id":"E0005","employee_name":"李桂芳","employee_level":"D1","department_id":"D005","position_role":"部门经理"},
    {"employee_id":"E0006","employee_name":"吴鹏","employee_level":"D1","department_id":"D006","position_role":"部门经理"},
    {"employee_id":"E0007","employee_name":"李丽娟","employee_level":"D1","department_id":"D007","position_role":"部门经理"},
    {"employee_id":"E0008","employee_name":"杨丹","employee_level":"D1","department_id":"D008","position_role":"部门经理"},
    {"employee_id":"E0009","employee_name":"张婷","employee_level":"D1","department_id":"D009","position_role":"部门经理"},
    {"employee_id":"E0010","employee_name":"闭想","employee_level":"D1","department_id":"D010","position_role":"部门经理"},
    {"employee_id":"E0011","employee_name":"杨凤兰","employee_level":"D1","department_id":"D001","position_role":"部门总经理"},
    {"employee_id":"E0012","employee_name":"杨丽华","employee_level":"X1","department_id":"D008","position_role":"分管副总"},
    {"employee_id":"E0013","employee_name":"李波","employee_level":"X1","department_id":"D004","position_role":"总经理办公会"},
]

for i in range(14, 81):
    pass  # placeholder
    
# Load from actual list
emp_data = [
    ("E0001","D1"),("E0002","D1"),("E0003","D1"),("E0004","D1"),("E0005","D1"),
    ("E0006","D1"),("E0007","D1"),("E0008","D1"),("E0009","D1"),("E0010","D1"),
    ("E0011","D1"),("E0012","X1"),("E0013","X1"),("E0014","M1"),("E0015","E1"),
    ("E0016","M1"),("E0017","D1"),("E0018","M1"),("E0019","M1"),("E0020","E1"),
    ("E0021","E1"),("E0022","D1"),("E0023","M1"),("E0024","E1"),("E0025","E1"),
    ("E0026","E1"),("E0027","D1"),("E0028","E1"),("E0029","M1"),("E0030","X1"),
    ("E0031","M1"),("E0032","E1"),("E0033","E1"),("E0034","E1"),("E0035","M1"),
    ("E0036","E1"),("E0037","E1"),("E0038","M1"),("E0039","E1"),("E0040","D1"),
    ("E0041","E1"),("E0042","M1"),("E0043","E1"),("E0044","D1"),("E0045","E1"),
    ("E0046","E1"),("E0047","E1"),("E0048","M1"),("E0049","E1"),("E0050","X1"),
    ("E0051","E1"),("E0052","M1"),("E0053","E1"),("E0054","E1"),("E0055","D1"),
    ("E0056","D1"),("E0057","E1"),("E0058","E1"),("E0059","E1"),("E0060","E1"),
    ("E0061","M1"),("E0062","E1"),("E0063","E1"),("E0064","E1"),("E0065","E1"),
    ("E0066","M1"),("E0067","M1"),("E0068","E1"),("E0069","M1"),("E0070","E1"),
    ("E0071","E1"),("E0072","M1"),("E0073","E1"),("E0074","E1"),("E0075","D1"),
    ("E0076","E1"),("E0077","E1"),("E0078","E1"),("E0079","M1"),("E0080","E1"),
]
emp_level = dict(emp_data)

# Travel lodging standards
# E1=员工: (450,380,300), M1=经理: (650,550,450), D1=部门: (850,700,600), X1=高管: (1100,900,750)
travel_std = {
    'E1': [450, 380, 300],
    'M1': [650, 550, 450],
    'D1': [850, 700, 600],
    'X1': [1100, 900, 750],
}

# Training lodging standards: (500,420,350) regardless of level
training_std = [500, 420, 350]

tier1_kw = ['北京','上海','广州','深圳']
tier2_kw = ['杭州','南京','成都','武汉','西安','重庆','苏州','天津','长沙','郑州','济南','合肥','福州','厦门','青岛','大连','宁波','昆明','沈阳','无锡']

def get_city_tier(reason):
    for kw in tier1_kw:
        if kw in reason:
            return 1
    for kw in tier2_kw:
        if kw in reason:
            return 2
    return 3

print("Employee levels and standards loaded OK")
