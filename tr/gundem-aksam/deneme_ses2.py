# -*- coding: utf-8 -*-
"""ElevenLabs TR ses denemesi — 2. tur adaylar."""
import urllib.request, json, os

KEY = "sk_a3ae1d56d3230d193e7bec1648b4b7b60290477173172763"
OUT = "/Users/claudius/clawd/frontion-site/tr/gundem-aksam"

METIN = (
    "Günün Özeti bültenimize hoş geldiniz. Ben Alperen; bugünün Türkiye ve dünya "
    "gündeminde öne çıkan başlıkları, lafı dolandırmadan, konuşarak geçeceğiz. "
    "Şimdi, Riyad'daki havalimanına yapılan saldırıyla başlayalım. Şunu peşinen "
    "söyleyeyim: Bu, atlanacak bir haber değil. Ölü sayısı on ikiye çıkmış, üç yüz "
    "dokuz yaralı var. Peki bu neden önemli? İşin özü şu: bir uluslararası "
    "havalimanının hedef alınması, artık işin askeri hedefler çerçevesinden çıkıp "
    "sivil altyapıya taşındığını gösteriyor."
)

ADAYLAR = {
    "tayfun":  "txkSpx5Cihj3VfByTZEA",   # Narrator
    "hasanyasin":"tILIOdKERNNbBHVEXk7I", # Warm Turkish Narrator
    "mehmet":  "yZbm7j1CIEKx6ENZw770",   # Warm tone
    "emir":    "Zf5d5NL8Ff09kdon4VVc",   # Confident, Friendly & Calm
    "basar":   "ezCWV7MZgiXVJgA0uLHP",   # Deep, Natural
    "umit":    "wnYuT1gfa3HKzvHKVOz3",   # Cinematic Narrator
    "rifat":   "fimU5maT4kiGO5BNA0CQ",   # Powerful & Deep
    "huseyin": "CGfZwekugETum6vPelES",   # Calm, Warm, Clear
}

for ad, vid in ADAYLAR.items():
    body = json.dumps({
        "text": METIN,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.45, "similarity_boost": 0.75,
                            "style": 0.35, "use_speaker_boost": True},
    }).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{vid}",
        data=body,
        headers={"xi-api-key": KEY, "Content-Type": "application/json",
                 "Accept": "audio/mpeg"},
    )
    yol = f"{OUT}/deneme2-{ad}.mp3"
    try:
        with urllib.request.urlopen(req, timeout=120) as r, open(yol, "wb") as f:
            f.write(r.read())
        print("OK", ad, os.path.getsize(yol), "bytes")
    except Exception as e:
        print("HATA", ad, e)
