# -*- coding: utf-8 -*-
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
VID = "t8fOU8zfPVWFYN34BllH"
VAR = {
    "a_default": {"stability":0.50,"similarity_boost":0.75,"style":0.0,"use_speaker_boost":True},
    "b_stil":    {"stability":0.45,"similarity_boost":0.75,"style":0.35,"use_speaker_boost":True},
    "c_canli":   {"stability":0.35,"similarity_boost":0.80,"style":0.55,"use_speaker_boost":True},
}
for ad, vs in VAR.items():
    body = json.dumps({"text":METIN,"model_id":"eleven_multilingual_v2","voice_settings":vs}).encode()
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{VID}", data=body,
        headers={"xi-api-key":KEY,"Content-Type":"application/json","Accept":"audio/mpeg"})
    yol=f"{OUT}/deneme3-zangess-{ad}.mp3"
    try:
        with urllib.request.urlopen(req, timeout=120) as r, open(yol,"wb") as f: f.write(r.read())
        print("OK",ad,os.path.getsize(yol))
    except Exception as e:
        print("HATA",ad,e)
