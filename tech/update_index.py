import json

idx_path = '/Users/claudius/clawd/frontion-site/tech/index.json'
with open(idx_path) as f:
    data = json.load(f)

new_entry = {
    'date': '2026-08-11',
    'title': 'South Korea Launches $3.5B Chip Fund and Relocates Airbase, House Dems Demand Answers on Rogue AI Agents, Unitree Raises $900M Amid US-China Robot Tensions'
}

# Remove any existing entry for this date
data = [e for e in data if e['date'] != '2026-08-11']
# Prepend new entry
data.insert(0, new_entry)

with open(idx_path, 'w') as f:
    json.dump(data, f, indent=2)

print(f"Index updated. Total entries: {len(data)}")
print(f"First entry: {data[0]['date']} - {data[0]['title']}")