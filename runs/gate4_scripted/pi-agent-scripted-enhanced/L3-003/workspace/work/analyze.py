import json
import sys

# Employee level mapping based on position_role
def get_lodging_level(position_role):
    mapping = {
        "员工": "员工级",
        "部门经理": "经理级",
        "部门总经理": "部门负责人级",
        "分管副总": "高管级",
        "总经理办公会": "高管级"
    }
    return mapping.get(position_role, "员工级")

# Lodging standards: [员工级, 经理级, 部门负责人级, 高管级]
lodging_standards = {
    "A": [450, 650, 850, 1100],  # 一类城市
    "B": [380, 550, 700, 900],   # 二类城市
    "C": [300, 450, 600, 750]    # 三类城市
}

level_idx = {"员工级": 0, "经理级": 1, "部门负责人级": 2, "高管级": 3}

# Local transport daily standards
transport_standards = {"A": 120, "B": 100, "C": 80}

# Already confirmed anomalies
confirmed = {
    "office_supplies": ["R004221"],
    "communication": ["R004222"],
    "training_fee": ["R004223"],
}

print("Already confirmed anomalies:")
for k, v in confirmed.items():
    print(f"  {k}: {v}")
print()

# Travel lodging X-series already checked:
travel_confirmed = [
    ("R004207", "E0007", "部门经理", "A", 7, 5200, 4550),
    ("R004208", "E0007", "部门经理", "A", 7, 5200, 4550),
    ("R004209", "E0008", "部门经理", "A", 5, 3400, 3250),
    ("R004210", "E0008", "部门经理", "A", 5, 3400, 3250),
    ("R004211", "E0008", "部门经理", "A", 5, 3400, 3250),
    ("R004212", "E0009", "部门经理", "A", 7, 5100, 4550),
    ("R004213", "E0009", "部门经理", "A", 7, 5100, 4550),
    ("R004214", "E0010", "部门经理", "A", 5, 3500, 3250),
    ("R004215", "E0010", "部门经理", "A", 5, 3500, 3250),
    ("R004216", "E0010", "部门经理", "A", 5, 3500, 3250),
]
print("Travel lodging X-series confirmed:")
for r in travel_confirmed:
    print(f"  {r[0]}: {r[5]} vs standard {r[6]}")
print(f"Total travel from X: {len(travel_confirmed)}")

# Also need R004225
print("\nNeed to check R004225 detail")

