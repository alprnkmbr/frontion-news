import json
from datetime import datetime, timezone, timedelta

with open('/Users/claudius/clawd/frontion-site/headlines.json') as f:
    d = json.load(f)

items = d['headlines'][:25]

rss_items = []
for h in items:
    desc = f"{h['emoji']} {h['headline']}"
    if h.get('summary'):
        desc += f"\n\n{h['summary']}"
    rss_items.append(f"""    <item>
      <title>{h['emoji']} {h['headline']}</title>
      <link>{h['url']}</link>
      <description>{h.get('summary', '')}</description>
      <category>{h['category']}</category>
      <pubDate>{datetime.fromisoformat(h['timestamp']).strftime('%a, %d %b %Y %H:%M:%S %z')}</pubDate>
      <source>{h['source']}</source>
    </item>""")

feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Frontion News Headlines</title>
    <link>https://frontion.com</link>
    <description>Breaking geopolitical headlines from Tier 1 sources</description>
    <language>en</language>
    <lastBuildDate>{datetime.now(timezone(timedelta(hours=3))).strftime('%a, %d %b %Y %H:%M:%S %z')}</lastBuildDate>
    <atom:link href="https://frontion.com/feed.xml" rel="self" type="application/rss+xml"/>
{chr(10).join(rss_items)}
  </channel>
</rss>"""

with open('/Users/claudius/clawd/frontion-site/feed.xml', 'w') as f:
    f.write(feed)

print(f"Feed generated with {len(items)} items")