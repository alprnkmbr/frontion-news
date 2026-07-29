import json
with open('/Users/claudius/clawd/frontion-site/headlines.json') as f:
    d = json.load(f)
print(f"Total: {len(d['headlines'])}")
print(f"Updated: {d['lastUpdated']}")
for i, h in enumerate(d['headlines'][:5]):
    print(f"  {i+1}. {h['headline'][:80]} | {h['source']}")