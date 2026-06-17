import json
from datetime import datetime, timezone, timedelta

d = json.load(open('headlines.json'))

new_items = [
    {
        'headline': 'Russia Launches Major Attack on Ukraine, Killing at Least 11',
        'summary': 'Russia launched one of its largest air assaults on Kyiv and other Ukrainian cities in months, firing 73 missiles and 656 drones. At least 11 people were killed and over 100 wounded in the overnight strikes, which Russia called a response to Kyiv\'s "terrorist acts" inside Russia.',
        'emoji': '🇺🇦⚔️',
        'category': 'Ukraine-Russia War',
        'source': 'Reuters',
        'url': 'https://www.reuters.com/business/aerospace-defense/russia-says-its-overnight-ukraine-strike-was-response-kyivs-terrorist-acts-2026-06-02/',
        'timestamp': '2026-06-02T12:03:00+03:00'
    },
    {
        'headline': 'Ukrainian Drone Attack Sets Russian Oil Refinery on Fire',
        'summary': 'Ukraine continued its campaign against Russian energy infrastructure as the Ilsky oil refinery in Russia\'s Krasnodar region caught fire after an overnight drone attack. Kyiv has been systematically targeting Russian oil facilities to starve Moscow of war revenue.',
        'emoji': '🇺🇦🛢️🔥',
        'category': 'Ukraine-Russia War',
        'source': 'Reuters',
        'url': 'https://www.reuters.com/business/energy/russias-ilsky-oil-refinery-on-fire-after-overnight-ukrainian-drone-attack-2026-06-02/',
        'timestamp': '2026-06-02T12:03:00+03:00'
    },
    {
        'headline': 'EU Agrees Major Migration Overhaul with Offshore Return Centers',
        'summary': 'The European Union has advanced a sweeping migration policy reform that would increase deportations and establish detention centers abroad. The deal represents a significant shift toward tougher border controls as the bloc responds to political pressure over migration.',
        'emoji': '🇪🇺🏛️',
        'category': 'Europe',
        'source': 'AP News',
        'url': 'https://apnews.com/article/migration-brussels-deportation-detention-27f04759acf5f9f4df73862c561a609b',
        'timestamp': '2026-06-02T12:03:00+03:00'
    },
    {
        'headline': 'Russia Increases Pressure on Armenia Ahead of Election',
        'summary': 'Russia is intensifying pressure on Armenia ahead of a June 7 election as the once-close ally pursues deeper ties with Brussels and Washington. The move reflects Moscow\'s efforts to maintain influence in its traditional sphere amid Armenia\'s Western pivot.',
        'emoji': '🇷🇺🇦🇲',
        'category': 'Diplomacy',
        'source': 'Reuters',
        'url': 'https://www.reuters.com/business/russia-ups-pressure-armenia-ahead-sundays-election-2026-06-01/',
        'timestamp': '2026-06-02T12:03:00+03:00'
    },
    {
        'headline': 'Motorola Solutions Buys Israeli Drone Defense Startup for $1.5 Billion',
        'summary': 'Motorola Solutions announced it will acquire Israeli startup D-Fend Solutions for $1.5 billion, highlighting growing demand for counter-drone technology as governments and critical infrastructure operators worldwide face increasing threats from rogue drones.',
        'emoji': '🛡️💰',
        'category': 'Defense Industry',
        'source': 'Reuters',
        'url': 'https://www.reuters.com/technology/motorola-solutions-buy-d-fend-solutions-15-billion-2026-06-01/',
        'timestamp': '2026-06-02T12:03:00+03:00'
    }
]

for item in reversed(new_items):
    d['headlines'].insert(0, item)

d['lastUpdated'] = datetime.now(timezone(timedelta(hours=3))).strftime('%Y-%m-%dT%H:%M:%S+03:00')

json.dump(d, open('headlines.json','w'), ensure_ascii=False, indent=2)
print(f'Done. Added {len(new_items)} items. Total: {len(d["headlines"])}')