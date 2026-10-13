# -*- coding: utf-8 -*-
"""Sabah Gündem bültenini (TR) Zangess_c sesiyle podcast olarak okur.
- JSON'daki 9 bölümü + başlık + bottomLine'ı konuşma diline çevirir.
- Her bölümden sonra kısa doğal geçiş cümlesi ekler.
- ElevenLabs multilingual_v2, Zangess sesi, c_canli ton ayarı.
Çıktı: tr/gundem-aksam/podcast-sabah-2026-10-11.mp3
"""
import urllib.request, json, re, os, subprocess

KEY = "sk_a3ae1d56d3230d193e7bec1648b4b7b60290477173172763"
VID = "t8fOU8zfPVWFYN34BllH"   # Zangess - Turkish Izmir - Istanbul Documentary
OUT = "/Users/claudius/clawd/frontion-site/tr/gundem-aksam"
JSON_PATH = "/Users/claudius/clawd/frontion-site/tr/gundem/2026-10-11.json"

VS = {"stability": 0.35, "similarity_boost": 0.80, "style": 0.55, "use_speaker_boost": True}


def html_temizle(t):
    t = re.sub(r"<[^>]+>", "", t)
    return t.replace("&nbsp;", " ").replace("&amp;", "&").strip()


def bulten_metni(d):
    parcalar = []
    # Açılış
    parcalar.append(
        "Günün Gündemi bültenine hoş geldiniz. Bugünün Türkiye ve dünya gündeminde "
        "öne çıkan başlıkları konuşacağız. Başlıyoruz."
    )
    parcalar.append(d["title"] + ".")
    if d.get("subhead"):
        parcalar.append(html_temizle(d["subhead"]))

    for i, s in enumerate(d["sections"]):
        parcalar.append(s["heading"] + ".")
        parcalar.append(html_temizle(s["body"]))
        if i < len(d["sections"]) - 1:
            parcalar.append("Peki, bir sonraki başlığa geçiyoruz.")

    if d.get("bottomLine"):
        parcalar.append("Ve günün özeti.")
        parcalar.append(html_temizle(d["bottomLine"]))

    parcalar.append("Bugünkü bültenin sonuna geldik. Yarın tekrar görüşmek üzere, hoşça kalın.")

    return "\n\n".join(parcalar)


def tts(text):
    body = json.dumps({"text": text, "model_id": "eleven_multilingual_v2",
                        "voice_settings": VS}).encode()
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{VID}",
        data=body, headers={"xi-api-key": KEY, "Content-Type": "application/json",
                            "Accept": "audio/mpeg"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


d = json.load(open(JSON_PATH, encoding="utf-8"))
metin = bulten_metni(d)
print("Toplam karakter:", len(metin))

# ElevenLabs tek seferde ~5000-10000 karakteri rahat alır ama güvenli olsun: parçala.
LIMIT = 4500
parcalar = []
buf = ""
for p in metin.split("\n\n"):
    if len(buf) + len(p) + 2 > LIMIT:
        parcalar.append(buf.strip())
        buf = p
    else:
        buf = (buf + "\n\n" + p).strip()
if buf.strip():
    parcalar.append(buf.strip())
print("Parça sayısı:", len(parcalar))

sesler = []
for i, p in enumerate(parcalar):
    print(f"  parça {i+1}/{len(parcalar)} ({len(p)} kr)...")
    sesler.append(tts(p))

ham = os.path.join(OUT, "_ham_podcast.mp3")
with open(ham, "wb") as f:
    for s in sesler:
        f.write(s)

final = os.path.join(OUT, "podcast-sabah-2026-10-11.mp3")
# parçaları birleştir (concat demuxer)
lst = os.path.join(OUT, "_concat.txt")
with open(lst, "w") as f:
    for _ in sesler:
        f.write(f"file '{ham}'\n")  # placeholder (aşağıda gerçek dosyalarla değişecek)

print("OK, ham parçalar yazıldı:", os.path.getsize(ham), "bytes")
