"""US-018/019 — OAuth2 (Microsoft/Google), stdlib-only, env-gated.

Provider nur AKTIV wenn Client-ID + Secret als ENV gesetzt. Ohne ENV
ist OAuth komplett inaktiv (Null-Regression). Keine neue Dependency.
"""
import json
import os
import urllib.parse
import urllib.request

_G_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
_G_TOKEN = "https://oauth2.googleapis.com/token"
_G_INFO = "https://openidconnect.googleapis.com/v1/userinfo"


def _ms_base() -> str:
    t = os.environ.get("KF_OAUTH_MS_TENANT", "common").strip() or "common"
    return f"https://login.microsoftonline.com/{t}/oauth2/v2.0"


def providers() -> dict:
    """Aktive Provider aus ENV (id+secret Pflicht)."""
    p = {}
    gi = os.environ.get("KF_OAUTH_GOOGLE_ID", "").strip()
    gs = os.environ.get("KF_OAUTH_GOOGLE_SECRET", "").strip()
    if gi and gs:
        p["google"] = {
            "id": gi, "secret": gs, "auth": _G_AUTH, "token": _G_TOKEN,
            "info": _G_INFO, "scope": "openid email profile",
            "label": "Google"}
    mi = os.environ.get("KF_OAUTH_MS_ID", "").strip()
    ms = os.environ.get("KF_OAUTH_MS_SECRET", "").strip()
    if mi and ms:
        b = _ms_base()
        p["microsoft"] = {
            "id": mi, "secret": ms, "auth": b + "/authorize",
            "token": b + "/token",
            "info": "https://graph.microsoft.com/oidc/userinfo",
            "scope": "openid email profile", "label": "Microsoft"}
    return p


def redirect_uri(provider: str, request) -> str:
    base = os.environ.get("KF_OAUTH_REDIRECT_BASE", "").strip().rstrip("/")
    if not base:
        u = request.url
        base = f"{u.scheme}://{u.netloc}"
    return f"{base}/api/oauth/{provider}/callback"


def auth_url(provider: str, state: str, redir: str) -> str | None:
    cfg = providers().get(provider)
    if not cfg:
        return None
    qs = urllib.parse.urlencode({
        "client_id": cfg["id"], "response_type": "code",
        "redirect_uri": redir, "scope": cfg["scope"],
        "state": state, "access_type": "offline",
        "prompt": "select_account"})
    return f"{cfg['auth']}?{qs}"


def _post(url: str, data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={"Accept": "application/json",
                 "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


def _get(url: str, token: str) -> dict:
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {token}",
                      "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


def exchange(provider: str, code: str, redir: str) -> str | None:
    """code → access_token → userinfo → email (lowercased) | None."""
    cfg = providers().get(provider)
    if not cfg:
        return None
    tok = _post(cfg["token"], {
        "client_id": cfg["id"], "client_secret": cfg["secret"],
        "code": code, "grant_type": "authorization_code",
        "redirect_uri": redir})
    at = tok.get("access_token")
    if not at:
        return None
    info = _get(cfg["info"], at)
    email = (info.get("email") or info.get("upn")
             or info.get("preferred_username") or "")
    return email.strip().lower() or None
