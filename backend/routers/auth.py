"""Auth-Router (US-053) — login/logout + OAuth2 (US-019).

1:1 aus app.py extrahiert. Reihenfolge der Routen-Registrierung bleibt
gleich (login → logout in app.py vor cats/image, oauth-Block am Ende vor
index/static). Auth-/Cookie-Helfer liegen in backend.engine_glue (kein
Import auf app.py — Pitfall 2)."""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from ..engine_glue import COOKIE, SESSION_DAYS, make_cookie, verify_login

router = APIRouter()


class Login(BaseModel):
    email: str
    password: str


@router.post("/api/login")
def login(b: Login):
    if not verify_login(b.email, b.password):
        return JSONResponse({"error": "ungültig"}, status_code=401)
    r = JSONResponse({"ok": True})
    r.set_cookie(COOKIE, make_cookie(b.email), max_age=SESSION_DAYS*86400,
                 httponly=True, samesite="lax", secure=True)
    return r


@router.post("/api/logout")
def logout():
    r = JSONResponse({"ok": True})
    r.delete_cookie(COOKIE)
    return r


# ---------------- OAuth2 (US-019, env-gated, zero-regression) -----
@router.get("/api/oauth/providers")
def oauth_providers():
    from .. import oauth as _o
    return {"providers": sorted(_o.providers().keys())}


@router.get("/api/oauth/{provider}/login")
def oauth_login(provider: str, request: Request):
    import secrets
    from .. import oauth as _o
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


@router.get("/api/oauth/{provider}/callback")
async def oauth_callback(provider: str, request: Request):
    from .. import oauth as _o
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
        from ..store import ensure_user
        await ensure_user(email)
    except Exception:                                               # noqa
        pass
    r = RedirectResponse("/", status_code=302)
    r.set_cookie(COOKIE, make_cookie(email),
                 max_age=SESSION_DAYS * 86400,
                 httponly=True, samesite="lax", secure=True)
    r.delete_cookie("kf_oauth_state"); r.delete_cookie("kf_oauth_redir")
    return r
