import json
from datetime import datetime

# Load headlines
d = json.load(open('headlines.json'))

# Take first 25 items
items = d['headlines'][:25]

# Build RSS feed
rss = '''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>Frontion News - Tier 1 Headlines</title>
<link>https://frontion.com</link>
<description>Breaking geopolitical news from Tier 1 sources</description>
<language>en-us</language>
<lastBuildDate>{lastUpdated}</lastBuildDate>
'''.format(lastUpdated=d['lastUpdated'])

for item in items:
    # Escape special characters
    headline = item['headline'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    summary = item['summary'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    source = item['source']
    url = item['url']
    timestamp = item['timestamp']
    
    rss += f'''
<item>
<title>{item['emoji']} {headline}</title>
<link>{url}</link>
<description>{summary}</description>
<source>{source}</source>
<pubDate>{timestamp}</pubDate>
<category>{item['category']}</category>
</item>
'''

rss += '''
</channel>
</rss>
'''

# Write feed
with open('feed.xml', 'w', encoding='utf-8') as f:
    f.write(rss)

print(f'Generated feed.xml with {len(items)} items')