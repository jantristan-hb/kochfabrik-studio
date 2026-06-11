"""Sprint 13 — API-Kette (US-061→062) TDD-Suite.

TestClient + make_cookie LOKAL (kein conftest-Umbau, Wave-Plan-konform).
Gemini-embed wird via monkeypatch auf Modul-Ebene gemockt — NIE echte
API-Calls (Boundary). Synchron, wie die Bestands-Suite (kein async-Plugin).
"""
import hashlib
import secrets

import pytest
from fastapi.testclient import TestClient

# Bekannter KF_USERS-Eintrag zum Minten eines gültigen Session-Cookies.
_EMAIL = "designer@kf.de"
_SALT = "saltsalt"
_PW = "pw-designer-13"
_HASH = hashlib.sha256((_SALT + ":" + _PW).encode()).hexdigest()


@pytest.fixture
def app_module(monkeypatch):
    """backend.app DB-los, definierte KF_USERS + Session-Secret."""
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
    """TestClient mit gültigem Session-Cookie (passiert das Auth-Gate)."""
    c = TestClient(app_module.app, follow_redirects=False)
    c.cookies.set(app_module.COOKIE, app_module.make_cookie(_EMAIL))
    return c


# ---------------- US-061 (FEATURE-011 EARS 2+3) ----------------

def test_designer_health_shape(auth_client):
    """GET /api/designer/health → 200, keys engine/korpus/embed (bool)."""
    r = auth_client.get("/api/designer/health")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"engine", "korpus", "embed"}
    assert isinstance(body["embed"], bool)


def test_suggest_requires_auth(client):
    """POST suggest ohne Cookie → 401 (hinter dem Auth-Gate)."""
    r = client.post("/api/designer/suggest", json={"offer": "x"})
    assert r.status_code == 401
    assert r.json() == {"error": "auth"}


def test_suggest_invalid_body(auth_client):
    """Weder PDF noch offer_id noch offer → 400/422."""
    r = auth_client.post("/api/designer/suggest", json={})
    assert r.status_code in (400, 422)


def test_suggest_offer_id_parsing(auth_client, monkeypatch):
    """gemockt: offer_id → offer-Block {kunde,datum,gaenge} (EARS 2)."""
    import backend.routers.designer as d
    # Engine/Korpus vorhanden gaukeln, DB-Offer-Laden + Parser mocken.
    monkeypatch.setattr(d, "ENGINE_OK", True)
    monkeypatch.setattr(d, "_korpus_ok", lambda: True)

    async def _fake_load(owner, oid):        # _load_offer_md ist async
        return "## Angebot — ACME (Sommerfest)"
    monkeypatch.setattr(d, "_load_offer_md", _fake_load)
    monkeypatch.setattr(
        d, "_parse_offer_md",
        lambda md: {"kunde": "ACME", "datum": "2026-07-01",
                    "gaenge": [{"label": "Vorspeise",
                                "dishes": [{"name": "Suppe",
                                            "desc": ""}]}]})
    r = auth_client.post("/api/designer/suggest", json={"offer_id": 42})
    assert r.status_code == 200
    body = r.json()
    assert set(body["offer"]) == {"kunde", "datum", "gaenge"}
    assert body["offer"]["kunde"] == "ACME"
    assert body["offer"]["gaenge"][0]["label"] == "Vorspeise"
    assert "groups" in body                      # Stub in US-061: []


def test_suggest_graceful_503(auth_client, monkeypatch):
    """Engine/Korpus weg → 503 mit Klartext (EARS 3), kein 500."""
    import backend.routers.designer as d
    monkeypatch.setattr(d, "ENGINE_OK", False)
    monkeypatch.setattr(d, "ENGINE_ERR", "Engine-Pfad fehlt")
    r = auth_client.post("/api/designer/suggest",
                         json={"offer": "## Angebot — X"})
    assert r.status_code == 503
    assert "error" in r.json()
    assert r.json()["error"]                      # Klartext, nicht leer
