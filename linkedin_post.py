#!/usr/bin/env python3
"""
linkedin_post.py — Generate and send LinkedIn posts for daily brief.

Usage:
  python3 linkedin_post.py bluf <date>          # Send BLUF post (with image)
  python3 linkedin_post.py section <date> <n>    # Send section n (1-based)
  python3 linkedin_post.py bottomline <date>      # Send Bottom Line post

Each post generates a card image, pushes to GitHub, then sends both
text and image URL to the Make.com webhook.

Environment:
  MAKE_WEBHOOK_URL — Make.com webhook URL
"""

import json
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

SITE_DIR = Path(__file__).parent
BRIEFS_DIR = SITE_DIR / "briefs"
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


def generate_card_and_push(date_str, card_type, section_num=None):
    """Generate card image and push to GitHub. Returns the image URL."""
    # Generate card
    args = ["python3", str(SITE_DIR / "linkedin_cards.py"), card_type, date_str]
    if section_num is not None:
        args.append(str(section_num))
    subprocess.run(args, check=True)

    # Determine card filename
    cards_dir = SITE_DIR / "linkedin-cards"
    if card_type == "bluf":
        card_file = f"bluf-{date_str}.png"
    elif card_type == "section":
        card_file = f"section-{section_num}-{date_str}.png"
    elif card_type == "bottomline":
        card_file = f"bottomline-{date_str}.png"
    else:
        print(f"Unknown card type: {card_type}")
        sys.exit(1)

    card_path = cards_dir / card_file

    # Git add, commit, push
    subprocess.run(["git", "add", str(card_path)], cwd=SITE_DIR, check=True)
    subprocess.run(
        ["git", "commit", "-m", f"LinkedIn card: {card_type} {date_str}"],
        cwd=SITE_DIR,
        check=True,
    )
    subprocess.run(["git", "push"], cwd=SITE_DIR, check=True)

    # Wait for GitHub Pages to serve the file
    time.sleep(5)

    image_url = f"{SITE_URL}/linkedin-cards/{card_file}"
    return image_url


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

    # Generate and push card image
    image_url = generate_card_and_push(date_str, "bluf")

    title = brief.get("title", "")
    subhead = brief.get("subhead", "")

    text = f"◆ {title}\n\n{subhead}"

    send_post(text, image_url=image_url)


def send_section(date_str, section_num):
    """Send a section post with image (1-based)."""
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
    if body:
        body = re.sub(r"<[^>]+>", "", body).strip()

    text = f"► {heading}\n\n{body}"
    if why:
        text += f"\n\nWhy it matters: {why}"

    # Generate and push card image
    image_url = generate_card_and_push(date_str, "section", section_num)

    send_post(text, image_url=image_url)


def send_bottomline(date_str):
    """Send Bottom Line post with image."""
    brief = load_brief(date_str)
    bottom_line = brief.get("bottomLine", "")

    if not bottom_line:
        print("Error: No bottom line found")
        sys.exit(1)

    text = f"■ The Bottom Line\n\n{bottom_line}"

    # Generate and push card image
    image_url = generate_card_and_push(date_str, "bottomline")

    send_post(text, image_url=image_url)


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