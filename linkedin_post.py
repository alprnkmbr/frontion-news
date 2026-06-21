#!/usr/bin/env python3
"""
linkedin_post.py — Generate and send LinkedIn posts for daily brief.

Usage:
  python3 linkedin_post.py bluf <date>          # Send BLUF post (with image)
  python3 linkedin_post.py section <date> <n>    # Send section n (1-based)
  python3 linkedin_post.py bottomline <date>      # Send Bottom Line post

Environment:
  MAKE_WEBHOOK_URL — Make.com webhook URL
"""

import json
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

SITE_DIR = Path(__file__).parent
BRIEFS_DIR = SITE_DIR / "briefs"
CARD_PATH = SITE_DIR / "linkedin-card.png"
SITE_URL = "https://alprnkmbr.github.io/frontion-news"

WEBHOOK_URL = "https://hook.eu1.make.com/w1evieps3ym9ihfkx9qgrwc386saaeis"


def load_brief(date_str):
    """Load brief JSON for a given date."""
    brief_path = BRIEFS_DIR / f"{date_str}.json"
    if not brief_path.exists():
        print(f"Error: Brief not found for {date_str}")
        sys.exit(1)
    with open(brief_path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_date_display(date_str):
    """Format date like 'June 21, 2026'."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%B %d, %Y")


def send_post(text, image_url=None):
    """Send a post to Make.com webhook."""
    payload = {"body": text}
    if image_url:
        payload["image_url"] = image_url
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        print(f"Post sent: {resp.status}")


def send_bluf(date_str):
    """Send BLUF post with image."""
    brief = load_brief(date_str)
    date_display = format_date_display(date_str)
    
    # Generate card image
    import subprocess
    subprocess.run(
        ["python3", str(SITE_DIR / "linkedin_card.py"), date_str],
        check=True,
    )
    
    # Git push the card
    subprocess.run(["git", "add", "linkedin-card.png"], cwd=SITE_DIR, check=True)
    subprocess.run(["git", "commit", "-m", f"LinkedIn card for {date_str}"], cwd=SITE_DIR, check=True)
    subprocess.run(["git", "push"], cwd=SITE_DIR, check=True)
    
    # Wait a moment for GitHub Pages
    import time
    time.sleep(5)
    
    title = brief.get("title", "")
    subhead = brief.get("subhead", "")
    
    text = (
        f"◆ {title}\n\n"
        f"{subhead}"
    )
    
    image_url = f"{SITE_URL}/linkedin-card.png"
    send_post(text, image_url=image_url)


def send_section(date_str, section_num):
    """Send a section post (1-based)."""
    brief = load_brief(date_str)
    sections = brief.get("sections", [])
    
    if section_num < 1 or section_num > len(sections):
        print(f"Error: Section {section_num} not found (brief has {len(sections)} sections)")
        sys.exit(1)
    
    section = sections[section_num - 1]
    heading = section.get("heading", "")
    body = section.get("body", "")
    why = section.get("whyItMatters", "")
    
    # Strip HTML tags from body
    import re
    if body:
        body = re.sub(r"<[^>]+>", "", body).strip()
    
    text = f"► {heading}\n\n{body}"
    if why:
        text += f"\n\nWhy it matters: {why}"
    
    send_post(text)


def send_bottomline(date_str):
    """Send Bottom Line post."""
    brief = load_brief(date_str)
    bottom_line = brief.get("bottomLine", "")
    
    if not bottom_line:
        print("Error: No bottom line found")
        sys.exit(1)
    
    text = f"■ The Bottom Line\n\n{bottom_line}"
    send_post(text)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 linkedin_post.py <bluf|section|bottomline> <date> [section_num]")
        sys.exit(1)
    
    command = sys.argv[1]
    date_str = sys.argv[2]
    
    if command == "bluf":
        send_bluf(date_str)
    elif command == "section":
        if len(sys.argv) < 4:
            print("Usage: python3 linkedin_post.py section <date> <section_num>")
            sys.exit(1)
        send_section(date_str, int(sys.argv[3]))
    elif command == "bottomline":
        send_bottomline(date_str)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)