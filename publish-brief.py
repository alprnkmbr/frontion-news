#!/usr/bin/env python3
"""
publish-brief.py — Convert a brief JSON to The Geopol Brief site format
and update index.json + RSS feed.

Usage:
  python3 publish-brief.py <brief.json>

The brief.json format (from cron):
{
  "slug": "2026-04-17-morning",
  "type": "morning"|"evening",
  "date": "2026-04-17T07:00:00+03:00",
  "title": "...",
  "standfirst": "...",
  "stories": [
    {
      "emoji": "🇺🇸🇮🇷",
      "category": "US-Iran War",
      "headline": "...",
      "body": "...",
      "source": "Reuters",
      "source_url": "https://..."
    }
  ]
}
"""

import json
import sys
import os
from datetime import datetime, timezone

SITE_DIR = os.path.dirname(os.path.abspath(__file__))
BRIEFS_DIR = os.path.join(SITE_DIR, "briefs")
SITE_URL = "https://alprnkmbr.github.io/geopol-brief"

def publish(brief_path):
    with open(brief_path, "r", encoding="utf-8") as f:
        brief = json.load(f)

    slug = brief["slug"]

    # Write the full brief JSON
    brief_file = os.path.join(BRIEFS_DIR, f"{slug}.json")
    with open(brief_file, "w", encoding="utf-8") as f:
        json.dump(brief, f, ensure_ascii=False, indent=2)
    print(f"Written: {brief_file}")

    # Update index.json
    index_file = os.path.join(BRIEFS_DIR, "index.json")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            index = json.load(f)
    else:
        index = []

    # Remove existing entry with same slug
    index = [e for e in index if e["slug"] != slug]

    # Add entry at the beginning
    entry = {
        "slug": brief["slug"],
        "type": brief["type"],
        "date": brief["date"],
        "title": brief["title"],
        "stories": [{"headline": s["headline"]} for s in brief.get("stories", [])]
    }
    index.insert(0, entry)

    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"Updated: {index_file}")

    # Update RSS feed
    update_rss(index, brief)
    print("Done! Brief published.")

def update_rss(index, latest_brief):
    import xml.etree.ElementTree as ET

    items = ""
    for entry in index[:20]:
        slug = entry["slug"]
        btype = entry["type"]
        label = "Morning Brief" if btype == "morning" else "Evening Analysis"
        emoji = "☀️" if btype == "morning" else "🌙"
        desc = entry.get("stories", [])
        desc_text = f"{emoji} {label}. " + ". ".join(s["headline"] for s in desc[:3]) if desc else f"{emoji} {label}"
        date_str = entry["date"]
        # Parse ISO date
        try:
            dt = datetime.fromisoformat(date_str)
            rfc_date = dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
        except:
            rfc_date = date_str

        items += f"""
    <item>
      <title>{entry["title"]}</title>
      <link>{SITE_URL}/brief.html?b={slug}</link>
      <description>{desc_text}</description>
      <pubDate>{rfc_date}</pubDate>
      <guid>{slug}</guid>
    </item>"""

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>The Geopol Brief</title>
    <description>Geopolitical analysis, twice daily</description>
    <link>{SITE_URL}</link>
    <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
    <language>en</language>
    <lastBuildDate>{datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")}</lastBuildDate>
{items}
  </channel>
</rss>"""

    feed_file = os.path.join(SITE_DIR, "feed.xml")
    with open(feed_file, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"Updated: {feed_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 publish-brief.py <brief.json>")
        sys.exit(1)
    publish(sys.argv[1])