"""Designer-Router (US-061/062) — Slide-Designer-Vorschläge.

POST /api/designer/suggest nimmt drei Input-Zweige (multipart-PDF |
{offer_id} | {offer}-md), parst das Angebot über die Engine-Kette
(parse_header/parse_offer_dishes, Muster praes_from_angebot) zu
{kunde, datum, gaenge[]} und liefert das Response-Schema aus
FEATURE-011 §3.

US-062 — Ranking: pro Gang ein Gemini-Embed (1 Batch über alle Gänge,
wie assemble.py), dann je Gang Top-N Kandidaten über die zentrale
Bundle-Schicht (bundle.normalize_query + bundle.rank, k=N — NICHT die
assemble-Top-1-Logik umbauen, nur die Bausteine neu kombinieren,
Pitfall 2). Plus EINE Pflicht-Gruppe aus static_slide.json
(inclusion=pflicht, ohne COVER — gleiche Auswahl wie pg_shim), je
Kategorie eine kunden-stabile Frame-Instanz via compose_offer.pick_frame.

Engine-Glue aus backend.engine_glue (kein Import auf app.py — kein
Import-Zyklus). Graceful: fehlt Engine/Korpus → 503 Klartext, embed-
Fehler → 502. Rankings ausschließlich über bundle (ADR-003) — der
Router lädt den Korpus nie selbst.
"""
import json
import os
import re

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
# request.form() liefert Starlette-UploadFiles (Elternklasse); die
# FastAPI-Subklasse matcht dort NIE — Bug #60 (Upload immer 400).
from starlette.datastructures import UploadFile as StarletteUploadFile

from ..engine_glue import (ENGINE_OK, ENGINE_ERR, _ENG, _ang2md,
                           _gemini_key, _owner)

router = APIRouter()

# Default Top-N je Gang (FEATURE-011 §3).
_DEFAULT_N = 5
# Preview-Route der Slidesuche (Previews liegen vorab im Volume; fehlt
# eine, liefern wir den Kandidaten trotzdem — Pitfall 3, FE-Platzhalter).
_PREVIEW_BASE = "/api/slidesuche/preview"

# Engine-Funktionen (embed = Gemini-Batch, pick_frame = kunden-stabile
# Frame-Wahl) graceful binden — Modul-Attribute, damit Tests sie auf
# Modul-Ebene mocken können (Pitfall 1: NIE echte Gemini-Calls im Test).
embed = pick_frame = None
if ENGINE_OK:
    try:
        from compose_offer import embed, pick_frame             # noqa
    except Exception:                                           # noqa
        embed = pick_frame = None


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


def _gang_query(gang: dict) -> str:
    """Gang → Embed-Text (Label + Gerichte), gleiche Form wie
    compose_offer (`f"{course} — {body}"`)."""
    body = " ".join(
        f"{d['name']} {d.get('desc', '')}".strip()
        for d in gang.get("dishes", []))
    return f"{gang['label']} — {body}".strip(" —")


def _gang_groups(gaenge: list, n: int) -> list:
    """Je Gang Top-N Kandidaten über die zentrale Bundle-Schicht.
    EIN Embed-Batch über alle Gänge (wie assemble.py), dann je Gang
    bundle.rank(k=N). Embed-Fehler propagiert (→ 502 im Endpoint)."""
    if not gaenge:
        return []
    import bundle as _b
    texts = [_gang_query(g) for g in gaenge]
    vecs = embed(texts)                              # 1 Batch (Pitfall 2)
    b = _b.load()
    out = []
    for g, vec in zip(gaenge, vecs):
        qv = _b.normalize_query(vec)
        order = _b.rank(qv, None, n)                 # global, Top-N
        sims = b["_normemb"][order] @ qv
        candidates = []
        for j, i in enumerate(order):
            # Pitfall 3: Kandidat IMMER liefern (kein PNG-Existenz-Filter
            # — fehlt das Preview-PNG, zeigt das FE einen Platzhalter).
            candidates.append({
                "deck": str(b["deck"][i]),
                "page": int(b["page"][i]),
                "score": round(float(sims[j]), 4),
                "preview": f"{_PREVIEW_BASE}/{b['deck'][i]}"
                           f"/{int(b['page'][i])}.png",
                "label": str(b["module_label"][i] or ""),
            })
        out.append({"label": g["label"], "kind": "gang",
                    "candidates": candidates})
    return out


# Abschnitts-Enden der Speisen-Positionstabelle (Pauschal-Angebote, #62).
_SPEISEN_STOP = ("GETRÄNKE", "GETRAENKE", "EQUIPMENT", "PERSONAL",
                 "LOGISTIK", "SONSTIGES", "GESAMT", "AGB")


def _konzept_text(src: str) -> str:
    """Pauschal-Fallback (#62): Hat ein Angebot keine Menü-Gänge
    (Positions-/Pauschal-Layout wie „Streetfood 500 Pax"), liefert das
    hier den Query-Text für EINE Konzept-Vorschlagsgruppe:
    Cateringkonzept + Veranstaltungsanlass + Speisen-Positionstexte
    (erste Spalte, Preis-/Mengen-Spalten abgeschnitten)."""
    import subprocess
    txt = subprocess.run(["pdftotext", "-layout", src, "-"],
                         capture_output=True, text=True).stdout
    parts, in_speisen = [], False
    for raw in txt.splitlines():
        s = raw.strip()
        m = re.match(r"(?:Cateringkonzept|Veranstaltungsanlass):\s*(.+)", s)
        if m:
            parts.append(m.group(1).strip())
            continue
        if re.match(r"Speisen(?:\s{2,}|$)", s):
            in_speisen = True
            continue
        if in_speisen:
            if not s:
                continue
            if any(s.upper().startswith(x) for x in _SPEISEN_STOP):
                break
            cell = re.split(r"\s{2,}", s)[0].strip()
            if (cell and re.search(r"[A-Za-zÄÖÜäöüß]", cell)
                    and not re.match(r"^[\d.,\s]+$", cell)):
                parts.append(cell)
    seen, out = set(), []
    for x in parts:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return " ".join(out)[:600]


def _frame_groups(kunde: str):
    """Frame-Slots in DECK-Reihenfolge (skel_pos aus static_slide.json:
    COVER 0.0 / CREW 0.1 vor den Gängen; PERSONAL 0.76 / AUSSTATTUNG
    0.78 / WERTSCHÄTZUNG 0.89 / KONTAKT 1.0 danach). Je Kategorie ALLE
    Alternativen als Kandidaten — die kunden-stabile pick_frame-Wahl
    zuerst (Default), Rest in stabiler deck/page-Reihenfolge (#64)."""
    ss_path = os.path.join(os.path.dirname(_ENG), "data",
                           "static_slide.json")
    try:
        rows = json.load(open(ss_path, encoding="utf-8"))
    except Exception:                                           # noqa
        rows = []
    by_cat: dict = {}
    pos: dict = {}
    for r in rows:
        if r.get("inclusion") != "pflicht":
            continue
        by_cat.setdefault(r["category"], []).append(r)
        sp = r.get("skel_pos")
        pos[r["category"]] = 0.99 if sp is None else float(sp)
    before, after = [], []
    for cat in sorted(by_cat, key=lambda c: pos[c]):
        opts = sorted(by_cat[cat],
                      key=lambda r: (str(r["deck"]), int(r["page"])))
        chosen = pick_frame(cat, opts, kunde) if pick_frame else opts[0]
        if chosen in opts:
            ordered = [chosen] + [o for o in opts if o is not chosen]
        else:
            ordered = opts
        cands = [{
            "deck": str(o["deck"]),
            "page": int(o["page"]),
            "score": 1.0,                            # Pflicht = gesetzt
            "preview": f"{_PREVIEW_BASE}/{o['deck']}"
                       f"/{int(o['page'])}.png",
            "label": str(o.get("category") or ""),
        } for o in ordered]
        group = {"label": cat,
                 "kind": "cover" if cat == "COVER" else "pflicht",
                 "candidates": cands}
        (before if pos[cat] < 0.5 else after).append(group)
    return before, after


def _build_response(offer: dict, n: int = _DEFAULT_N) -> dict:
    """Response-Schema FEATURE-011 §3: offer + groups (je Gang eine
    gang-Gruppe Top-N, plus genau EINE pflicht-Gruppe)."""
    konzept = offer.pop("konzept", None)
    food = _gang_groups(offer.get("gaenge", []), n)
    if not food and konzept:
        # Pauschal-Angebot (#62): eine Konzept-Gruppe über dieselbe
        # Ranking-Maschinerie statt einer leeren Vorschlagsliste.
        food = _gang_groups(
            [{"label": "Catering-Konzept",
              "dishes": [{"name": konzept, "desc": ""}]}], n)
        for g in food:
            g["kind"] = "konzept"
    # Slots in DECK-Reihenfolge (#64): Cover/Crew → Food → Frame-Rest.
    before, after = _frame_groups(offer.get("kunde", ""))
    groups = before + food + after
    return {"offer": offer, "groups": groups}


@router.get("/api/designer/health")
def designer_health():
    return {"engine": ENGINE_OK, "korpus": _korpus_ok(),
            "embed": bool(_gemini_key())}


def _respond(offer: dict):
    """offer → Response (200) ODER 502, wenn der Gemini-Embed bzw. das
    Ranking fehlschlägt (EARS 3, gekürzte Meldung)."""
    try:
        return _build_response(offer)
    except Exception as e:                                          # noqa
        return JSONResponse({"error": "Embed/Ranking: " + str(e)[:200]},
                            status_code=502)


@router.post("/api/designer/suggest")
async def designer_suggest(request: Request):
    """Drei Input-Zweige: multipart-PDF | {offer_id} | {offer}-md →
    Response-Schema (offer + Top-N-Gang-Gruppen + Pflicht-Gruppe)."""
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
        if not isinstance(up, StarletteUploadFile):
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
            if not gaenge:
                # Pauschal-Angebot ohne Menü-Gänge (#62) → Konzept-Text
                # als Fallback-Query (Speisen-Positionen + Konzept).
                kt = _konzept_text(src)
                if kt:
                    offer["konzept"] = kt
        except Exception as e:                                      # noqa
            return JSONResponse({"error": "Parsing: " + str(e)[:200]},
                                status_code=502)
        return _respond(offer)

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
    return _respond(offer)
