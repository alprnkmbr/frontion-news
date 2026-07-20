#!/usr/bin/env python3
"""Generate podcast episodes for 2026-07-20."""

import json
import re
import subprocess
import os
import html

DATE = "2026-07-20"
DATE_DISPLAY = "July 20, 2026"
PODCAST_DIR = "/Users/claudius/clawd/frontion-site/podcast"
COVER_ART = os.path.join(PODCAST_DIR, "podcast-cover-3000.jpg")

# Section config: (json_path, prefix, brief_type_label, website_url)
SECTIONS = [
    ("briefs", "global", "Strategic Brief", "https://frontion.news"),
    ("defense", "defence", "Defence & Industry Brief", "https://frontion.news/defence"),
    ("energy", "energy", "Energy & Power Brief", "https://frontion.news/energy"),
    ("finance", "finance", "Finance & Markets Brief", "https://frontion.news/finance"),
    ("tech", "tech", "Tech Brief", "https://frontion.news/tech"),
]

def strip_html(text):
    """Strip HTML tags, replace <p> with newlines, decode entities."""
    if not text:
        return ""
    # Replace <p> and </p> with newlines
    text = re.sub(r'<p>', '\n', text)
    text = re.sub(r'</p>', '', text)
    # Remove all other HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    text = html.unescape(text)
    # Clean up whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()
    return text

def build_script(data, brief_type_label, date_display):
    """Build the podcast script from JSON data."""
    lines = []
    lines.append(f"Welcome to Frontion News' {brief_type_label} for {date_display}.")
    lines.append("")
    lines.append(strip_html(data["title"]))
    lines.append("")
    lines.append(strip_html(data["subhead"]))
    lines.append("")
    
    for section in data["sections"]:
        lines.append(strip_html(section["heading"]))
        lines.append("")
        lines.append(strip_html(section["body"]))
        lines.append("")
    
    lines.append("The Bottom Line.")
    lines.append("")
    lines.append(strip_html(data["bottomLine"]))
    
    return "\n".join(lines)

def get_duration_seconds(mp3_path):
    """Get duration of MP3 in seconds using mutagen."""
    from mutagen.mp3 import MP3
    audio = MP3(mp3_path)
    return int(audio.info.length)

def format_duration(seconds):
    """Format seconds as MM:SS."""
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins}:{secs:02d}"

def tag_mp3(mp3_path, title, date_str):
    """Add ID3 tags and cover art to MP3."""
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK, APIC
    
    # Remove existing tags
    try:
        audio = MP3(mp3_path)
        audio.delete()
        audio.save()
    except:
        pass
    
    audio = MP3(mp3_path)
    
    # Add ID3 tags
    audio.add_tags()
    audio.tags.add(TIT2(encoding=3, text=[title]))
    audio.tags.add(TPE1(encoding=3, text=["Frontion News"]))
    audio.tags.add(TALB(encoding=3, text=["Frontion News"]))
    audio.tags.add(TDRC(encoding=3, text=[date_str]))
    audio.tags.add(TRCK(encoding=3, text=["1"]))
    
    # Add cover art
    with open(COVER_ART, 'rb') as img:
        audio.tags.add(APIC(
            encoding=3,
            mime='image/jpeg',
            type=3,  # Cover (front)
            desc='Cover',
            data=img.read()
        ))
    
    audio.save()

def main():
    os.chdir("/Users/claudius/clawd/frontion-site")
    
    for json_dir, prefix, brief_label, url in SECTIONS:
        json_path = f"{json_dir}/{DATE}.json"
        print(f"\n=== Processing {brief_label} ({prefix}) ===")
        
        # Read JSON
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Build script
        script = build_script(data, brief_label, DATE_DISPLAY)
        
        # Save text file
        txt_path = f"/tmp/brief-text-{prefix}-{DATE}.txt"
        with open(txt_path, 'w') as f:
            f.write(script)
        print(f"Saved script to {txt_path} ({len(script)} chars)")
        
        # Generate TTS
        mp3_path = os.path.join(PODCAST_DIR, f"frontion-{prefix}-{DATE}.mp3")
        cmd = [
            "python3", "-m", "edge_tts",
            "-f", txt_path,
            "-v", "en-GB-RyanNeural",
            "--rate=-10%",
            "--write-media", mp3_path
        ]
        print(f"Generating TTS: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"TTS ERROR: {result.stderr}")
            continue
        print(f"Generated {mp3_path}")
        
        # Get file size
        file_size = os.path.getsize(mp3_path)
        print(f"File size: {file_size} bytes")
        
        # Tag MP3
        headline = strip_html(data["title"])
        # Truncate title if too long for ID3
        title_tag = f"{brief_label} — {DATE_DISPLAY}: {headline}"
        if len(title_tag) > 250:
            title_tag = title_tag[:247] + "..."
        tag_mp3(mp3_path, title_tag, DATE)
        print(f"Tagged: {title_tag}")
        
        # Get duration
        duration_secs = get_duration_seconds(mp3_path)
        duration_str = format_duration(duration_secs)
        print(f"Duration: {duration_str} ({duration_secs} seconds)")
        
        print(f"\n--- {prefix} summary ---")
        print(f"  MP3: {mp3_path}")
        print(f"  Size: {file_size}")
        print(f"  Duration: {duration_str}")
        print(f"  Title: {title_tag}")
        print(f"  URL: {url}")
        print(f"  Description ends with: Read the full analysis at {url}")

if __name__ == "__main__":
    main()