import json

# Employee data from the list
employees_raw = [
    {"employee_id":"E0001","employee_level":"D1"}, {"employee_id":"E0002","employee_level":"D1"},
    {"employee_id":"E0003","employee_level":"D1"}, {"employee_id":"E0004","employee_level":"D1"},
    {"employee_id":"E0005","employee_level":"D1"}, {"employee_id":"E0006","employee_level":"D1"},
    {"employee_id":"E0007","employee_level":"D1"}, {"employee_id":"E0008","employee_level":"D1"},
    {"employee_id":"E0009","employee_level":"D1"}, {"employee_id":"E0010","employee_level":"D1"},
    {"employee_id":"E0011","employee_level":"D1"}, {"employee_id":"E0012","employee_level":"X1"},
    {"employee_id":"E0013","employee_level":"X1"}, {"employee_id":"E0014","employee_level":"M1"},
    {"employee_id":"E0015","employee_level":"E1"}, {"employee_id":"E0016","employee_level":"M1"},
    {"employee_id":"E0017","employee_level":"D1"}, {"employee_id":"E0018","employee_level":"M1"},
    {"employee_id":"E0019","employee_level":"M1"}, {"employee_id":"E0020","employee_level":"E1"},
    {"employee_id":"E0021","employee_level":"E1"}, {"employee_id":"E0022","employee_level":"D1"},
    {"employee_id":"E0023","employee_level":"M1"}, {"employee_id":"E0024","employee_level":"E1"},
    {"employee_id":"E0025","employee_level":"E1"}, {"employee_id":"E0026","employee_level":"E1"},
    {"employee_id":"E0027","employee_level":"D1"}, {"employee_id":"E0028","employee_level":"E1"},
    {"employee_id":"E0029","employee_level":"M1"}, {"employee_id":"E0030","employee_level":"X1"},
    {"employee_id":"E0031","employee_level":"M1"}, {"employee_id":"E0032","employee_level":"E1"},
    {"employee_id":"E0033","employee_level":"E1"}, {"employee_id":"E0034","employee_level":"E1"},
    {"employee_id":"E0035","employee_level":"M1"}, {"employee_id":"E0036","employee_level":"E1"},
    {"employee_id":"E0037","employee_level":"E1"}, {"employee_id":"E0038","employee_level":"M1"},
    {"employee_id":"E0039","employee_level":"E1"}, {"employee_id":"E0040","employee_level":"D1"},
    {"employee_id":"E0041","employee_level":"E1"}, {"employee_id":"E0042","employee_level":"M1"},
    {"employee_id":"E0043","employee_level":"E1"}, {"employee_id":"E0044","employee_level":"D1"},
    {"employee_id":"E0045","employee_level":"E1"}, {"employee_id":"E0046","employee_level":"E1"},
    {"employee_id":"E0047","employee_level":"E1"}, {"employee_id":"E0048","employee_level":"M1"},
    {"employee_id":"E0049","employee_level":"E1"}, {"employee_id":"E0050","employee_level":"X1"},
    {"employee_id":"E0051","employee_level":"E1"}, {"employee_id":"E0052","employee_level":"M1"},
    {"employee_id":"E0053","employee_level":"E1"}, {"employee_id":"E0054","employee_level":"E1"},
    {"employee_id":"E0055","employee_level":"D1"}, {"employee_id":"E0056","employee_level":"D1"},
    {"employee_id":"E0057","employee_level":"E1"}, {"employee_id":"E0058","employee_level":"E1"},
    {"employee_id":"E0059","employee_level":"E1"}, {"employee_id":"E0060","employee_level":"E1"},
    {"employee_id":"E0061","employee_level":"M1"}, {"employee_id":"E0062","employee_level":"E1"},
    {"employee_id":"E0063","employee_level":"E1"}, {"employee_id":"E0064","employee_level":"E1"},
    {"employee_id":"E0065","employee_level":"E1"}, {"employee_id":"E0066","employee_level":"M1"},
    {"employee_id":"E0067","employee_level":"M1"}, {"employee_id":"E0068","employee_level":"E1"},
    {"employee_id":"E0069","employee_level":"M1"}, {"employee_id":"E0070","employee_level":"E1"},
    {"employee_id":"E0071","employee_level":"E1"}, {"employee_id":"E0072","employee_level":"M1"},
    {"employee_id":"E0073","employee_level":"E1"}, {"employee_id":"E0074","employee_level":"E1"},
    {"employee_id":"E0075","employee_level":"D1"}, {"employee_id":"E0076","employee_level":"E1"},
    {"employee_id":"E0077","employee_level":"E1"}, {"employee_id":"E0078","employee_level":"E1"},
    {"employee_id":"E0079","employee_level":"M1"}, {"employee_id":"E0080","employee_level":"E1"}
]

emp_levels = {e["employee_id"]: e["employee_level"] for e in employees_raw}

# Level mapping for travel lodging
# E1 = Employee (员工级), M1 = Manager (经理级), D1 = Dept Head (部门负责人级), X1 = Executive (高管级)
# Standards per night:
lodging_standards = {
    "E1": {"class1": 450, "class2": 380, "class3": 300},
    "M1": {"class1": 650, "class2": 550, "class3": 450},
    "D1": {"class1": 850, "class2": 700, "class3": 600},
    "X1": {"class1": 1100, "class2": 900, "class3": 750}
}

# City tier mapping based on common knowledge
# 一类城市: 上海, 北京, 深圳, 广州
# 二类城市: 杭州, 合肥, 成都, 南京, etc.
# 三类城市: others

def infer_city_tier(reason, department_name, expense_date):
    """Infer city tier from reason or department context."""
    reason_lower = reason.lower() if reason else ""
    
    # Class 1 cities (一类城市)
    class1_keywords = ["上海", "北京", "深圳", "广州"]
    for kw in class1_keywords:
        if kw in reason:
            return "class1"
    
    # Class 2 cities (二类城市)
    class2_keywords = ["杭州", "合肥", "成都", "南京", "武汉", "西安", "重庆", "天津", "苏州"]
    for kw in class2_keywords:
        if kw in reason:
            return "class2"
    
    # Default to class2 if no city mentioned (most are provincial capitals)
    return "class2"

# Local transport daily standards
transport_standards = {
    "class1": 120,
    "class2": 100,
    "class3": 80
}

print("Employee levels loaded:", len(emp_levels))
print("Ready for analysis")
