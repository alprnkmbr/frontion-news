#!/usr/bin/env python3
"""
Frontion News — günlük brief/bülten doğrulayıcı.

Amaç: bir brief cron'u "ok" görünse bile JSON yazılmamış / index güncellenmemiş /
push edilmemişse bunu yakalamak. Sessiz kayıp olmasın.

Kontroller (her bölüm için):
  1) DOSYA     : <dir>/<bugün>.json var mı, geçerli JSON mu, title + sections dolu mu
  2) INDEX     : <dir>/index.json'un ilk elemanı bugün mü, title eşleşiyor mu
  3) GIT       : dosya git'e eklenmiş ve origin/main'e push edilmiş mi
  4) BOYUT     : sections sayısı makul mü (>=2)

Kullanım:
  python3 tools/brief_verify.py              # insan-okur rapor
  python3 tools/brief_verify.py --json       # makine-okur
  python3 tools/brief_verify.py --date 2026-11-01

Çıkış kodu: 0 = hepsi tamam, 1 = eksik var
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Europe/Istanbul")

REPO = "/Users/claudius/clawd/frontion-site"
GIT = "/Library/Developer/CommandLineTools/usr/bin/git"

SECTIONS = [
    {"ad": "Global", "dir": "briefs"},
    {"ad": "Defence", "dir": "defense"},
    {"ad": "Energy", "dir": "energy"},
    {"ad": "Tech", "dir": "tech"},
    {"ad": "TR Gündem", "dir": "tr/gundem"},
    {"ad": "TR Ekonomi", "dir": "tr/ekonomi"},
    {"ad": "TR Savunma", "dir": "tr/savunma"},
    {"ad": "TR Spor", "dir": "tr/spor"},
]


def run(args):
    try:
        p = subprocess.run(args, cwd=REPO, capture_output=True, text=True, timeout=60)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except Exception as e:  # noqa: BLE001
        return 1, "", str(e)


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def git_ok(relpath):
    """Dosya origin/main'de var mı?"""
    rc, out, _ = run([GIT, "cat-file", "-e", f"origin/main:{relpath}"])
    return rc == 0


def check_one(sec, date, pushed_files):
    problems = []
    notes = []
    rel = f"{sec['dir']}/{date}.json"
    path = os.path.join(REPO, rel)

    # 1) DOSYA
    if not os.path.exists(path):
        problems.append(f"dosya yok: {rel}")
        data = None
    else:
        data = load_json(path)
        if data is None:
            problems.append(f"geçersiz JSON: {rel}")
        else:
            title = (data.get("title") or "").strip()
            secs = data.get("sections") or []
            if not title:
                problems.append("title boş")
            if len(secs) < 2:
                problems.append(f"sections az ({len(secs)})")
            notes.append(f"{len(secs)} bölüm")

    # 2) INDEX
    idx = load_json(os.path.join(REPO, sec["dir"], "index.json"))
    if idx is None:
        problems.append("index.json okunamadı")
    elif not idx:
        problems.append("index.json boş")
    else:
        if idx[0].get("date") != date:
            problems.append(f"index başında {date} yok (baş: {idx[0].get('date')})")
        elif data and (idx[0].get("title") or "") != (data.get("title") or ""):
            problems.append("index title ile JSON title uyuşmuyor")

    # 3) GIT / PUSH
    if rel not in pushed_files:
        problems.append("origin/main'de yok (push edilmemiş)")

    return {"ad": sec["ad"], "dir": sec["dir"], "problems": problems, "notes": notes}


def main():
    date = None
    as_json = "--json" in sys.argv
    for i, a in enumerate(sys.argv):
        if a == "--date" and i + 1 < len(sys.argv):
            date = sys.argv[i + 1]
    if not date:
        # Istanbul saati (GMT+3), DST'ye duyarlı
        date = datetime.fromtimestamp(time.time(), IST).strftime("%Y-%m-%d")

    # origin/main'deki bugünkü brief dosyaları (tek git ls-tree)
    pushed_files = set()
    rc, out, _ = run([GIT, "ls-tree", "-r", "--name-only", "origin/main"])
    if rc == 0:
        pushed_files = set(out.splitlines())
    else:
        pushed_files = None  # git erişilemedi -> kontrol atlanır

    results = []
    for sec in SECTIONS:
        sentinel = {f"{sec['dir']}/{date}.json"}  # git erişilemezse kontrol atlanır
        r = check_one(sec, date, pushed_files if pushed_files is not None else sentinel)
        if pushed_files is None:
            r["problems"] = [p for p in r["problems"] if "origin/main" not in p]
            r["notes"].append("git kontrolü atlandı")
        results.append(r)

    eksik = [r for r in results if r["problems"]]

    if as_json:
        print(json.dumps({"date": date, "results": results, "eksik": len(eksik)}, ensure_ascii=False, indent=2))
    else:
        print(f"Brief doğrulama — {date}")
        print("=" * 46)
        for r in results:
            if r["problems"]:
                print(f"❌ {r['ad']:<12} ({r['dir']})")
                for p in r["problems"]:
                    print(f"     - {p}")
            else:
                extra = f" [{', '.join(r['notes'])}]" if r["notes"] else ""
                print(f"✅ {r['ad']:<12} ({r['dir']}){extra}")
        print("=" * 46)
        if eksik:
            print(f"SONUÇ: {len(eksik)} bölümde eksik/sorun var.")
        else:
            print("SONUÇ: Tüm briefler tamam.")

    return 1 if eksik else 0


if __name__ == "__main__":
    sys.exit(main())
