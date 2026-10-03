#!/usr/bin/env python3
"""
Frontion Feed — yerel silme servisi.

Site feed.html'deki × butonu buraya POST eder; haber hidden.json'a yazılır
(kalıcı silme). Token yok, sadece yerel ağdan erişilebilir.

Çalıştırma:  python3 feed_delete_server.py
Endpoints:
  POST /hide   {"id","title","source","link","summary"}  -> hidden.json'a ekler
  GET  /hidden -> mevcut hidden listesini döner
  GET  /health -> durum
"""

import json
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
HIDDEN = ROOT / "hidden.json"
PORT = int(os.environ.get("FEED_DELETE_PORT", "8791"))


def load_hidden():
    if HIDDEN.exists():
        try:
            d = json.loads(HIDDEN.read_text())
            if isinstance(d, dict):
                d.setdefault("items", [])
                return d
        except Exception:
            pass
    return {"updated": "", "count": 0, "items": []}


def save_hidden(store):
    store["count"] = len(store.get("items", []))
    store["updated"] = datetime.now(timezone.utc).isoformat()
    tmp = HIDDEN.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(store, ensure_ascii=False, indent=2))
    tmp.replace(HIDDEN)


def norm_link(url):
    try:
        p = urlparse(url or "")
        host = (p.netloc or "").lower()
        if host.startswith("www."):
            host = host[4:]
        return f"{host}{(p.path or '').rstrip('/')}"
    except Exception:
        return (url or "").strip()


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            return self._json(200, {"ok": True, "hidden_count": load_hidden().get("count", 0)})
        if path == "/hidden":
            return self._json(200, load_hidden())
        return self._json(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/hide":
            return self._json(404, {"error": "not found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            return self._json(400, {"error": "bad json"})

        item_id = (data.get("id") or "").strip()
        link = (data.get("link") or "").strip()
        if not item_id and not link:
            return self._json(400, {"error": "id or link required"})

        store = load_hidden()
        items = store.get("items", [])
        nl = norm_link(link)

        # zaten varsa tekrar ekleme
        exists = any(
            (item_id and h.get("id") == item_id) or (nl and norm_link(h.get("link", "")) == nl)
            for h in items
        )
        if not exists:
            items.insert(0, {
                "id": item_id,
                "title": (data.get("title") or "")[:300],
                "summary": (data.get("summary") or "")[:400],
                "source": (data.get("source") or "")[:120],
                "link": link,
                "deletedAt": datetime.now(timezone.utc).isoformat(),
            })
            store["items"] = items
            save_hidden(store)

        return self._json(200, {"ok": True, "hidden_count": len(items), "already": exists})

    def log_message(self, fmt, *args):
        pass  # sessiz


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Feed delete service on http://localhost:{PORT}  (hidden: {HIDDEN})")
    srv.serve_forever()
