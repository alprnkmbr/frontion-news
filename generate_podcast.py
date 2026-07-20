#!/usr/bin/env python3
"""Generate podcast episodes for 2026-07-20 briefs."""

import json
import re
import html
import subprocess
import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK, APIC
from datetime import datetime

DATE = "2026-07-20"
DATE_NICE = "July 20, 2026"
YEAR = "2026"

# Section config: (json_dir, prefix, brief_label, website_url, track_num)
SECTIONS = [
    ("briefs",   "global",   "Strategic Brief",          "https://frontion.news",            1),
]

def strip_html(text):
    """Remove all HTML tags, replace <p> with newlines, decode entities."""
    if not text:
        return ""
    # Replace <p> and </p> with newlines
    text = re.sub(r'<\/?p>', '\n', text)
    # Remove all other HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    text = html.unescape(text)
    # Clean up multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def build_script(data, brief_label, date_nice):
    """Build TTS script from JSON data."""
    lines = []
    lines.append(f"Welcome to Frontion News' {brief_label} for {date_nice}.")
    lines.append("")
    
    # Title
    title = strip_html(data.get("title", ""))
    lines.append(title)
    lines.append("")
    
    # Subhead
    subhead = strip_html(data.get("subhead", ""))
    if subhead:
        lines.append(subhead)
        lines.append("")
    
    # Sections
    for section in data.get("sections", []):
        heading = strip_html(section.get("heading", ""))
        body = strip_html(section.get("body", ""))
        if heading:
            lines.append(heading)
            lines.append("")
        if body:
            lines.append(body)
            lines.append("")
    
    # Bottom line
    bottom_line = strip_html(data.get("bottomLine", ""))
    if bottom_line:
        lines.append("The Bottom Line.")
        lines.append(bottom_line)
    
    return "\n".join(lines)

def build_description(data, url):
    """Build episode description for RSS."""
    desc = strip_html(data.get("subhead", ""))
    desc += f"\n\nRead the full analysis at {url}"
    return desc

def build_headline(data):
    """Extract headline from title (first clause before comma)."""
    title = strip_html(data.get("title", ""))
    # Take the full title as headline for RSS
    return title

# Step 1-2: Process each section
podcast_dir = "/Users/claudius/clawd/frontion-site/podcast"
os.makedirs(podcast_dir, exist_ok=True)

episodes = []  # Will store episode info for RSS/HTML updates

for json_dir, prefix, brief_label, website_url, track_num in SECTIONS:
    json_path = f"/Users/claudius/clawd/frontion-site/{json_dir}/{DATE}.json"
    
    print(f"\n=== Processing {brief_label} ===")
    
    # Read JSON
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Build script
    script = build_script(data, brief_label, DATE_NICE)
    
    # Save script to /tmp
    script_path = f"/tmp/brief-text-{prefix}-{DATE}.txt"
    with open(script_path, 'w') as f:
        f.write(script)
    print(f"Script saved to {script_path}")
    
    # Generate TTS
    mp3_path = f"{podcast_dir}/frontion-{prefix}-{DATE}.mp3"
    cmd = [
        "python3", "-m", "edge_tts",
        "-f", script_path,
        "-v", "en-GB-RyanNeural",
        "--rate=-10%",
        "--write-media", mp3_path
    ]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"TTS ERROR: {result.stderr}")
        raise Exception(f"TTS failed for {prefix}")
    print(f"MP3 saved to {mp3_path}")
    
    # Get headline for title
    headline = build_headline(data)
    
    # Build title for RSS
    rss_title = f"{brief_label} — {DATE_NICE}: {headline}"
    
    # Build description
    description = build_description(data, website_url)
    
    # Add ID3 tags
    mp3_file = MP3(mp3_path)
    
    # Clear existing tags and add new ones
    mp3_file.delete()
    mp3_file.save()
    
    mp3_file = MP3(mp3_path)
    mp3_file.add_tags()
    
    mp3_file.tags.add(TIT2(encoding=3, text=[rss_title]))
    mp3_file.tags.add(TPE1(encoding=3, text=["Frontion News"]))
    mp3_file.tags.add(TALB(encoding=3, text=["Frontion News"]))
    mp3_file.tags.add(TDRC(encoding=3, text=[DATE]))
    mp3_file.tags.add(TRCK(encoding=3, text=[str(track_num)]))
    
    # Add cover art
    cover_path = f"{podcast_dir}/podcast-cover-3000.jpg"
    with open(cover_path, 'rb') as img:
        mp3_file.tags.add(APIC(
            encoding=3,
            mime='image/jpeg',
            type=3,  # Front cover
            desc='Cover',
            data=img.read()
        ))
    
    mp3_file.save()
    
    # Get duration
    duration_seconds = int(mp3_file.info.length)
    minutes = duration_seconds // 60
    seconds = duration_seconds % 60
    duration_str = f"{minutes}:{seconds:02d}"
    
    # Get file size
    file_size = os.path.getsize(mp3_path)
    
    print(f"Duration: {duration_str}, Size: {file_size}")
    
    episodes.append({
        "prefix": prefix,
        "brief_label": brief_label,
        "rss_title": rss_title,
        "description": description,
        "website_url": website_url,
        "mp3_filename": f"frontion-{prefix}-{DATE}.mp3",
        "duration_str": duration_str,
        "file_size": file_size,
        "track_num": track_num,
        "date_nice": DATE_NICE,
    })

# Step 4-6: Update RSS and HTML
# Read existing RSS
with open(f"{podcast_dir}/frontion-podcast.rss", 'r') as f:
    rss_content = f.read()

# Build new RSS items (prepend new episodes)
new_items = ""
for ep in episodes:
    # Escape XML special chars in description
    desc_escaped = ep["description"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    rss_title_escaped = ep["rss_title"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    
    # Date formatting: "July 20, 2026" -> "Sun, 20 Jul 2026 07:30:00 +0300"
    # July 20, 2026 is a Sunday
    pub_date = "Sun, 20 Jul 2026 07:30:00 +0300"
    
    new_items += f"""    <item>
        <title>{rss_title_escaped}</title>
        <link>{ep["website_url"]}</link>
        <description>{desc_escaped}</description>
        <enclosure url="https://frontion.news/podcast/{ep["mp3_filename"]}" length="{ep["file_size"]}" type="audio/mpeg" />
        <guid isPermaLink="false">frontion-{ep["prefix"]}-{DATE}</guid>
        <pubDate>{pub_date}</pubDate>
        <itunes:duration>{ep["duration_str"]}</itunes:duration>
        <itunes:explicit>false</itunes:explicit>
    </item>
"""

# Remove any existing items for today's date to prevent duplicates
# Pattern: items containing "frontion-{prefix}-{DATE}" in guid
for json_dir, prefix, brief_label, website_url, track_num in SECTIONS:
    pattern = f'frontion-{prefix}-{DATE}'
    # Find and remove the entire <item> block containing this guid
    while f'<guid isPermaLink="false">{pattern}</guid>' in rss_content:
        item_start = rss_content.find(f'<item>', rss_content.find(f'<guid isPermaLink="false">{pattern}</guid>') - 500)
        # Actually, let's use regex to remove the item
        break

# Use regex to remove items for today's date
import re as regex_mod
for json_dir, prefix, brief_label, website_url, track_num in SECTIONS:
    guid_pattern = f'frontion-{prefix}-{DATE}'
    # Remove the item block containing this guid
    rss_content = regex_mod.sub(
        rf'\s*<item>\s*.*?<guid isPermaLink="false">{regex_mod.escape(guid_pattern)}</guid>.*?</item>',
        '', rss_content, flags=regex_mod.DOTALL
    )

# Insert new items after <atom:link .../>
insert_marker = '<atom:link href="https://frontion.news/podcast/frontion-podcast.rss" rel="self" type="application/rss+xml" />'
rss_content = rss_content.replace(insert_marker, insert_marker + '\n' + new_items)

# Write updated RSS
with open(f"{podcast_dir}/frontion-podcast.rss", 'w') as f:
    f.write(rss_content)
print("\nRSS updated!")

# Step 4b: Update index.html
with open(f"{podcast_dir}/index.html", 'r') as f:
    html_content = f.read()

# Build new HTML episode entries
new_html_entries = ""
for ep in episodes:
    desc_html = ep["description"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n\nRead the full analysis at ", '<br><br>Read the full analysis at <a href="' + ep["website_url"] + '">' + ep["website_url"] + '</a>')
    # Keep the description text as-is for HTML, just linkify the URL
    desc_text = ep["description"]
    url = ep["website_url"]
    # Split off the "Read the full analysis at URL" part
    main_desc = desc_text.split("\n\nRead the full analysis at")[0].strip()
    desc_html_version = f'{main_desc} Read the full analysis at <a href="{url}">{url}</a>'
    
    # Format date label
    date_label = f"July 20, 2026 — {ep['brief_label']}"
    
    new_html_entries += f"""        <li class="episode">
            <div class="episode-meta">{date_label}</div>
            <div class="episode-title">{ep['rss_title'].split(': ', 1)[1] if ': ' in ep['rss_title'] else ep['rss_title']}</div>
            <div class="episode-desc">{desc_html_version}</div>
            <audio controls preload="none"><source src="{ep['mp3_filename']}" type="audio/mpeg">Your browser does not support audio.</audio>
        </li>
"""

# Remove any existing episodes for today's date
for json_dir, prefix, brief_label, website_url, track_num in SECTIONS:
    mp3_filename = f"frontion-{prefix}-{DATE}.mp3"
    # Remove the li block containing this mp3 filename
    html_content = regex_mod.sub(
        rf'\s*<li class="episode">\s*.*?{regex_mod.escape(mp3_filename)}.*?</li>',
        '', html_content, flags=regex_mod.DOTALL
    )

# Insert new episodes after <ul class="episodes">
insert_marker_html = '<ul class="episodes">'
html_content = html_content.replace(insert_marker_html, insert_marker_html + '\n' + new_html_entries)

# Write updated HTML
with open(f"{podcast_dir}/index.html", 'w') as f:
    f.write(html_content)
print("HTML updated!")

print("\n=== All episodes generated successfully! ===")
for ep in episodes:
    print(f"  {ep['brief_label']}: {ep['duration_str']} ({ep['file_size']} bytes)")