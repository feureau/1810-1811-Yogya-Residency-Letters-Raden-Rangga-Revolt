#!/usr/bin/env python3
"""
build_site_data.py
Generates data.json in the repository root from manifest.json for the static web viewer.
"""

import json
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
MANIFEST_FILE = WORKSPACE_DIR / "manifest.json"
DATA_FILE = WORKSPACE_DIR / "data.json"

def build_site_data():
    if not MANIFEST_FILE.exists():
        raise FileNotFoundError(f"Manifest not found: {MANIFEST_FILE}")

    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    items = manifest.get("items", [])
    site_items = []

    for item in items:
        site_entry = {
            "id": item["id"],
            "image": f"jpg/{item['filename']}",
            "text": item.get("transcription_file"),
            "status": item.get("status", "pending"),
            "category": item.get("category", "research_notes"),
            "description": item.get("description", ""),
            "index": item.get("index", 0)
        }
        site_items.append(site_entry)

    with open(DATA_FILE, "w", encoding="utf-8") as out:
        json.dump(site_items, out, indent=2, ensure_ascii=False)

    completed_count = sum(1 for e in site_items if e["status"] == "completed")
    print(f"data.json written to {DATA_FILE}")
    print(f"Total entries: {len(site_items)} (Completed: {completed_count}, Pending: {len(site_items) - completed_count})")
    return site_items

if __name__ == "__main__":
    build_site_data()
