"""KOCHfabrik Studio — Backend (Phase 1: Bildgenerator + Login).

BEWUSST KEIN Präsentationsgenerator (Jans Vorgabe — Phase 2).
Framework-agnostischer Kern (image_kochfabrik). Auth + User rein
env-getrieben (Repo ist public → NIE Klartext/Hash im Code):
  KF_USERS         = "email|salt|sha256hex;email2|salt2|hash2"
  KF_SESSION_SECRET= random hex (Cookie-Signatur)
Hash-Schema: sha256(salt + ":" + passwort).

Bild: KOCHfabrik-Signature-Tisch als ROTIERENDE Referenz (Pool
web/assets/bg/) — Default an, aber kontext-aware & abschaltbar
(table=false → passender realistischer Kontext statt Tisch).
Immer maximal fotografiert (kein Render/AI-Look).

US-053: App ist Komposition — Routen leben in backend/routers/* und im
geteilten Kern backend/engine_glue.py (Auth-/Cookie-Helfer, Bild-Kern,
Kategorien, Engine-Import-Block). Router importieren NICHT auf app.py
(kein Import-Zyklus — Pitfall 2). Angebot/Präsentation folgen US-054.
"""
import base64
import json
import os

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Re-Export der Auth-/Cookie-Helfer hält das bestehende app-Modul-
# Surface stabil (Charakterisierungs-Tests greifen app._secret /
# app.make_cookie / app.valid_cookie / app._owner / app.COOKIE).
from .engine_glue import (                                          # noqa
    WEB, MODEL, IMG_SIZE, IMG_ASPECT, COOKIE, SESSION_DAYS, CATS,
    _gemini_key, _bg_pool, _users, _secret, make_cookie, verify_login,
    valid_cookie, _owner, image_kochfabrik,
    ENGINE_OK, ENGINE_ERR, _ENG, _AMODEL, _ASCHEMA, _akey, _aextract,
    _ang2md, _render_pdf)


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


app = FastAPI(title="KOCHfabrik Studio")

# Slide-Suche — eigener Router, prefix /api/slidesuche, unabhängig
from backend.slidesuche import router as _slidesuche_router  # noqa: E402
app.include_router(_slidesuche_router)

# US-053: Auth (login/logout/oauth) + Bildgenerator (cats/image) als Router.
from backend.routers.auth import router as _auth_router  # noqa: E402
from backend.routers.bildgenerator import (  # noqa: E402
    router as _bildgenerator_router)

PUBLIC = ("/login.html", "/api/login", "/api/health", "/favicon.ico",
          "/api/oauth/providers")
_PUBLIC_PREFIX = ("/assets/", "/api/oauth/")     # oauth login/callback


@app.middleware("http")
async def auth_gate(request: Request, call_next):
    path = request.url.path
    if (path in PUBLIC or path.startswith(_PUBLIC_PREFIX)
            or valid_cookie(request.cookies.get(COOKIE, ""))):
        return await call_next(request)
    if path.startswith("/api/"):
        return JSONResponse({"error": "auth"}, status_code=401)
    return RedirectResponse("/login.html", status_code=302)


@app.get("/api/health")
async def health():
    try:
        from . import db as _db
        db_ok = await _db.ping()
        db_err = "" if db_ok else _db.DB_ERR
    except Exception as e:                                          # noqa
        db_ok, db_err = False, f"{type(e).__name__}: {e}"
    return {"ok": True, "model": MODEL, "size": IMG_SIZE,
            "aspect": IMG_ASPECT, "key": bool(_gemini_key()),
            "bg_pool": len(_bg_pool()), "users": len(_users()),
            "cats": len(CATS), "db": db_ok, "db_error": db_err}


# login/logout (US-053) — Reihenfolge wie zuvor (nach /api/health).
app.include_router(_auth_router)
# cats/image (US-053).
app.include_router(_bildgenerator_router)


class AngebotChatReq(BaseModel):
    message: str
    angebot: dict | None = None


class AngebotPdfReq(BaseModel):
    angebot: dict


@app.get("/api/angebot/health")
def angebot_health():
    return {"engine": ENGINE_OK, "error": ENGINE_ERR,
            "model": _AMODEL if ENGINE_OK else None}


@app.post("/api/angebot/chat")
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
            from .store import add_chat
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
        from . import db as _db
        if not owner or not await _db.ping():
            return None, "DB nicht verfügbar — ohne Persistenz"
        from .store import save_offer
        return await save_offer(owner, angebot), None
    except Exception as e:                                          # noqa
        return None, f"Persistenz übersprungen: {type(e).__name__}"


@app.post("/api/angebot/pdf")
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


@app.post("/api/angebot/save")
async def angebot_save(r: AngebotPdfReq, request: Request):
    owner = _owner(request)
    if not owner:
        return JSONResponse({"error": "auth"}, status_code=401)
    res, warn = await _persist(owner, dict(r.angebot))
    if not res:
        return JSONResponse({"error": warn or "DB nicht verfügbar"},
                            status_code=503)
    return res


@app.get("/api/angebote")
async def angebote_list(request: Request):
    owner = _owner(request)
    if not owner:
        return JSONResponse({"error": "auth"}, status_code=401)
    try:
        from . import db as _db
        if not await _db.ping():
            return JSONResponse({"error": "DB nicht verfügbar",
                                 "offers": []}, status_code=503)
        from .store import list_offers
        q = request.query_params.get("q", "")
        st = request.query_params.get("status", "")
        return {"offers": await list_offers(owner, q, st)}
    except Exception as e:                                          # noqa
        return JSONResponse({"error": str(e)[:200], "offers": []},
                            status_code=503)


@app.get("/api/stats")
async def api_stats(request: Request):
    owner = _owner(request)
    if not owner:
        return JSONResponse({"error": "auth"}, status_code=401)
    _empty = {"angebote": 0, "kunden": 0, "volumen": 0.0, "letzte": []}
    try:
        from . import db as _db
        if not await _db.ping():
            return JSONResponse({**_empty, "error": "DB nicht verfügbar"},
                                status_code=503)
        from .store import stats
        return await stats(owner)
    except Exception as e:                                          # noqa
        return JSONResponse({**_empty, "error": str(e)[:200]},
                            status_code=503)


@app.get("/api/kunden")
async def api_kunden(request: Request):
    owner = _owner(request)
    if not owner:
        return JSONResponse({"error": "auth"}, status_code=401)
    try:
        from . import db as _db
        if not await _db.ping():
            return JSONResponse({"error": "DB nicht verfügbar",
                                 "kunden": []}, status_code=503)
        from .store import list_customers
        return {"kunden": await list_customers(owner)}
    except Exception as e:                                          # noqa
        return JSONResponse({"error": str(e)[:200], "kunden": []},
                            status_code=503)


@app.get("/api/kunde/{customer_id}")
async def api_kunde(customer_id: int, request: Request):
    owner = _owner(request)
    if not owner:
        return JSONResponse({"error": "auth"}, status_code=401)
    try:
        from . import db as _db
        if not await _db.ping():
            return JSONResponse({"error": "DB nicht verfügbar"},
                                status_code=503)
        from .store import get_customer
        d = await get_customer(owner, customer_id)
    except Exception as e:                                          # noqa
        return JSONResponse({"error": str(e)[:200]}, status_code=503)
    if d is None:
        return JSONResponse({"error": "nicht gefunden"},
                            status_code=404)
    return d


@app.get("/api/angebot/{offer_id}")
async def angebot_get(offer_id: int, request: Request):
    owner = _owner(request)
    if not owner:
        return JSONResponse({"error": "auth"}, status_code=401)
    try:
        from . import db as _db
        if not await _db.ping():
            return JSONResponse({"error": "DB nicht verfügbar"},
                                status_code=503)
        from .store import get_offer_full
        full = await get_offer_full(owner, offer_id)   # US-007/009
    except Exception as e:                                          # noqa
        return JSONResponse({"error": str(e)[:200]}, status_code=503)
    if full is None:
        return JSONResponse({"error": "nicht gefunden"},
                            status_code=404)
    # abwärtskompat: 'angebot' bleibt Top-Level (S1 chat.html);
    # 'chat' additiv (US-007).
    return {"angebot": full["angebot"], "chat": full["chat"]}


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


@app.get("/api/praesentation/health")
def praes_health():
    return {"engine": ENGINE_OK, "korpus": _korpus_ok(),
            "error": ENGINE_ERR}


@app.post("/api/praesentation/generate")
def praes_generate(r: PraesReq):
    g = _praes_guard()
    if g:
        return g
    if not r.offer.strip():
        return JSONResponse({"error": "leer"}, status_code=400)
    return _assemble_md(r.offer)


@app.post("/api/praesentation/from-angebot")
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


@app.post("/api/praesentation/from-pdf")
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


@app.get("/")
def index():
    return FileResponse(os.path.join(WEB, "index.html"))


app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
