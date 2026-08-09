#!/bin/bash
cd /Users/claudius/clawd/frontion-site
echo "=== Verify brief ===" > /tmp/verify_out.txt
python3 -c "
import json
try:
    with open('briefs/2026-08-06.json') as f:
        d = json.load(f)
    print('BRIEF OK:', d['date'], len(d['sections']), 'sections', file=open('/tmp/verify_out.txt','a'))
except Exception as e:
    print('BRIEF ERROR:', e, file=open('/tmp/verify_out.txt','a'))

try:
    with open('briefs/index.json') as f:
        idx = json.load(f)
    print('INDEX OK:', len(idx), 'entries', file=open('/tmp/verify_out.txt','a'))
    print('First entry:', idx[0], file=open('/tmp/verify_out.txt','a'))
except Exception as e:
    print('INDEX ERROR:', e, file=open('/tmp/verify_out.txt','a'))
" >> /tmp/verify_out.txt 2>&1

echo "=== Generate feed ===" >> /tmp/verify_out.txt
python3 -c "import generate_brief_feed; generate_brief_feed.generate_feed()" >> /tmp/verify_out.txt 2>&1

echo "=== Fix perms ===" >> /tmp/verify_out.txt
chmod 644 briefs/*.json >> /tmp/verify_out.txt 2>&1

echo "=== Git status ===" >> /tmp/verify_out.txt
git status >> /tmp/verify_out.txt 2>&1

echo "=== Git add ===" >> /tmp/verify_out.txt
git add briefs/2026-08-06.json briefs/index.json feed.xml >> /tmp/verify_out.txt 2>&1

echo "=== Git commit ===" >> /tmp/verify_out.txt
git commit -m "strategic brief 2026-08-06" >> /tmp/verify_out.txt 2>&1

echo "=== Git push ===" >> /tmp/verify_out.txt
git push >> /tmp/verify_out.txt 2>&1

echo "=== DONE ===" >> /tmp/verify_out.txt