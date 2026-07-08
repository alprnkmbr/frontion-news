#!/usr/bin/env python3
"""Verify the 2026-07-08 energy brief and update index."""
import json
import os

brief_path = '/Users/claudius/clawd/frontion-site/energy/2026-07-08.json'
idx_path = '/Users/claudius/clawd/frontion-site/energy/index.json'

# Verify brief exists and is valid JSON
with open(brief_path) as f:
    brief = json.load(f)
print(f"Brief date: {brief.get('date')}")
print(f"Brief title: {brief.get('title')[:80]}")
print(f"Sections: {len(brief.get('sections', []))}")
print(f"File size: {os.path.getsize(brief_path)} bytes")

# Update index
with open(idx_path) as f:
    data = json.load(f)
new_entry = {'date': '2026-07-08', 'title': 'Iran Deal Opens Hormuz and Unleashes Oil Sales as G7 Scrambles to Contain the Fallout'}
data = [new_entry] + [e for e in data if e['date'] != new_entry['date']]
with open(idx_path, 'w') as f:
    json.dump(data, f, indent=2)
print(f"Index updated: {len(data)} entries, first: {data[0]}")