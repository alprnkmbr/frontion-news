#!/usr/bin/env python3
"""
generate_brief_feed.py — Generate RSS feed from briefs (Global + Weekly only).

Output: feed.xml with items for each Global daily brief and Weekly brief.
Each item contains: title, description (subhead), link to the brief on the site.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

SITE_DIR = Path(__file__).parent
BRIEFS_DIR = SITE_DIR / "briefs"
WEEKLY_DIR = SITE_DIR / "weekly"
FEED_FILE = SITE_DIR / "feed.xml"
SITE_URL = "https://alprnkmbr.github.io/frontion-news"

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def xml_escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def generate_feed():
    items = []

    # Load brief index
    brief_index = load_json(BRIEFS_DIR / "index.json")
    for entry in brief_index:
        # Index may use 'slug' or just 'date'
        slug = entry.get("slug") or entry.get("date", "")
        brief_path = BRIEFS_DIR / f"{slug}.json"
        if not brief_path.exists():
            continue

        brief = load_json(brief_path)

        # Skip morning briefs — only include evening/strategic briefs
        if brief.get("type") == "morning" or "-morning" in slug:
            continue

        title = xml_escape(brief.get("title", entry.get("title", "")))
        subhead = xml_escape(brief.get("subhead", ""))
        bottom_line = xml_escape(brief.get("bottomLine", ""))
        date_str = entry.get("date", brief.get("date", ""))
        label = "Evening Strategic Brief"

        # Build rich description with sections and whyItMatters
        desc_parts = [subhead]
        for section in brief.get("sections", []):
            heading = section.get("heading", "")
            why = section.get("whyItMatters", "")
            if heading and why:
                desc_parts.append(f"\n\n{heading}\nWhy it matters: {why}")
        if bottom_line:
            desc_parts.append(f"\n\nThe Bottom Line: {bottom_line}")
        description = xml_escape(" ".join(desc_parts))

        # Parse date for sorting and pubDate
        try:
            dt = datetime.fromisoformat(date_str)
            pub_date = dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
            sort_date = dt
        except:
            pub_date = date_str
            sort_date = datetime.min

        link = f"{SITE_URL}/brief.html?b={slug}"
        items.append({
            "title": f"{label}: {title}",
            "link": link,
            "description": description,
            "pubDate": pub_date,
            "guid": slug,
            "category": "Evening Strategic Brief",
            "sort_date": sort_date
        })

    # Sort by date descending (newest first)
    items.sort(key=lambda x: x["sort_date"], reverse=True)

    # Build RSS
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    rss_items = ""
    for item in items[:30]:  # Keep last 30 items
        rss_items += f"""<item>
<title>{item['title']}</title>
<link>{item['link']}</link>
<description>{item['description']}</description>
<category>{item['category']}</category>
<pubDate>{item['pubDate']}</pubDate>
<guid>{item['guid']}</guid>
</item>
"""

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Frontion News</title>
    <description>Strategic analysis of the events reshaping the world.</description>
    <link>{SITE_URL}</link>
    <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
    <language>en</language>
    <lastBuildDate>{now}</lastBuildDate>
    <ttl>60</ttl>
{rss_items}  </channel>
</rss>"""

    with open(FEED_FILE, "w", encoding="utf-8") as f:
        f.write(rss)

    print(f"Generated feed.xml with {len(items)} items")

if __name__ == "__main__":
    generate_feed()