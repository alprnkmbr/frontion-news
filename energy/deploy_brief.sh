#!/bin/bash
# Energy brief 2026-07-08 deploy script
# Run this manually if the automated deploy failed:
#   bash /Users/claudius/clawd/frontion-site/energy/deploy_brief.sh

set -e
cd /Users/claudius/clawd/frontion-site

echo "=== Updating index ==="
python3 -c "
import json
idx_path = 'energy/index.json'
with open(idx_path) as f:
    data = json.load(f)
new_entry = {'date': '2026-07-08', 'title': 'Iran Deal Opens Hormuz and Unleashes Oil Sales as G7 Scrambles to Contain the Fallout'}
data = [new_entry] + [e for e in data if e['date'] != new_entry['date']]
with open(idx_path, 'w') as f:
    json.dump(data, f, indent=2)
print(f'Index updated: {len(data)} entries')
"

echo "=== Chmod ==="
chmod 644 energy/*.json

echo "=== Git add ==="
git add energy/

echo "=== Git commit ==="
git commit -m "energy brief 20260708"

echo "=== Git push ==="
git push

echo "=== DONE ==="