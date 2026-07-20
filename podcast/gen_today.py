#!/usr/bin/env python3
"""Regenerate defence and tech MP3s, tag all 5, update RSS and HTML, git push."""
import json, re, os, sys, subprocess, html
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK, APIC

DATE = "2026-07-20"
DATE_DISPLAY = "July 20, 2026"
DATE_RSS = "Sun, 20 Jul 2026 07:30:00 +0300"
SITE_DIR = "/Users/claudius/clawd/frontion-site"
PODCAST_DIR = os.path.join(SITE_DIR, "podcast")
COVER_ART = os.path.join(PODCAST_DIR, "podcast-cover-3000.jpg")

SECTIONS = [
    ("briefs", "global", "Strategic Brief", "https://frontion.news"),
    ("defense", "defence", "Defence & Industry Brief", "https://frontion.news/defence"),
    ("energy", "energy", "Energy & Power Brief", "https://frontion.news/energy"),
    ("finance", "finance", "Finance & Markets Brief", "https://frontion.news/finance"),
    ("tech", "tech", "Tech Brief", "https://frontion.news/tech"),
]

def strip_html(text):
    if not text:
        return ""
    text = re.sub(r'<p>', '\n', text)
    text = re.sub(r'</p>', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def build_script(data, brief_label, date_display):
    lines = []
    lines.append(f"Welcome to Frontion News' {brief_label} for {date_display}.")
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

def tag_mp3(mp3_path, title, date_str):
    # Delete existing tags by removing the ID3 tag completely
    from mutagen.id3 import ID3
    try:
        ID3(mp3_path).delete()
    except:
        pass
    audio = MP3(mp3_path)
    # Now add fresh tags
    audio.add_tags()
    audio.tags.add(TIT2(encoding=3, text=[title]))
    audio.tags.add(TPE1(encoding=3, text=["Frontion News"]))
    audio.tags.add(TALB(encoding=3, text=["Frontion News"]))
    audio.tags.add(TDRC(encoding=3, text=[date_str]))
    audio.tags.add(TRCK(encoding=3, text=["1"]))
    with open(COVER_ART, 'rb') as img:
        audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=img.read()))
    audio.save()

def format_duration(seconds):
    return f"{seconds // 60}:{seconds % 60:02d}"

os.chdir(SITE_DIR)
results = []

# Step 1: Regenerate TTS for defence and tech (the two broken ones)
regenerate = ["defence", "tech"]

for json_dir, prefix, brief_label, url in SECTIONS:
    json_path = os.path.join(SITE_DIR, json_dir, f"{DATE}.json")
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    mp3_path = os.path.join(PODCAST_DIR, f"frontion-{prefix}-{DATE}.mp3")
    
    if prefix in regenerate:
        print(f"\n=== Regenerating {brief_label} ({prefix}) ===")
        sys.stdout.flush()
        
        script = build_script(data, brief_label, DATE_DISPLAY)
        txt_path = f"/tmp/brief-text-{prefix}-{DATE}.txt"
        with open(txt_path, 'w') as f:
            f.write(script)
        print(f"Script: {len(script)} chars")
        sys.stdout.flush()
        
        # Remove old file
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
        
        cmd = ["python3", "-m", "edge_tts", "-f", txt_path, "-v", "en-GB-RyanNeural", "--rate=-10%", "--write-media", mp3_path]
        print(f"Running TTS for {prefix}...")
        sys.stdout.flush()
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            print(f"TTS FAILED for {prefix}: {r.stderr}")
            sys.exit(1)
        print(f"TTS done for {prefix}")
        sys.stdout.flush()

# Step 2: Tag all 5 MP3s
for json_dir, prefix, brief_label, url in SECTIONS:
    json_path = os.path.join(SITE_DIR, json_dir, f"{DATE}.json")
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    mp3_path = os.path.join(PODCAST_DIR, f"frontion-{prefix}-{DATE}.mp3")
    headline = strip_html(data["title"])
    title_tag = f"{brief_label} — {DATE_DISPLAY}: {headline}"
    if len(title_tag) > 250:
        title_tag = title_tag[:247] + "..."
    
    print(f"Tagging {prefix}...")
    sys.stdout.flush()
    tag_mp3(mp3_path, title_tag, DATE)
    
    audio = MP3(mp3_path)
    dur = int(audio.info.length)
    file_size = os.path.getsize(mp3_path)
    desc = strip_html(data["subhead"]) + f"\n\nRead the full analysis at {url}"
    
    results.append({
        "prefix": prefix,
        "brief_label": brief_label,
        "url": url,
        "title_tag": title_tag,
        "headline": headline,
        "description": desc,
        "file_size": file_size,
        "duration_str": format_duration(dur),
        "mp3_filename": f"frontion-{prefix}-{DATE}.mp3",
    })
    print(f"  {prefix}: {format_duration(dur)} | {file_size:,} bytes | {title_tag[:60]}")
    sys.stdout.flush()

# Step 3: Update RSS - remove existing July 20 entries, add new ones
with open(os.path.join(PODCAST_DIR, "frontion-podcast.rss"), 'r') as f:
    rss = f.read()

# Remove existing items for 2026-07-20
import re as re_mod
item_pattern = re_mod.compile(r'<item>.*?</item>', re_mod.DOTALL)
all_items = item_pattern.findall(rss)
kept_items = [item for item in all_items if "2026-07-20" not in item]
removed = len(all_items) - len(kept_items)
print(f"\nRemoved {removed} existing RSS items for {DATE}")

# Build new items
new_items = []
for r in results:
    desc_esc = r["description"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "\n        ")
    title_esc = r["title_tag"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    item = f"""    <item>
        <title>{title_esc}</title>
        <link>{r["url"]}</link>
        <description>{desc_esc}</description>
        <enclosure url="https://frontion.news/podcast/{r["mp3_filename"]}" length="{r["file_size"]}" type="audio/mpeg" />
        <guid isPermaLink="false">frontion-{r["prefix"]}-{DATE}</guid>
        <pubDate>{DATE_RSS}</pubDate>
        <itunes:duration>{r["duration_str"]}</itunes:duration>
        <itunes:explicit>false</itunes:explicit>
    </item>"""
    new_items.append(item)

# Reconstruct RSS
header_end = rss.find('<item>')
header = rss[:header_end]
all_items_xml = '\n'.join(new_items) + '\n' + '\n'.join(kept_items)
footer = '\n\n</channel>\n</rss>'
new_rss = header + all_items_xml + footer

with open(os.path.join(PODCAST_DIR, "frontion-podcast.rss"), 'w') as f:
    f.write(new_rss)
print(f"RSS updated: {len(new_items)} new + {len(kept_items)} kept items")

# Step 4: Update HTML
with open(os.path.join(PODCAST_DIR, "index.html"), 'r') as f:
    html_content = f.read()

# Remove existing July 20 episodes from HTML
li_pattern = re_mod.compile(r'<li class="episode">.*?</li>', re_mod.DOTALL)
all_lis = li_pattern.findall(html_content)
kept_lis = [li for li in all_lis if "2026-07-20" not in li and DATE_DISPLAY not in li]
html_removed = len(all_lis) - len(kept_lis)
print(f"Removed {html_removed} existing HTML items for {DATE}")

# Build new <li> elements
new_lis = []
for r in results:
    desc_text = r["description"].split("\n\nRead the full analysis at")[0].strip()
    li = f"""        <li class="episode">
            <div class="episode-meta">{DATE_DISPLAY} — {r["brief_label"]}</div>
            <div class="episode-title">{r["headline"]}</div>
            <div class="episode-desc">{desc_text} Read the full analysis at <a href="{r["url"]}">{r["url"]}</a></div>
            <audio controls preload="none"><source src="{r["mp3_filename"]}" type="audio/mpeg">Your browser does not support audio.</audio>
        </li>"""
    new_lis.append(li)

li_start = html_content.find('<li class="episode">')
ul_end = html_content.find('</ul>')
header_html = html_content[:li_start]
footer_html = html_content[ul_end:]
all_episodes = '\n\n'.join(new_lis) + '\n' + '\n\n'.join(kept_lis)
new_html = header_html + all_episodes + '\n    ' + footer_html

with open(os.path.join(PODCAST_DIR, "index.html"), 'w') as f:
    f.write(new_html)
print(f"HTML updated: {len(new_lis)} new + {len(kept_lis)} kept episodes")

# Step 5: Git add, commit, push
subprocess.run(["git", "add", "podcast/"], check=True)
subprocess.run(["git", "commit", "-m", f"Podcast episodes for {DATE}"], check=True)
subprocess.run(["git", "push"], check=True)
print(f"\nGit committed and pushed!")
print(f"\n=== COMPLETE ===")
for r in results:
    print(f"  {r['brief_label']}: {r['mp3_filename']} ({r['file_size']:,} bytes, {r['duration_str']})")