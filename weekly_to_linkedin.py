#!/usr/bin/env python3
"""
Convert a weekly brief JSON into a LinkedIn Newsletter-ready plain-text file.

LinkedIn's newsletter editor does not accept HTML or PDF — it takes plain text
pasted into its "Write here" body field, with the title/subtitle typed into
separate fields. This script produces exactly that: a single .txt with TITLE,
SUBTITLE and the body, ready to copy-paste.

Usage:
    python3 weekly_to_linkedin.py YYYY-MM-DD
    python3 weekly_to_linkedin.py            # uses latest from index.json
"""

import html
import json
import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEEKLY_DIR = os.path.join(BASE_DIR, 'weekly')


def load_weekly_data(date_str=None):
    if date_str is None:
        with open(os.path.join(WEEKLY_DIR, 'index.json')) as f:
            date_str = json.load(f)[0]['date']
    with open(os.path.join(WEEKLY_DIR, f'{date_str}.json')) as f:
        return json.load(f)


def plain(text):
    """Strip HTML, keep readable plain text (no markdown markers)."""
    if not text:
        return ''
    t = text
    t = re.sub(r'<\s*br\s*/?\s*>', '\n', t, flags=re.I)
    t = re.sub(r'<\s*/p\s*>\s*<\s*p[^>]*>', '\n\n', t, flags=re.I)
    t = re.sub(r'<\s*/?p[^>]*>', '', t, flags=re.I)
    t = re.sub(r'<\s*strong[^>]*>(.*?)<\s*/\s*strong\s*>', r'\1', t, flags=re.I | re.S)
    t = re.sub(r'<\s*b[^>]*>(.*?)<\s*/\s*b\s*>', r'\1', t, flags=re.I | re.S)
    t = re.sub(r'<\s*em[^>]*>(.*?)<\s*/\s*em\s*>', r'\1', t, flags=re.I | re.S)
    t = re.sub(r'<\s*i[^>]*>(.*?)<\s*/\s*i\s*>', r'\1', t, flags=re.I | re.S)
    t = re.sub(r'<[^>]+>', '', t)
    t = html.unescape(t)
    t = re.sub(r'[ \t]+', ' ', t)
    t = re.sub(r'\n\s*\n\s*\n+', '\n\n', t)
    return t.strip()


def short_title(title, limit=100):
    """LinkedIn newsletter title field is limited to 100 characters."""
    if len(title) <= limit:
        return title
    cut = title[:limit]
    if ':' in cut:
        part = cut.split(':')[0].strip()
        if 20 <= len(part) <= limit:
            return part
    return cut.rsplit(' ', 1)[0].strip()


def build_text(data):
    out = []
    out.append("TITLE:")
    out.append(short_title(data['title']))
    out.append("")
    out.append("SUBTITLE:")
    sub = data.get('subhead', '')
    # Use the first sentence of the subhead as a short subtitle
    first_sentence = re.split(r'(?<=[.!?])\s', plain(sub))[0] if sub else ''
    out.append(first_sentence)
    out.append("")
    out.append("=" * 60)
    out.append("")
    out.append("BODY (paste this into the LinkedIn editor):")
    out.append("")
    out.append(plain(sub))
    out.append("")

    for sec in data.get('sections', []):
        out.append(sec.get('heading', '').upper())
        out.append("")
        out.append(plain(sec.get('body', '')))
        out.append("")
        if sec.get('whyItMatters'):
            out.append("Why it matters — " + plain(sec['whyItMatters']))
            out.append("")
        out.append("-" * 40)
        out.append("")

    if data.get('bottomLine'):
        out.append("THE BOTTOM LINE")
        out.append("")
        out.append(plain(data['bottomLine']))
        out.append("")

    if data.get('sources'):
        out.append("Sources: " + plain(data['sources']))
        out.append("")

    out.append("Read the full analysis at https://frontion.news/weekly")
    out.append("Subscribe on LinkedIn: https://www.linkedin.com/build-relation/newsletter-follow?entityUrn=7510047689506713601")
    return '\n'.join(out)


def main():
    date_str = sys.argv[1] if len(sys.argv) > 1 else None
    data = load_weekly_data(date_str)
    txt = build_text(data)
    out_path = os.path.join(WEEKLY_DIR, f"linkedin-newsletter-{data['date']}.txt")
    with open(out_path, 'w') as f:
        f.write(txt)
    print(f"OK {out_path}")
    print(f"   title: {short_title(data['title'])}")
    print(f"   chars: {len(txt)}")


if __name__ == '__main__':
    main()
