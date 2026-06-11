"""Angebots-Router (US-054) — Angebotsgenerator + Kunden/Stats.

1:1 aus app.py extrahiert: /api/angebot/* (health/chat/pdf/save/{id}),
/api/angebote, /api/stats, /api/kunden, /api/kunde/{id} samt der
zugehörigen Helfer (_angebot_from_dict, _today_de, _ensure_correct_dates,
_chat_patch, _persist). Engine-Glue + Auth-Helfer kommen aus
backend.engine_glue (kein Import auf app.py — Pitfall 2). Verhalten
unverändert (gleiche Pfade, gleiche Reihenfolge der Registrierung)."""
import base64
import json
import os

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..engine_glue import (
    ENGINE_OK, ENGINE_ERR, _AMODEL, _ASCHEMA, _akey, _aextract,
    _render_pdf, Angebot, _owner)

router = APIRouter()


def _angebot_from_dict(d):
    """dict → Angebot (reuse angebot_chat-Mapping ohne LLM)."""
    import angebot_chat as _ac
    a = _ac.beschreibung_zu_angebot.__wrapped__ if hasattr(
        _ac.beschreibung_zu_angebot, "__wrapped__") else None
    # eigenes Mapping (Schema-stabil, kein LLM):
    from angebot_model import (Veranstaltung, Positionsblock,
                               Position, Footer)
    v = d.get("veranstaltung", {})
    bl = [Positionsblock(
        typ=b.get("typ", "pos"), titel=b.get("titel", ""),
        positionen=[Position(**{k: p[k] for k in ("bezeichnung",
                    "menge", "einzelpreis", "gesamt", "is_header")
                    if k in p}) for p in b.get("positionen", [])],
        zwischensumme=b.get("zwischensumme", 0.0))
        for b in d.get("bloecke", [])]
    return Angebot(
        kunde=d.get("kunde", ""), adresse=d.get("adresse", ""),
        angebots_nr=d.get("angebots_nr", ""), datum=d.get("datum", ""),
        kundennr=d.get("kundennr", ""),
        lieferdatum=d.get("lieferdatum", ""),
        ansprechpartner=d.get("ansprechpartner", ""),
        veranstaltung=Veranstaltung(
            anlass=v.get("anlass", ""), datum=v.get("datum", ""),
            beginn=v.get("beginn", ""),
            personen=int(v.get("personen", 0) or 0),
            ort=v.get("ort", ""), konzept=v.get("konzept", "")),
        bloecke=bl, footer=Footer())


def _today_de() -> str:
    import datetime
    M = ("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
         "August", "September", "Oktober", "November", "Dezember")
    h = datetime.date.today()
    return f"{h.day}. {M[h.month - 1]} {h.year}"


def _ensure_correct_dates(d: dict) -> dict:
    """Server-seitig zwingend richtige Daten:
    - 'datum' (Angebots-Erstellung) = HEUTE (Server-Zeit), immer.
    - 'lieferdatum' default = veranstaltung.datum (Lieferung am Event-
      Tag), falls leer + v_datum gesetzt.
    - 'veranstaltung.datum' bleibt unverändert (Chatbot/Kunde vorgibt).
    LLM-Output egal — diese Felder werden post-mortem gerade gezogen."""
    if not isinstance(d, dict):
        return d
    d["datum"] = _today_de()
    v = d.get("veranstaltung") or {}
    if not d.get("lieferdatum") and v.get("datum"):
        d["lieferdatum"] = v["datum"]
    return d


def _chat_patch(angebot_dict, message):
    """Aktuelles Angebot + Chat-Nachricht → aktualisiertes Angebot-dict
    (LLM patcht das ganze JSON). Leeres Angebot → Neu-Generierung.
    Heute-Anker + DE-Format + Anti-Fabrikation + Feld-Disambiguierung
    (analog beschreibung_zu_angebot)."""
    import datetime
    from anthropic import Anthropic
    MON = ("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
           "August", "September", "Oktober", "November", "Dezember")
    h = datetime.date.today()
    heute = f"{h.day}. {MON[h.month - 1]} {h.year}"
    c = Anthropic(api_key=_akey())
    cur = json.dumps(angebot_dict or {}, ensure_ascii=False)
    msg = c.messages.create(
        model=_AMODEL, max_tokens=4000,
        messages=[{"role": "user", "content":
                   "Du bearbeitest ein KOCHfabrik-Angebot. AKTUELLES "
                   "JSON:\n" + cur + "\n\nÄNDERUNGSWUNSCH:\n" + message
                   + "\n\nGib das VOLLSTÄNDIGE aktualisierte Angebot "
                   "als striktes kompaktes JSON zurück (nur JSON, "
                   "keine Fences, keine trailing commas, Footer "
                   "NICHT setzen). **Fehlende Angaben PLAUSIBEL "
                   "ERGÄNZEN — insbesondere bloecke (Speisen/Getränke/"
                   "Personal/Logistik) mit KOCHfabrik-typischen, zum "
                   "Anlass/Konzept passenden Positionen, Mengen, "
                   "Preisen und Zwischensummen je Block. JEDES "
                   "Angebot hat reale Menüs/Positionen — nicht leer "
                   "lassen.**\n\n"
                   f"HEUTE ist der {heute}. REGELN (strikt):\n"
                   f"- Erstellungsdatum 'datum' = {heute} wenn leer "
                   f"oder nicht plausibel.\n"
                   f"- Alle Datumswerte im deutschen Format "
                   f"'T. Monat JJJJ' (z.B. '{heute}'), NIEMALS ISO/"
                   f"JJJJ-MM-TT. Jahre = {h.year} oder später, nie "
                   f"in der Vergangenheit. Fehlt im Datum das Jahr "
                   f"(z.B. 'am 18. Juni'), ergänze IMMER {h.year} "
                   f"(bzw. {h.year + 1} falls dieses Jahr vorbei).\n"
                   "- Anti-Fabrikation NUR für IDENTITÄTSFELDER "
                   "(ansprechpartner, kundennr, angebots_nr, Mail, "
                   "Telefon, konkrete Kundenadresse): die LEER "
                   "lassen wenn nicht ableitbar; kein 'Max "
                   "Mustermann', keine 'KF-2025-…', keine Fake-"
                   "Kontakte. POSITIONEN/MENÜS DAVON AUSGENOMMEN — "
                   "die SOLLEN reichhaltig und plausibel erfunden "
                   "werden (das ist Kernfunktion).\n"
                   "- FELDER: 'kunde' = Firmenname. 'adresse' = "
                   "Postanschrift OHNE die Firma (Format "
                   "'[Ansprechpartner-Name, ]Straße Nr, PLZ Ort'). "
                   "'veranstaltung.ort' = Event-LOCATION, NICHT die "
                   "Kundenadresse/-PLZ. 'ansprechpartner' = KOCH"
                   "fabrik-Sachbearbeiter (Name), NICHT der Kunde.\n\n"
                   "Schema:\n" + _ASCHEMA}])
    return json.loads(_aextract("".join(
        b.text for b in msg.content if b.type == "text")))


class AngebotChatReq(BaseModel):
    message: str
    angebot: dict | None = None


class AngebotPdfReq(BaseModel):
    angebot: dict


@router.get("/api/angebot/health")
def angebot_health():
    return {"engine": ENGINE_OK, "error": ENGINE_ERR,
            "model": _AMODEL if ENGINE_OK else None}


@router.post("/api/angebot/chat")
async def angebot_chat(r: AngebotChatReq, request: Request):
    if not ENGINE_OK:
        return JSONResponse(
            {"error": "Angebots-Engine in diesem Deploy nicht "
             "verfügbar: " + (ENGINE_ERR or "")}, status_code=503)
    if not r.message.strip():
        return JSONResponse({"error": "leer"}, status_code=400)
    try:
        upd = _chat_patch(r.angebot, r.message)
        _ensure_correct_dates(upd)              # datum=heute, lieferdatum=v
        _angebot_from_dict(upd)                 # Schema-Validierung
    except Exception as e:
        return JSONResponse({"error": str(e)[:240]}, status_code=502)
    # US-006: Offer sicherstellen + Chat-Turns persistieren (graceful —
    # DB-Ausfall bricht den Chat NICHT).
    owner = _owner(request)
    res, persist_warn = await _persist(owner, upd)   # create-or-update
    if res:
        upd["angebots_nr"] = res["angebotsnummer"]
        upd["kundennr"] = res["kundennummer"]
        upd["_offer_id"] = res["offer_id"]
    offer_id = ((res or {}).get("offer_id")
                or (r.angebot or {}).get("_offer_id"))
    if owner and offer_id:
        try:
            from ..store import add_chat
            await add_chat(owner, offer_id, "me", r.message)
            await add_chat(owner, offer_id, "bot",
                           "Angebot aktualisiert.")
        except Exception as e:                                  # noqa
            persist_warn = (persist_warn
                            or f"Chat-Persistenz übersprungen: "
                               f"{type(e).__name__}")
    return {"angebot": upd, "offer_id": offer_id,
            "persist_warn": persist_warn}


async def _persist(owner, angebot):
    """Graceful: speichert Angebot + gibt zugewiesene Nummern zurück.
    DB-Ausfall darf den PDF-/Save-Flow NICHT brechen."""
    try:
        from .. import db as _db
        if not owner or not await _db.ping():
            return None, "DB nicht verfügbar — ohne Persistenz"
        from ..store import save_offer
        return await save_offer(owner, angebot), None
    except Exception as e:                                          # noqa
        return None, f"Persistenz übersprungen: {type(e).__name__}"


@router.post("/api/angebot/pdf")
async def angebot_pdf(r: AngebotPdfReq, request: Request):
    if not ENGINE_OK:
        return JSONResponse(
            {"error": "Angebots-Engine in diesem Deploy nicht "
             "verfügbar: " + (ENGINE_ERR or "")}, status_code=503)
    import tempfile
    ang = _ensure_correct_dates(dict(r.angebot))      # datum=heute
    res, warn = await _persist(_owner(request), ang)
    if res:                       # zugewiesene Nummern ins PDF mergen
        ang["angebots_nr"] = res["angebotsnummer"]
        ang["kundennr"] = res["kundennummer"]
        ang["_offer_id"] = res["offer_id"]
    try:
        a = _angebot_from_dict(ang)
        out = os.path.join(tempfile.mkdtemp(prefix="stud_ang_"),
                           "angebot.pdf")
        _render_pdf(a, out)
        data = base64.b64encode(open(out, "rb").read()).decode()
    except Exception as e:
        return JSONResponse({"error": str(e)[:240]}, status_code=502)
    return {"pdf": "data:application/pdf;base64," + data,
            "saved": res, "persist_warn": warn}


@router.post("/api/angebot/save")
async def angebot_save(r: AngebotPdfReq, request: Request):
    owner = _owner(request)
    if not owner:
        return JSONResponse({"error": "auth"}, status_code=401)
    res, warn = await _persist(owner, dict(r.angebot))
    if not res:
        return JSONResponse({"error": warn or "DB nicht verfügbar"},
                            status_code=503)
    return res


@router.get("/api/angebote")
async def angebote_list(request: Request):
    owner = _owner(request)
    if not owner:
        return JSONResponse({"error": "auth"}, status_code=401)
    try:
        from .. import db as _db
        if not await _db.ping():
            return JSONResponse({"error": "DB nicht verfügbar",
                                 "offers": []}, status_code=503)
        from ..store import list_offers
        q = request.query_params.get("q", "")
        st = request.query_params.get("status", "")
        return {"offers": await list_offers(owner, q, st)}
    except Exception as e:                                          # noqa
        return JSONResponse({"error": str(e)[:200], "offers": []},
                            status_code=503)


@router.get("/api/stats")
async def api_stats(request: Request):
    owner = _owner(request)
    if not owner:
        return JSONResponse({"error": "auth"}, status_code=401)
    _empty = {"angebote": 0, "kunden": 0, "volumen": 0.0, "letzte": []}
    try:
        from .. import db as _db
        if not await _db.ping():
            return JSONResponse({**_empty, "error": "DB nicht verfügbar"},
                                status_code=503)
        from ..store import stats
        return await stats(owner)
    except Exception as e:                                          # noqa
        return JSONResponse({**_empty, "error": str(e)[:200]},
                            status_code=503)


@router.get("/api/kunden")
async def api_kunden(request: Request):
    owner = _owner(request)
    if not owner:
        return JSONResponse({"error": "auth"}, status_code=401)
    try:
        from .. import db as _db
        if not await _db.ping():
            return JSONResponse({"error": "DB nicht verfügbar",
                                 "kunden": []}, status_code=503)
        from ..store import list_customers
        return {"kunden": await list_customers(owner)}
    except Exception as e:                                          # noqa
        return JSONResponse({"error": str(e)[:200], "kunden": []},
                            status_code=503)


@router.get("/api/kunde/{customer_id}")
async def api_kunde(customer_id: int, request: Request):
    owner = _owner(request)
    if not owner:
        return JSONResponse({"error": "auth"}, status_code=401)
    try:
        from .. import db as _db
        if not await _db.ping():
            return JSONResponse({"error": "DB nicht verfügbar"},
                                status_code=503)
        from ..store import get_customer
        d = await get_customer(owner, customer_id)
    except Exception as e:                                          # noqa
        return JSONResponse({"error": str(e)[:200]}, status_code=503)
    if d is None:
        return JSONResponse({"error": "nicht gefunden"},
                            status_code=404)
    return d


@router.get("/api/angebot/{offer_id}")
async def angebot_get(offer_id: int, request: Request):
    owner = _owner(request)
    if not owner:
        return JSONResponse({"error": "auth"}, status_code=401)
    try:
        from .. import db as _db
        if not await _db.ping():
            return JSONResponse({"error": "DB nicht verfügbar"},
                                status_code=503)
        from ..store import get_offer_full
        full = await get_offer_full(owner, offer_id)   # US-007/009
    except Exception as e:                                          # noqa
        return JSONResponse({"error": str(e)[:200]}, status_code=503)
    if full is None:
        return JSONResponse({"error": "nicht gefunden"},
                            status_code=404)
    # abwärtskompat: 'angebot' bleibt Top-Level (S1 chat.html);
    # 'chat' additiv (US-007).
    return {"angebot": full["angebot"], "chat": full["chat"]}
