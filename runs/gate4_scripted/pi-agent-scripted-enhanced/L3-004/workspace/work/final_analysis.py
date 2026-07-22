# Based on the data gathered, here are the estimated crossing records
# by reimburse_date order. Let me now verify with specific queries.

# Key findings so far:
# D001: R001388 (special_approval=0, reimburse_date=2025-09-27, amount=625.78)
#   cum before ~229,926.35, cum after ~230,552.13 > budget 230,395.17

# For remaining departments, let me query the specific candidate records
# based on the crossing point estimated from expense_date ordering
# and verify special_approval

departments = {
    "D001": {"budget": 230395.17, "candidate": "R001388", "special_approval": 0},
    "D002": {"budget": 107785.42},
    "D003": {"budget": 109772.07},
    "D004": {"budget": 264890.39},
    "D005": {"budget": 278540.94},
    "D006": {"budget": 340961.75},
}

print("Need to find crossing records for D002-D006")
print("Will query records near crossing points and check special_approval")
