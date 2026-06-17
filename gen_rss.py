import json
from datetime import datetime

d = json.load(open("headlines.json"))
items = d["headlines"][:25]

rss = '''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel>
<title>Frontion News - Geopolitical Headlines</title>
<link>https://frontion.news</link>
<description>Breaking geopolitical news from Tier 1 sources worldwide</description>
<language>en-us</language>
<lastBuildDate>{}</lastBuildDate>
<ttl>15</ttl>
'''.format(datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0300"))

for h in items:
    desc = h.get("summary", "")
    if "perspectives" in h:
        desc += "<br/><br/><b>Perspectives:</b><ul>"
        for p in h["perspectives"]:
            desc += '<li><a href="{}">{}</a> ({}): {}</li>'.format(
                p["url"], p["angle"], p["source"], p["summary"]
            )
        desc += "</ul>"
    
    rss += '''<item>
<title>{} {}</title>
<link>{}</link>
<description>{}</description>
<dc:creator>{}</dc:creator>
<category>{}</category>
<pubDate>{}</pubDate>
</item>
'''.format(
        h.get("emoji", ""), h["headline"], h["url"], desc,
        h["source"], h["category"], h["timestamp"]
    )

rss += "</channel>\n</rss>"

with open("feed.xml", "w") as f:
    f.write(rss)

print("Generated feed.xml with", len(items), "items")