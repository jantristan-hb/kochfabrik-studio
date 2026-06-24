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
                           _gemini_key, _owner, _akey, _AMODEL)

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


def _offer_meta(src: str) -> tuple:
    """Veranstaltungsanlass + -ort aus md/PDF (Cover-Prompt-Quelle, #95).
    Additiv — der Anlass ist der bessere Cover-Aufhänger als die Gänge."""
    import re
    import subprocess
    try:
        if src.lower().endswith(".pdf"):
            txt = subprocess.run(["pdftotext", "-layout", src, "-"],
                                 capture_output=True, text=True).stdout
        else:
            with open(src, encoding="utf-8") as fh:
                txt = fh.read()
    except Exception:                                           # noqa
        return "", ""

    def grab(label):
        m = re.search(label + r"\s*:?\s*(.+)", txt)
        return m.group(1).strip() if m else ""
    return grab("Veranstaltungsanlass"), grab("Veranstaltungsort")


def _parse_offer_md(offer_md: str) -> dict:
    """Offer-md → {kunde, datum, anlass, ort, gaenge[]} via Engine-Parser
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
    anlass, ort = _offer_meta(src)
    dishes = compose_offer.parse_offer_dishes(src, offer="Angebot")
    gaenge = [{"label": course,
               "dishes": [{"name": n, "desc": de} for n, de in items]}
              for course, items in dishes]
    return {"kunde": kunde, "datum": datum, "anlass": anlass,
            "ort": ort, "gaenge": gaenge}


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
    bundle.rank_mixed(k=N). Embed-Fehler propagiert (→ 502 im Endpoint)."""
    if not gaenge:
        return []
    import bundle as _b
    texts = [_gang_query(g) for g in gaenge]
    vecs = embed(texts)                              # 1 Batch (Pitfall 2)
    b = _b.load()
    out = []
    # US-072: gemischtes Ranking (Text + Bild) über die zentrale Bundle-
    # Schicht. Fehlt das imgbundle, liefert rank_mixed graceful exakt die
    # text-only-Ordnung (== rank, EARS 4 IF). alpha via KF_RANK_ALPHA.
    alpha = float(os.environ.get("KF_RANK_ALPHA", "0.7"))
    for g, vec in zip(gaenge, vecs):
        qv = _b.normalize_query(vec)
        order = _b.rank_mixed(qv, n, alpha=alpha)    # global, Top-N
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
        # W2: Gang-Objekt (label + dishes) MITLIEFERN, damit der Wizard die
        # angebotsbezogenen Text-Vorschläge bauen kann. Ohne dieses Feld kam
        # im Wizard immer gang=null an → _suggest_overrides lieferte nichts
        # Angebotsbezogenes (Korpus-Originaltext blieb stehen). Single Source
        # of Truth: gilt auch für die Konzept-Gruppe (nutzt dieselbe Funktion).
        out.append({"label": g["label"], "kind": "gang",
                    "gang": {"label": g["label"], "dishes": g.get("dishes", [])},
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
            anlass, ort = _offer_meta(src)
            dishes = compose_offer.parse_offer_dishes(src)
            gaenge = [{"label": c,
                       "dishes": [{"name": n, "desc": de}
                                  for n, de in items]}
                      for c, items in dishes]
            offer = {"kunde": kunde, "datum": datum, "anlass": anlass,
                     "ort": ort, "gaenge": gaenge}
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


# ---------------- Text-Overrides (#66, EPIC-006/D5) ----------------
# Texte der gewählten Slides (aus elements.json) + automatisch aus dem
# Angebot generierte Override-Vorschläge (menu_overlay-Heuristik:
# Headline = Gang, größter Caps-Block = Gerichte; Cover = Kunde/Datum).

class TextSlideRef(BaseModel):
    deck: str
    page: int
    kind: str | None = None                  # gang | cover | pflicht | …
    gang: dict | None = None                 # {label, dishes:[{name,desc}]}


class TextsReq(BaseModel):
    slides: list[TextSlideRef]
    offer: dict | None = None                # {kunde, datum, …}


def _slide_text_elements(deck: str, page: int):
    """[(seq_idx, element)] der Text-Elemente einer Cache-Slide."""
    seq = _slide_seq(deck, page)
    if seq is None:
        return None
    return [(i, e) for i, e in enumerate(seq)
            if e.get("t") == "text" and e.get("lines")]


def _slide_seq(deck: str, page: int):
    """Rohe Element-Sequenz einer Cache-Slide (None = Slide/Deck fehlt)."""
    from ..slidesuche import _CACHE, _SAFE
    if not _SAFE.match(deck) or page < 1:
        return None
    el_path = os.path.join(_CACHE, deck, "elements.json")
    if not os.path.isfile(el_path):
        return None
    return json.load(open(el_path, encoding="utf-8")).get(str(int(page)))


def _slide_meta(deck: str):
    """_meta {w_pt,h_pt} eines Decks (Maßstab variiert je Deck, Pitfall 2 —
    nie hartkodieren). Default 960×540, falls _meta fehlt."""
    from ..slidesuche import _CACHE, _SAFE
    default = {"w_pt": 960.0, "h_pt": 540.0}
    if not _SAFE.match(deck):
        return default
    el_path = os.path.join(_CACHE, deck, "elements.json")
    if not os.path.isfile(el_path):
        return default
    try:
        m = json.load(open(el_path, encoding="utf-8")).get("_meta") or {}
    except Exception:                                               # noqa
        return default
    return {"w_pt": float(m.get("w_pt", default["w_pt"])),
            "h_pt": float(m.get("h_pt", default["h_pt"]))}


def _slide_images(deck: str, page: int):
    """images[] = {i,x,y,w,h} der t=='image'-Elemente einer Cache-Slide."""
    seq = _slide_seq(deck, page)
    if not seq:
        return []
    return [{"i": i, "x": e.get("x"), "y": e.get("y"),
             "w": e.get("w"), "h": e.get("h")}
            for i, e in enumerate(seq) if e.get("t") == "image"]


def _suggest_overrides(texts, kind, gang, offer):
    """Auto-Overrides je Slide-Art — gleiche Schwellen wie menu_overlay
    (Headline = size >= 0.5*max; Caps = Rest = Gerichte-Slots)."""
    if not texts:
        return {}
    sizes = [max(ln["size"] for ln in e["lines"]) for _, e in texts]
    mx = max(sizes)
    heads = [(i, sz) for (i, _), sz in zip(texts, sizes) if sz >= 0.5 * mx]
    caps = [(i, e) for (i, e), sz in zip(texts, sizes) if sz < 0.5 * mx]
    sug = {}
    if kind == "gang" and gang:
        primary = max(heads, key=lambda t: t[1])[0]
        sug[str(primary)] = str(gang.get("label", "")).upper()
        for i, _ in heads:
            if i != primary:
                sug[str(i)] = ""             # leere Override = entfernen
        dishes = "\n".join(
            d.get("name", "") + (" — " + d["desc"] if d.get("desc") else "")
            for d in (gang.get("dishes") or []) if d.get("name"))
        if caps and dishes:
            big = max(caps, key=lambda t: t[1]["w"] * t[1]["h"])[0]
            sug[str(big)] = dishes
            for i, _ in caps:
                if i != big:
                    sug[str(i)] = ""
    elif kind == "cover" and offer:
        if heads:
            primary = max(heads, key=lambda t: t[1])[0]
            kunde = str(offer.get("kunde") or "").strip()
            datum = str(offer.get("datum") or "").strip()
            val = (kunde + ("\n" + datum if datum else "")).strip()
            if val:
                sug[str(primary)] = val
    return sug


# Notext-Preview-Route der Slidesuche (US-070): textfreie Renders je
# Slide, Grundlage für die Overlay-Positionierung im Editor.
_NOTEXT_BASE = "/api/slidesuche/preview-notext"


def _text_entry(i: int, e: dict) -> dict:
    """Ein Text-Element → Editor-Eintrag: Bestands-Felder (i/text/size,
    #66) + Geometrie (x/y/w/h) + Stil (color/weight/italic) aus lines[0]
    — genug, um Overlays pixelgenau zu setzen (FEATURE-014 EARS 1)."""
    ln0 = e["lines"][0]
    return {
        "i": i,
        "text": "\n".join(ln.get("txt", "") for ln in e["lines"]),
        "size": max(ln["size"] for ln in e["lines"]),
        "x": e.get("x"), "y": e.get("y"),
        "w": e.get("w"), "h": e.get("h"),
        "color": ln0.get("color"),
        "weight": ln0.get("weight"),
        "italic": bool(ln0.get("italic", False)),
    }


@router.post("/api/designer/texts")
def designer_texts(r: TextsReq, request: Request):
    """Pro Board-Slide: Ist-Texte (elements.json) inkl. Geometrie/Stil +
    Slide-meta (w_pt/h_pt) + image-Elemente + Notext-Preview-URL + Auto-
    Override-Vorschläge. Editor-/Overlay-Grundlage (#66, FEATURE-014)."""
    if not _owner(request):
        return JSONResponse({"error": "auth"}, status_code=401)
    out = []
    for sl in r.slides[:50]:
        meta = _slide_meta(sl.deck)
        notext = f"{_NOTEXT_BASE}/{sl.deck}/{int(sl.page)}.png"
        texts = _slide_text_elements(sl.deck, sl.page)
        if texts is None:
            out.append({"deck": sl.deck, "page": sl.page, "texts": [],
                        "images": [], "meta": meta,
                        "preview_notext": notext, "suggestions": {}})
            continue
        out.append({
            "deck": sl.deck, "page": sl.page, "meta": meta,
            "preview_notext": notext,
            "texts": [_text_entry(i, e) for i, e in texts],
            "images": _slide_images(sl.deck, sl.page),
            "suggestions": _suggest_overrides(texts, sl.kind, sl.gang,
                                              r.offer),
        })
    return {"slides": out}


# ---------------- Formulieren (US-072, FEATURE-014 EARS 3) ----------------
# Kurz-Umformulierung von Slide-Texten im KOCHfabrik-Ton. Anthropic-Muster
# wie angebot_chat.beschreibung_zu_angebot (gleiche MODEL/Key-Bindung via
# engine_glue: _AMODEL/_akey). DNA = echte, kuratierte Korpus-Zeilen als
# Tonanker (Pitfall 5: als Konstante im Router, nicht aus dem Cache zur
# Laufzeit geladen). Knapp, deutsch, norddeutsch-direkt, kein Marketing-
# Geschwurbel.
_DNA = (
    "Ausstattung und Location",
    "Deine Catering- & Event-Crew im Norden",
    "Frisch gekocht, ehrlich serviert.",
    "Wir bringen den Norden auf den Teller.",
)

_FORMULATE_SYS = (
    "Du bist Texter:in der KOCHfabrik, eines norddeutschen Catering- & "
    "Event-Unternehmens. Formuliere den gegebenen Slide-Text neu — im "
    "KOCHfabrik-Ton. So klingt die KOCHfabrik (Beispiele aus echten "
    "Decks):\n- " + "\n- ".join(_DNA) + "\n\nREGELN (strikt):\n"
    "- Deutsch, echte Umlaute. Knapp und markig, kein Marketing-"
    "Geschwurbel, keine Floskeln.\n"
    "- Höchstens etwa doppelt so lang wie der Eingabetext.\n"
    "- KEIN Markdown, keine Anführungszeichen, keine Aufzählungs-"
    "zeichen — nur der reine Text (Zeilenumbrüche erlaubt).\n"
    "- Gib AUSSCHLIESSLICH den neuen Text zurück, nichts sonst.")


class FormulateReq(BaseModel):
    text: str
    kind: str | None = None                  # gang | cover | pflicht | …
    gang_label: str | None = None


@router.post("/api/designer/formulate")
def designer_formulate(r: FormulateReq, request: Request):
    """Slide-Text → Umformulierung im KOCHfabrik-Ton (EARS 3). LLM-Fehler
    → 502 (gekürzt). Anthropic-Bindung wie angebot_chat."""
    if not _owner(request):
        return JSONResponse({"error": "auth"}, status_code=401)
    text = (r.text or "").strip()
    if not text:
        return JSONResponse({"error": "leerer Text"}, status_code=400)
    key = _akey() if _akey else None
    if not key:
        return JSONResponse(
            {"error": "Anthropic-Key fehlt in diesem Deploy."},
            status_code=503)
    ctx = []
    if r.kind:
        ctx.append(f"Slide-Art: {r.kind}")
    if r.gang_label:
        ctx.append(f"Gang/Abschnitt: {r.gang_label}")
    prompt = (("\n".join(ctx) + "\n\n" if ctx else "")
              + "Formuliere diesen Slide-Text neu:\n\n" + text)
    try:
        from anthropic import Anthropic
        c = Anthropic(api_key=key)
        msg = c.messages.create(
            model=_AMODEL or "claude-sonnet-4-6", max_tokens=600,
            system=_FORMULATE_SYS,
            messages=[{"role": "user", "content": prompt}])
        out = "".join(b.text for b in msg.content
                      if getattr(b, "type", None) == "text").strip()
    except Exception as e:                                          # noqa
        return JSONResponse({"error": "Formulieren: " + str(e)[:200]},
                            status_code=502)
    if not out:
        return JSONResponse({"error": "leere LLM-Antwort"},
                            status_code=502)
    return {"text": out}
