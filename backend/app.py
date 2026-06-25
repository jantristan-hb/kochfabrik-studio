"""KOCHfabrik Studio — Backend (Phase 1: Bildgenerator + Login).

BEWUSST KEIN Präsentationsgenerator (Jans Vorgabe — Phase 2).
Framework-agnostischer Kern (image_kochfabrik). Auth + User rein
env-getrieben (Repo ist public → NIE Klartext/Hash im Code):
  KF_USERS         = "email|salt|sha256hex;email2|salt2|hash2"
  KF_SESSION_SECRET= random hex (Cookie-Signatur)
Hash-Schema: sha256(salt + ":" + passwort).

US-053/054: app.py ist reine KOMPOSITION (<200 Z.) — FastAPI()-Setup,
Auth-Gate-Middleware, include_router(×5), /api/health, / und Static-Mount.
Die Domänen-Routen leben in backend/routers/* , der geteilte Kern (Auth-/
Cookie-Helfer, Bild-Kern, Kategorien, Gemini-Prompts, Engine-Import-Block)
in backend/engine_glue.py. Router importieren NICHT auf app.py (kein
Import-Zyklus — Pitfall 2).
"""
import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

# Re-Export der Helfer hält das bestehende app-Modul-Surface stabil
# (Charakterisierungs-Tests greifen app._secret / app.make_cookie /
# app.valid_cookie / app._owner / app.COOKIE).
from .engine_glue import (                                          # noqa
    WEB, MODEL, IMG_SIZE, IMG_ASPECT, COOKIE, SESSION_DAYS, CATS,
    _gemini_key, _bg_pool, _users, _secret, make_cookie, verify_login,
    valid_cookie, _owner, image_kochfabrik, ENGINE_OK, ENGINE_ERR)
# _today_de / _ensure_correct_dates leben jetzt im Angebots-Router —
# Re-Export, weil Charakterisierungs-Tests app._today_de /
# app._ensure_correct_dates aufrufen.
from .routers.angebot import _today_de, _ensure_correct_dates       # noqa

app = FastAPI(title="KOCHfabrik Studio")

# Router (US-053/054) — Registrier-Reihenfolge wie im Pre-Refactor-Stand:
# slidesuche → auth (login/logout) → bildgenerator (cats/image) →
# angebot/kunden/stats → praesentation; oauth steckt im auth-Router.
from backend.slidesuche import router as _slidesuche_router  # noqa: E402
from backend.routers.auth import router as _auth_router  # noqa: E402
from backend.routers.bildgenerator import (  # noqa: E402
    router as _bildgenerator_router)
from backend.routers.angebot import router as _angebot_router  # noqa: E402
from backend.routers.praesentation import (  # noqa: E402
    router as _praesentation_router)
from backend.routers.designer import router as _designer_router  # noqa: E402

app.include_router(_slidesuche_router)

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


@app.middleware("http")
async def no_cache_assets(request: Request, call_next):
    """HTML/JS/CSS immer revalidieren lassen. Ohne explizite Header cacht der
    Browser die Seiten heuristisch — geänderte Inline-CSS in *.html (kein
    Query-Buster möglich) schlägt dann nicht durch. `no-cache` erzwingt
    Revalidierung (ETag → 304 wenn unverändert, also weiter effizient)."""
    resp = await call_next(request)
    p = request.url.path
    if p == "/" or p.endswith((".html", ".js", ".css")):
        resp.headers["Cache-Control"] = "no-cache"
    return resp


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


app.include_router(_auth_router)            # login/logout/oauth
app.include_router(_bildgenerator_router)   # cats/image
app.include_router(_angebot_router)         # angebot/kunden/stats
app.include_router(_praesentation_router)   # praesentation
app.include_router(_designer_router)        # designer (US-061)


@app.get("/")
def index():
    return FileResponse(os.path.join(WEB, "index.html"))


app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
