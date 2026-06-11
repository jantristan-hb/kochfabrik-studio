"""Geteilter Backend-Kern (US-053 Modularisierung).

Zentrale Sammelstelle für Zustand/Helfer, die VON MEHREREN Stellen
gebraucht werden (app.py-Middleware + Router auth/bildgenerator + die
Router angebot/praesentation aus US-054). Eigenes Modul, damit Router
NICHT auf app.py importieren müssen (kein Import-Zyklus — Pitfall 2).

Inhalt 1:1 aus app.py extrahiert (Auth-/Cookie-Helfer, Bild-Kern,
Kategorie-/Prompt-Konstanten, Engine-Import-Block). Verhalten unverändert.
"""
import base64
import hashlib
import hmac
import json
import os
import random
import sys as _sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
BG_DIR = os.path.join(WEB, "assets", "bg")
MODEL = os.environ.get("KF_IMG_MODEL", "gemini-3-pro-image-preview")
IMG_SIZE = os.environ.get("KF_IMG_SIZE", "2K")
IMG_ASPECT = os.environ.get("KF_IMG_ASPECT", "16:9")
COOKIE = "kf_sess"
SESSION_DAYS = 7

# Kategorie-spezifische Photo-Preambel.
# PHOTO (food-spezifisch) bleibt 1:1 wie vorher → Food-Generierung
# byte-identisch zum Pre-Fix-Stand (keine Regression).
# PHOTO_NEUTRAL wird nur für non-food-Kategorien verwendet (cover,
# location, ausstattung, goldschaetzchen, kochfabrik, freitext) —
# entfernt das "food photograph" + "fine-dining quality"-Bias, das
# sonst auch Location-/Ausstattungs-Prompts food-lastig macht.
PHOTO = ("Ultra-realistic professional food photograph, shot on a "
         "full-frame DSLR, 85mm prime, f/2.8, soft natural light, "
         "shallow depth of field, true-to-life colours, textures and "
         "natural imperfections, editorial fine-dining quality. This is "
         "a REAL PHOTOGRAPH — not an illustration, 3D render or AI art; "
         "no oversaturation, no plastic look, no text, no logo. ")
PHOTO_NEUTRAL = ("Ultra-realistic professional photograph, shot on a "
                 "full-frame DSLR, 85mm prime, f/2.8, soft natural "
                 "light, shallow depth of field, true-to-life colours, "
                 "textures and natural imperfections, editorial quality. "
                 "This is a REAL PHOTOGRAPH — not an illustration, 3D "
                 "render or AI art; no oversaturation, no plastic look, "
                 "no text, no logo. ")
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
    # ON_TABLE (rustic KF-table-Foto als Referenz) und FREE ("place
    # the dish in a fitting setting") sind food-spezifisch — nur in
    # FOOD_LIKE-Kategorien anwenden. Sonst leakt z.B. ein cat=cover-
    # Prompt mit table=True einen Tischhintergrund + Food-Phrasen.
    if cat in FOOD_LIKE and table and pool:
        bg = random.choice(pool)
        parts.append({"inlineData": {"mimeType": "image/png",
                      "data": base64.b64encode(open(bg, "rb").read())
                      .decode()}})
        ctx = ON_TABLE
    elif cat in FOOD_LIKE:
        ctx = FREE
    else:
        ctx = ""        # Kontext trägt das Kategorie-Scaffold
    # Photo-Preambel: FOOD bleibt 1:1 (food photograph / fine-dining),
    # alle anderen Kategorien bekommen PHOTO_NEUTRAL (kein food-Bias).
    photo = PHOTO if cat in FOOD_LIKE else PHOTO_NEUTRAL
    parts.append({"text": photo + ctx + scaffold
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
# Engine liegt repo-intern unter engine/ (subtree, ADR-002). Import
# gekapselt: fehlt sie (Deploy ohne node/soffice/Asset-Bundle) →
# Endpoints melden sauber 503 statt App-Crash.
ENGINE_OK, ENGINE_ERR = False, ""
_ENG = os.path.join(ROOT, "engine", "scripts")
_AMODEL = _ASCHEMA = None
Angebot = _adump = _desc2a = _ang2md = _render_pdf = None
_akey = _aextract = None
try:
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
