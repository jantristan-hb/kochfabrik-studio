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
"""
import base64
import hashlib
import hmac
import json
import os
import random
import time
import urllib.request

from fastapi import FastAPI, File, Request, Response, UploadFile
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
BG_DIR = os.path.join(WEB, "assets", "bg")
MODEL = os.environ.get("KF_IMG_MODEL", "gemini-3-pro-image-preview")
IMG_SIZE = os.environ.get("KF_IMG_SIZE", "2K")
IMG_ASPECT = os.environ.get("KF_IMG_ASPECT", "16:9")
COOKIE = "kf_sess"
SESSION_DAYS = 7

PHOTO = ("Ultra-realistic professional food photograph, shot on a "
         "full-frame DSLR, 85mm prime, f/2.8, soft natural light, "
         "shallow depth of field, true-to-life colours, textures and "
         "natural imperfections, editorial fine-dining quality. This is "
         "a REAL PHOTOGRAPH — not an illustration, 3D render or AI art; "
         "no oversaturation, no plastic look, no text, no logo. ")
ON_TABLE = ("Plate the dish beautifully and place it naturally ON the "
            "rustic reclaimed-wood KOCHfabrik table shown in the "
            "reference photo, keeping that exact table and its warm "
            "restaurant ambiance, correct perspective and scale. ONLY "
            "if the dish genuinely does not suit this catering-table "
            "setting, instead use a fitting realistic setting. ")
FREE = ("Place the dish in a fitting, realistic setting/background "
        "appropriate to the dish and its cuisine. ")

# ---------------- Kategorien ----------------
# Jede Kategorie = eigener Use-Case (dedizierte Generator-Seite).
# `scaffold` (EN) wird serverseitig zwischen Kontext und Motiv gesetzt.
# HINWEIS: `goldschaetzchen` + `kochfabrik` sind meine Auslegung der
# KOCHfabrik-Begriffe — Scaffold-Text hier zentral & isoliert tunebar.
CATS = {
    "food": {
        "label": "Foodbilder",
        "hint": "Gericht eingeben — fotorealistischer Speisen-Shot.",
        "icon": "&#9788;", "table": True, "scaffold": "",
        "chips": [
            "Klassisches deutsches Frühstück: frische Brötchen, "
            "Aufschnitt, Käse, gekochtes Ei, Butter, Marmelade, Kaffee",
            "T-Bone Steak medium rare vom Grill mit Kräuterbutter, "
            "Rosmarin und Meersalz auf rustikalem Holzbrett",
            "Perfektes Sashimi: Lachs, Thunfisch, Gelbschwanz, Wasabi, "
            "eingelegter Ingwer, Sojaschälchen"]},
    "cover": {
        "label": "Deckblatt",
        "hint": "Stimmungsvolles Titelbild — Platz für Text, kein "
                "Text im Bild.",
        "icon": "&#9635;", "table": False,
        "scaffold": ("Compose an elegant, atmospheric TITLE/COVER "
                     "background image for a catering offer "
                     "presentation: cinematic depth, generous negative "
                     "space for an overlaid headline, warm KOCHfabrik "
                     "gold-and-natural mood. Render NO text or letters. "),
        "chips": [
            "Sommerfest unter freiem Himmel, lange festlich gedeckte "
            "Tafeln im Abendlicht",
            "Eleganter Galaabend, Kerzenlicht, Goldakzente, dunkler "
            "edler Hintergrund",
            "Modernes Business-Event, klare Architektur, warmes "
            "Catering-Ambiente"]},
    "location": {
        "label": "Location-Fotos",
        "hint": "Veranstaltungsort als Architektur-/Ambiente-Foto.",
        "icon": "&#9906;", "table": False,
        "scaffold": ("Architectural / venue photograph of the event "
                     "LOCATION itself (interior or exterior), "
                     "professional real-estate-quality wide shot, "
                     "natural daylight or warm evening ambiance, no "
                     "food in focus. "),
        "chips": [
            "Industrieloft mit Sichtbeton und großen Fenstern",
            "Reetgedeckte Scheune, rustikal, festlich bestuhlt",
            "Hafenterrasse mit Wasserblick bei Abendlicht"]},
    "ausstattung": {
        "label": "Ausstattungsfotos",
        "hint": "Catering-Equipment, Buffet- & Service-Stationen.",
        "icon": "&#9881;", "table": False,
        "scaffold": ("Professional product/reportage photograph of "
                     "catering EQUIPMENT and service setup: mobile "
                     "kitchen, buffet and live-cooking stations, "
                     "elegant serviceware and table-top styling, "
                     "high-end and clean, no people in focus. "),
        "chips": [
            "Live-Cooking-Station mit Plancha und Kupfertöpfen",
            "Elegant eingedecktes Buffet mit Holz und Schiefer",
            "Mobile Profiküche im Eventzelt"]},
    "goldschaetzchen": {
        "label": "Goldschätzchen",
        "hint": "Eventlocation Peiner Hof Prisdorf — Herrenhaus, "
                "Reetscheune, Biergarten.",
        "icon": "&#8962;", "table": False,
        "scaffold": ("Architectural / venue photograph of the historic "
                     "'Goldschätzchen' event location at Peiner Hof in "
                     "Prisdorf near Hamburg: a 200-year-old manor house "
                     "and a large thatched-roof barn on a rural estate "
                     "reached via a lime-tree avenue, grand interior "
                     "with four-metre stucco ceilings and chandeliers, "
                     "a wide sun terrace and beer garden overlooking "
                     "meadows and a pond. Elegant-rural, real-estate-"
                     "quality wide shot, warm natural light, no food "
                     "in focus. "),
        "chips": [
            "Reetgedeckte Scheune im Abendlicht, festlich bestuhlt",
            "Herrenhaus-Saal mit Stuckdecke und Kronleuchter",
            "Sonnenterrasse und Biergarten mit Wiesenblick"]},
    "kochfabrik": {
        "label": "KOCHfabrik-Fotos",
        "hint": "Marke & Team — nachhaltiges Eventcatering, Streetfood-"
                "Court, Köche.",
        "icon": "&#10070;", "table": False,
        "scaffold": ("Authentic brand reportage photograph of Die "
                     "KOCHfabrik's sustainable North-German event "
                     "catering: chefs and service team at work with "
                     "natural movement, streetfood courts and live "
                     "food stations built at event venues (waterfront, "
                     "industrial-chic halls), fresh regional produce, "
                     "warm natural light, human and emotional rather "
                     "than corporate, documentary style, no rendered "
                     "text or logos. "),
        "chips": [
            "Streetfood-Court mit mehreren Live-Stationen im "
            "Industrieloft",
            "Köche-Team beim Anrichten, natürliche Bewegung",
            "Nachhaltiges ELEMENTUM-Setup, regionale Produkte, "
            "Naturlicht"]},
    "freitext": {
        "label": "Freitext",
        "hint": "Beliebiges Motiv — voller Prompt, kein Kategorie-Bias.",
        "icon": "&#9998;", "table": False, "scaffold": "",
        "chips": [
            "Detailaufnahme von Kräutern und Gewürzen auf Marmor",
            "Weinglas im Gegenlicht, unscharfer Eventhintergrund",
            "Rustikales Brot frisch aus dem Holzofen"]},
}
FOOD_LIKE = ("food",)   # nur hier: Tisch / freier Speisen-Kontext sinnvoll


# ---------------- Auth (env-getrieben) ----------------
def _users():
    out = {}
    for e in (os.environ.get("KF_USERS", "")).split(";"):
        p = e.strip().split("|")
        if len(p) == 3:
            out[p[0].lower()] = (p[1], p[2])
    return out


def _secret():
    return os.environ.get("KF_SESSION_SECRET", "")


def verify_login(email, pw):
    u = _users().get((email or "").strip().lower())
    if not u:
        return False
    salt, h = u
    return hmac.compare_digest(
        hashlib.sha256((salt + ":" + pw).encode()).hexdigest(), h)


def make_cookie(email):
    exp = int(time.time()) + SESSION_DAYS * 86400
    raw = f"{email.lower()}|{exp}"
    sig = hmac.new(_secret().encode(), raw.encode(),
                   hashlib.sha256).hexdigest()[:32]
    return base64.urlsafe_b64encode(f"{raw}|{sig}".encode()).decode()


_DBU_CACHE: dict = {}                       # email -> (expires, bool)


def _db_user_ok(email: str) -> bool:
    """US-020 — OAuth-User über app_user (DB) akzeptieren. NUR für
    Nicht-KF_USERS aufgerufen (Short-Circuit davor). psycopg2 sync,
    TTL-Cache 60s, 2s-Timeout, EXCEPTION-SAFE: jeder Fehler → False
    (nie Raise, nie Lockout bestehender KF_USERS-User)."""
    e = (email or "").strip().lower()
    if not e:
        return False
    c = _DBU_CACHE.get(e)
    if c and c[0] > time.time():
        return c[1]
    ok = False
    try:
        import psycopg2
        u = os.environ.get("DATABASE_URL", "").strip()
        for p in ("postgres://", "postgresql://",
                  "postgresql+asyncpg://", "postgresql+psycopg2://"):
            if u.startswith(p):
                u = "postgresql://" + u[len(p):]
                break
        if u:
            cx = psycopg2.connect(u, connect_timeout=2)
            try:
                cur = cx.cursor()
                cur.execute("SELECT 1 FROM app_user WHERE email=%s",
                            (e,))
                ok = cur.fetchone() is not None
            finally:
                cx.close()
    except Exception:
        ok = False                          # safe: nie Raise/Lockout
    _DBU_CACHE[e] = (time.time() + 60, ok)
    return ok


def valid_cookie(tok):
    try:
        raw = base64.urlsafe_b64decode(tok.encode()).decode()
        email, exp, sig = raw.rsplit("|", 2)
        good = hmac.new(_secret().encode(), f"{email}|{exp}".encode(),
                        hashlib.sha256).hexdigest()[:32]
        if not (hmac.compare_digest(sig, good)
                and int(exp) > time.time()):
            return False
        if email in _users():               # KF_USERS — unverändert
            return True
        return _db_user_ok(email)            # nur OAuth-User (US-020)
    except Exception:
        return False


def _owner(request) -> str | None:
    """owner_email aus gültigem Cookie (Multi-Tenant-Scope). OAuth
    später: gleiche Abstraktion, nur diese Funktion erweitern."""
    tok = request.cookies.get(COOKIE, "")
    if not valid_cookie(tok):
        return None
    try:
        raw = base64.urlsafe_b64decode(tok.encode()).decode()
        return raw.rsplit("|", 2)[0].strip().lower()
    except Exception:
        return None


# ---------------- Bild-Kern ----------------
def _gemini_key():
    k = os.environ.get("GEMINI_API_KEY")
    if k:
        return k
    env = os.path.expanduser("~/work/.env")
    if os.path.isfile(env):
        for ln in open(env):
            if ln.startswith("GEMINI_API_KEY="):
                return ln.split("=", 1)[1].strip().strip('"')
    return None


def _bg_pool():
    if not os.path.isdir(BG_DIR):
        return []
    return [os.path.join(BG_DIR, f) for f in sorted(os.listdir(BG_DIR))
            if f.lower().endswith((".png", ".jpg", ".jpeg"))]


def image_kochfabrik(prompt: str, table: bool = True, cat: str = "food"):
    """Prompt → KOCHfabrik-Style-PNG (bytes). table=True: zufällige
    Tisch-Referenz aus dem Pool (kontext-aware). `cat` wählt das
    Kategorie-Scaffold. Gibt (bytes, bg) zurück."""
    key = _gemini_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY fehlt")
    scaffold = CATS.get(cat, CATS["freitext"])["scaffold"]
    parts, bg = [], None
    pool = _bg_pool()
    if table and pool:
        bg = random.choice(pool)
        parts.append({"inlineData": {"mimeType": "image/png",
                      "data": base64.b64encode(open(bg, "rb").read())
                      .decode()}})
        ctx = ON_TABLE
    elif cat in FOOD_LIKE:
        ctx = FREE
    else:
        ctx = ""        # Kontext trägt das Kategorie-Scaffold
    parts.append({"text": PHOTO + ctx + scaffold
                  + "Motiv: " + prompt.strip()})
    body = {"contents": [{"parts": parts}],
            "generationConfig": {"responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": IMG_ASPECT,
                            "imageSize": IMG_SIZE}}}
    url = (f"https://generativelanguage.googleapis.com/v1beta/"
           f"models/{MODEL}:generateContent?key={key}")
    req = urllib.request.Request(url, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    res = json.loads(urllib.request.urlopen(req, timeout=160).read())
    for p in (res.get("candidates", [{}])[0].get("content", {})
              .get("parts", [])):
        if "inlineData" in p:
            return base64.b64decode(p["inlineData"]["data"]), bg
    raise RuntimeError("Kein Bild in Gemini-Antwort")


# ---------------- Angebotsgenerator-Engine (graceful) ----------------
# Engine lebt in Schwester-Repo pptxgenerator_v2. Import gekapselt:
# fehlt sie (Deploy ohne node/soffice/Asset-Bundle) → Endpoints melden
# sauber 503 statt App-Crash. Containerisierung = Post-Epic-Ops-Item.
import sys as _sys

ENGINE_OK, ENGINE_ERR = False, ""
try:
    _VEND = os.path.join(ROOT, "engine", "phase0", "scripts")
    _SIB = os.path.join(os.path.dirname(ROOT), "pptxgenerator_v2",
                        "phase0", "scripts")
    _ENG = _VEND if os.path.isdir(_VEND) else _SIB
    if os.path.isdir(_ENG):
        _sys.path.insert(0, _ENG)
        from angebot_model import Angebot, dump as _adump          # noqa
        from angebot_chat import beschreibung_zu_angebot as _desc2a  # noqa
        from angebot_chat import angebot_to_offer_md as _ang2md      # noqa
        from angebot_render import render_pdf as _render_pdf        # noqa
        from gen_fiktiv import MODEL as _AMODEL, SCHEMA as _ASCHEMA, \
            _key as _akey, _extract as _aextract                    # noqa
        ENGINE_OK = True
    else:
        ENGINE_ERR = f"Engine-Pfad fehlt: {_ENG}"
except Exception as _e:                                            # noqa
    ENGINE_ERR = f"Engine-Import: {str(_e)[:160]}"


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


class Login(BaseModel):
    email: str
    password: str


class ImgReq(BaseModel):
    prompt: str
    table: bool = True
    category: str = "food"


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


@app.post("/api/login")
def login(b: Login):
    if not verify_login(b.email, b.password):
        return JSONResponse({"error": "ungültig"}, status_code=401)
    r = JSONResponse({"ok": True})
    r.set_cookie(COOKIE, make_cookie(b.email), max_age=SESSION_DAYS*86400,
                 httponly=True, samesite="lax", secure=True)
    return r


@app.post("/api/logout")
def logout():
    r = JSONResponse({"ok": True})
    r.delete_cookie(COOKIE)
    return r


@app.get("/api/cats")
def api_cats():
    return {"cats": [{"key": k, "label": v["label"], "hint": v["hint"],
                      "icon": v["icon"], "table": v["table"],
                      "chips": v["chips"]} for k, v in CATS.items()]}


@app.post("/api/image")
def api_image(r: ImgReq):
    if not r.prompt.strip():
        return JSONResponse({"error": "prompt leer"}, status_code=400)
    cat = r.category if r.category in CATS else "food"
    try:
        png, bg = image_kochfabrik(r.prompt, r.table, cat)
    except Exception as e:
        return JSONResponse({"error": str(e)[:200]}, status_code=502)
    return {"image": "data:image/png;base64,"
            + base64.b64encode(png).decode(), "model": MODEL,
            "bg": os.path.basename(bg) if bg else None}


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


# ---------------- OAuth2 (US-019, env-gated, zero-regression) -----
@app.get("/api/oauth/providers")
def oauth_providers():
    from . import oauth as _o
    return {"providers": sorted(_o.providers().keys())}


@app.get("/api/oauth/{provider}/login")
def oauth_login(provider: str, request: Request):
    import secrets
    from . import oauth as _o
    if provider not in _o.providers():
        return JSONResponse({"error": "provider inaktiv"},
                            status_code=404)
    state = secrets.token_urlsafe(24)
    redir = _o.redirect_uri(provider, request)
    url = _o.auth_url(provider, state, redir)
    if not url:
        return JSONResponse({"error": "config"}, status_code=500)
    r = RedirectResponse(url, status_code=302)
    r.set_cookie("kf_oauth_state", state, max_age=600, httponly=True,
                 samesite="lax", secure=True)
    r.set_cookie("kf_oauth_redir", redir, max_age=600, httponly=True,
                 samesite="lax", secure=True)
    return r


@app.get("/api/oauth/{provider}/callback")
async def oauth_callback(provider: str, request: Request):
    from . import oauth as _o
    if provider not in _o.providers():
        return RedirectResponse("/login.html?err=oauth", status_code=302)
    qs = request.query_params
    code = qs.get("code", "")
    state = qs.get("state", "")
    state_c = request.cookies.get("kf_oauth_state", "")
    if not code or not state or not state_c or state != state_c:
        return RedirectResponse("/login.html?err=oauth", status_code=302)
    redir = (request.cookies.get("kf_oauth_redir", "")
             or _o.redirect_uri(provider, request))
    try:
        email = _o.exchange(provider, code, redir)
    except Exception:                                               # noqa
        email = None
    if not email:
        return RedirectResponse("/login.html?err=oauth", status_code=302)
    try:
        from .store import ensure_user
        await ensure_user(email)
    except Exception:                                               # noqa
        pass
    r = RedirectResponse("/", status_code=302)
    r.set_cookie(COOKIE, make_cookie(email),
                 max_age=SESSION_DAYS * 86400,
                 httponly=True, samesite="lax", secure=True)
    r.delete_cookie("kf_oauth_state"); r.delete_cookie("kf_oauth_redir")
    return r


@app.get("/")
def index():
    return FileResponse(os.path.join(WEB, "index.html"))


app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
