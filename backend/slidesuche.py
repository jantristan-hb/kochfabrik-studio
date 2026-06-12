"""Slide-Suche — Vektor-Suche über Korpus + PNG-Vorschau + PPTX-Bundle.

Strikt unabhängig vom /api/angebot/*-Pfad: eigener Router, eigener
Prefix /api/slidesuche, eigene Engine-Helper. Berührt weder app.py
(außer 2 include-Zeilen) noch assemble.py / Angebotsgenerator.

Routes:
- POST /api/slidesuche/search        — query → top-5 (deck,page,preview)
- GET  /api/slidesuche/preview/{deck}/{page}.png  — PNG aus cache/<deck>/preview
- POST /api/slidesuche/download      — 1-PPTX-Bundle aus Liste {deck,page}

Vorschau-PNGs werden vorab via engine/tooling/render_previews.py erzeugt
und liegen unter cache/<deck>/preview/p<page>.png im Coolify-Volume.
"""
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
from typing import List, Dict, Optional

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel


router = APIRouter(prefix="/api/slidesuche", tags=["slidesuche"])

# Engine-Pfade analog backend/app.py — späte Imports, damit Module ohne
# Engine nicht crashen (graceful — Routen geben dann 503 statt 500).
# Engine liegt repo-intern unter engine/ (subtree, ADR-002).
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENG = os.path.join(_ROOT, "engine", "scripts")
_CACHE = os.path.join(os.path.dirname(_ENG), "data", "cache")
_SPIKE = os.path.join(os.path.dirname(_ENG), "spike-pptxgenjs")

# Engine-Module lazy laden (gleich wie app.py macht's)
_engine_ready = False
_embed = None
_DEDUP = None                              # {"redirect": {...}, "kept": [...]}


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


def _load_dedup():
    """Lädt dedup_manifest.json (vom render+dedup-Pipeline lokal
    erzeugt, liegt repo-intern unter engine/data/). Graceful: wenn nicht
    da, läuft die Suche ohne Dedup (alle PNGs werden gerendert/served
    falls vorhanden)."""
    global _DEDUP
    if _DEDUP is not None:
        return _DEDUP
    path = os.path.join(os.path.dirname(_ENG), "data",
                        "dedup_manifest.json")
    try:
        with open(path, encoding="utf-8") as f:
            _DEDUP = json.load(f)
    except Exception:
        _DEDUP = {"redirect": {}, "kept": []}
    return _DEDUP


def _dedup_key(deck, page):
    """Mappt (deck, page) auf den Repräsentanten gemäß manifest;
    Identity wenn kein Eintrag (z.B. lokal ohne dedup-Run)."""
    d = _load_dedup()
    k = f"{deck}::{int(page)}"
    repr_k = d.get("redirect", {}).get(k, k)
    deck2, _, page2 = repr_k.partition("::")
    try:
        return deck2, int(page2)
    except Exception:
        return deck, int(page)


def _bundle():
    """Bundle über die gemeinsame Schicht (US-055/ADR-003). pg_shim ist
    für assemble.py-spezifische LIMIT-8-Queries gebaut (kein LIMIT %s,
    kein module_label); unsere ANN nutzt deshalb direkt bundle.load()/
    bundle.rank() — dieselbe einzige Ladestelle, kein eigener Load mehr.
    Cache + Normalisierung liegen in `bundle`."""
    import bundle as _b
    return _b.load()


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

    # ANN über die gemeinsame Bundle-Schicht (US-055/ADR-003) — gleiche
    # EINE Ladestelle wie pg_shim, Ranking bit-identisch (bundle.rank).
    # 4x oversampling — nach Dedup-Redirect + PNG-Existenz-Filter
    # bleiben so genug Treffer für `limit`.
    import bundle as _b
    b = _bundle()
    qv = _b.normalize_query(vec)
    over = limit * 4
    order = _b.rank(qv, None, over)
    rows = [(str(b["deck"][i]),
             int(b["page"][i]),
             str(b["module_label"][i])) for i in order]

    base = "/api/slidesuche/preview"
    out = []
    seen = set()
    for deck, page, label in rows:
        # 1) Auf Repräsentanten umlenken (Dubletten kollabieren)
        rd, rp = _dedup_key(str(deck), int(page))
        key = (rd, rp)
        if key in seen:
            continue
        # 2) PNG muss tatsächlich existieren (Server-Volume hat nur
        #    Repräsentanten — sonst 404 in der Vorschau)
        png = os.path.join(_CACHE, rd, "preview", f"p{rp}.png")
        if not os.path.isfile(png):
            continue
        seen.add(key)
        out.append({
            "deck": rd,
            "page": rp,
            "headline": str(label or ""),
            "preview_url": f"{base}/{rd}/{rp}.png",
        })
        if len(out) >= limit:
            break
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


# ---------- GET /preview-notext/{deck}/{page}.png ----------
# Textfreie Renders (US-069 erzeugt sie nach cache/<deck>/preview_notext/)
# als Overlay-Untergrund für den Editor (US-070, FEATURE-014). Identische
# Auth-/Traversal-/Cache-Semantik wie /preview, nur anderes Unterverzeichnis.


@router.get("/preview-notext/{deck}/{page}.png")
def preview_notext(deck: str, page: int, request: Request):
    g = _auth_or_401(request)
    if g:
        return g
    if not _SAFE.match(deck) or page < 1 or page > 9999:
        return JSONResponse({"error": "ungültiger Pfad"},
                            status_code=400)
    path = os.path.join(_CACHE, deck, "preview_notext", f"p{page}.png")
    if not os.path.isfile(path):
        return JSONResponse({"error": "preview fehlt"},
                            status_code=404)
    return FileResponse(path, media_type="image/png",
                        headers={"Cache-Control":
                                 "public, max-age=86400"})


# ---------- POST /download ----------

class SlideRef(BaseModel):
    deck: str
    page: int
    # Text-Overrides (#66): seq-Index -> neuer Text ("\n" = Zeilen,
    # leer = Element entfernen). Optional, Default = verbatim.
    overrides: Optional[Dict[str, str]] = None
    # Bild-Overrides (#71): seq-Index -> Data-URL. Ersetzt die src des
    # image-Elements an idx durch ein ins Bundle gelegtes Override-Bild.
    image_overrides: Optional[Dict[str, str]] = None


class DownloadReq(BaseModel):
    slides: List[SlideRef]


# Data-URL-Limit je Bild (Pitfall 3 — 413 statt Riesen-PPTX).
_MAX_IMG_BYTES = 8 * 1024 * 1024


class _ImgErr(Exception):
    """Override-Bild ungültig (Klartext) + HTTP-Status (400/413)."""
    def __init__(self, msg: str, status: int):
        super().__init__(msg)
        self.status = status


def _decode_image_override(data_url: str) -> bytes:
    """Data-URL → rohe Bild-Bytes. Validiert PNG/JPEG-Magic + 8-MB-Limit.
    _ImgErr(400) = kein gültiges Bild, _ImgErr(413) = zu groß."""
    s = (data_url or "").strip()
    b64 = s.split(",", 1)[1] if s.startswith("data:") and "," in s else s
    try:
        raw = base64.b64decode(b64, validate=True)
    except Exception:
        raise _ImgErr("Bild-Override: ungültige Data-URL", 400)
    if len(raw) > _MAX_IMG_BYTES:
        raise _ImgErr("Bild-Override > 8 MB", 413)
    is_png = raw[:8] == b"\x89PNG\r\n\x1a\n"
    is_jpeg = raw[:3] == b"\xff\xd8\xff"
    if not (is_png or is_jpeg):
        raise _ImgErr("Bild-Override: kein PNG/JPEG", 400)
    return raw


def _apply_image_overrides(seq, ov, shared, slot):
    """Bild-Overrides (#71) auf eine Element-Sequenz anwenden: Override-
    Bytes nach shared/_overrides/s<slot>_<idx>.png schreiben (NIE in den
    READ-ONLY-Cache/Symlink — Symlink-Falle), src des t=="image"-Elements
    an idx auf den Bundle-relativen Pfad setzen. Frische Element-Kopie wie
    _apply_overrides — die geladene Cache-Struktur bleibt unberührt."""
    ovdir = os.path.join(shared, "_overrides")
    os.makedirs(ovdir, exist_ok=True)
    out = []
    for idx, e in enumerate(seq):
        new = ov.get(str(idx))
        if new is None or e.get("t") != "image":
            out.append(e)
            continue
        raw = _decode_image_override(new)          # wirft _ImgErr (400/413)
        rel = f"s{slot}_{idx}.png"
        with open(os.path.join(ovdir, rel), "wb") as fh:
            fh.write(raw)
        out.append(dict(e, src="_overrides/" + rel))
    return out


def _apply_overrides(seq, ov):
    """Text-Overrides (#66) auf eine Element-Sequenz anwenden: Zeilen
    des Elements ersetzen (Stil der ersten Original-Zeile erben),
    leerer Override entfernt das Element. Nicht-Text bleibt unberührt."""
    out = []
    for idx, e in enumerate(seq):
        new = ov.get(str(idx))
        if new is None or e.get("t") != "text" or not e.get("lines"):
            out.append(e)
            continue
        if not new.strip():
            continue                          # leer = Element entfernen
        st = {k: e["lines"][0][k]
              for k in ("size", "color", "weight", "italic")
              if k in e["lines"][0]}
        out.append(dict(e, lines=[st | {"txt": ln}
                                  for ln in new.split("\n")
                                  if ln.strip()]))
    return out


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
        if s.overrides:
            seq = _apply_overrides(seq, s.overrides)
        if s.image_overrides:
            try:
                seq = _apply_image_overrides(seq, s.image_overrides,
                                             shared, i)
            except _ImgErr as e:
                return JSONResponse({"error": str(e)},
                                    status_code=e.status)
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
