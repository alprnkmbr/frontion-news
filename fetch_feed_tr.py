#!/usr/bin/env python3
"""
Frontion News — Türkçe Feed (turkeyfeed) toplayıcısı.

fetch_feed.py'nin YAPISAL KOPYASIDIR. Mevcut İngilizce feed'e dokunmaz.
Farkı: kaynaklar GLOBAL değil, TÜRKÇE kaynaklardır. Haberler Türkçe
RSS'lerden Türkçe olarak çekilir; çeviri yapılmaz.

Çıktı: tr-feed.json  (frontion.news/turkeyfeed sayfası bunu okur)
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
OUTPUT = ROOT / "tr-feed.json"
HIDDEN = ROOT / "hidden-tr.json"
LLM_CACHE = ROOT / ".feed_tr_llm_cache.json"

# --- LLM seçici (yalnızca YENİ item'lar skorlanır) ---
LLM_ENABLED = True
LLM_MODEL = "deepseek-v4.1-flash:cloud"
LLM_MAX_NEW = 1200
LLM_EXAMPLES = 40
LLM_BATCH = 15

# Repo'da tutulacak maksimum haber
MAX_ITEMS = 300

# Sadece bu penceredeki haberler (gün)
MAX_AGE_DAYS = 4

# thumbnail sınırı
THUMB_MAX = 120
THUMB_WIDTH = 480
THUMBS_DIR = ROOT / "feed" / "images"

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
GOOGLEBOT_UA = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
HEADERS = {"User-Agent": UA, "Accept": "*/*"}
TIMEOUT = 12

GOOGLEBOT_HOSTS = set()

# ---------------------------------------------------------------------------
# SOURCES — TÜRKÇE KAYNAKLAR (Tier-1 = ana akım/köklü, Tier-2 = ek)
# ---------------------------------------------------------------------------

SOURCES = [
    # ---------------- TIER 1 ----------------
    {"name": "Anadolu Ajansı", "tier": 1, "feeds": [
        "https://www.aa.com.tr/tr/rss/default?cat=dunya",
        "https://www.aa.com.tr/tr/rss/default?cat=ekonomi",
    ]},
    {"name": "TRT Haber", "tier": 1, "feeds": [
        "https://www.trthaber.com/dunya_articles.rss",
        "https://www.trthaber.com/ekonomi_articles.rss",
    ]},
    {"name": "Hürriyet", "tier": 1, "feeds": [
        "https://www.hurriyet.com.tr/rss/dunya",
        "https://www.hurriyet.com.tr/rss/ekonomi",
    ]},
    {"name": "Sabah", "tier": 1, "feeds": [
        "https://www.sabah.com.tr/rss/dunya.xml",
        "https://www.sabah.com.tr/rss/ekonomi.xml",
    ]},
    {"name": "NTV", "tier": 1, "feeds": [
        "https://www.ntv.com.tr/dunya.rss",
        "https://www.ntv.com.tr/ekonomi.rss",
    ]},
    {"name": "Habertürk", "tier": 1, "feeds": [
        "https://www.haberturk.com/rss/ekonomi.xml",
        "https://www.haberturk.com/rss/dunya.xml",
    ]},
    {"name": "BBC Türkçe", "tier": 1, "feeds": [
        "https://feeds.bbci.co.uk/turkce/rss.xml",
    ]},
    {"name": "DW Türkçe", "tier": 1, "feeds": [
        "https://rss.dw.com/rdf/rss-tur-all",
    ]},
    {"name": "Dünya", "tier": 1, "feeds": [
        "https://www.dunya.com/rss?listtype=top",
        "https://www.dunya.com/rss?listtype=ekonomi",
    ]},
    {"name": "Ekonomim", "tier": 1, "feeds": [
        "https://www.ekonomim.com/rss",
    ]},

    # ---------------- TIER 2 ----------------
    {"name": "Sözcü", "tier": 2, "feeds": [
        "https://www.sozcu.com.tr/rss/dunya.xml",
    ]},
    {"name": "Cumhuriyet", "tier": 2, "feeds": [
        "https://www.cumhuriyet.com.tr/rss/dunya",
        "https://www.cumhuriyet.com.tr/rss/ekonomi",
    ]},
    {"name": "T24", "tier": 2, "feeds": [
        "https://t24.com.tr/rss/haber/dunya",
        "https://t24.com.tr/rss/haber/ekonomi",
    ]},
    {"name": "Medyascope", "tier": 2, "feeds": [
        "https://medyascope.tv/feed/",
    ]},
    {"name": "Milliyet", "tier": 2, "feeds": [
        "https://www.milliyet.com.tr/rss/rssNew/dunyaRss.xml",
        "https://www.milliyet.com.tr/rss/rssNew/ekonomiRss.xml",
    ]},
    {"name": "Star", "tier": 2, "feeds": [
        "https://www.star.com.tr/rss/dunya.xml",
    ]},
    {"name": "Yeni Şafak", "tier": 2, "feeds": [
        "https://www.yenisafak.com/rss?category=dunya",
        "https://www.yenisafak.com/rss?category=ekonomi",
    ]},
    {"name": "Independent Türkçe", "tier": 2, "feeds": [
        "https://www.indyturk.com/rss.xml",
    ]},
    {"name": "Gazete Duvar", "tier": 2, "feeds": [
        "https://www.gazeteduvar.com.tr/export/rss",
    ]},
    {"name": "Bloomberg HT", "tier": 2, "feeds": [
        "https://www.bloomberght.com/rss",
    ]},
    {"name": "Euronews Türkçe", "tier": 2, "feeds": [
        "https://tr.euronews.com/rss",
    ]},
    {"name": "VOA Türkçe", "tier": 2, "feeds": [
        "https://www.voaturkce.com/api/zq$omekvi_",
    ]},
]

# Domain -> (source name, tier) — link doğrulama + filtre için
DOMAIN_MAP = {
    "aa.com.tr": ("Anadolu Ajansı", 1),
    "trthaber.com": ("TRT Haber", 1),
    "trt.com.tr": ("TRT Haber", 1),
    "hurriyet.com.tr": ("Hürriyet", 1),
    "sabah.com.tr": ("Sabah", 1),
    "ntv.com.tr": ("NTV", 1),
    "haberturk.com": ("Habertürk", 1),
    "bbc.com": ("BBC Türkçe", 1),
    "bbc.co.uk": ("BBC Türkçe", 1),
    "dw.com": ("DW Türkçe", 1),
    "dunya.com": ("Dünya", 1),
    "ekonomim.com": ("Ekonomim", 1),
    "sozcu.com.tr": ("Sözcü", 2),
    "cumhuriyet.com.tr": ("Cumhuriyet", 2),
    "t24.com.tr": ("T24", 2),
    "medyascope.tv": ("Medyascope", 2),
    "milliyet.com.tr": ("Milliyet", 2),
    "star.com.tr": ("Star", 2),
    "yenisafak.com": ("Yeni Şafak", 2),
    "indyturk.com": ("Independent Türkçe", 2),
    "gazeteduvar.com.tr": ("Gazete Duvar", 2),
    "bloomberght.com": ("Bloomberg HT", 2),
    "tr.euronews.com": ("Euronews Türkçe", 2),
    "voaturkce.com": ("VOA Türkçe", 2),
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
    s = re.sub(r"^(SON DAKİKA|CANLI|VİDEO|İZLE|GÖRÜNTÜLÜ|FLAŞ|ÖZEL|ANALİZ|YORUM|GÜNCELLEME)[:\s\-–—]+", "", s, flags=re.I)
    return s.strip()


def one_sentence(s: str, limit: int = 240) -> str:
    """Metnin ilk cümlesini (ya da ilk `limit` karakterini) döndürür."""
    s = strip_html(s)
    if not s:
        return ""
    m = re.search(r"(.+?[.!?])(\s|$)", s)
    if m:
        s = m.group(1).strip()
    if len(s) > limit:
        s = s[:limit].rsplit(" ", 1)[0] + "…"
    return s


# ---------------------------------------------------------------------------
# İÇERİK FİLTRESİ — Türkçe başlık/özet için
# Spor / magazin / yaşam tarzı / yerel haberler AKIŞA GİRMEZ.
# ---------------------------------------------------------------------------

# 0) Jeopolitik istisna (spor görünümlü ama siyasi anlam taşıyan)
GEOPOLITICAL_SPORT_PATTERNS = [
    r"\b(boykot|forma|bandaj|protesto|siyasi mesaj|sahadan çekil|madalyasını (redd|iade)|ayakta durma|diz çökme|istiklal marşı)\b",
    r"\b(uefa|fifa|olimpiyat|nations league)\b.{0,80}\b(israil|rusya|belarus|iran|gazze|filistin|ukrayna|taiwan|tayvan|hong kong)\b",
    r"\b(israil|rusya|belarus|iran|gazze|filistin|ukrayna|taiwan|tayvan|hong kong)\b.{0,80}\b(uefa|fifa|olimpiyat|maç|milli takım)\b",
]

# 1) Kesin eleme (güçlü magazin/spor/magazin sinyali)
BLOCK_PATTERNS = [
    # magazin / ünlü
    r"\b(magazin|ünlü|kardashian|taylor swift|madonna|özel hayat|paparazzi|kırmızı halı|gala|dizi|dizi(ler|si)?\b|reyting|final bölümü|yeni sezon|oscar|grammy|festival\b)\b",
    r"\b(moda|podyum|defile|güzellik yarışması)\b",
    # Türkçe click-bait / sansasyonel / yerel kalıplar
    r"\b(korkutan görüntü|korkutan anlar|nefes kesen|şoke eden|şaşırtan|pes dedirten|bakın ne oldu|gözler inanamadı|yürekleri ağıza getiren|kan donduran|çılgına çeviren)\b",
    r"\b(raflardaydı|artık marketlerde görülmeyecek|markette fiyat|fiyatı düştü|indirimli|kampanyalı|kaçırmayın|fırsatı kaçırma)\b",
    r"\b(vatandaşa müjde|flaş gelişme|çok konuşulacak|bomba iddia|ortalık karıştı|alarm verdi|sosyal medyada gündem)\b",
    r"\b(denizin rengi|rengi değişti|kamerada|kamera kaydı|canlı yayında)\b",
    r"\b(hayatını kaybetti|hayatını kaybeden|ölü bulundu|cesedi|cinayet|trafik kazası|yangın|doğal afet|sel baskını|depremde)\b",
    r"\b(hava sıcaklığı|meteoroloji|sağanak|fırtına uyarısı|kar yağışı|hava durumu)\b",
    r"\b(meb\b|öğretmen ataması|yks\b|lgs\b|üniversite tercih|okullar tatil)\b",
    r"\b(hastane|ameliyat|salgın|aşı kampanyası|obezite|kanser taraması)\b",
    r"\b(pazar fiyatı|et fiyatı|süt fiyatı|akaryakıt zammı|doğalgaz zammı|elektrik zammı|market fiyatları)\b",
    r"\b(emekli maaşı|asgari ücret zammı|ehliyet|araç muayene|trafik cezası|vergi affı)\b",
    r"\b(günlük burç|hangi burç|astroloji|rüya tabiri)\b",
    # spor
    r"\b(süper lig|premier lig|şampiyonlar ligi|uefa|fifa|dünya kupası|avrupa şampiyonası|euro \d{4}|nba|nfl|basketbol|futbol|maç\b|maçta|gol\b|golcü|teknik direktör|hakem|penaltı|kupası|transfer\b.*\b(futbolcu|oyuncu)|futbolcu|santrafor|orta saha|forvet|antrenör)\b",
    r"\b(derbi|derbide|yendi|yenildi|berabere|galibiyet|mağlubiyet|puan durumu|gol attı|forma giydi|sakatlandı|kadro dışı)\b",
    r"\b(tenis|golf|boks|ufc|voleybol|hentbol|atletizm|formula 1|pist\b|grand prix|motor sporları)\b",
    # yaşam tarzı / tüketim / sağlık-magazin
    r"\b(altın günü|tarif|yemek tarifi|diyet\b|kilo verme|zayıflama|fitness|indirim|kampanya|bedava|kupon|alışveriş|kredi kartı|konut kredisi faizi|ihtiyaç kredisi|bireysel kredi)\b",
    r"\b(burç|burçlar|astroloji|kraliyet ailesi|magazin programı|yarışma programı|reality)\b",
    r"\b(tatil (rehberi|önerileri)|otel (kampanya|fırsat)|ucuz uçak bileti|gezi rehberi|en güzel plajlar)\b",
    r"\b(hava durumu|hava tahmini|meteoroloji)\b",
]

# 2) Kesin kabul (jeopolitik/stratejik değer)
ALLOW_PATTERNS = [
    r"\b(savaş|ateşkes|saldırı|füze|İHA|SİHA|drone|hava saldırısı|işgal|taarruz|cephe|asker|ordu|donanma|hava kuvvetleri|nato|savunma|silah|silahlı|ambargo|yaptırım)\b",
    r"\b(iran|israil|gazze|husi|yemen|hizbullah|hamas|ukrayna|rusya|putin|zelenski|çin|tayvan|pekin|kuzey kore|nükleer|uaeb|hurmus|hürmüz|kızıldeniz|bab-ül mendep)\b",
    r"\b(trump|biden|beyaz saray|pentagon|dışişleri|kremlin|ab\b|avrupa birliği|birleşmiş milletler|güvenlik konseyi|diplomasi|anlaşma|zirve|g7|g20|brics|opec)\b",
    r"\b(petrol|doğal gaz|lng|boru hattı|rafineri|ham petrol|opec|enerji (krizi|güvenliği|arzı)|elektrik şebekesi|nükleer (santral|enerji)|yenilenebilir|hidrojen)\b",
    r"\b(enflasyon|faiz|merkez bankası|fed\b|ecb\b|resesyon|gsyh|tarife|ticaret savaşı|borsa|tahvil|kur\b|döviz|temerrüt|imf|dünya bankası|tedarik zinciri)\b",
    r"\b(çip|yarı iletken|yapay zeka|kuantum|siber (saldırı|güvenlik|savaş)|veri ihlali|uydu|uzay (yarışı|programı)|starlink|ihracat kontrolü)\b",
    r"\b(terör|terörist|isyan|militan|aşırılıkçı|rehin|darbe|ayaklanma|sıkıyönetim|mülteci|göç (krizi|politikası)|sınır (anlaşmazlığı|çatışması))\b",
    r"\b(dış politika|jeopolitik|mutabakat|zirve|kabine|parlamento|meclis|bütçe görüşmesi|nato üyeliği|ab üyeliği|yaptırım paketi|resmi açıklama|seçim sonucu|seçime gidiyor)\b",
]

_BLOCK_RE = re.compile("|".join(BLOCK_PATTERNS), re.I)
_ALLOW_RE = re.compile("|".join(ALLOW_PATTERNS), re.I)
_GEOSPORT_RE = re.compile("|".join(GEOPOLITICAL_SPORT_PATTERNS), re.I)


def is_geopolitical(title: str, summary: str = "") -> bool:
    """Spor/magazin/yaşam tarzı/yerel haberleri eler (Türkçe)."""
    title = title or ""
    summary = summary or ""
    text = f"{title} {summary}".strip()
    if not text:
        return False
    if _GEOSPORT_RE.search(text):
        return True
    if _BLOCK_RE.search(title):
        return False
    if _BLOCK_RE.search(summary):
        return bool(_ALLOW_RE.search(text))
    if _ALLOW_RE.search(text):
        return True
    return True


def domain_of(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        if host.startswith("www."):
            host = host[4:]
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
    for key in ("media_content", "media_thumbnail"):
        for m in entry.get(key, []) or []:
            u = m.get("url")
            if u and u.lower().split("?")[0].endswith((".jpg", ".jpeg", ".png", ".webp")):
                return u
    for e in entry.get("enclosures", []) or []:
        if e.get("href") and str(e.get("type", "")).startswith("image"):
            return e["href"]
        if e.get("href", "").lower().split("?")[0].endswith((".jpg", ".jpeg", ".png", ".webp")):
            return e["href"]
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
    return hashlib.sha1((link or title).encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# HIDDEN + LLM SEÇİCİ
# ---------------------------------------------------------------------------


def load_hidden():
    if not HIDDEN.exists():
        return []
    try:
        data = json.loads(HIDDEN.read_text())
        if isinstance(data, dict):
            return data.get("items", []) or []
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def hidden_keys(items):
    ids, links = set(), set()
    for h in items:
        if h.get("id"):
            ids.add(h["id"])
        if h.get("link"):
            links.add(norm_link(h["link"]))
    return ids, links


def norm_link(url: str) -> str:
    try:
        p = urlparse(url or "")
        host = (p.netloc or "").lower()
        if host.startswith("www."):
            host = host[4:]
        path = (p.path or "").rstrip("/")
        return f"{host}{path}"
    except Exception:
        return (url or "").strip()


def load_llm_cache():
    if LLM_CACHE.exists():
        try:
            d = json.loads(LLM_CACHE.read_text())
            if isinstance(d, dict):
                return d
        except Exception:
            pass
    return {}


def save_llm_cache(cache):
    if len(cache) > 2500:
        for k in list(cache.keys())[:len(cache) - 2500]:
            cache.pop(k, None)
    try:
        LLM_CACHE.write_text(json.dumps(cache, ensure_ascii=False))
    except Exception:
        pass


def llm_score_batch(batch, examples):
    import urllib.request
    ex_txt = ""
    for ex in examples:
        ex_txt += f"- [{ex.get('source','?')}] {ex.get('title','')}\n"
    if not ex_txt:
        ex_txt = "(henüz örnek yok)\n"

    lines = ""
    for i, it in enumerate(batch):
        lines += f"{i+1}. [{it.get('source','?')}] {it.get('title','')} - {it.get('summary','')[:160]}\n"

    prompt = (
        "Sen Frontion News'in Türkçe jeopolitik haber akışının editörüsün. "
        "Frontion News jeopolitik, güvenlik, savunma, enerji, diplomasi, makroekonomi ve teknoloji-güç odaklı bir yayındır. "
        "Magazin, ünlü/sanatçı haberleri, spor, yaşam tarzı, tüketici haberleri, yerel olaylar, hava durumu, deprem-sorgulama haberleri, banka faiz/mevduat oranları, eğitim/atama, sağlık-rutin, kültür/arkeoloji, seyahat ve click-bait İSTENMEZ.\n"
        "Editör aşağıdaki haberleri ilgisiz olduğu için SİLDİ (magazin / ünlü / spor / yaşam tarzı / yerel / click-bait / tüketici). "
        "Bunları Frontion'un İSTEMEDİĞİ haberlerin NEGATİF örnekleri olarak kullan:\n"
        f"{ex_txt}\n"
        "ÖRNEK ELEME (bu tarz haberleri her zaman ELE):\n"
        "- 'Angelina Jolie'den Gazze sözleri' → ünlü haberi, ELE\n"
        "- 'Halil Ergün'den Kadir İnanır'ın mirasıyla ilgili sert çıkış' → magazin, ELE\n"
        "- 'deprem mi oldu? Az önce deprem nerede oldu?' → deprem sorgulama, ELE\n"
        "- 'En yüksek mevduat faizi hangi bankada?' → tüketici/banka oranı, ELE\n"
        "- '14 günlük yıllık izin tarihe karışıyor' → iç/mevzuat-tüketici, ELE\n"
        "- 'Bakıcı maliyetini azaltabilirsiniz' → yaşam tarzı, ELE\n"
        "- 'Jadeli azı dişi, antik Mayaların dişçilik ustalığını ortaya koyuyor' → arkeoloji/kültür, ELE\n"
        "- 'Süs için bölgeye getirilen çiçekler felaketi yaşattı' → yerel/ilginç ama jeopolitik değil, ELE\n"
        "Şimdi aşağıdaki aday haberleri değerlendir. TUT = gerçek jeopolitik / güvenlik / savunma / enerji / teknoloji-güç / diplomasi / makroekonomi / dış politika değeri olan haber. "
        "ELE = magazin, ünlü, eğlence, spor, yaşam tarzı, tüketici, yerel olay, kültür/arkeoloji, click-bait veya Frontion için ilgisiz.\n"
        "Şüphede kalırsan ELE.\n"
        "Adaylar:\n"
        f"{lines}\n"
        'Yalnızca aynı sırada bir JSON dizisi ile cevap ver, örn. ["TUT","ELE"]. Başka metin yazma.'
    )

    payload = json.dumps({
        "model": LLM_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0},
        "format": "json",
    }).encode("utf-8")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    endpoints = ("http://127.0.0.1:11434/api/generate",
                 "http://localhost:11434/api/generate")
    last_err = None
    resp = None
    for attempt in range(3):
        for endpoint in endpoints:
            try:
                req = urllib.request.Request(
                    endpoint,
                    data=payload,
                    headers={"Content-Type": "application/json"},
                )
                with opener.open(req, timeout=120) as r:
                    resp = json.loads(r.read().decode("utf-8"))
                last_err = None
                break
            except Exception as e:
                last_err = e
                resp = None
        if resp is not None:
            break
        time.sleep(2)
    if resp is None:
        raise last_err
    text = (resp.get("response") or "").strip()
    m = re.search(r"\[.*\]", text, re.S)
    if not m:
        return {}
    try:
        arr = json.loads(m.group(0))
    except Exception:
        return {}
    out = {}
    for i, dec in enumerate(arr):
        if i >= len(batch):
            break
        d = str(dec).strip().upper()
        out[batch[i]["id"]] = d.startswith("T") or d.startswith("K")
    return out


def llm_filter(items):
    if not LLM_ENABLED or not items:
        return 0, 0
    cache = load_llm_cache()
    hidden = load_hidden()
    examples = list(reversed(hidden))[:LLM_EXAMPLES]

    new = [it for it in items if it.get("id") not in cache][:LLM_MAX_NEW]
    if not new:
        return 0, 0

    scored = 0
    for i in range(0, len(new), LLM_BATCH):
        chunk = new[i:i + LLM_BATCH]
        try:
            decisions = llm_score_batch(chunk, examples)
        except Exception as e:
            print(f"  LLM seçici hatası (yeni item'lar korunuyor): {e}")
            decisions = {}
        for it in chunk:
            d = decisions.get(it["id"])
            if d is None:
                continue
            cache[it["id"]] = bool(d)
            scored += 1
    save_llm_cache(cache)
    return scored, 0


def apply_llm_drop(items):
    """FAIL-CLOSED: LLM kararı olmayan veya ELE diyen item'ları çıkarır."""
    if not LLM_ENABLED:
        return items, 0
    cache = load_llm_cache()
    kept, n = [], 0
    for it in items:
        if cache.get(it["id"]) is not True:
            # True değilse (False veya karar yok) → ele
            n += 1
            continue
        kept.append(it)
    return kept, n


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
    blocked = 0

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
                known = source_for_url(link)
                if not known and "news.google.com" in link:
                    known = (src["name"], src["tier"])
                if not known:
                    continue
                name, tier = known

                title = clean_title(e.get("title", ""))
                title = re.sub(r"\s+[-–]\s+(Anadolu Ajansı|AA|TRT|Hürriyet|Sabah|NTV|Habertürk|Dünya)\s*$", "", title, flags=re.I).strip()
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

                summary = one_sentence(raw_summary)

                if not is_geopolitical(title, summary):
                    blocked += 1
                    continue

                items.append({
                    "id": make_id(link, title),
                    "title": title,
                    "summary": summary,
                    "source": name,
                    "tier": tier,
                    "link": link,
                    "ts": int(dt.timestamp()),
                    "time": dt.isoformat(),
                    "image": entry_image(e),
                })

    return items, ok_feeds, bad_feeds, blocked


# ---------------------------------------------------------------------------
# THUMBNAILS
# ---------------------------------------------------------------------------


def download_thumb(url: str, key: str) -> str:
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
        if img.width > THUMB_WIDTH:
            h = int(img.height * (THUMB_WIDTH / img.width))
            img = img.resize((THUMB_WIDTH, h), Image.LANCZOS)
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
    print("Frontion News Türkçe Feed — toplayıcı başlıyor…")

    old = load_existing()
    old_items = {it["id"]: it for it in (old or {}).get("items", [])} if old else {}

    fresh, ok_feeds, bad_feeds, blocked = collect()
    print(f"  {len(fresh)} ham haber geldi ({len(ok_feeds)} feed OK, {len(bad_feeds)} feed hatalı)")
    print(f"  İçerik filtresi (regex): {blocked} spor/magazin/yaşam tarzı/yerel haber elendi")

    hid_items = load_hidden()
    hid_ids, hid_links = hidden_keys(hid_items)
    if hid_ids or hid_links:
        before = len(fresh)
        fresh = [it for it in fresh
                 if it["id"] not in hid_ids and norm_link(it["link"]) not in hid_links]
        print(f"  Silinenler filtresi: {before - len(fresh)} haber hidden-tr.json nedeniyle elendi")

    scored, _ = llm_filter(fresh)
    fresh, llm_dropped = apply_llm_drop(fresh)
    if scored or llm_dropped:
        print(f"  LLM seçici: {scored} yeni haber skorlandı, {llm_dropped} tanesi elendi")

    merged = {}
    for it in fresh:
        merged[it["id"]] = it

    for k, v in old_items.items():
        if k not in merged:
            if v.get("ts", 0) >= (datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)).timestamp():
                merged[k] = v

    items = sorted(merged.values(), key=lambda x: x.get("ts", 0), reverse=True)
    items = items[:MAX_ITEMS]

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
    print(f"  tr-feed.json yazıldı: {len(items)} haber, {n_img} görselli, {t1-t0:.1f}s")
    if bad_feeds:
        print("  Hatalı feed'ler:")
        for name, fu in bad_feeds:
            print(f"    - {name}: {fu}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
