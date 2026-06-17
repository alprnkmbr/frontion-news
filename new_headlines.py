import json
from datetime import datetime, timezone, timedelta

d = json.load(open('headlines.json'))

new_items = [
    {
        "headline": "Iran Reviewing US Peace Proposal as Trump Warns of Further Strikes",
        "summary": "Tehran is reviewing Washington's latest response to a ceasefire proposal, with Trump saying negotiations are in final stages but threatening renewed attacks if no deal is reached.",
        "emoji": "🇮🇷",
        "category": "US-Iran War",
        "source": "Reuters",
        "url": "https://www.reuters.com/world/asia-pacific/tehran-reviewing-latest-us-response-trump-suggests-he-can-wait-2026-05-21/",
        "timestamp": "2026-05-21T09:03:00+03:00"
    },
    {
        "headline": "Germany Proposes Associate EU Membership for Ukraine",
        "summary": "Chancellor Friedrich Merz has proposed giving Ukraine a direct role in EU structures as an interim step toward full membership, potentially helping facilitate a deal to end the war with Russia.",
        "emoji": "🇺🇦🇩🇪",
        "category": "Ukraine-Russia War",
        "source": "Reuters",
        "url": "https://www.reuters.com/world/europe/germanys-merz-pitches-associate-eu-membership-ukraine-2026-05-21/",
        "timestamp": "2026-05-21T09:03:00+03:00"
    },
    {
        "headline": "Russia Delivers Nuclear Munitions to Belarus for Drills",
        "summary": "Russia has delivered nuclear munitions to field storage facilities in Belarus as part of major nuclear exercises, escalating tensions with the West over Ukraine.",
        "emoji": "⚔️☢️",
        "category": "Military",
        "source": "Reuters",
        "url": "https://www.reuters.com/world/europe/russia-delivers-nuclear-munitions-belarus-part-nuclear-drills-2026-05-21/",
        "timestamp": "2026-05-21T09:03:00+03:00"
    },
    {
        "headline": "Russian Oil and Gas Revenue Surges 39% Due to Iran War Price Rally",
        "summary": "Russia's state oil and gas revenues are projected to rise 39% year-on-year in May to 700 billion roubles, driven by global oil price increases from the Iran conflict.",
        "emoji": "💰🛢️",
        "category": "Energy",
        "source": "Reuters",
        "url": "https://www.reuters.com/business/energy/russias-oil-gas-revenue-seen-up-39-yy-may-thanks-iran-war-2026-05-20/",
        "timestamp": "2026-05-21T09:03:00+03:00"
    },
    {
        "headline": "Central Russian Oil Refineries Halt Output After Ukrainian Drone Strikes",
        "summary": "Major oil refineries in central Russia have been forced to stop or reduce fuel production following Ukrainian drone attacks, according to official data and industry sources.",
        "emoji": "💥🛢️",
        "category": "Ukraine-Russia War",
        "source": "Reuters",
        "url": "https://www.reuters.com/business/energy/oil-refining-standstill-central-russia-after-ukrainian-drone-strikes-sources-say-2026-05-20/",
        "timestamp": "2026-05-21T09:03:00+03:00"
    }
]

for item in reversed(new_items):
    d['headlines'].insert(0, item)

d['lastUpdated'] = datetime.now(timezone(timedelta(hours=3))).strftime('%Y-%m-%dT%H:%M:%S+03:00')
json.dump(d, open('headlines.json','w'), ensure_ascii=False, indent=2)
print(f'Done. Total: {len(d["headlines"])}')