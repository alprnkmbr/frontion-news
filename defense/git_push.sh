#!/bin/bash
set -e
cd /Users/claudius/clawd/frontion-site

# Update index.json using python
python3 << 'PYEOF'
import json

idx_path = '/Users/claudius/clawd/frontion-site/defense/index.json'

# Read the brief to get the title
with open('/Users/claudius/clawd/frontion-site/defense/2026-07-13.json') as f:
    brief = json.load(f)

new_entry = {'date': '2026-07-13', 'title': brief['title']}

try:
    with open(idx_path) as f:
        data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    data = []

# Remove any existing entry for today and prepend
data = [new_entry] + [e for e in data if e['date'] != new_entry['date']]

with open(idx_path, 'w') as f:
    json.dump(data, f, indent=2)

print(f"Index updated with {len(data)} entries")
PYEOF

# Git operations
git add defense/
git commit -m "defense brief 20260713" || echo "Nothing to commit"
git push

echo "DONE"