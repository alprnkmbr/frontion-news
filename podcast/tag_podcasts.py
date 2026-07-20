#!/usr/bin/env python3
"""Add ID3 tags and cover art to podcast MP3s using mutagen."""

import os
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TDRC, TRCK, error as ID3Error
from mutagen.mp3 import MP3

DATE = "2026-07-19"
BASE = "/Users/claudius/clawd/frontion-site"
COVER = os.path.join(BASE, "podcast", "podcast-cover-3000.jpg")

EPISODES = [
    {
        "prefix": "global",
        "title": f"Strategic Brief — July 19, 2026: Two US Troops Killed in Jordan as Iran War Escalates, Canada Wildfires Trigger Tariff Threats, Hungary Ousts Orbán-Era President",
        "track": 1,
    },
    {
        "prefix": "defence",
        "title": f"Defence & Industry Brief — July 19, 2026: Hormuz Standoff Escalates as Strikes Resume, Farnborough Opens Under Iran War Shadow, Helsing Raises $1.8B",
        "track": 2,
    },
    {
        "prefix": "finance",
        "title": f"Finance & Markets Brief — July 19, 2026: US Restores Hong Kong Trade Status as Container Rates Surge, Rare Earths Spike, and IEA Warns on Hormuz",
        "track": 3,
    },
    {
        "prefix": "tech",
        "title": f"Tech Brief — July 19, 2026: Iranian Drones Hit AWS Data Centers, SpaceX Buys Cursor for $60B, Alibaba Open-Sources CUDA Rival",
        "track": 4,
    },
]

# Read cover art
with open(COVER, 'rb') as f:
    cover_data = f.read()

for ep in EPISODES:
    mp3_path = os.path.join(BASE, "podcast", f"frontion-{ep['prefix']}-{DATE}.mp3")
    
    try:
        tags = ID3(mp3_path)
    except ID3Error:
        tags = ID3()
    
    tags.delall("TIT2")
    tags.delall("TPE1")
    tags.delall("TALB")
    tags.delall("TDRC")
    tags.delall("TRCK")
    tags.delall("APIC")
    
    tags.add(TIT2(encoding=3, text=[ep["title"]]))
    tags.add(TPE1(encoding=3, text=["Frontion News"]))
    tags.add(TALB(encoding=3, text=["Frontion News"]))
    tags.add(TDRC(encoding=3, text=[DATE]))
    tags.add(TRCK(encoding=3, text=[str(ep["track"])]))
    tags.add(APIC(
        encoding=3,
        mime="image/jpeg",
        type=3,  # Front cover
        desc="Cover",
        data=cover_data,
    ))
    
    tags.save(mp3_path)
    print(f"Tagged: {mp3_path}")

print("All ID3 tags added.")

# Now get durations
for ep in EPISODES:
    mp3_path = os.path.join(BASE, "podcast", f"frontion-{ep['prefix']}-{DATE}.mp3")
    audio = MP3(mp3_path)
    total_seconds = int(audio.info.length)
    mins = total_seconds // 60
    secs = total_seconds % 60
    file_size = os.path.getsize(mp3_path)
    print(f"{ep['prefix']}: duration={mins}:{secs:02d}, size={file_size}")