#!/bin/bash
cd /Users/claudius/clawd/frontion-site
rm -f tech/push.sh
echo "=== Git log ==="
git log --oneline -5
echo "=== Index head ==="
head -15 tech/index.json
echo "=== Brief head ==="
head -5 tech/2026-07-23.json