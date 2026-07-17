import json

# Build the record_id list from the query results
# These are the department queries I need to process
# For each over-budget department, records from crossing month onward

departments = {
    "D001": {"crossing": "2025-09-01", "anomaly_id": "BUDGET_OVER_D001"},
    "D002": {"crossing": "2025-08-01", "anomaly_id": "BUDGET_OVER_D002"},
    "D003": {"crossing": "2025-08-01", "anomaly_id": "BUDGET_OVER_D003"},
    "D004": {"crossing": "2025-09-01", "anomaly_id": "BUDGET_OVER_D004"},
    "D005": {"crossing": "2025-09-01", "anomaly_id": "BUDGET_OVER_D005"},
    "D006": {"crossing": "2025-09-01", "anomaly_id": "BUDGET_OVER_D006"},
}

print("Script ready. Will use MCP tools to query records.")
