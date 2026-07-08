#!/usr/bin/env python3
"""Verify and deploy the 2026-07-08 energy brief."""
import json
import os
import subprocess

brief_path = '/Users/claudius/clawd/frontion-site/energy/2026-07-08.json'
idx_path = '/Users/claudius/clawd/frontion-site/energy/index.json'
log_path = '/tmp/energy_deploy_log.txt'

log = []

# 1. Verify brief file
try:
    with open(brief_path) as f:
        brief = json.load(f)
    log.append(f"Brief OK: date={brief.get('date')}, sections={len(brief.get('sections',[]))}, size={os.path.getsize(brief_path)}")
except Exception as e:
    log.append(f"Brief ERROR: {e}")

# 2. Update index
try:
    with open(idx_path) as f:
        data = json.load(f)
    new_entry = {'date': '2026-07-08', 'title': 'Iran Deal Opens Hormuz and Unleashes Oil Sales as G7 Scrambles to Contain the Fallout'}
    data = [new_entry] + [e for e in data if e['date'] != new_entry['date']]
    with open(idx_path, 'w') as f:
        json.dump(data, f, indent=2)
    log.append(f"Index OK: {len(data)} entries, first={data[0]}")
except Exception as e:
    log.append(f"Index ERROR: {e}")

# 3. Chmod
try:
    os.system('chmod 644 /Users/claudius/clawd/frontion-site/energy/*.json')
    log.append("Chmod OK")
except Exception as e:
    log.append(f"Chmod ERROR: {e}")

# 4. Git operations
try:
    os.chdir('/Users/claudius/clawd/frontion-site')
    r1 = subprocess.run(['git', 'add', 'energy/'], capture_output=True, text=True)
    log.append(f"Git add: rc={r1.returncode}, stderr={r1.stderr[:200] if r1.stderr else 'none'}")
    
    r2 = subprocess.run(['git', 'commit', '-m', 'energy brief 20260708'], capture_output=True, text=True)
    log.append(f"Git commit: rc={r2.returncode}, stdout={r2.stdout[:200] if r2.stdout else 'none'}, stderr={r2.stderr[:200] if r2.stderr else 'none'}")
    
    r3 = subprocess.run(['git', 'push'], capture_output=True, text=True, timeout=60)
    log.append(f"Git push: rc={r3.returncode}, stdout={r3.stdout[:200] if r3.stdout else 'none'}, stderr={r3.stderr[:200] if r3.stderr else 'none'}")
except Exception as e:
    log.append(f"Git ERROR: {e}")

# Write log
with open(log_path, 'w') as f:
    f.write('\n'.join(log))

print("DONE - check /tmp/energy_deploy_log.txt")