import json

idx_path = '/Users/claudius/clawd/frontion-site/turkey/index.json'

with open(idx_path) as f:
    data = json.load(f)

new_entry = {'date': '2026-08-11', 'title': 'Iran Assassination Threat Forced Secret Trump Departure From Ankara, PKK Peace Law Passes 468-88, Kazakhstan Turns to BTC Pipeline'}

# Remove any existing entry for same date, then prepend
data = [new_entry] + [e for e in data if e['date'] != new_entry['date']]

with open(idx_path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Index updated. Total entries: {len(data)}")
print(f"First entry: {data[0]['date']} - {data[0]['title']}")