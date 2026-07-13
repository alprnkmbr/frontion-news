import json, os

d = '/Users/claudius/clawd/frontion-site/defense'
brief = os.path.join(d, '2026-07-13.json')
idx = os.path.join(d, 'index.json')

print(f"Brief exists: {os.path.isfile(brief)}")
print(f"Index exists: {os.path.isfile(idx)}")

if os.path.isfile(brief):
    with open(brief) as f:
        data = json.load(f)
    print(f"Title: {data['title']}")
    print(f"Sections: {len(data['sections'])}")
    print(f"Date: {data['date']}")
    print(f"Bottom line length: {len(data['bottomLine'])}")
else:
    print("Brief file not found!")

# Check if index needs updating
if os.path.isfile(idx):
    with open(idx) as f:
        idx_data = json.load(f)
    print(f"Current index entries: {len(idx_data)}")
    dates = [e['date'] for e in idx_data]
    if '2026-07-13' not in dates:
        idx_data = [{'date': '2026-07-13', 'title': data['title']}] + idx_data
        with open(idx, 'w') as f:
            json.dump(idx_data, f, indent=2)
        print("Updated index with new entry")
    else:
        print("Index already contains today's entry")
else:
    # Create index
    with open(idx, 'w') as f:
        json.dump([{'date': '2026-07-13', 'title': data['title']}], f, indent=2)
    print("Created new index file")