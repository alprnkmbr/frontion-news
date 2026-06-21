#!/usr/bin/env python3
"""
linkedin_card.py — Generate LinkedIn BLUF card image for daily brief.
Outputs: linkedin-card.png (overwritten each day)
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SITE_DIR = Path(__file__).parent
BRIEFS_DIR = SITE_DIR / "briefs"
CARD_PATH = SITE_DIR / "linkedin-card.png"

WIDTH, HEIGHT = 1200, 675
BG_COLOR = "#ffffff"
ACCENT_COLOR = "#b33a3a"
TEXT_COLOR = "#111111"
DATE_COLOR = "#666666"

# Serif font paths (Georgia preferred)
SERIF_FONTS = [
    "/Library/Fonts/Georgia.ttf",
    "/System/Library/Fonts/Georgia.ttf",
    "/System/Library/Fonts/Supplemental/Georgia.ttf",
    "/System/Library/Fonts/Times.ttc",
]


def find_font(size):
    for fp in SERIF_FONTS:
        if Path(fp).exists():
            return ImageFont.truetype(fp, size)
    # Fallback
    return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)


def generate_card(date_str=None, title=None):
    """Generate a LinkedIn card image.
    
    Args:
        date_str: Date string like "2026-06-21" or "June 21, 2026"
        title: Brief title (currently not used on card, kept for future)
    """
    if date_str and "-" in date_str:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        date_display = dt.strftime("%B %d, %Y")
    elif date_str:
        date_display = date_str
    else:
        date_display = datetime.now().strftime("%B %d, %Y")

    img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Top and bottom red accent lines
    draw.rectangle([0, 0, WIDTH, 5], fill=ACCENT_COLOR)
    draw.rectangle([0, HEIGHT - 5, WIDTH, HEIGHT], fill=ACCENT_COLOR)

    # Fonts
    title_font = find_font(100)
    subtitle_font = find_font(80)
    date_font = find_font(34)

    # Title
    draw.text((70, 140), "Frontion News", fill=TEXT_COLOR, font=title_font)
    draw.text((70, 260), "Strategic Brief", fill=ACCENT_COLOR, font=subtitle_font)

    # Date
    draw.text((70, 390), date_display, fill=DATE_COLOR, font=date_font)

    img.save(CARD_PATH, "PNG")
    print(f"Card saved to {CARD_PATH}")
    return CARD_PATH


if __name__ == "__main__":
    date_str = sys.argv[1] if len(sys.argv) > 1 else None
    generate_card(date_str=date_str)