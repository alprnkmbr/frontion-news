#!/bin/bash
set -e
cd /Users/claudius/clawd/frontion-site
echo "=== Git Status ==="
git status
echo ""
echo "=== Recent Commits ==="
git log --oneline -3
echo ""
echo "=== Headlines Count ==="
python3 -c "import json; d=json.load(open('headlines.json')); print(f'Total: {len(d[\"headlines\"])}'); print(f'Updated: {d[\"lastUpdated\"]}'); print('Top 3:'); [print(f'  {h[\"headline\"][:80]} | {h[\"source\"]}') for h in d['headlines'][:3]]"
echo ""
echo "=== Feed Check ==="
head -5 feed.xml