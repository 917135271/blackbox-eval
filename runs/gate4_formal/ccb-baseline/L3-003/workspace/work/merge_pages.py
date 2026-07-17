#!/usr/bin/env python3
"""Merge page JSON files into all_records.json"""
import json, os, sys, glob

WORK_DIR = "/workspace/work"
PAGES_DIR = os.path.join(WORK_DIR, "pages")
ALL_RECORDS = os.path.join(WORK_DIR, "all_records.json")

def main():
    # Read existing records
    existing = []
    if os.path.exists(ALL_RECORDS):
        with open(ALL_RECORDS) as f:
            existing = json.load(f)

    seen_ids = {r['record_id'] for r in existing}

    # Process page files
    page_files = sorted(glob.glob(os.path.join(PAGES_DIR, "page_*.json")))
    new_count = 0
    for pf in page_files:
        with open(pf) as f:
            data = json.load(f)
        records = data.get("records", [])
        for r in records:
            if r['record_id'] not in seen_ids:
                existing.append(r)
                seen_ids.add(r['record_id'])
                new_count += 1

    with open(ALL_RECORDS, 'w') as f:
        json.dump(existing, f, ensure_ascii=False)

    print(f"Merged {new_count} new records from {len(page_files)} page files, total now: {len(existing)}")

if __name__ == "__main__":
    main()
