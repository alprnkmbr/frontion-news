#!/usr/bin/env python3
"""Generate podcast episodes from daily briefs."""
import json, re, html, os, subprocess, sys
from datetime import datetime
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TDRC, TRCK

DATE = "2026-07-20"
DATE_FMT = "July 20, 2026"
PUB_DATE = "Sun, 20 Jul 2026 07:30:00 +0300"

SECTIONS = [
    ("briefs",  "global",  "Strategic Brief",       "https://frontion.news"),
]

COVER = "podcast/podcast-cover-3000.jpg"

def strip_html(text):
    """Remove HTML tags, replace <p> with newlines, decode entities."""
    text = text.replace('</p>', '\n')
    text = re.sub(r'<p[^>]*>', '', text)
    text = re.sub(r'<strong[^>]*>', '', text)
    text = text.replace('</strong>', '')
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    # Clean up multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def build_script(data, brief_type_label):
    """Build TTS script from JSON data."""
    lines = []
    lines.append(f"Welcome to Frontion News' {brief_type_label} for {DATE_FMT}.")
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
    lines.append("")
    lines.append(strip_html(data["bottomLine"]))
    lines.append("")
    lines.append(f"Read the full analysis at ")  # URL will be appended per section
    return "\n".join(lines)

def get_duration_str(seconds):
    """Format seconds as M:SS."""
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"

os.chdir("/Users/claudius/clawd/frontion-site")

results = []

for i, (folder, prefix, label, url) in enumerate(SECTIONS):
    json_path = f"{folder}/{DATE}.json"
    with open(json_path, 'r') as f:
        data = json.load(f)

    script = build_script(data, label)
    # Append URL at the end
    script += url

    txt_path = f"/tmp/brief-text-{prefix}-{DATE}.txt"
    mp3_path = f"podcast/frontion-{prefix}-{DATE}.mp3"

    with open(txt_path, 'w') as f:
        f.write(script)

    print(f"Generating TTS for {label}...")
    result = subprocess.run(
        ["python3", "-m", "edge_tts", "-f", txt_path,
         "-v", "en-GB-RyanNeural", "--rate=-10%",
         "--write-media", mp3_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"TTS FAILED for {label}: {result.stderr}")
        sys.exit(1)
    print(f"  TTS done: {mp3_path}")

    # ID3 tags
    headline = strip_html(data["title"])
    # Truncate if needed for title tag
    title_val = f"{label} — {DATE_FMT}: {headline}"
    track_num = i + 1

    mp3 = MP3(mp3_path)
    try:
        mp3.remove_tags(ID3)
    except:
        pass
    mp3.save()

    mp3 = MP3(mp3_path)
    mp3.tags.add(TIT2(encoding=3, text=title_val))
    mp3.tags.add(TPE1(encoding=3, text="Frontion News"))
    mp3.tags.add(TALB(encoding=3, text="Frontion News"))
    mp3.tags.add(TDRC(encoding=3, text=DATE))
    mp3.tags.add(TRCK(encoding=3, text=str(track_num)))

    with open(COVER, 'rb') as img:
        mp3.tags.add(APIC(
            encoding=3, mime='image/jpeg', type=3,
            desc='Cover', data=img.read()
        ))

    mp3.save()

    duration_secs = mp3.info.length
    duration_str = get_duration_str(duration_secs)
    file_size = os.path.getsize(mp3_path)

    # Description (clean, with URL)
    desc_text = strip_html(data["subhead"])
    desc_text += f"\n\nRead the full analysis at {url}"

    results.append({
        "prefix": prefix,
        "label": label,
        "url": url,
        "title": title_val,
        "headline": headline,
        "desc": desc_text,
        "mp3_path": mp3_path,
        "mp3_file": f"frontion-{prefix}-{DATE}.mp3",
        "duration": duration_str,
        "size": file_size,
        "track": track_num,
    })
    print(f"  Duration: {duration_str}, Size: {file_size}")

print("\nAll TTS generated. Now updating RSS and HTML...")

# ===== UPDATE RSS =====
with open("podcast/frontion-podcast.rss", 'r') as f:
    rss_content = f.read()

# Remove any existing items for today's date
rss_content = re.sub(
    rf'\s*<item>.*?</item>\s*',
    '',
    rss_content,
    flags=re.DOTALL
)

# Wait, that removes ALL items. Let me be more targeted - remove only items with today's date
# Re-read the original
with open("podcast/frontion-podcast.rss", 'r') as f:
    rss_content = f.read()

# Remove items containing our date pattern
rss_content = re.sub(
    rf'\n\s*<item>\s*.*?frontion-(?:global|defence|energy|finance|tech)-{DATE}\.mp3.*?</item>\s*',
    '',
    rss_content,
    flags=re.DOTALL
)

# Build new items
new_items = ""
for r in reversed(results):  # reverse so global comes first in final
    # Escape XML special chars in description
    desc_escaped = (r["desc"]
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    title_escaped = (r["title"]
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

    item = f"""
    <item>
        <title>{title_escaped}</title>
        <link>{r['url']}</link>
        <description>{desc_escaped}</description>
        <enclosure url="https://frontion.news/podcast/{r['mp3_file']}" length="{r['size']}" type="audio/mpeg" />
        <guid isPermaLink="false">frontion-{r['prefix']}-{DATE}</guid>
        <pubDate>{PUB_DATE}</pubDate>
        <itunes:duration>{r['duration']}</itunes:duration>
        <itunes:explicit>false</itunes:explicit>
    </item>"""
    new_items = item + new_items  # prepend each so order is: tech, finance, energy, defence, global

# Insert after the atom:link line
insert_after = '<atom:link href="https://frontion.news/podcast/frontion-podcast.rss" rel="self" type="application/rss+xml" />'
rss_content = rss_content.replace(insert_after, insert_after + new_items, 1)

with open("podcast/frontion-podcast.rss", 'w') as f:
    f.write(rss_content)

print("RSS updated.")

# ===== UPDATE HTML =====
# Build new <li> entries for today, inserted at the top of the <ul>
html_entries = ""
for r in results:
    brief_type_short = r["label"].replace("Strategic Brief", "Strategic Brief").replace("Defence & Industry Brief", "Defence & Industry Brief").replace("Energy & Power Brief", "Energy & Power Brief").replace("Finance & Markets Brief", "Finance & Markets Brief").replace("Tech Brief", "Tech Brief")
    # Map label to short display
    label_display = r["label"]
    desc_html = r["desc"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Use actual line breaks for HTML
    desc_html = desc_html.replace("\n\n", "<br><br>")
    desc_html_raw = r["desc"]

    entry = f"""
        <li class="episode">
            <div class="episode-meta">{DATE_FMT} — {label_display}</div>
            <div class="episode-title">{r['headline']}</div>
            <div class="episode-desc">{desc_html_raw} <a href="{r['url']}">{r['url']}</a></div>
            <audio controls preload="none"><source src="{r['mp3_file']}" type="audio/mpeg">Your browser does not support audio.</audio>
        </li>"""
    html_entries += entry

with open("podcast/index.html", 'r') as f:
    html_content = f.read()

# Remove any existing entries for today's date to prevent duplicates
html_content = re.sub(
    rf'\n\s*<li class="episode">\s*.*?frontion-(?:global|defence|energy|finance|tech)-{DATE}\.mp3.*?</li>\s*',
    '\n',
    html_content,
    flags=re.DOTALL
)

# Insert after the <ul class="episodes"> tag
html_content = html_content.replace(
    '<ul class="episodes">\n',
    '<ul class="episodes">\n' + html_entries + '\n'
)

with open("podcast/index.html", 'w') as f:
    f.write(html_content)

print("HTML updated.")
print("\nDone! Episodes:")
for r in results:
    print(f"  {r['label']}: {r['mp3_file']} ({r['duration']}, {r['size']} bytes)")