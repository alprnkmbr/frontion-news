#!/usr/bin/env python3
"""
Frontion News Feed — RSS aggregator.

Tier-1 / Tier-2 kaynakların RSS feed'lerini çeker, normalize eder,
dedupe yapar ve site için feed.json üretir.

Her haber: başlık · 1 cümle özet · kaynak adı · Tier · kaynak linki · zaman · resim
"""

import json
import html
import re
import sys
import time
import hashlib
import concurrent.futures
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse

import requests
import feedparser

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "feed.json"

# Repo'da tutulacak maksimum haber
MAX_ITEMS = 300

# Sadece bu penceredeki haberler (gün)
MAX_AGE_DAYS = 4

# feed.json dışında feed/images altına inen thumbnail sayısı sınırı (hafif kalsın)
THUMB_MAX = 120
THUMB_WIDTH = 480
THUMBS_DIR = ROOT / "feed" / "images"

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
GOOGLEBOT_UA = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
HEADERS = {"User-Agent": UA, "Accept": "*/*"}
TIMEOUT = 12

# Bazı kaynaklar normal UA'ya 403 verir; Googlebot UA ile açılırlar.
GOOGLEBOT_HOSTS = {"timesofisrael.com", "alarabiya.net", "telegraph.co.uk"}

# ---------------------------------------------------------------------------
# SOURCES  (Tier-1 = validate_sources.py TIER1_SOURCES, Tier-2 = TIER2_SOURCES)
# RSS'i olmayan kaynaklar (Reuters, AFP, AP, CNN...) listede durur ama feed
# yoksa sessizce atlanır.
# ---------------------------------------------------------------------------

SOURCES = [
    # ---------------- TIER 1 ----------------
    {"name": "Reuters", "tier": 1, "feeds": []},
    {"name": "AP News", "tier": 1, "feeds": [], "hub": "https://apnews.com/hub/ap-top-news"},
    {"name": "AFP", "tier": 1, "feeds": []},
    {"name": "BBC", "tier": 1, "feeds": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://feeds.bbci.co.uk/news/business/rss.xml",
        "https://feeds.bbci.co.uk/news/technology/rss.xml",
    ]},
    {"name": "Al Jazeera", "tier": 1, "feeds": ["https://www.aljazeera.com/xml/rss/all.xml"]},
    {"name": "CNN", "tier": 1, "feeds": ["http://rss.cnn.com/rss/edition_world.rss"]},
    {"name": "CBS News", "tier": 1, "feeds": ["https://www.cbsnews.com/latest/rss/world"]},
    {"name": "NBC News", "tier": 1, "feeds": [
        "https://feeds.nbcnews.com/nbcnews/public/world",
        "https://feeds.nbcnews.com/nbcnews/public/news",
    ]},
    {"name": "CNBC", "tier": 1, "feeds": ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"]},
    {"name": "NPR", "tier": 1, "feeds": ["https://feeds.npr.org/1004/rss.xml"]},
    {"name": "New York Times", "tier": 1, "feeds": [
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    ]},
    {"name": "Washington Post", "tier": 1, "feeds": [
        "https://feeds.washingtonpost.com/rss/world",
        "https://feeds.washingtonpost.com/rss/business",
    ]},
    {"name": "Financial Times", "tier": 1, "feeds": ["https://www.ft.com/rss/home"]},
    {"name": "The Guardian", "tier": 1, "feeds": [
        "https://www.theguardian.com/world/rss",
        "https://www.theguardian.com/business/rss",
        "https://www.theguardian.com/technology/rss",
    ]},
    {"name": "The Economist", "tier": 1, "feeds": ["https://www.economist.com/the-world-this-week/rss.xml"]},
    {"name": "Wall Street Journal", "tier": 1, "feeds": []},
    {"name": "Bloomberg", "tier": 1, "feeds": []},

    # ---------------- TIER 2 ----------------
    {"name": "TRT World", "tier": 2, "feeds": ["https://www.trtworld.com/feed/rss.xml"]},
    {"name": "DW", "tier": 2, "feeds": ["https://rss.dw.com/rdf/rss-en-all"]},
    {"name": "France 24", "tier": 2, "feeds": ["https://www.france24.com/en/rss"]},
    {"name": "Euronews", "tier": 2, "feeds": ["https://www.euronews.com/rss?format=mrss&level=theme&name=news"]},
    {"name": "SCMP", "tier": 2, "feeds": ["https://www.scmp.com/rss/91/feed"]},
    {"name": "Times of Israel", "tier": 2, "feeds": ["https://www.timesofisrael.com/feed/"]},
    {"name": "Anadolu Agency", "tier": 2, "feeds": ["https://www.aa.com.tr/en/rss/default?cat=guncel"]},
    {"name": "RT", "tier": 2, "feeds": []},
    {"name": "Defense News", "tier": 2, "feeds": ["https://www.defensenews.com/arc/outboundfeeds/rss/"]},
    {"name": "Sky News", "tier": 2, "feeds": ["https://feeds.skynews.com/feeds/rss/world.xml"]},
    {"name": "CNA", "tier": 2, "feeds": ["https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml"]},
    {"name": "Al Arabiya", "tier": 2, "feeds": ["https://english.alarabiya.net/tools/rss"]},
    {"name": "NHK", "tier": 2, "feeds": ["https://www3.nhk.or.jp/rss/news/cat0.xml"]},
    {"name": "Le Monde", "tier": 2, "feeds": ["https://www.lemonde.fr/en/rss/une.xml"]},
    {"name": "El País", "tier": 2, "feeds": ["https://feeds.elpais.com/mrss-s/pages/ep/site/english.elpais.com/portada"]},
    {"name": "The Times", "tier": 2, "feeds": []},
    {"name": "The Telegraph", "tier": 2, "feeds": ["https://www.telegraph.co.uk/rss.xml"]},
    {"name": "The Independent", "tier": 2, "feeds": ["https://www.independent.co.uk/news/world/rss"]},
    {"name": "Politico", "tier": 2, "feeds": ["https://rss.politico.com/politics-news.xml"]},
    {"name": "The Hill", "tier": 2, "feeds": ["https://thehill.com/news/feed/"]},
    {"name": "Axios", "tier": 2, "feeds": ["https://api.axios.com/feed/"]},
    {"name": "Business Insider", "tier": 2, "feeds": ["https://www.businessinsider.com/rss"]},
    {"name": "Fortune", "tier": 2, "feeds": ["https://fortune.com/feed/"]},
    {"name": "Forbes", "tier": 2, "feeds": ["https://www.forbes.com/business/feed/"]},
    {"name": "MarketWatch", "tier": 2, "feeds": ["https://feeds.content.dowjones.io/public/rss/mw_topstories"]},
    {"name": "TechCrunch", "tier": 2, "feeds": ["https://techcrunch.com/feed/"]},
    {"name": "The Verge", "tier": 2, "feeds": ["https://www.theverge.com/rss/index.xml"]},
    {"name": "Ars Technica", "tier": 2, "feeds": ["https://feeds.arstechnica.com/arstechnica/index"]},
    {"name": "Wired", "tier": 2, "feeds": ["https://www.wired.com/feed/rss"]},
    {"name": "MIT Tech Review", "tier": 2, "feeds": ["https://www.technologyreview.com/feed/"]},
    {"name": "Space.com", "tier": 2, "feeds": ["https://www.space.com/feeds/all"]},
    {"name": "NASA", "tier": 2, "feeds": ["https://www.nasa.gov/rss/dyn/breaking_news.rss"]},
    {"name": "Science Daily", "tier": 2, "feeds": ["https://www.sciencedaily.com/rss/all.xml"]},
]

# Domain -> (source name, tier) — link doğrulama + filtre için
DOMAIN_MAP = {
    "reuters.com": ("Reuters", 1),
    "apnews.com": ("AP News", 1),
    "afp.com": ("AFP", 1),
    "news.yahoo.com": ("AFP", 1),
    "bbc.com": ("BBC", 1),
    "bbc.co.uk": ("BBC", 1),
    "aljazeera.com": ("Al Jazeera", 1),
    "cnn.com": ("CNN", 1),
    "cbsnews.com": ("CBS News", 1),
    "nbcnews.com": ("NBC News", 1),
    "cnbc.com": ("CNBC", 1),
    "npr.org": ("NPR", 1),
    "nytimes.com": ("New York Times", 1),
    "washingtonpost.com": ("Washington Post", 1),
    "ft.com": ("Financial Times", 1),
    "theguardian.com": ("The Guardian", 1),
    "economist.com": ("The Economist", 1),
    "wsj.com": ("Wall Street Journal", 1),
    "bloomberg.com": ("Bloomberg", 1),
    "trtworld.com": ("TRT World", 2),
    "dw.com": ("DW", 2),
    "france24.com": ("France 24", 2),
    "euronews.com": ("Euronews", 2),
    "scmp.com": ("SCMP", 2),
    "timesofisrael.com": ("Times of Israel", 2),
    "aa.com.tr": ("Anadolu Agency", 2),
    "rt.com": ("RT", 2),
    "defensenews.com": ("Defense News", 2),
    "news.sky.com": ("Sky News", 2),
    "sky.com": ("Sky News", 2),
    "channelnewsasia.com": ("CNA", 2),
    "alarabiya.net": ("Al Arabiya", 2),
    "nhk.or.jp": ("NHK", 2),
    "lemonde.fr": ("Le Monde", 2),
    "elpais.com": ("El País", 2),
    "thetimes.co.uk": ("The Times", 2),
    "telegraph.co.uk": ("The Telegraph", 2),
    "independent.co.uk": ("The Independent", 2),
    "politico.com": ("Politico", 2),
    "thehill.com": ("The Hill", 2),
    "axios.com": ("Axios", 2),
    "businessinsider.com": ("Business Insider", 2),
    "fortune.com": ("Fortune", 2),
    "forbes.com": ("Forbes", 2),
    "marketwatch.com": ("MarketWatch", 2),
    "techcrunch.com": ("TechCrunch", 2),
    "theverge.com": ("The Verge", 2),
    "arstechnica.com": ("Ars Technica", 2),
    "wired.com": ("Wired", 2),
    "technologyreview.com": ("MIT Tech Review", 2),
    "space.com": ("Space.com", 2),
    "nasa.gov": ("NASA", 2),
    "sciencedaily.com": ("Science Daily", 2),
}

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def strip_html(s: str) -> str:
    if not s:
        return ""
    s = TAG_RE.sub(" ", s)
    s = html.unescape(s)
    return WS_RE.sub(" ", s).strip()


def clean_title(s: str) -> str:
    s = strip_html(s)
    s = re.sub(r"^(BREAKING|LIVE|VIDEO|WATCH|OPINION|ANALYSIS|EXCLUSIVE|UPDATE)[:\s\-–—]+", "", s, flags=re.I)
    return s.strip()


def one_sentence(s: str, limit: int = 240) -> str:
    """Metnin ilk cümlesini (ya da ilk `limit` karakterini) döndürür."""
    s = strip_html(s)
    if not s:
        return ""
    # ilk cümle sonu
    m = re.search(r"(.+?[.!?])(\s|$)", s)
    if m:
        s = m.group(1).strip()
    if len(s) > limit:
        s = s[:limit].rsplit(" ", 1)[0] + "…"
    return s


def domain_of(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        # alt domain eşleşmesi (ör. m.bbc.co.uk -> bbc.co.uk)
        parts = host.split(".")
        for i in range(len(parts) - 1):
            cand = ".".join(parts[i:])
            if cand in DOMAIN_MAP:
                return cand
        return host
    except Exception:
        return ""


def source_for_url(url: str):
    d = domain_of(url)
    return DOMAIN_MAP.get(d)


def parse_time(entry) -> datetime:
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        t = entry.get(key)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return datetime.now(timezone.utc)


def entry_image(entry) -> str:
    """RSS entry içinden görsel URL'i çıkarır (enclosure / media / içerik)."""
    # media:content / media:thumbnail
    for key in ("media_content", "media_thumbnail"):
        for m in entry.get(key, []) or []:
            u = m.get("url")
            if u and u.lower().split("?")[0].endswith((".jpg", ".jpeg", ".png", ".webp")):
                return u
    # enclosures
    for e in entry.get("enclosures", []) or []:
        if e.get("href") and str(e.get("type", "")).startswith("image"):
            return e["href"]
        if e.get("href", "").lower().split("?")[0].endswith((".jpg", ".jpeg", ".png", ".webp")):
            return e["href"]
    # içerikten <img src>
    for key in ("content", "summary"):
        val = entry.get(key)
        if isinstance(val, list) and val:
            val = val[0].get("value", "")
        if isinstance(val, str) and val:
            m = re.search(r'<img[^>]+src="([^"]+)"', val)
            if m:
                return html.unescape(m.group(1))
    return ""


def make_id(link: str, title: str) -> str:
    h = hashlib.sha1((link or title).encode("utf-8")).hexdigest()[:16]
    return h


# ---------------------------------------------------------------------------
# FETCH
# ---------------------------------------------------------------------------


def fetch_feed(url: str):
    host = domain_of(url)
    hdrs = dict(HEADERS)
    if host in GOOGLEBOT_HOSTS:
        hdrs["User-Agent"] = GOOGLEBOT_UA
    try:
        r = requests.get(url, headers=hdrs, timeout=TIMEOUT)
        if r.status_code != 200:
            return url, None
        return url, feedparser.parse(r.content)
    except Exception:
        return url, None


def collect():
    jobs = []
    for src in SOURCES:
        for feed_url in src.get("feeds", []):
            jobs.append((src, feed_url))

    items = []
    ok_feeds, bad_feeds = [], []

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        futures = {pool.submit(fetch_feed, fu): (src, fu) for src, fu in jobs}
        for fut in concurrent.futures.as_completed(futures):
            src, feed_url = futures[fut]
            _, parsed = fut.result()
            if not parsed or not getattr(parsed, "entries", None):
                bad_feeds.append((src["name"], feed_url))
                continue
            ok_feeds.append((src["name"], feed_url, len(parsed.entries)))
            for e in parsed.entries:
                link = (e.get("link") or "").strip()
                if not link:
                    continue
                # Linkin domaini bilinen bir kaynak mı? Değilse atla.
                known = source_for_url(link)
                if not known:
                    continue
                name, tier = known

                title = clean_title(e.get("title", ""))
                if not title:
                    continue

                dt = parse_time(e)
                if dt < datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS):
                    continue

                raw_summary = ""
                if e.get("summary"):
                    raw_summary = e["summary"]
                elif e.get("description"):
                    raw_summary = e["description"]
                elif e.get("content"):
                    c = e["content"]
                    raw_summary = c[0].get("value", "") if isinstance(c, list) and c else ""

                items.append({
                    "id": make_id(link, title),
                    "title": title,
                    "summary": one_sentence(raw_summary),
                    "source": name,
                    "tier": tier,
                    "link": link,
                    "ts": int(dt.timestamp()),
                    "time": dt.isoformat(),
                    "image": entry_image(e),
                })

    return items, ok_feeds, bad_feeds


# ---------------------------------------------------------------------------
# THUMBNAILS  (hafif: sadece ilk N haber için, ~480px genişlik)
# ---------------------------------------------------------------------------


def download_thumb(url: str, key: str) -> str:
    """Görseli indirip 480px JPEG thumbnail üretir. Yerel yol döner."""
    try:
        from PIL import Image
        from io import BytesIO
    except Exception:
        return ""
    dest = THUMBS_DIR / f"{key}.jpg"
    if dest.exists():
        return f"feed/images/{key}.jpg"
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code != 200 or not r.content:
            return ""
        img = Image.open(BytesIO(r.content)).convert("RGB")
        if img.width < 120 or img.height < 80:
            return ""
        # oranı koru, hedef genişlik
        if img.width > THUMB_WIDTH:
            h = int(img.height * (THUMB_WIDTH / img.width))
            img = img.resize((THUMB_WIDTH, h), Image.LANCZOS)
        # çok uzun/dikey olanları kırp (kart oranı ~16:10)
        target_h = int(img.width * 0.625)
        if img.height > target_h:
            top = (img.height - target_h) // 2
            img = img.crop((0, top, img.width, top + target_h))
        THUMBS_DIR.mkdir(parents=True, exist_ok=True)
        img.save(dest, "JPEG", quality=78, optimize=True)
        return f"feed/images/{key}.jpg"
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------


def load_existing():
    if OUTPUT.exists():
        try:
            data = json.loads(OUTPUT.read_text())
            if isinstance(data, dict) and "items" in data:
                return data
        except Exception:
            pass
    return None


def main():
    t0 = time.time()
    print("Frontion News Feed — toplayıcı başlıyor…")

    old = load_existing()
    old_items = {it["id"]: it for it in (old or {}).get("items", [])} if old else {}

    fresh, ok_feeds, bad_feeds = collect()
    print(f"  {len(fresh)} ham haber geldi ({len(ok_feeds)} feed OK, {len(bad_feeds)} feed hatalı)")

    # id bazlı dedupe — en yenisi kazanır
    merged = {}
    for it in fresh:
        merged[it["id"]] = it

    # eskileri koru (feed.json sürekliliği için)
    for k, v in old_items.items():
        if k not in merged:
            # 4 günden eskiyse at
            if v.get("ts", 0) >= (datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)).timestamp():
                merged[k] = v

    items = sorted(merged.values(), key=lambda x: x.get("ts", 0), reverse=True)
    items = items[:MAX_ITEMS]

    # ---- Thumbnail'ler: sadece görseli olan, en yeni THUMB_MAX haber ----
    need = [it for it in items if it.get("image") and not it.get("thumb")][:THUMB_MAX]
    have = sum(1 for it in items if it.get("thumb"))
    budget = max(0, THUMB_MAX - have)
    need = need[:budget]

    if need:
        print(f"  {len(need)} thumbnail indiriliyor…")
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            futs = {pool.submit(download_thumb, it["image"], it["id"]): it for it in need}
            for fut in concurrent.futures.as_completed(futs):
                it = futs[fut]
                local = fut.result()
                if local:
                    it["thumb"] = local

    # Eski kayıtlardan thumb'ı olanları koru
    for it in items:
        if not it.get("thumb") and it["id"] in old_items:
            if old_items[it["id"]].get("thumb"):
                it["thumb"] = old_items[it["id"]]["thumb"]

    out = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "updated_iso": int(datetime.now(timezone.utc).timestamp()),
        "count": len(items),
        "items": items,
    }
    OUTPUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))

    t1 = time.time()
    n_img = sum(1 for it in items if it.get("thumb"))
    print(f"  feed.json yazıldı: {len(items)} haber, {n_img} görselli, {t1-t0:.1f}s")
    if bad_feeds:
        print("  Hatalı feed'ler:")
        for name, fu in bad_feeds:
            print(f"    - {name}: {fu}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
