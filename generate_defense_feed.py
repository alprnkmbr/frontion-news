#!/usr/bin/env python3
"""Generate RSS feed for Defence briefs."""

import json, re
from datetime import datetime, timezone
from pathlib import Path

SITE_DIR = Path(__file__).parent
SECTION_DIR = SITE_DIR / "defense"
FEED_FILE = SITE_DIR / "defense-feed.xml"
SITE_URL = "https://frontion.news"
SECTION_URL = f"{SITE_URL}/defence"

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def xml_escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def summarize_text(text, max_chars=250):
    sentences = []
    current = ""
    for char in text:
        current += char
        if char in ".!?":
            sentences.append(current.strip())
            current = ""
    if current.strip():
        sentences.append(current.strip())
    if not sentences:
        return text[:max_chars]
    result = ""
    for s in sentences:
        if len(result) + len(s) + 1 <= max_chars:
            result = (result + " " + s).strip()
        else:
            break
    if not result:
        result = sentences[0][:max_chars]
    return result

def generate_feed():
    items = []
    index = load_json(SECTION_DIR / "index.json")
    for entry in index:
        slug = entry.get("slug") or entry.get("date", "")
        brief_path = SECTION_DIR / f"{slug}.json"
        if not brief_path.exists():
            continue
        brief = load_json(brief_path)
        title = xml_escape(brief.get("title", entry.get("title", "")))
        subhead = xml_escape(brief.get("subhead", ""))
        bottom_line = xml_escape(brief.get("bottomLine", ""))
        date_str = entry.get("date", brief.get("date", ""))

        desc_parts = []
        if subhead:
            desc_parts.append(subhead)
            desc_parts.append("")
        for section in brief.get("sections", []):
            heading = section.get("heading", "")
            body = section.get("body", "")
            why = section.get("whyItMatters", "")
            if heading:
                desc_parts.append(f"► {heading}")
            if body:
                clean_body = re.sub(r'<[^>]+>', '', body).strip()
                if clean_body:
                    desc_parts.append(summarize_text(clean_body, max_chars=250))
            if why:
                desc_parts.append(f"Why it matters: {summarize_text(why, max_chars=350)}")
                desc_parts.append("")
        if bottom_line:
            desc_parts.append("■ The Bottom Line")
            desc_parts.append(bottom_line)

        description = xml_escape("\n".join(desc_parts))
        if len(description) > 3900:
            description = description[:3890] + "..."

        try:
            dt = datetime.fromisoformat(date_str)
            pub_date = dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
            sort_date = dt
        except:
            pub_date = date_str
            sort_date = datetime.min

        items.append({
            "title": f"Defence Brief: {title}",
            "link": f"{SECTION_URL}/{slug}",
            "description": description,
            "pubDate": pub_date,
            "guid": f"defense-{slug}",
            "category": "Defence",
            "sort_date": sort_date
        })

    items.sort(key=lambda x: x["sort_date"], reverse=True)
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    rss_items = ""
    for item in items[:30]:
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
    <title>Frontion Defence</title>
    <description>Defence and military industry analysis</description>
    <link>{SECTION_URL}</link>
    <atom:link href="{SECTION_URL}/defense-feed.xml" rel="self" type="application/rss+xml"/>
    <language>en</language>
    <lastBuildDate>{now}</lastBuildDate>
    <ttl>60</ttl>
{rss_items}  </channel>
</rss>"""

    with open(FEED_FILE, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"Generated defense-feed.xml with {len(items)} items")

if __name__ == "__main__":
    generate_feed()