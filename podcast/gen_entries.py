#!/usr/bin/env python3
"""Generate new RSS items and HTML episode entries for 2026-07-19 podcasts."""

import json
import html
import re

DATE = "2026-07-19"
DATE_DISPLAY = "July 19, 2026"
DATE_RFC = "Sat, 19 Jul 2026 07:30:00 +0300"
DATE_HTML = "July 19, 2026"

BASE = "/Users/claudius/clawd/frontion-site"

EPISODES = [
    {
        "prefix": "global",
        "folder": "briefs",
        "label": "Strategic Brief",
        "url": "https://frontion.news",
        "duration": "9:35",
        "size": 4973390,
        "track": 1,
    },
    {
        "prefix": "defence",
        "folder": "defense",
        "label": "Defence & Industry Brief",
        "url": "https://frontion.news/defence",
        "duration": "8:58",
        "size": 4752547,
        "track": 2,
    },
    {
        "prefix": "finance",
        "folder": "finance",
        "label": "Finance & Markets Brief",
        "url": "https://frontion.news/finance",
        "duration": "9:28",
        "size": 4929408,
        "track": 3,
    },
    {
        "prefix": "tech",
        "folder": "tech",
        "label": "Tech Brief",
        "url": "https://frontion.news/tech",
        "duration": "7:26",
        "size": 4197570,
        "track": 4,
    },
]

def strip_html(text):
    if not text:
        return ""
    text = re.sub(r'<p\s*[^>]*>', '\n', text)
    text = re.sub(r'</p>', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    return text

for ep in EPISODES:
    json_path = f"{BASE}/{ep['folder']}/{DATE}.json"
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    title = strip_html(data["title"])
    subhead = strip_html(data["subhead"])
    description = f"{subhead}\n\nRead the full analysis at {ep['url']}"
    
    # RSS title
    rss_title = f"{ep['label']} — {DATE_DISPLAY}: {title}"
    
    print(f"=== {ep['prefix']} ===")
    print(f"Title: {rss_title}")
    print(f"Description: {description}")
    print(f"Duration: {ep['duration']}, Size: {ep['size']}")
    print()
