"""US-046 — Charakterisierungs-Tests (HTTP-Verhaltens-Netz, DB-los).

Friert das HEUTE beobachtete IST-Verhalten der HTTP-Oberflaeche ein, bevor
der Monorepo-Schnitt (Sprint 11) Dateien verschiebt. Die Assertions
beschreiben, wie das System sich verhaelt — NICHT wie es sich verhalten
sollte. Bewusste Charakterisierung: z.B. dass die Sub-Health-Routen
(`/api/angebot/health`, `/api/praesentation/health`) hinter dem Auth-Gate
liegen (401 ohne Cookie), waehrend `/api/health` public ist.

Laeuft DB-los (kein DATABASE_URL): die getesteten Routen brauchen keine DB.
TestClient kommt aus `fastapi.testclient` (httpx im venv, nicht in
requirements.txt — reine Test-Dependency).

Fixtures bewusst lokal (keine conftest-Aenderung — geteilte Test-Infra
eingefroren).
"""
import hashlib
import secrets

import pytest
from fastapi.testclient import TestClient

# Bekannter KF_USERS-Eintrag zum Minten eines gueltigen Session-Cookies.
_EMAIL = "charakter@kf.de"
_SALT = "saltsalt"
_PW = "pw-charakterisierung"
_HASH = hashlib.sha256((_SALT + _PW).encode()).hexdigest()


@pytest.fixture
def app_module(monkeypatch):
    """backend.app DB-los, mit definiertem KF_USERS + Session-Secret.

    DATABASE_URL wird entfernt; die Cookie-Helfer (`make_cookie`,
    `valid_cookie`) lesen KF_USERS/KF_SESSION_SECRET zur Laufzeit, daher
    reicht das Setzen via monkeypatch ohne Re-Import des Moduls.
    """
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("KF_USERS", f"{_EMAIL}|{_SALT}|{_HASH}")
    monkeypatch.setenv("KF_SESSION_SECRET", secrets.token_hex(16))
    import backend.app as a
    return a


@pytest.fixture
def client(app_module):
    return TestClient(app_module.app, follow_redirects=False)


@pytest.fixture
def auth_client(app_module):
    """TestClient mit gueltigem Session-Cookie (passiert das Auth-Gate)."""
    c = TestClient(app_module.app, follow_redirects=False)
    c.cookies.set(app_module.COOKIE, app_module.make_cookie(_EMAIL))
    return c


# (a) /api/health — public, 200, JSON-Shape mit db-Key
def test_health_ok_and_shape(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    # IST: db-Key immer vorhanden; DB-los -> False (kein Crash).
    assert "db" in body
    assert body["db"] is False
    # Weitere Felder der heutigen Shape (Charakterisierung, kein Wunsch).
    for k in ("model", "size", "aspect", "key", "users", "cats", "db_error"):
        assert k in body


# (b) Sub-Health-Routen — IST: hinter dem Auth-Gate (401 ohne Cookie),
#     200 mit gueltigem Cookie. Das ist HEUTE-Verhalten, kein Wunsch:
#     nur /api/health steht in PUBLIC, die beiden Sub-Routen nicht.
def test_angebot_health_gated_without_cookie(client):
    r = client.get("/api/angebot/health")
    assert r.status_code == 401
    assert r.json() == {"error": "auth"}


def test_praesentation_health_gated_without_cookie(client):
    r = client.get("/api/praesentation/health")
    assert r.status_code == 401
    assert r.json() == {"error": "auth"}


def test_angebot_health_authenticated(auth_client):
    r = auth_client.get("/api/angebot/health")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"engine", "error", "model"}


def test_praesentation_health_authenticated(auth_client):
    r = auth_client.get("/api/praesentation/health")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"engine", "korpus", "error"}


# (c) Geschuetzte Routen ohne Cookie — IST einfrieren:
#     API-Pfad -> 401 JSON, Nicht-API-Pfad -> 302 Redirect /login.html.
def test_protected_api_route_returns_401(client):
    r = client.get("/api/angebote")
    assert r.status_code == 401
    assert r.json() == {"error": "auth"}


def test_protected_page_redirects_to_login(client):
    r = client.get("/")
    assert r.status_code == 302
    assert r.headers["location"] == "/login.html"


def test_protected_html_redirects_to_login(client):
    # Auch nicht existierende Seiten laufen ins Gate-Redirect (IST).
    r = client.get("/index.html")
    assert r.status_code == 302
    assert r.headers["location"] == "/login.html"


# (d) Statische/public Seiten erreichbar (kein Cookie noetig).
def test_login_html_reachable(client):
    r = client.get("/login.html")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_oauth_providers_public(client):
    # In PUBLIC gelistet -> erreichbar ohne Cookie (IST: leere Liste DB-los).
    r = client.get("/api/oauth/providers")
    assert r.status_code == 200
    assert "providers" in r.json()
