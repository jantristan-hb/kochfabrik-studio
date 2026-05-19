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

from fastapi import FastAPI, Request, Response
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


def valid_cookie(tok):
    try:
        raw = base64.urlsafe_b64decode(tok.encode()).decode()
        email, exp, sig = raw.rsplit("|", 2)
        good = hmac.new(_secret().encode(), f"{email}|{exp}".encode(),
                        hashlib.sha256).hexdigest()[:32]
        return (hmac.compare_digest(sig, good)
                and int(exp) > time.time()
                and email in _users())
    except Exception:
        return False


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


def image_kochfabrik(prompt: str, table: bool = True):
    """Prompt → KOCHfabrik-Style-PNG (bytes). table=True: zufällige
    Tisch-Referenz aus dem Pool (kontext-aware). Gibt (bytes, bg) zurück."""
    key = _gemini_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY fehlt")
    parts, bg = [], None
    pool = _bg_pool()
    if table and pool:
        bg = random.choice(pool)
        parts.append({"inlineData": {"mimeType": "image/png",
                      "data": base64.b64encode(open(bg, "rb").read())
                      .decode()}})
        ctx = ON_TABLE
    else:
        ctx = FREE
    parts.append({"text": PHOTO + ctx + "Motiv: " + prompt.strip()})
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


app = FastAPI(title="KOCHfabrik Studio")
PUBLIC = ("/login.html", "/api/login", "/api/health", "/favicon.ico")


@app.middleware("http")
async def auth_gate(request: Request, call_next):
    path = request.url.path
    if (path in PUBLIC or path.startswith("/assets/")
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


@app.get("/api/health")
def health():
    return {"ok": True, "model": MODEL, "size": IMG_SIZE,
            "aspect": IMG_ASPECT, "key": bool(_gemini_key()),
            "bg_pool": len(_bg_pool()), "users": len(_users())}


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


@app.post("/api/image")
def api_image(r: ImgReq):
    if not r.prompt.strip():
        return JSONResponse({"error": "prompt leer"}, status_code=400)
    try:
        png, bg = image_kochfabrik(r.prompt, r.table)
    except Exception as e:
        return JSONResponse({"error": str(e)[:200]}, status_code=502)
    return {"image": "data:image/png;base64,"
            + base64.b64encode(png).decode(), "model": MODEL,
            "bg": os.path.basename(bg) if bg else None}


@app.get("/")
def index():
    return FileResponse(os.path.join(WEB, "index.html"))


app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
