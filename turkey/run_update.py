#!/usr/bin/env python3
import json
import os
import sys

# Step 1: Verify the brief file exists
brief_path = '/Users/claudius/clawd/frontion-site/turkey/2026-08-11.json'
if os.path.exists(brief_path):
    with open(brief_path) as f:
        data = json.load(f)
    with open('/Users/claudius/clawd/frontion-site/turkey/verify_output.txt', 'w') as out:
        out.write(f"Brief exists: date={data['date']}\n")
        out.write(f"Title: {data['title'][:80]}\n")
        out.write(f"Sections: {len(data['sections'])}\n")
else:
    with open('/Users/claudius/clawd/frontion-site/turkey/verify_output.txt', 'w') as out:
        out.write("BRIEF FILE NOT FOUND\n")
    sys.exit(1)

# Step 2: Update index
idx_path = '/Users/claudius/clawd/frontion-site/turkey/index.json'
with open(idx_path) as f:
    idx = json.load(f)

new_entry = {'date': '2026-08-11', 'title': 'Iran Assassination Threat Forced Secret Trump Departure From Ankara, PKK Peace Law Passes 468-88, Kazakhstan Turns to BTC Pipeline'}
idx = [new_entry] + [e for e in idx if e['date'] != new_entry['date']]

with open(idx_path, 'w') as f:
    json.dump(idx, f, indent=2, ensure_ascii=False)

with open('/Users/claudius/clawd/frontion-site/turkey/verify_output.txt', 'a') as out:
    out.write(f"Index updated. First entry: {idx[0]['date']} - {idx[0]['title'][:60]}\n")
    out.write(f"Total entries: {len(idx)}\n")

print("Done!")