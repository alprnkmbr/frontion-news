#!/bin/bash
set -e
cd /Users/claudius/clawd/frontion-site

# Verify JSON files are valid
python3 -c "
import json
with open('briefs/2026-08-06.json') as f:
    d = json.load(f)
assert d['date'] == '2026-08-06'
assert len(d['sections']) >= 4
print('Brief validated: ' + d['date'] + ' - ' + str(len(d['sections'])) + ' sections')

with open('briefs/index.json') as f:
    idx = json.load(f)
assert idx[0]['date'] == '2026-08-06'
print('Index validated: ' + str(len(idx)) + ' entries')
"

# Generate RSS feed
python3 -c "import generate_brief_feed; generate_brief_feed.generate_feed()"

# Fix permissions
chmod 644 briefs/*.json

# Git operations
git add briefs/2026-08-06.json briefs/index.json feed.xml
git commit -m "strategic brief 2026-08-06"
git push

echo "DEPLOY COMPLETE"