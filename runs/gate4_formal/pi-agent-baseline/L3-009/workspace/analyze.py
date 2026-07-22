import json, sys
from datetime import datetime, timedelta

# We'll build the analysis incrementally using data from MCP calls
# Let's save the data we have and compute anomalies

# Budget data
budgets = {
    "D001": 230395.17, "D002": 107785.42, "D003": 109772.07,
    "D004": 264890.39, "D005": 278540.94, "D006": 340961.75,
    "D007": 301500.00, "D008": 381600.00, "D009": 191300.00,
    "D010": 164500.00
}

# Standards
# Travel lodging: by level and city tier
lodging_std = {
    "员工级": {"一类": 450, "二类": 380, "三类": 300},
    "经理级": {"一类": 650, "二类": 550, "三类": 450},
    "部门负责人级": {"一类": 850, "二类": 700, "三类": 600},
    "高管级": {"一类": 1100, "二类": 900, "三类": 750},
}
# Training lodging
training_lodging_std = {"一类": 500, "二类": 420, "三类": 350}
# Training course: 3500/person/period
# Internal training: 800/day, External: 1200/day
# Entertainment: 5000/event, 300/person
# Office: 600/person/month
# Communication: 300/person/month
# Local transport daily: 一类120, 二类100, 三类80

print("Analysis script ready")
print("Will process data from MCP results")

