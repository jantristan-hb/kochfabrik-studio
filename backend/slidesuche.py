"""Slide-Suche — Vektor-Suche über Korpus + PNG-Vorschau + PPTX-Bundle.

Strikt unabhängig vom /api/angebot/*-Pfad: eigener Router, eigener
Prefix /api/slidesuche, eigene Engine-Helper. Berührt weder app.py
(außer 2 include-Zeilen) noch assemble.py / Angebotsgenerator.

Routes:
- POST /api/slidesuche/search        — query → top-5 (deck,page,preview)
- GET  /api/slidesuche/preview/{deck}/{page}.png  — PNG aus cache/<deck>/preview
- POST /api/slidesuche/download      — 1-PPTX-Bundle aus Liste {deck,page}

Vorschau-PNGs werden vorab via phase0/scripts/render_previews.py erzeugt
und liegen unter cache/<deck>/preview/p<page>.png im Coolify-Volume.
"""
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
from typing import List

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel


router = APIRouter(prefix="/api/slidesuche", tags=["slidesuche"])

# Engine-Pfade analog backend/app.py — späte Imports, damit Module ohne
# Engine nicht crashen (graceful — Routen geben dann 503 statt 500).
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_VEND = os.path.join(_ROOT, "engine", "phase0", "scripts")
_SIB = os.path.join(os.path.dirname(_ROOT), "pptxgenerator_v2",
                    "phase0", "scripts")
_ENG = _VEND if os.path.isdir(_VEND) else _SIB
_CACHE = os.path.join(os.path.dirname(_ENG), "data", "cache")
_SPIKE = os.path.join(os.path.dirname(_ENG), "spike-pptxgenjs")

# Engine-Module lazy laden (gleich wie app.py macht's)
_engine_ready = False
_embed = None


def _ensure_engine():
    global _engine_ready, _embed
    if _engine_ready:
        return True
    if not os.path.isdir(_ENG):
        return False
    try:
        if _ENG not in sys.path:
            sys.path.insert(0, _ENG)
        from compose_offer import embed as _e                     # noqa
        _embed = _e
        _engine_ready = True
        return True
    except Exception:
        return False


def _db_connect():
    """Echte Postgres falls verfügbar, sonst pg_shim (Container)."""
    try:
        import psycopg2
        from compose_offer import DSN                             # noqa
        return psycopg2.connect(**DSN)
    except Exception:
        if _ENG not in sys.path:
            sys.path.insert(0, _ENG)
        import pg_shim                                            # noqa
        return pg_shim.connect()


def _auth_or_401(request):
    """Eigene Auth-Hülle — späte Auflösung gegen Cycles."""
    from backend.app import _owner
    if not _owner(request):
        return JSONResponse({"error": "auth"}, status_code=401)
    return None


# ---------- POST /search ----------

class SearchReq(BaseModel):
    query: str
    limit: int = 5


@router.post("/search")
def search(r: SearchReq, request: Request):
    g = _auth_or_401(request)
    if g:
        return g
    if not _ensure_engine():
        return JSONResponse({"error": "Engine nicht verfügbar"},
                            status_code=503)
    q = (r.query or "").strip()
    if not q:
        return JSONResponse({"error": "leer"}, status_code=400)
    limit = max(1, min(int(r.limit or 5), 20))

    # Query embedden — 1 Gemini-Call
    try:
        vec = _embed([q])[0]
    except Exception as e:
        return JSONResponse({"error": "embed: " + str(e)[:160]},
                            status_code=502)
    qv = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"

    cx = _db_connect()
    cu = cx.cursor()
    # Union über menu_composition + static_slide, beide haben embedding-
    # Spalten? static_slide hat KEIN embedding (Cluster-frei). Daher
    # nur menu_composition für ANN; static_slide als ergänzende
    # Lexical-Treffer kann später kommen.
    cu.execute("SELECT deck, page, module_label "
               "FROM menu_composition "
               "ORDER BY embedding<=>%s::vector LIMIT %s", (qv, limit))
    rows = cu.fetchall()
    cu.close()
    cx.close()

    base = "/api/slidesuche/preview"
    out = []
    for deck, page, label in rows:
        out.append({
            "deck": str(deck),
            "page": int(page),
            "headline": str(label or ""),
            "preview_url": f"{base}/{deck}/{int(page)}.png",
        })
    return {"results": out, "query": q}


# ---------- GET /preview/{deck}/{page}.png ----------

_SAFE = re.compile(r"^[A-Za-z0-9._-]+$")


@router.get("/preview/{deck}/{page}.png")
def preview(deck: str, page: int, request: Request):
    g = _auth_or_401(request)
    if g:
        return g
    # Pfad-Traversal absichern
    if not _SAFE.match(deck) or page < 1 or page > 9999:
        return JSONResponse({"error": "ungültiger Pfad"},
                            status_code=400)
    path = os.path.join(_CACHE, deck, "preview", f"p{page}.png")
    if not os.path.isfile(path):
        return JSONResponse({"error": "preview fehlt"},
                            status_code=404)
    # Browser cachen lassen — Inhalt ist immutable pro deck+page
    return FileResponse(path, media_type="image/png",
                        headers={"Cache-Control":
                                 "public, max-age=86400"})


# ---------- POST /download ----------

class SlideRef(BaseModel):
    deck: str
    page: int


class DownloadReq(BaseModel):
    slides: List[SlideRef]


@router.post("/download")
def download(r: DownloadReq, request: Request):
    g = _auth_or_401(request)
    if g:
        return g
    if not r.slides:
        return JSONResponse({"error": "keine Slides"}, status_code=400)
    if len(r.slides) > 50:
        return JSONResponse({"error": "max 50 Slides pro Bundle"},
                            status_code=400)

    # Combined elements.json bauen — jede ausgewählte Slide bekommt
    # eine eigene Position (1..N). Assets per Symlink vom Cache.
    shared = tempfile.mkdtemp(prefix="slbundle_")
    combined = {}
    logos = {}
    meta = None
    seen_decks = set()

    for i, s in enumerate(r.slides, 1):
        if not _SAFE.match(s.deck) or s.page < 1:
            continue
        el_path = os.path.join(_CACHE, s.deck, "elements.json")
        if not os.path.isfile(el_path):
            continue
        el = json.load(open(el_path))
        seq = el.get(str(int(s.page)))
        if not seq:
            continue
        combined[str(i)] = seq
        if meta is None:
            meta = el.get("_meta", {"w_pt": 960, "h_pt": 540})
        # logos.json merge (deck-übergreifend additiv)
        lg = os.path.join(_CACHE, s.deck, "logos.json")
        if os.path.isfile(lg):
            try:
                logos.update(json.load(open(lg)))
            except Exception:
                pass
        # Asset-Symlink je Deck (einmalig)
        if s.deck not in seen_decks:
            os.makedirs(os.path.join(shared, s.deck), exist_ok=True)
            src_assets = os.path.join(_CACHE, s.deck, "assets")
            dst_assets = os.path.join(shared, s.deck, "assets")
            if os.path.isdir(src_assets) and not os.path.exists(dst_assets):
                os.symlink(src_assets, dst_assets)
            seen_decks.add(s.deck)

    if not combined:
        return JSONResponse({"error": "keine valide Slides"},
                            status_code=400)

    combined["_meta"] = dict(meta or {"w_pt": 960, "h_pt": 540},
                             deck="slidesuche-bundle",
                             notes={k: f"slide{k}" for k in combined})
    json.dump(combined, open(os.path.join(shared, "elements.json"), "w"))
    json.dump(logos, open(os.path.join(shared, "logos.json"), "w"))

    out = os.path.join(shared, "bundle.pptx")
    p = subprocess.run(["node", os.path.join(_SPIKE, "reconstruct.js"),
                        "elements.json", out], cwd=shared,
                       capture_output=True, text=True, timeout=300)
    if p.returncode != 0 or not os.path.isfile(out):
        return JSONResponse({"error": "render: "
                             + (p.stderr or p.stdout)[-200:]},
                            status_code=502)
    data = base64.b64encode(open(out, "rb").read()).decode()
    return {"pptx": "data:application/vnd.openxmlformats-officedocument"
            ".presentationml.presentation;base64," + data,
            "slides_in_bundle": len(combined) - 1}
