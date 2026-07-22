import json

# Employee levels
emp_levels = {
    "E0001":"D1","E0002":"D1","E0003":"D1","E0004":"D1","E0005":"D1",
    "E0006":"D1","E0007":"D1","E0008":"D1","E0009":"D1","E0010":"D1",
    "E0011":"D1","E0012":"X1","E0013":"X1","E0014":"M1","E0015":"E1",
    "E0016":"M1","E0017":"D1","E0018":"M1","E0019":"M1","E0020":"E1",
    "E0021":"E1","E0022":"D1","E0023":"M1","E0024":"E1","E0025":"E1",
    "E0026":"E1","E0027":"D1","E0028":"E1","E0029":"M1","E0030":"X1",
    "E0031":"M1","E0032":"E1","E0033":"E1","E0034":"E1","E0035":"M1",
    "E0036":"E1","E0037":"E1","E0038":"M1","E0039":"E1","E0040":"D1",
    "E0041":"E1","E0042":"M1","E0043":"E1","E0044":"D1","E0045":"E1",
    "E0046":"E1","E0047":"E1","E0048":"M1","E0049":"E1","E0050":"X1",
    "E0051":"E1","E0052":"M1","E0053":"E1","E0054":"E1","E0055":"D1",
    "E0056":"D1","E0057":"E1","E0058":"E1","E0059":"E1","E0060":"E1",
    "E0061":"M1","E0062":"E1","E0063":"E1","E0064":"E1","E0065":"E1",
    "E0066":"M1","E0067":"M1","E0068":"E1","E0069":"M1","E0070":"E1",
    "E0071":"E1","E0072":"M1","E0073":"E1","E0074":"E1","E0075":"D1",
    "E0076":"E1","E0077":"E1","E0078":"E1","E0079":"M1","E0080":"E1",
    "E0008":"X1"  # Corrected - E0008 is X1 from original employee list
}

# Wait, let me check: E0008 is listed as "杨丹", D1 in the employee list.
# But R004222 has employee_id E0008 and employee_level D1.
# Let me re-check the employee list.
# From the list_employees output: E0008: 杨丹, D1, 部门经理
# E0012: 杨丽华, X1, 分管副总
# So E0008 is D1, not X1. Let me fix.

emp_levels["E0008"] = "D1"

# Per-night lodging standards
lodging_std = {
    "E1": {"A": 450, "B": 380, "C": 300},
    "M1": {"A": 650, "B": 550, "C": 450},
    "D1": {"A": 850, "B": 700, "C": 600},
    "X1": {"A": 1100, "B": 900, "C": 750}
}

# Records to check (from our earlier pull of >1500 travel_lodging)
# These are the suspicious ones - let me check by record_id to get their details later
# For now, let me check the ones I know

# Known checked:
# R004207: D1, A, 7 nights, 5200 → 742.86 < 850 OK
# R004225: D1, A, 1 night, 900 → 900 > 850 VIOLATION
# R000328: D1, A, 3 nights, 1789.19 → 596.40 < 850 OK
# R000081: D1, B, 4 nights, 1654 → 413.50 < 700 OK
# R000369: D1, A, 3 nights, 2164.85 → 721.62 < 850 OK

# Let's print the suspicious record IDs that need checking
suspicious = [
    "R004207","R004208","R004209","R004210","R004211",
    "R004212","R004213","R004214","R004215","R004216",
    "R004217","R004218","R004219","R004220","R004225",
    "R004233","R004236","R004237"
]

print("Suspicious record IDs:", suspicious)
print("\nNeed to check these via get_expense_detail")
print("R004225 confirmed: D1, A city, 1 night, 900 → per-night 900 > 850 VIOLATION")
