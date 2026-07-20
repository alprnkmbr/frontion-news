#!/usr/bin/env python3
"""Build podcast scripts from JSON briefs, stripping HTML and generating TTS-ready text."""

import json
import html
import re
import os

DATE = "2026-07-19"
BASE = "/Users/claudius/clawd/frontion-site"

BRIEF_CONFIG = {
    "briefs": {
        "prefix": "global",
        "label": "Strategic Brief",
        "url": "https://frontion.news",
    },
    "defense": {
        "prefix": "defence",
        "label": "Defence & Industry Brief",
        "url": "https://frontion.news/defence",
    },
    "finance": {
        "prefix": "finance",
        "label": "Finance & Markets Brief",
        "url": "https://frontion.news/finance",
    },
    "tech": {
        "prefix": "tech",
        "label": "Tech Brief",
        "url": "https://frontion.news/tech",
    },
}

def strip_html(text):
    """Remove all HTML tags, replace <p> with newlines, decode entities."""
    if not text:
        return ""
    # Replace <p> tags with newlines
    text = re.sub(r'<p\s*[^>]*>', '\n', text)
    text = re.sub(r'</p>', '', text)
    # Remove all other HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    text = html.unescape(text)
    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    return text

def format_date(date_str):
    """Convert 2026-07-19 to 'July 19, 2026'."""
    from datetime import datetime
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%B %-d, %Y")

def build_script(data, config):
    """Build the TTS script from JSON data."""
    date_formatted = format_date(data["date"])
    label = config["label"]
    url = config["url"]
    
    lines = []
    
    # Intro
    lines.append(f"Welcome to Frontion News' {label} for {date_formatted}.")
    lines.append("")
    
    # Title
    lines.append(strip_html(data["title"]))
    lines.append("")
    
    # Subhead
    lines.append(strip_html(data["subhead"]))
    lines.append("")
    
    # Sections
    for section in data["sections"]:
        lines.append(strip_html(section["heading"]))
        lines.append("")
        lines.append(strip_html(section["body"]))
        lines.append("")
    
    # Bottom line
    lines.append("The Bottom Line.")
    lines.append(strip_html(data["bottomLine"]))
    lines.append("")
    lines.append(f"Read the full analysis at {url}")
    
    return "\n".join(lines)

# Process each brief
for folder, config in BRIEF_CONFIG.items():
    json_path = os.path.join(BASE, folder, f"{DATE}.json")
    if not os.path.exists(json_path):
        print(f"SKIP: {json_path} not found")
        continue
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    script = build_script(data, config)
    
    txt_path = f"/tmp/brief-text-{config['prefix']}-{DATE}.txt"
    with open(txt_path, 'w') as f:
        f.write(script)
    
    print(f"Written: {txt_path} ({len(script)} chars)")