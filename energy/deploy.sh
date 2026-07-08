#!/bin/bash
echo "=== VERIFY BRIEF ==="
python3 -c "
import json, os
brief_path = '/Users/claudius/clawd/frontion-site/energy/2026-07-08.json'
idx_path = '/Users/claudius/clawd/frontion-site/energy/index.json'
with open(brief_path) as f:
    brief = json.load(f)
with open(idx_path) as f:
    idx = json.load(f)
result = f'Brief: date={brief.get(\"date\")}, sections={len(brief.get(\"sections\",[]))}, size={os.path.getsize(brief_path)}\n'
result += f'Index: entries={len(idx)}, first={idx[0]}\n'
print(result)
"
echo "=== CHMOD ==="
chmod 644 /Users/claudius/clawd/frontion-site/energy/*.json
echo "=== GIT STATUS ==="
cd /Users/claudius/clawd/frontion-site && git status --short energy/
echo "=== GIT ADD ==="
cd /Users/claudius/clawd/frontion-site && git add energy/
echo "=== GIT COMMIT ==="
cd /Users/claudius/clawd/frontion-site && git commit -m "energy brief 20260708"
echo "=== GIT PUSH ==="
cd /Users/claudius/clawd/frontion-site && git push