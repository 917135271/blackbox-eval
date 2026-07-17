import json, os

# This script will be called to build final results
# We'll save query results and extract record IDs

def process():
    records_dir = "/workspace/work/records"
    os.makedirs(records_dir, exist_ok=True)
    
    # These will be populated from MCP query results
    all_record_ids = []
    anomaly_map = {}
    
    # Department info
    dept_info = {
        "D001": {"anomaly_id": "BUDGET_OVER_D001", "name": "投资银行部", "budget": 230395.17, "used": 363614.58, "over": 133219.41, "usage_rate": 1.5782},
        "D002": {"anomaly_id": "BUDGET_OVER_D002", "name": "固定收益部", "budget": 107785.42, "used": 164928.12, "over": 57142.70, "usage_rate": 1.5302},
        "D003": {"anomaly_id": "BUDGET_OVER_D003", "name": "财富管理部", "budget": 109772.07, "used": 174150.67, "over": 64378.60, "usage_rate": 1.5865},
        "D004": {"anomaly_id": "BUDGET_OVER_D004", "name": "研究所", "budget": 264890.39, "used": 408832.95, "over": 143942.56, "usage_rate": 1.5434},
        "D005": {"anomaly_id": "BUDGET_OVER_D005", "name": "机构业务部", "budget": 278540.94, "used": 433442.76, "over": 154901.82, "usage_rate": 1.5561},
        "D006": {"anomaly_id": "BUDGET_OVER_D006", "name": "运营管理部", "budget": 340961.75, "used": 530241.29, "over": 189279.54, "usage_rate": 1.5551},
    }
    
    for did, info in dept_info.items():
        fname = f"{records_dir}/{did}.json"
        if os.path.exists(fname):
            with open(fname) as f:
                data = json.load(f)
            records = [r["record_id"] for r in data.get("records", [])]
            all_record_ids.extend(records)
            anomaly_map[info["anomaly_id"]] = records
            print(f"{did}: {len(records)} records")
    
    print(f"Total: {len(all_record_ids)} records")
    return all_record_ids, anomaly_map

if __name__ == "__main__":
    process()
