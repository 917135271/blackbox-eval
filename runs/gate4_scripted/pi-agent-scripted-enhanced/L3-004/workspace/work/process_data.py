# Now let me compute with the data at hand
# Key findings from summarize calls (expense_date based):
# D001: cum@2025-09-20=229926.35, cum@2025-09-21=230552.13, crossing record R001388
# D002: cum@2025-08-25=106977.46, cum@2025-08-31=108327.03
# D003: cum@2025-08-15=106766.83, cum@2025-08-20=110983.44

# Let me query the specific crossing records
print("D001 crossing record: R001388 (amount=625.78, cum before=229926.35, cum after=230552.13)")
print("Budget D001: 230395.17, so cum after exceeds by 156.96")

# For D002, D003 let me query the exact records
import json
budgets = {"D001": 230395.17, "D002": 107785.42, "D003": 109772.07,
           "D004": 264890.39, "D005": 278540.94, "D006": 340961.75}

# Daily cumulatives from summarize calls
d001_daily = [(20250920, 229926.35), (20250921, 230552.13)]
d002_daily = [(20250825, 106977.46), (20250831, 108327.03)]
d003_daily = [(20250815, 106766.83), (20250820, 110983.44)]

print("\nD002: records needed between 2025-08-25 and 2025-08-31 (expense_date)")
print("Need:", 107785.42 - 106977.46, "to cross")
print("D003: records needed between 2025-08-15 and 2025-08-20 (expense_date)")
print("Need:", 109772.07 - 106766.83, "to cross")
