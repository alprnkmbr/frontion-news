#!/usr/bin/env python3
"""Generate podcast episodes for 2026-07-16 from brief JSON files."""

import json
import re
import html
import subprocess
import os
import sys
from pathlib import Path
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK, APIC

DATE = "2026-07-16"
DATE_NICE = "July 16, 2026"
YEAR = "2026"

SECTIONS = [
    {
        "prefix": "global",
        "json_path": f"briefs/{DATE}.json",
        "brief_type": "Strategic Brief",
        "website_url": "https://frontion.news",
        "track_num": 1,
    },
    {
        "prefix": "defence",
        "json_path": f"defense/{DATE}.json",
        "brief_type": "Defence & Industry Brief",
        "website_url": "https://frontion.news/defence",
        "track_num": 2,
    },
    {
        "prefix": "energy",
        "json_path": f"energy/{DATE}.json",
        "brief_type": "Energy & Power Brief",
        "website_url": "https://frontion.news/energy",
        "track_num": 3,
    },
    {
        "prefix": "finance",
        "json_path": f"finance/{DATE}.json",
        "brief_type": "Finance & Markets Brief",
        "website_url": "https://frontion.news/finance",
        "track_num": 4,
    },
    {
        "prefix": "tech",
        "json_path": f"tech/{DATE}.json",
        "brief_type": "Tech Brief",
        "website_url": "https://frontion.news/tech",
        "track_num": 5,
    },
]


def strip_html(text):
    """Remove all HTML tags, replace <p> with newlines, decode entities."""
    if not text:
        return ""
    # Replace <p> tags with newlines
    text = re.sub(r'<p\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
    # Remove all remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    text = html.unescape(text)
    # Clean up excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    return text


def build_script(data, brief_type, date_nice, website_url):
    """Build TTS script from JSON data."""
    lines = []
    
    # Intro
    lines.append(f"Welcome to Frontion News' {brief_type} for {date_nice}.")
    lines.append("")
    
    # Title and subhead
    title = strip_html(data["title"])
    subhead = strip_html(data["subhead"])
    lines.append(title)
    lines.append(subhead)
    lines.append("")
    
    # Sections
    for section in data["sections"]:
        heading = strip_html(section["heading"])
        body = strip_html(section["body"])
        lines.append(heading)
        lines.append(body)
        lines.append("")
    
    # Bottom line
    bottom_line = strip_html(data["bottomLine"])
    lines.append("The Bottom Line.")
    lines.append(bottom_line)
    
    return "\n".join(lines)


def main():
    os.chdir("/Users/claudius/clawd/frontion-site")
    
    episodes = []
    
    for section in SECTIONS:
        prefix = section["prefix"]
        json_path = section["json_path"]
        brief_type = section["brief_type"]
        website_url = section["website_url"]
        track_num = section["track_num"]
        
        print(f"\n=== Processing {brief_type} ===")
        
        # Load JSON
        with open(json_path, "r") as f:
            data = json.load(f)
        
        # Build script
        script = build_script(data, brief_type, DATE_NICE, website_url)
        
        # Save script text
        txt_path = f"/tmp/brief-text-{prefix}-{DATE}.txt"
        with open(txt_path, "w") as f:
            f.write(script)
        print(f"Script saved to {txt_path} ({len(script)} chars)")
        
        # Generate TTS
        mp3_path = f"podcast/frontion-{prefix}-{DATE}.mp3"
        cmd = [
            "python3", "-m", "edge_tts",
            "-f", txt_path,
            "-v", "en-GB-RyanNeural",
            "--rate=-10%",
            "--write-media", mp3_path
        ]
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"TTS ERROR for {prefix}: {result.stderr}")
            sys.exit(1)
        print(f"MP3 saved to {mp3_path}")
        
        # Add ID3 tags
        title_clean = strip_html(data["title"])
        episode_title = f"{brief_type} — {DATE_NICE}: {title_clean}"
        
        mp3 = MP3(mp3_path)
        # Remove existing tags
        try:
            mp3.delete()
        except:
            pass
        mp3 = MP3(mp3_path)
        
        # Add tags
        mp3["TIT2"] = TIT2(encoding=3, text=[episode_title])
        mp3["TPE1"] = TPE1(encoding=3, text=["Frontion News"])
        mp3["TALB"] = TALB(encoding=3, text=["Frontion News"])
        mp3["TDRC"] = TDRC(encoding=3, text=[DATE])
        mp3["TRCK"] = TRCK(encoding=3, text=[str(track_num)])
        
        # Add cover art
        with open("podcast/podcast-cover-3000.jpg", "rb") as img_f:
            cover_data = img_f.read()
        mp3["APIC"] = APIC(
            encoding=3,
            mime="image/jpeg",
            type=3,  # Front cover
            desc="Cover",
            data=cover_data
        )
        
        mp3.save()
        print(f"ID3 tags added: {episode_title}")
        
        # Get duration
        mp3 = MP3(mp3_path)
        duration_secs = int(mp3.info.length)
        mins = duration_secs // 60
        secs = duration_secs % 60
        duration_str = f"{mins}:{secs:02d}"
        file_size = os.path.getsize(mp3_path)
        
        print(f"Duration: {duration_str}, Size: {file_size}")
        
        # Build description (HTML-stripped subhead + bottom line summary + link)
        desc = strip_html(data["subhead"])
        desc += f"\n\nRead the full analysis at {website_url}"
        
        episodes.append({
            "prefix": prefix,
            "brief_type": brief_type,
            "title": episode_title,
            "description": desc,
            "mp3_path": mp3_path,
            "duration": duration_str,
            "file_size": file_size,
            "website_url": website_url,
            "track_num": track_num,
        })
    
    print("\n\n=== All episodes generated ===")
    for ep in episodes:
        print(f"  {ep['title']}")
        print(f"    Duration: {ep['duration']}, Size: {ep['file_size']}")
    
    # Now update RSS and HTML
    # Read existing RSS
    with open("podcast/frontion-podcast.rss", "r") as f:
        rss_content = f.read()
    
    # Build new item entries (prepend before existing items)
    new_items = ""
    for ep in episodes:
        new_items += f"""
    <item>
        <title>{ep['title']}</title>
        <link>{ep['website_url']}</link>
        <description>{ep['description']}</description>
        <enclosure url="https://frontion.news/podcast/frontion-{ep['prefix']}-{DATE}.mp3" length="{ep['file_size']}" type="audio/mpeg" />
        <guid isPermaLink="false">frontion-{ep['prefix']}-{DATE}</guid>
        <pubDate>Wed, 16 Jul 2026 07:30:00 +0300</pubDate>
        <itunes:duration>{ep['duration']}</itunes:duration>
        <itunes:explicit>false</itunes:explicit>
    </item>
"""
    
    # Remove any existing episodes for today's date to prevent duplicates
    # Match items that contain frontion-{prefix}-{DATE} in guid
    for prefix in ["global", "defence", "energy", "finance", "tech"]:
        pattern = rf'\s*<item>.*?frontion-{prefix}-{DATE}.*?</item>'
        rss_content = re.sub(pattern, '', rss_content, flags=re.DOTALL)
    
    # Insert new items after the atom:link line
    atom_link_pattern = r'(<atom:link[^>]* />\s*\n)'
    match = re.search(atom_link_pattern, rss_content)
    if match:
        insert_pos = match.end()
        rss_content = rss_content[:insert_pos] + new_items + rss_content[insert_pos:]
    
    with open("podcast/frontion-podcast.rss", "w") as f:
        f.write(rss_content)
    print("RSS updated")
    
    # Update index.html
    # Build new episode HTML entries
    new_html_items = ""
    for ep in episodes:
        # Format date nicely for HTML
        date_label = "July 16, 2026"
        brief_label = ep['brief_type']
        # Extract just the headline (after date prefix)
        headline = ep['title'].split(": ", 1)[1] if ": " in ep['title'] else ep['title']
        desc_text = ep['description'].split("\n\nRead the full")[0]
        
        new_html_items += f"""
        <li class="episode">
            <div class="episode-meta">{date_label} — {brief_label}</div>
            <div class="episode-title">{headline}</div>
            <div class="episode-desc">{desc_text}</div>
            <audio controls preload="none"><source src="frontion-{ep['prefix']}-{DATE}.mp3" type="audio/mpeg">Your browser does not support audio.</audio>
        </li>"""
    
    with open("podcast/index.html", "r") as f:
        html_content = f.read()
    
    # Remove any existing entries for today's date
    html_content = re.sub(
        rf'\s*<li class="episode">\s*<div class="episode-meta">July 16, 2026.*?</li>',
        '', html_content, flags=re.DOTALL
    )
    
    # Insert new episodes after the <ul class="episodes"> tag
    html_content = html_content.replace(
        '<ul class="episodes">',
        '<ul class="episodes">' + new_html_items
    )
    
    with open("podcast/index.html", "w") as f:
        f.write(html_content)
    print("HTML updated")
    
    print("\nDone! All podcast episodes generated and files updated.")


if __name__ == "__main__":
    main()