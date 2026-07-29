import json
from datetime import datetime, timezone, timedelta

d = json.load(open('headlines.json'))
items = d['headlines'][:25]

now_iso = datetime.now(timezone(timedelta(hours=3))).strftime('%Y-%m-%dT%H:%M:%S+03:00')

def esc(s):
    return s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')

xml_items = ''
for h in items:
    xml_items += f"""
      <item>
        <title>{esc(h['emoji'])} {esc(h['headline'])}</title>
        <link>{esc(h['url'])}</link>
        <description>{esc(h['summary'])}</description>
        <category>{esc(h['category'])}</category>
        <pubDate>{h['timestamp']}</pubDate>
        <source>{esc(h['source'])}</source>
      </item>"""

feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Frontion News</title>
    <link>https://frontion.com</link>
    <description>Breaking geopolitics headlines from Tier 1 sources</description>
    <language>en</language>
    <lastBuildDate>{now_iso}</lastBuildDate>
    <atom:link href="https://frontion.com/feed.xml" rel="self" type="application/rss+xml"/>{xml_items}
  </channel>
</rss>"""

with open('feed.xml','w') as f:
    f.write(feed)
print(f'Feed written with {len(items)} items')