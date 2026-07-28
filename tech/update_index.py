import json

idx_path = '/Users/claudius/clawd/frontion-site/tech/index.json'
with open(idx_path) as f:
    data = json.load(f)

new_entry = {'date': '2026-07-28', 'title': 'Korean Chips Crash as CXMT Rattles DRAM, Nvidia Launches Open AI Alliance, US 6G Pact Counters China'}
data = [new_entry] + [e for e in data if e['date'] != new_entry['date']]

with open(idx_path, 'w') as f:
    json.dump(data, f, indent=2)

print("Done")