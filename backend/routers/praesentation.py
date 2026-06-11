"""Präsentations-Router (US-054) — Deck-Generierung.

1:1 aus app.py extrahiert: /api/praesentation/* (health/generate/
from-angebot/from-pdf) samt Helfer (_korpus_ok, _praes_guard,
_assemble_src, _assemble_md). Engine-Glue aus backend.engine_glue
(kein Import auf app.py — Pitfall 2). Verhalten unverändert."""
import base64
import os

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..engine_glue import ENGINE_OK, ENGINE_ERR, _ENG, _ang2md

router = APIRouter()


def _korpus_ok():
    """Präsentationsgenerator braucht den Multi-Deck-Korpus-Cache
    (~4.8 GB, NICHT vendorbar). Vorhanden = >5 Deck-Dirs im Cache."""
    if not ENGINE_OK:
        return False
    cdir = os.path.join(os.path.dirname(_ENG), "data", "cache")
    try:
        return sum(os.path.isdir(os.path.join(cdir, d))
                   for d in os.listdir(cdir)) > 5
    except Exception:
        return False


class PraesReq(BaseModel):
    offer: str                                  # Angebotstext (md/Plain)


class PraesAngebotReq(BaseModel):
    angebot: dict                               # Angebot aus Angebotsgen.


def _praes_guard():
    if not ENGINE_OK:
        return JSONResponse({"error": "Engine nicht verfügbar: "
                             + (ENGINE_ERR or "")}, status_code=503)
    if not _korpus_ok():
        return JSONResponse(
            {"error": "Korpus-Cache (~4,8 GB) in diesem Deploy nicht "
             "gemountet — Infra-Schritt (Coolify-Volume)."},
            status_code=503)
    return None


def _assemble_src(src: str):
    """Offer-Quelle (md ODER pdf) → assemble.py → PPTX (base64-data-URL)
    | (JSONResponse-Fehler). assemble.py branched per Extension."""
    import subprocess
    out = os.path.join(os.path.dirname(src), "deck.pptx")
    try:
        p = subprocess.run(
            ["python3", os.path.join(_ENG, "assemble.py"), src,
             "-o", out], cwd=_ENG,
            env=dict(os.environ, PPTX_PGSHIM="1"),
            capture_output=True, text=True, timeout=240)
        if not os.path.isfile(out):
            raise RuntimeError((p.stderr or p.stdout or "")[-260:])
        data = base64.b64encode(open(out, "rb").read()).decode()
    except Exception as e:
        return JSONResponse({"error": str(e)[:260]}, status_code=502)
    return {"pptx": "data:application/vnd.openxmlformats-officedocument"
            ".presentationml.presentation;base64," + data}


def _assemble_md(offer_md: str):
    import tempfile
    src = os.path.join(tempfile.mkdtemp(prefix="praes_"), "offer.md")
    open(src, "w").write(offer_md)
    return _assemble_src(src)


@router.get("/api/praesentation/health")
def praes_health():
    return {"engine": ENGINE_OK, "korpus": _korpus_ok(),
            "error": ENGINE_ERR}


@router.post("/api/praesentation/generate")
def praes_generate(r: PraesReq):
    g = _praes_guard()
    if g:
        return g
    if not r.offer.strip():
        return JSONResponse({"error": "leer"}, status_code=400)
    return _assemble_md(r.offer)


@router.post("/api/praesentation/from-angebot")
def praes_from_angebot(r: PraesAngebotReq):
    """Übernahme aus dem Angebotsgenerator: Angebot-JSON → Offer-md →
    Deck. Kein Hand-Paste mehr."""
    g = _praes_guard()
    if g:
        return g
    if not r.angebot:
        return JSONResponse({"error": "kein Angebot"}, status_code=400)
    try:
        md = _ang2md(r.angebot)
    except Exception as e:
        return JSONResponse({"error": "Konvertierung: "
                             + str(e)[:200]}, status_code=502)
    return _assemble_md(md)


@router.post("/api/praesentation/from-pdf")
async def praes_from_pdf(file: UploadFile = File(...)):
    """Angebots-PDF hochladen → KOCHfabrik-Deck. assemble.py parst
    PDFs nativ (Per-Gericht-Parser + Kategorie-Lock)."""
    g = _praes_guard()
    if g:
        return g
    import tempfile
    raw = await file.read()
    if not raw or raw[:4] != b"%PDF":
        return JSONResponse({"error": "Keine gültige PDF-Datei"},
                            status_code=400)
    if len(raw) > 25 * 1024 * 1024:
        return JSONResponse({"error": "PDF zu groß (>25 MB)"},
                            status_code=400)
    src = os.path.join(tempfile.mkdtemp(prefix="praes_"), "offer.pdf")
    open(src, "wb").write(raw)
    return _assemble_src(src)
