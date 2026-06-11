"""Designer-Router (US-061) — Slide-Designer-Vorschläge.

POST /api/designer/suggest nimmt drei Input-Zweige (multipart-PDF |
{offer_id} | {offer}-md), parst das Angebot über die Engine-Kette
(parse_header/parse_offer_dishes, Muster praes_from_angebot) zu
{kunde, datum, gaenge[]} und liefert das Response-Schema aus
FEATURE-011 §3. Das Ranking (groups[]) ist hier noch ein Stub ([]) —
es kommt in US-062.

Engine-Glue aus backend.engine_glue (kein Import auf app.py — kein
Import-Zyklus). Graceful: fehlt Engine/Korpus → 503 Klartext, kein
500. Korpus wird über bundle.available() ermittelt (EINE Bundle-
Schicht, ADR-003) — der Router lädt den Korpus nie selbst.
"""
import os

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..engine_glue import (ENGINE_OK, ENGINE_ERR, _ENG, _ang2md,
                           _gemini_key, _owner)

router = APIRouter()


def _korpus_ok() -> bool:
    """Korpus vorhanden = lesbar über die zentrale Bundle-Schicht
    (bundle.available()). Eigene Lade-/Norm-Logik ist verboten
    (ADR-003)."""
    if not ENGINE_OK:
        return False
    try:
        import bundle                        # engine/scripts auf sys.path
        return bool(bundle.available())
    except Exception:
        return False


class SuggestReq(BaseModel):
    offer: str | None = None                 # Angebotstext (md/Plain)
    offer_id: int | None = None              # gespeichertes Angebot (DB)


def _guard():
    """Graceful Degradation: Engine fehlt → 503 Klartext, kein Crash."""
    if not ENGINE_OK:
        return JSONResponse(
            {"error": "Engine nicht verfügbar: " + (ENGINE_ERR or "")},
            status_code=503)
    if not _korpus_ok():
        return JSONResponse(
            {"error": "Korpus in diesem Deploy nicht verfügbar — "
             "Infra-Schritt."}, status_code=503)
    return None


def _parse_offer_md(offer_md: str) -> dict:
    """Offer-md → {kunde, datum, gaenge[]} via Engine-Parser
    (parse_header + parse_offer_dishes). Schreibt das md in eine
    Tempdatei (Parser nehmen Pfade, kein String — Muster
    praesentation._assemble_md)."""
    import tempfile

    import assemble                          # engine/scripts auf sys.path
    import compose_offer
    src = os.path.join(tempfile.mkdtemp(prefix="designer_"), "offer.md")
    with open(src, "w", encoding="utf-8") as fh:
        fh.write(offer_md)
    kunde, datum = assemble.parse_header(src, offer="Angebot")
    dishes = compose_offer.parse_offer_dishes(src, offer="Angebot")
    gaenge = [{"label": course,
               "dishes": [{"name": n, "desc": de} for n, de in items]}
              for course, items in dishes]
    return {"kunde": kunde, "datum": datum, "gaenge": gaenge}


async def _load_offer_md(owner: str, offer_id: int) -> str | None:
    """Gespeichertes Angebot laden (Muster /api/angebot/{offer_id}) und
    über _ang2md in Offer-md überführen (Wiederverwendung der Kette aus
    engine_glue). None = nicht gefunden."""
    from .. import db as _db
    if not await _db.ping():
        return None
    from ..store import get_offer_full
    full = await get_offer_full(owner, offer_id)
    if full is None:
        return None
    return _ang2md(full["angebot"])


def _build_response(offer: dict) -> dict:
    """Response-Schema FEATURE-011 §3. groups[] = Stub (US-061);
    das Ranking pro Gang + Pflicht-Gruppe liefert US-062."""
    return {"offer": offer, "groups": []}


@router.get("/api/designer/health")
def designer_health():
    return {"engine": ENGINE_OK, "korpus": _korpus_ok(),
            "embed": bool(_gemini_key())}


@router.post("/api/designer/suggest")
async def designer_suggest(request: Request):
    """Drei Input-Zweige: multipart-PDF | {offer_id} | {offer}-md →
    Response-Schema. Ranking-Stub (groups: []) bis US-062."""
    owner = _owner(request)
    if not owner:
        return JSONResponse({"error": "auth"}, status_code=401)
    g = _guard()
    if g:
        return g

    ctype = request.headers.get("content-type", "")

    # Zweig 1: multipart-PDF (Validierung exakt wie from-pdf).
    if ctype.startswith("multipart/form-data"):
        form = await request.form()
        up = form.get("file")
        if not isinstance(up, UploadFile):
            return JSONResponse({"error": "kein PDF im Upload"},
                                status_code=400)
        raw = await up.read()
        if not raw or raw[:4] != b"%PDF":
            return JSONResponse({"error": "Keine gültige PDF-Datei"},
                                status_code=400)
        if len(raw) > 25 * 1024 * 1024:
            return JSONResponse({"error": "PDF zu groß (>25 MB)"},
                                status_code=400)
        import tempfile
        src = os.path.join(tempfile.mkdtemp(prefix="designer_"),
                           "offer.pdf")
        with open(src, "wb") as fh:
            fh.write(raw)
        try:
            import assemble
            import compose_offer
            kunde, datum = assemble.parse_header(src)
            dishes = compose_offer.parse_offer_dishes(src)
            gaenge = [{"label": c,
                       "dishes": [{"name": n, "desc": de}
                                  for n, de in items]}
                      for c, items in dishes]
            offer = {"kunde": kunde, "datum": datum, "gaenge": gaenge}
        except Exception as e:                                      # noqa
            return JSONResponse({"error": "Parsing: " + str(e)[:200]},
                                status_code=502)
        return _build_response(offer)

    # Zweig 2/3: JSON-Body ({offer_id} ODER {offer}).
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "ungültiger Body"},
                            status_code=400)
    try:
        req = SuggestReq(**body)
    except Exception:
        return JSONResponse({"error": "ungültiger Body"},
                            status_code=422)

    if req.offer_id is not None:
        try:
            md = await _load_offer_md(owner, req.offer_id)
        except Exception as e:                                      # noqa
            return JSONResponse({"error": str(e)[:200]},
                                status_code=503)
        if md is None:
            return JSONResponse({"error": "Angebot nicht gefunden"},
                                status_code=404)
    elif req.offer and req.offer.strip():
        md = req.offer
    else:
        return JSONResponse(
            {"error": "weder PDF noch offer_id noch offer übergeben"},
            status_code=400)

    try:
        offer = _parse_offer_md(md)
    except Exception as e:                                          # noqa
        return JSONResponse({"error": "Parsing: " + str(e)[:200]},
                            status_code=502)
    return _build_response(offer)
