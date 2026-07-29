#!/usr/bin/env python3
import json
import subprocess
import os

os.chdir('/Users/claudius/clawd/frontion-site')

# Read existing index
with open('briefs/index.json', 'r') as f:
    data = json.load(f)

# Prepend new entry
new_entry = {'date': '2026-07-23', 'title': 'US-Saudi Nuclear Deal Reshapes Gulf Power Map, Trump Threatens Iranian Infrastructure Over Hormuz, Houthi Blockade Chokes Red Sea Oil Route'}
data.insert(0, new_entry)

# Write back
with open('briefs/index.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f'Updated index with {len(data)} entries')

# Generate RSS feed
import generate_brief_feed
generate_brief_feed.generate_feed()
print('RSS feed generated')

# Fix permissions
subprocess.run(['chmod', '644', 'briefs/2026-07-23.json'], check=True)
print('Permissions fixed')

# Git push
subprocess.run(['git', 'add', 'briefs/2026-07-23.json', 'briefs/index.json', 'feed.xml'], check=True)
subprocess.run(['git', 'commit', '-m', 'strategic brief 2026-07-23'], check=True)
subprocess.run(['git', 'push'], check=True)
print('Pushed to git')