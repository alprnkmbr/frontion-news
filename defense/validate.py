import os, json

path1 = '/Users/claudius/clawd/frontion-site/defense/2026-07-04.json'
path2 = '/Users/claudius/clawd/frontion-site/defense/index.json'

print("=== VALIDATION ===")
print(f"Brief file exists: {os.path.exists(path1)}")
if os.path.exists(path1):
    print(f"Brief file size: {os.path.getsize(path1)}")
    with open(path1) as f:
        d = json.load(f)
    print(f"Date: {d['date']}")
    print(f"Title: {d['title']}")
    print(f"Sections: {len(d['sections'])}")
    print(f"Sources: {d['sources'][:80]}...")
else:
    print("BRIEF FILE NOT FOUND!")

print(f"\nIndex file exists: {os.path.exists(path2)}")
if os.path.exists(path2):
    print(f"Index file size: {os.path.getsize(path2)}")
    with open(path2) as f:
        idx = json.load(f)
    print(f"Index entries: {len(idx)}")
    for e in idx[:5]:
        print(f"  {e}")
else:
    print("INDEX FILE NOT FOUND!")

print("\n=== FILES IN DEFENSE DIR ===")
for f in os.listdir('/Users/claudius/clawd/frontion-site/defense/'):
    fpath = os.path.join('/Users/claudius/clawd/frontion-site/defense/', f)
    print(f"  {f} ({os.path.getsize(fpath)} bytes)")