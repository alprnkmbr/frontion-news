#!/bin/bash
set -e
cd /Users/claudius/clawd/frontion-site
echo "=== Git Status ==="
git status --short
echo "=== Adding files ==="
git add tech/2026-08-06.json tech/index.json tech-feed.xml
echo "=== Committing ==="
git commit -m "tech brief 20260806" || echo "Nothing to commit or already committed"
echo "=== Pushing ==="
git push
echo "=== Done ==="