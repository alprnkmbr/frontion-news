#!/usr/bin/env python3
"""Deploy energy brief 2026-07-08: update index, chmod, git add/commit/push."""
import json, os, subprocess, sys

os.chdir('/Users/claudius/clawd/frontion-site')

log = []

# 1. Verify brief exists
brief_path = 'energy/2026-07-08.json'
if not os.path.exists(brief_path):
    log.append(f"ERROR: Brief file not found at {brief_path}")
    with open('/tmp/deploy_log.txt', 'w') as f:
        f.write('\n'.join(log))
    sys.exit(1)

with open(brief_path) as f:
    brief = json.load(f)
log.append(f"Brief verified: {brief['date']}, {len(brief['sections'])} sections")

# 2. Update index
idx_path = 'energy/index.json'
with open(idx_path) as f:
    data = json.load(f)
new_entry = {'date': '2026-07-08', 'title': 'Iran Deal Opens Hormuz and Unleashes Oil Sales as G7 Scrambles to Contain the Fallout'}
data = [new_entry] + [e for e in data if e['date'] != new_entry['date']]
with open(idx_path, 'w') as f:
    json.dump(data, f, indent=2)
log.append(f"Index updated: {len(data)} entries")

# 3. Chmod
subprocess.run(['chmod', '644'] + [f'energy/{f}' for f in os.listdir('energy') if f.endswith('.json')], check=True)
log.append("Chmod 644 done")

# 4. Git add
r = subprocess.run(['git', 'add', 'energy/'], capture_output=True, text=True)
log.append(f"Git add: rc={r.returncode}")

# 5. Git commit
r = subprocess.run(['git', 'commit', '-m', 'energy brief 20260708'], capture_output=True, text=True)
log.append(f"Git commit: rc={r.returncode}")

# 6. Git push
r = subprocess.run(['git', 'push'], capture_output=True, text=True, timeout=60)
log.append(f"Git push: rc={r.returncode}")

with open('/tmp/deploy_log.txt', 'w') as f:
    f.write('\n'.join(log))

print('\n'.join(log))