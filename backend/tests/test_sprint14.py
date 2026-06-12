"""Sprint 14 — API-Kette (US-070→072) TDD-Suite.

TestClient + Cookie-Helfer LOKAL (kein conftest-Umbau, Wave-Plan-konform,
Muster test_sprint13.py). Engine-/Korpus-Calls werden gemockt — NIE echte
Gemini-Calls (Pitfall 1). Synchron, wie die Bestands-Suite.
"""
import hashlib
import os
import secrets

import pytest
from fastapi.testclient import TestClient

# Bekannter KF_USERS-Eintrag zum Minten eines gültigen Session-Cookies.
_EMAIL = "designer@kf.de"
_SALT = "saltsalt"
_PW = "pw-designer-14"
_HASH = hashlib.sha256((_SALT + ":" + _PW).encode()).hexdigest()

_CACHE = os.path.join(os.path.dirname(__file__), "..", "..",
                      "engine", "data", "cache")


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


# ---------------- US-070 (FEATURE-014 EARS 1) ----------------
# /api/designer/texts liefert je Cache-Slide Element-Geometrie + meta
# (w_pt/h_pt) + die image-Elemente — genug für pixelgenaue Overlays.

# Deck mit Text- UND Image-Elementen (kf-ausstattung-location p1 hat beides).
_DECK = "kf-ausstattung-location"


def test_texts_response_has_meta(auth_client):
    """texts-Response liefert meta {w_pt,h_pt} der Slide."""
    r = auth_client.post("/api/designer/texts", json={
        "slides": [{"deck": _DECK, "page": 1}], "offer": None})
    assert r.status_code == 200
    sl = r.json()["slides"][0]
    assert "meta" in sl, sl
    assert set(sl["meta"]) >= {"w_pt", "h_pt"}
    assert isinstance(sl["meta"]["w_pt"], (int, float))
    assert isinstance(sl["meta"]["h_pt"], (int, float))
    assert sl["meta"]["w_pt"] > 0 and sl["meta"]["h_pt"] > 0


def test_texts_have_geometry_and_style(auth_client):
    """Jeder Text trägt zusätzlich x/y/w/h + color/weight/italic."""
    r = auth_client.post("/api/designer/texts", json={
        "slides": [{"deck": _DECK, "page": 1}], "offer": None})
    assert r.status_code == 200
    texts = r.json()["slides"][0]["texts"]
    assert texts, "Ist-Texte fehlen"
    t = texts[0]
    # Bestands-Felder (#66) unverändert vorhanden.
    assert {"i", "text", "size"} <= set(t), t
    # Neue Geometrie/Stil-Felder.
    for k in ("x", "y", "w", "h"):
        assert k in t, (k, t)
        assert isinstance(t[k], (int, float))
    assert "color" in t and "weight" in t and "italic" in t
    assert isinstance(t["italic"], bool)


def test_texts_images_list(auth_client):
    """images[] = {i,x,y,w,h} der t=='image'-Elemente der Slide."""
    r = auth_client.post("/api/designer/texts", json={
        "slides": [{"deck": _DECK, "page": 1}], "offer": None})
    assert r.status_code == 200
    sl = r.json()["slides"][0]
    assert "images" in sl, sl
    assert sl["images"], "kf-ausstattung-location p1 hat ein Bild"
    img = sl["images"][0]
    assert set(img) == {"i", "x", "y", "w", "h"}, img
    assert isinstance(img["i"], int)
    for k in ("x", "y", "w", "h"):
        assert isinstance(img[k], (int, float))


def test_texts_preview_notext_url(auth_client):
    """preview_notext-URL je Slide, zeigt auf die Notext-Preview-Route."""
    r = auth_client.post("/api/designer/texts", json={
        "slides": [{"deck": _DECK, "page": 1}], "offer": None})
    assert r.status_code == 200
    sl = r.json()["slides"][0]
    assert sl.get("preview_notext") == \
        f"/api/slidesuche/preview-notext/{_DECK}/1.png"


def test_texts_bestandsfelder_unveraendert(auth_client):
    """#66-Regression: i/text/size + suggestions bleiben unverändert."""
    gang = {"label": "Hauptgang", "dishes": [
        {"name": "Rinderfilet", "desc": "mit Jus"}]}
    r = auth_client.post("/api/designer/texts", json={
        "slides": [{"deck": "10-182-raumkarussell-gmbh-12-09-2026",
                    "page": 2, "kind": "gang", "gang": gang}],
        "offer": None})
    assert r.status_code == 200
    sl = r.json()["slides"][0]
    assert "suggestions" in sl
    for t in sl["texts"]:
        assert isinstance(t["i"], int)
        assert isinstance(t["text"], str)
        assert isinstance(t["size"], (int, float))


def test_texts_unknown_slide_graceful(auth_client):
    """Unbekannte Slide → leere texts/images, meta-Default, kein Crash."""
    r = auth_client.post("/api/designer/texts", json={
        "slides": [{"deck": "gibtsnicht", "page": 1}], "offer": None})
    assert r.status_code == 200
    sl = r.json()["slides"][0]
    assert sl["texts"] == [] and sl["images"] == []
    assert "meta" in sl


# ---------------- US-070 — Notext-Preview-Route ----------------

def test_preview_notext_requires_auth(client):
    """Route hinter dem Auth-Gate (401 ohne Cookie)."""
    r = client.get(f"/api/slidesuche/preview-notext/{_DECK}/1.png")
    assert r.status_code == 401


def test_preview_notext_404_for_unrendered(auth_client):
    """Ungerenderte Slide (kein preview_notext-PNG) → 404, kein Crash."""
    r = auth_client.get(f"/api/slidesuche/preview-notext/{_DECK}/1.png")
    assert r.status_code == 404


def test_preview_notext_path_traversal(auth_client):
    """Pfad-Traversal/ungültiger Deck → 400."""
    r = auth_client.get("/api/slidesuche/preview-notext/..%2F..%2Fx/1.png")
    assert r.status_code in (400, 404)


def test_preview_notext_200_when_present(auth_client):
    """200 + image/png, sobald ein Notext-PNG existiert (sonst skip)."""
    png = os.path.join(_CACHE, _DECK, "preview_notext", "p1.png")
    if not os.path.isfile(png):
        pytest.skip("kein Notext-Sample-PNG (US-069 rendert die)")
    r = auth_client.get(f"/api/slidesuche/preview-notext/{_DECK}/1.png")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
