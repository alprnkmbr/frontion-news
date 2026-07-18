#!/usr/bin/env python3
"""Generate podcast episodes for 2026-07-18 briefs."""
import json
import re
import html
import subprocess
import os
from pathlib import Path
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK, APIC

DATE = "2026-07-18"
DATE_FMT = "July 18, 2026"

# Section configs: (json_dir, prefix, brief_label, website_url)
BRIEFS = [
    ("briefs",  "global",   "Strategic Brief",            "https://frontion.news"),
    ("defense", "defence",  "Defence & Industry Brief",   "https://frontion.news/defence"),
    ("energy",  "energy",   "Energy & Power Brief",       "https://frontion.news/energy"),
    ("finance", "finance",  "Finance & Markets Brief",    "https://frontion.news/finance"),
    ("tech",    "tech",     "Tech Brief",                 "https://frontion.news/tech"),
]

WORKDIR = Path("/Users/claudius/clawd/frontion-site")

def strip_html(text):
    """Remove HTML tags, replace <p> with newlines, decode entities."""
    if not text:
        return ""
    # Replace <p> tags with newlines
    text = re.sub(r'<p\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '', text, flags=re.IGNORECASE)
    # Remove all remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    text = html.unescape(text)
    # Clean up whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()
    return text

def build_script(data, brief_label, date_fmt):
    """Build TTS script from JSON data."""
    lines = []
    lines.append(f"Welcome to Frontion News' {brief_label} for {date_fmt}.")
    lines.append("")
    lines.append(strip_html(data["title"]))
    lines.append("")
    lines.append(strip_html(data["subhead"]))
    lines.append("")
    
    for section in data["sections"]:
        lines.append(section["heading"])
        lines.append("")
        lines.append(strip_html(section["body"]))
        lines.append("")
    
    lines.append("The Bottom Line.")
    lines.append(strip_html(data["bottomLine"]))
    
    return "\n".join(lines)

def get_duration_str(seconds):
    """Format seconds as M:SS or H:MM:SS."""
    m, s = divmod(int(seconds), 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

# Track info for each brief
tracks = []

for json_dir, prefix, brief_label, website_url in BRIEFS:
    json_path = WORKDIR / json_dir / f"{DATE}.json"
    
    print(f"Processing {json_dir}/{DATE}.json ...")
    with open(json_path, "r") as f:
        data = json.load(f)
    
    # Build script
    script = build_script(data, brief_label, DATE_FMT)
    
    # Save script text
    txt_path = f"/tmp/brief-text-{prefix}-{DATE}.txt"
    with open(txt_path, "w") as f:
        f.write(script)
    print(f"  Script saved to {txt_path}")
    
    # Run TTS
    mp3_path = WORKDIR / "podcast" / f"frontion-{prefix}-{DATE}.mp3"
    cmd = [
        "python3", "-m", "edge_tts",
        "-f", txt_path,
        "-v", "en-GB-RyanNeural",
        "--rate=-10%",
        "--write-media", str(mp3_path)
    ]
    print(f"  Running TTS: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  TTS ERROR: {result.stderr}")
        raise RuntimeError(f"TTS failed for {prefix}: {result.stderr}")
    print(f"  MP3 saved to {mp3_path}")
    
    # Build episode title
    headline = strip_html(data["title"])
    episode_title = f"{brief_label} — {DATE_FMT}: {headline}"
    
    # Build description
    subhead = strip_html(data["subhead"])
    desc = f"{subhead}\n\nRead the full analysis at {website_url}"
    
    # Get track number
    track_num = BRIEFS.index((json_dir, prefix, brief_label, website_url)) + 1
    
    # Add ID3 tags
    audio = MP3(mp3_path)
    if audio.tags is None:
        audio.add_tags()
    tags = audio.tags
    
    tags.delall("TIT2")
    tags.delall("TPE1")
    tags.delall("TALB")
    tags.delall("TDRC")
    tags.delall("TRCK")
    tags.delall("APIC")
    
    tags.add(TIT2(encoding=3, text=[episode_title]))
    tags.add(TPE1(encoding=3, text=["Frontion News"]))
    tags.add(TALB(encoding=3, text=["Frontion News"]))
    tags.add(TDRC(encoding=3, text=[DATE]))
    tags.add(TRCK(encoding=3, text=[str(track_num)]))
    
    # Add cover art
    cover_path = WORKDIR / "podcast" / "podcast-cover-3000.jpg"
    with open(cover_path, "rb") as img:
        tags.add(APIC(
            encoding=3,
            mime="image/jpeg",
            type=3,  # Front cover
            desc="Front Cover",
            data=img.read()
        ))
    
    audio.save()
    print(f"  ID3 tags added")
    
    # Get duration
    duration_sec = int(audio.info.length)
    duration_str = get_duration_str(duration_sec)
    file_size = os.path.getsize(mp3_path)
    
    tracks.append({
        "prefix": prefix,
        "brief_label": brief_label,
        "website_url": website_url,
        "episode_title": episode_title,
        "desc": desc,
        "duration_str": duration_str,
        "duration_sec": duration_sec,
        "file_size": file_size,
        "mp3_filename": f"frontion-{prefix}-{DATE}.mp3",
        "track_num": track_num,
    })
    
    print(f"  Duration: {duration_str}, Size: {file_size}")

# Save tracks info for shell script to use
with open("/tmp/podcast_tracks_20260718.json", "w") as f:
    json.dump(tracks, f, indent=2)
    
print("\nAll episodes generated successfully!")
for t in tracks:
    print(f"  {t['episode_title']}: {t['duration_str']} ({t['file_size']} bytes)")