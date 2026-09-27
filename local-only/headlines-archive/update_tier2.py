import json
from datetime import datetime, timezone, timedelta

d = json.load(open('/Users/claudius/clawd/frontion-site/headlines.json'))

# Check last 30 URLs to avoid duplicates
existing_urls = set(h['url'] for h in d['headlines'][:30])

new_items = []

# Moldova story - unique Tier 2
if 'https://kyivindependent.com/moldovas-former-most-powerful-person-sentenced-to-19-years-in-jail/' not in existing_urls:
    new_items.append({
        'headline': "Moldova's former powerful oligarch Plahotniuc sentenced to 19 years in prison",
        'summary': "Vladimir Plahotniuc, Moldova's wealthiest businessman who de facto controlled the country's government in the 2010s, was sentenced in absentia. His fall is seen as part of Moldova's alignment with European democratic values.",
        'emoji': '🇲🇩',
        'category': 'Europe',
        'source': 'Kyiv Independent',
        'url': 'https://kyivindependent.com/moldovas-former-most-powerful-person-sentenced-to-19-years-in-jail/',
        'timestamp': '2026-04-23T00:10:00+03:00'
    })

# Germany military strategy - unique Tier 2 Defense News
if 'https://www.defensenews.com/global/europe/2026/04/22/germany-unveils-strategy-for-becoming-europe-strongest-military-by-2039/' not in existing_urls:
    new_items.append({
        'headline': "Germany unveils strategy to become Europe's strongest military by 2039",
        'summary': 'The Bundeswehr will move away from rigid hardware quotas toward a flexible, effects-based planning model. The plan comes amid concerns about Russian military buildup.',
        'emoji': '🇩🇪',
        'category': 'Defense Industry',
        'source': 'Defense News',
        'url': 'https://www.defensenews.com/global/europe/2026/04/22/germany-unveils-strategy-for-becoming-europe-strongest-military-by-2039/',
        'timestamp': '2026-04-23T00:10:00+03:00'
    })

# Dutch NATO warning - unique Tier 2 Defense News
if 'https://www.defensenews.com/global/europe/2026/04/22/russia-could-be-ready-for-nato-conflict-year-after-ukraine-dutch-warn/' not in existing_urls:
    new_items.append({
        'headline': 'Russia could be ready for NATO conflict a year after Ukraine, Dutch intelligence warns',
        'summary': "Moscow's goal would not be to defeat NATO militarily but to divide it through limited territorial gains, according to a new Dutch intelligence report.",
        'emoji': '⚔️',
        'category': 'Europe',
        'source': 'Defense News',
        'url': 'https://www.defensenews.com/global/europe/2026/04/22/russia-could-be-ready-for-nato-conflict-year-after-ukraine-dutch-warn/',
        'timestamp': '2026-04-23T00:10:00+03:00'
    })

# Canada PM responds to Trump demands - unique SCMP story
if 'https://www.scmp.com/news/world/united-states-canada/article/3351028/canada-pm-hits-back-after-trump-team-demands-entry-fee-trade-talks' not in existing_urls:
    new_items.append({
        'headline': "Canada PM hits back after Trump team demands 'entry fee' before trade talks",
        'summary': "Canadian Prime Minister Mark Carney rejected US demands for concessions before trade negotiations could begin, pushing back against the Trump administration's approach.",
        'emoji': '🇨🇦',
        'category': 'Diplomacy',
        'source': 'SCMP',
        'url': 'https://www.scmp.com/news/world/united-states-canada/article/3351028/canada-pm-hits-back-after-trump-team-demands-entry-fee-trade-talks',
        'timestamp': '2026-04-23T00:10:00+03:00'
    })

# Baltic nations Iran war impact - unique Defense News
if 'https://www.defensenews.com/global/europe/2026/04/19/baltic-nations-brace-for-impact-of-iran-war-delaying-us-weapons-shipments/' not in existing_urls:
    new_items.append({
        'headline': 'Baltic nations brace for Iran war impact on US weapons shipments',
        'summary': "Delays in ammunition deliveries could reopen a thorny question for Baltic HIMARS users: Would the US permit non-Lockheed rockets to be loaded?",
        'emoji': '🇪🇪',
        'category': 'Defense Industry',
        'source': 'Defense News',
        'url': 'https://www.defensenews.com/global/europe/2026/04/19/baltic-nations-brace-for-impact-of-iran-war-delaying-us-weapons-shipments/',
        'timestamp': '2026-04-23T00:10:00+03:00'
    })

for item in reversed(new_items):
    d['headlines'].insert(0, item)

d['lastUpdated'] = datetime.now(timezone(timedelta(hours=3))).strftime('%Y-%m-%dT%H:%M:%S+03:00')
json.dump(d, open('/Users/claudius/clawd/frontion-site/headlines.json','w'), ensure_ascii=False, indent=2)
print(f'Added {len(new_items)} new stories. Total: {len(d["headlines"])}')