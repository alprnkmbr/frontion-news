#!/bin/bash
cd /Users/claudius/clawd/frontion-site
chmod 644 briefs/*.json
git add briefs/2026-07-31.json briefs/index.json feed.xml
git commit -m "strategic brief 2026-07-31" || true
git push
echo "PUSH_COMPLETE"