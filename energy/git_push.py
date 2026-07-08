#!/usr/bin/env python3
import json, os, subprocess

os.chdir('/Users/claudius/clawd/frontion-site')

# Update index
idx_path = 'energy/index.json'
with open(idx_path) as f:
    data = json.load(f)
new_entry = {'date': '2026-07-08', 'title': 'Iran Deal Opens Hormuz and Unleashes Oil Sales as G7 Scrambles to Contain the Fallout'}
data = [new_entry] + [e for e in data if e['date'] != new_entry['date']]
with open(idx_path, 'w') as f:
    json.dump(data, f, indent=2)

# Chmod
os.system('chmod 644 energy/*.json')

# Git add
subprocess.run(['git', 'add', 'energy/'], check=True)

# Git commit
subprocess.run(['git', 'commit', '-m', 'energy brief 20260708'], check=True)

# Git push
subprocess.run(['git', 'push'], check=True, timeout=60)

print('DEPLOY COMPLETE')