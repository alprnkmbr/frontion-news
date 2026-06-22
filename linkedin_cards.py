#!/usr/bin/env python3
"""
linkedin_cards.py — Generate LinkedIn card images for daily brief.

Usage:
  python3 linkedin_cards.py <date>            # Generate all cards for a brief
  python3 linkedin_cards.py bluf <date>        # Generate BLUF card only
  python3 linkedin_cards.py section <date> <n>   # Generate section n card only
  python3 linkedin_cards.py bottomline <date>    # Generate Bottom Line card only

Cards are saved to /Users/claudius/clawd/frontion-site/linkedin-cards/ as PNGs.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SITE_DIR = Path(__file__).parent
BRIEFS_DIR = SITE_DIR / "briefs"
CARDS_DIR = SITE_DIR / "linkedin-cards"

WIDTH = 1080
MARGIN_X = 50
MAX_TEXT_WIDTH = 980

# Colors
BG_COLOR = "#ffffff"
ACCENT_COLOR = "#b33a3a"
TEXT_COLOR = "#111111"
SUBTEXT_COLOR = "#333333"
MUTED_COLOR = "#555555"
DATE_COLOR = "#888888"
PAGE_COLOR = "#999999"

# Fonts
SERIF_FONTS = [
    "/Library/Fonts/Georgia.ttf",
    "/System/Library/Fonts/Georgia.ttf",
    "/System/Library/Fonts/Supplemental/Georgia.ttf",
]


def find_font(size):
    for fp in SERIF_FONTS:
        if Path(fp).exists():
            return ImageFont.truetype(fp, size)
    return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)


# Font sizes
BRAND_FONT = find_font(42)
HEADLINE_FONT = find_font(60)
HEADING_FONT = find_font(36)
BODY_FONT = find_font(34)
SMALL_FONT = find_font(26)
PAGE_FONT = find_font(22)


def load_brief(date_str):
    brief_path = BRIEFS_DIR / f"{date_str}.json"
    if not brief_path.exists():
        print(f"Error: Brief not found for {date_str}")
        sys.exit(1)
    with open(brief_path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_date_display(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%B %d, %Y")


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    line = ""
    for word in words:
        test_line = line + " " + word if line else word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] > max_width:
            if line:
                lines.append(line)
            line = word
        else:
            line = test_line
    if line:
        lines.append(line)
    return lines


def draw_justified(draw, lines, x, y, font, fill, max_width, line_height):
    for i, line in enumerate(lines):
        if i == len(lines) - 1:
            draw.text((x, y), line, fill=fill, font=font)
        else:
            words = line.split()
            if len(words) <= 1:
                draw.text((x, y), line, fill=fill, font=font)
            else:
                total_word_width = sum(
                    draw.textbbox((0, 0), w, font=font)[2]
                    - draw.textbbox((0, 0), w, font=font)[0]
                    for w in words
                )
                total_spaces = max_width - total_word_width
                space_width = total_spaces / (len(words) - 1)
                cx = x
                for word in words:
                    draw.text((cx, y), word, fill=fill, font=font)
                    word_w = (
                        draw.textbbox((0, 0), word, font=font)[2]
                        - draw.textbbox((0, 0), word, font=font)[0]
                    )
                    cx += word_w + space_width
        y += line_height
    return y


def draw_header(draw, date_display):
    """Draw the common header (brand + date)."""
    draw.rectangle([0, 0, WIDTH, 8], fill=ACCENT_COLOR)
    draw.text((MARGIN_X, 40), "FRONTION NEWS", fill=TEXT_COLOR, font=BRAND_FONT)
    draw.text((MARGIN_X, 92), "Strategic Brief", fill=ACCENT_COLOR, font=BRAND_FONT)
    draw.text((MARGIN_X, 150), date_display, fill=DATE_COLOR, font=SMALL_FONT)
    draw.rectangle([MARGIN_X, 195, 340, 197], fill=ACCENT_COLOR)


def draw_page_number(draw, page_num, total_pages, height):
    """Draw page number in top-right corner."""
    text = f"{page_num}/{total_pages}"
    bbox = draw.textbbox((0, 0), text, font=PAGE_FONT)
    tw = bbox[2] - bbox[0]
    draw.text((WIDTH - tw - 50, 35), text, fill=PAGE_COLOR, font=PAGE_FONT)


def draw_footer(draw, height):
    """Draw bottom red bar."""
    draw.rectangle([0, height - 8, WIDTH, height], fill=ACCENT_COLOR)


def generate_bluf_card(brief, date_str, page_num, total_pages):
    """Generate BLUF card image."""
    title = brief.get("title", "")
    subhead = brief.get("subhead", "")
    date_display = format_date_display(date_str)

    # Calculate height
    tmp_img = Image.new("RGB", (WIDTH, 100), BG_COLOR)
    tmp_draw = ImageDraw.Draw(tmp_img)
    title_lines = wrap_text(tmp_draw, title, HEADLINE_FONT, MAX_TEXT_WIDTH)
    subhead_lines = wrap_text(tmp_draw, subhead, BODY_FONT, MAX_TEXT_WIDTH)

    total_h = 8 + 200 + 15 + len(title_lines) * 68 + 30 + len(subhead_lines) * 42 + 40
    total_h = max(total_h, 900)

    img = Image.new("RGB", (WIDTH, total_h), color=BG_COLOR)
    draw = ImageDraw.Draw(img)

    draw_header(draw, date_display)
    draw_page_number(draw, page_num, total_pages, total_h)

    y = 225
    title_wrapped = wrap_text(draw, title, HEADLINE_FONT, MAX_TEXT_WIDTH)
    for line in title_wrapped:
        draw.text((MARGIN_X, y), line, fill=TEXT_COLOR, font=HEADLINE_FONT)
        y += 68

    y += 20
    subhead_wrapped = wrap_text(draw, subhead, BODY_FONT, MAX_TEXT_WIDTH)
    y = draw_justified(draw, subhead_wrapped, MARGIN_X, y, BODY_FONT, SUBTEXT_COLOR, MAX_TEXT_WIDTH, 42)

    y += 40
    draw_footer(draw, total_h)

    CARDS_DIR.mkdir(exist_ok=True)
    path = CARDS_DIR / f"bluf-{date_str}.png"
    img.save(path, "PNG")
    print(f"BLUF card saved: {path}")
    return path


def generate_section_card(brief, date_str, section_num, page_num, total_pages):
    """Generate a section card image."""
    sections = brief.get("sections", [])
    if section_num < 1 or section_num > len(sections):
        print(f"Error: Section {section_num} not found")
        sys.exit(1)

    section = sections[section_num - 1]
    heading = section.get("heading", "")
    body = re.sub(r"<[^>]+>", "", section.get("body", "")).strip()
    why = section.get("whyItMatters", "")
    date_display = format_date_display(date_str)

    # Calculate height
    tmp_img = Image.new("RGB", (WIDTH, 100), BG_COLOR)
    tmp_draw = ImageDraw.Draw(tmp_img)
    head_lines = wrap_text(tmp_draw, heading, HEADING_FONT, MAX_TEXT_WIDTH)
    body_lines = wrap_text(tmp_draw, body, BODY_FONT, MAX_TEXT_WIDTH)
    why_lines = wrap_text(tmp_draw, why, BODY_FONT, MAX_TEXT_WIDTH) if why else []

    total_h = 8 + 200 + 15 + len(head_lines) * 44 + 20 + len(body_lines) * 42 + 25
    if why:
        total_h += 15 + 50 + len(why_lines) * 42
    total_h += 60
    total_h = max(total_h, 800)

    img = Image.new("RGB", (WIDTH, total_h), color=BG_COLOR)
    draw = ImageDraw.Draw(img)

    draw_header(draw, date_display)
    draw_page_number(draw, page_num, total_pages, total_h)

    y = 225
    head_wrapped = wrap_text(draw, heading, HEADING_FONT, MAX_TEXT_WIDTH)
    for line in head_wrapped:
        draw.text((MARGIN_X, y), line, fill=TEXT_COLOR, font=HEADING_FONT)
        y += 44
    y += 15

    body_wrapped = wrap_text(draw, body, BODY_FONT, MAX_TEXT_WIDTH)
    y = draw_justified(draw, body_wrapped, MARGIN_X, y, BODY_FONT, SUBTEXT_COLOR, MAX_TEXT_WIDTH, 42)

    if why:
        y += 25
        draw.rectangle([MARGIN_X, y, 280, y + 2], fill=ACCENT_COLOR)
        y += 15
        draw.text((MARGIN_X, y), "Why it matters:", fill=ACCENT_COLOR, font=HEADING_FONT)
        y += 50
        why_wrapped = wrap_text(draw, why, BODY_FONT, MAX_TEXT_WIDTH)
        y = draw_justified(draw, why_wrapped, MARGIN_X, y, BODY_FONT, MUTED_COLOR, MAX_TEXT_WIDTH, 42)

    y += 40
    draw_footer(draw, total_h)

    CARDS_DIR.mkdir(exist_ok=True)
    path = CARDS_DIR / f"section-{section_num}-{date_str}.png"
    img.save(path, "PNG")
    print(f"Section {section_num} card saved: {path}")
    return path


def generate_bottomline_card(brief, date_str, page_num, total_pages):
    """Generate Bottom Line card image."""
    bottom_line = brief.get("bottomLine", "")
    date_display = format_date_display(date_str)

    # Calculate height
    tmp_img = Image.new("RGB", (WIDTH, 100), BG_COLOR)
    tmp_draw = ImageDraw.Draw(tmp_img)
    bl_lines = wrap_text(tmp_draw, bottom_line, BODY_FONT, MAX_TEXT_WIDTH)

    total_h = 8 + 200 + 15 + 70 + 30 + len(bl_lines) * 42 + 60
    total_h = max(total_h, 800)

    img = Image.new("RGB", (WIDTH, total_h), color=BG_COLOR)
    draw = ImageDraw.Draw(img)

    draw_header(draw, date_display)
    draw_page_number(draw, page_num, total_pages, total_h)

    y = 225
    draw.text((MARGIN_X, y), "The Bottom Line", fill=TEXT_COLOR, font=HEADLINE_FONT)
    y += 75

    bl_wrapped = wrap_text(draw, bottom_line, BODY_FONT, MAX_TEXT_WIDTH)
    y = draw_justified(draw, bl_wrapped, MARGIN_X, y, BODY_FONT, SUBTEXT_COLOR, MAX_TEXT_WIDTH, 42)

    y += 40
    draw_footer(draw, total_h)

    CARDS_DIR.mkdir(exist_ok=True)
    path = CARDS_DIR / f"bottomline-{date_str}.png"
    img.save(path, "PNG")
    print(f"Bottom Line card saved: {path}")
    return path


def generate_all_cards(date_str):
    """Generate all cards for a brief."""
    brief = load_brief(date_str)
    sections = brief.get("sections", [])
    total_pages = 1 + len(sections) + 1  # BLUF + sections + Bottom Line

    CARDS_DIR.mkdir(exist_ok=True)

    generate_bluf_card(brief, date_str, 1, total_pages)
    for i in range(1, len(sections) + 1):
        generate_section_card(brief, date_str, i, i + 1, total_pages)
    generate_bottomline_card(brief, date_str, total_pages, total_pages)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 linkedin_cards.py <date> [bluf|section|bottomline] [section_num]")
        print("  python3 linkedin_cards.py 2026-06-22          # Generate all cards")
        print("  python3 linkedin_cards.py 2026-06-22 bluf      # BLUF card only")
        print("  python3 linkedin_cards.py 2026-06-22 section 1  # Section 1 card only")
        print("  python3 linkedin_cards.py 2026-06-22 bottomline # Bottom Line card only")
        sys.exit(1)

    date_str = sys.argv[1]

    if len(sys.argv) == 2:
        # Generate all
        generate_all_cards(date_str)
    else:
        command = sys.argv[2]
        if command == "bluf":
            brief = load_brief(date_str)
            sections = brief.get("sections", [])
            total_pages = 1 + len(sections) + 1
            generate_bluf_card(brief, date_str, 1, total_pages)
        elif command == "section":
            section_num = int(sys.argv[3])
            brief = load_brief(date_str)
            sections = brief.get("sections", [])
            total_pages = 1 + len(sections) + 1
            generate_section_card(brief, date_str, section_num, section_num + 1, total_pages)
        elif command == "bottomline":
            brief = load_brief(date_str)
            sections = brief.get("sections", [])
            total_pages = 1 + len(sections) + 1
            generate_bottomline_card(brief, date_str, total_pages, total_pages)
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)