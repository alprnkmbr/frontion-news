import json
from datetime import datetime, timezone, timedelta

d = json.load(open("headlines.json"))

new_items = [
  {
    "headline": "Trump warns Iran 'clock is ticking' as peace talks stall",
    "summary": "President Donald Trump issued his most direct warning to Iran yet, saying time is running out for negotiations as Tehran has not made concrete concessions.",
    "emoji": "⚠️",
    "category": "US-Iran War",
    "source": "BBC",
    "url": "https://www.bbc.com/news/world-us-canada-69052134",
    "timestamp": "2026-05-18T03:03:00+03:00"
  },
  {
    "headline": "Taiwan President responds to Trump summit: 'We will not be sacrificed'",
    "summary": "Taiwan President Lai Ching-te pushed back after Trump raised doubts about US arms sales and willingness to defend the island following his Beijing summit with Xi Jinping.",
    "emoji": "🇹🇼",
    "category": "US-China",
    "source": "Reuters",
    "url": "https://www.reuters.com/world/china/taiwan-independence-means-we-dont-belong-beijing-president-says-2026-05-17/",
    "timestamp": "2026-05-18T03:03:00+03:00"
  },
  {
    "headline": "Senate parliamentarian blocks $1 billion White House security funding",
    "summary": "The Senate parliamentarian ruled that Republican efforts to allocate funding for Trumps proposed White House ballroom project cannot proceed through budget reconciliation.",
    "emoji": "🏛️",
    "category": "US Politics",
    "source": "Reuters",
    "url": "https://www.reuters.com/world/us/federal-funding-trumps-ballroom-jeopardy-after-senate-ruling-2026-05-17/",
    "timestamp": "2026-05-18T03:03:00+03:00"
  },
  {
    "headline": "Political executions surge in Iran since war began, UN verifies at least 32",
    "summary": "The United Nations has verified the execution of at least 32 political prisoners in Iran since the US-Israel war began on February 28.",
    "emoji": "🏴",
    "category": "Middle East",
    "source": "BBC",
    "url": "https://www.bbc.com/news/world-middle-east-69052156",
    "timestamp": "2026-05-18T03:03:00+03:00"
  },
  {
    "headline": "Ukraine launches largest drone attack on Moscow in over a year, killing 4",
    "summary": "Ukraine conducted one of its largest drone strikes of the war, killing at least 4 people near Moscow and wounding 12 others.",
    "emoji": "🇺🇦",
    "category": "Ukraine-Russia War",
    "source": "AP News",
    "url": "https://apnews.com/article/russia-ukraine-drones-moscow-strike-attack-killed-3164d723ca8331e5780ec7942245a2e6",
    "timestamp": "2026-05-18T03:03:00+03:00"
  }
]

for item in reversed(new_items):
    d["headlines"].insert(0, item)

d["lastUpdated"] = datetime.now(timezone(timedelta(hours=3))).strftime("%Y-%m-%dT%H:%M:%S+03:00")
json.dump(d, open("headlines.json","w"), ensure_ascii=False, indent=2)
print("Done. Added", len(new_items), "stories. Total:", len(d["headlines"]), "headlines")