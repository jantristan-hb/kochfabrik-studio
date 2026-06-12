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
    # Engine/Korpus vorhanden gaukeln, DB-Offer-Laden + Parser + embed
    # mocken (embed Modul-Ebene — NIE echte Gemini-Calls, Pitfall 1).
    monkeypatch.setattr(d, "ENGINE_OK", True)
    monkeypatch.setattr(d, "_korpus_ok", lambda: True)
    monkeypatch.setattr(d, "embed", _fake_embed_factory())

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


# ---------------- US-062 (FEATURE-011 EARS 1+4) ----------------

# Ein Offer-md mit zwei echten Gängen — geht durch parse_offer_dishes.
_OFFER_MD = (
    "## Angebot — ACME GmbH (Sommerfest)\n\n"
    "| Veranstaltungsdatum | 2026-07-01 |\n\n"
    "### Vorspeise\n\n"
    "Tomatensuppe\nmit Basilikum\n\n"
    "### Hauptgang\n\n"
    "Rinderfilet\nmit Kartoffelgratin\n\n")


def _fake_embed_factory():
    """embed(texts) → ein 768-dim Vektor je Text (deterministisch, ohne
    Netz). Modul-Ebene-Mock (Pitfall 1)."""
    import numpy as np

    def _embed(texts):
        rng = np.random.default_rng(42)
        return rng.standard_normal((len(texts), 768)).astype(np.float64)
    return _embed


def _prep_ranking(d, monkeypatch):
    monkeypatch.setattr(d, "ENGINE_OK", True)
    monkeypatch.setattr(d, "_korpus_ok", lambda: True)
    monkeypatch.setattr(d, "embed", _fake_embed_factory())


def test_suggest_groups_topn(auth_client, monkeypatch):
    """gemockter embed → je Gang Gruppe mit ≤5 Kandidaten, jeder mit
    deck/page/score/preview/label (EARS 1)."""
    import backend.routers.designer as d
    _prep_ranking(d, monkeypatch)
    r = auth_client.post("/api/designer/suggest",
                         json={"offer": _OFFER_MD})
    assert r.status_code == 200
    body = r.json()
    gangs = [g for g in body["groups"] if g["kind"] == "gang"]
    assert len(gangs) == 2                         # Vorspeise + Hauptgang
    for g in gangs:
        assert 1 <= len(g["candidates"]) <= 5
        c = g["candidates"][0]
        assert set(c) == {"deck", "page", "score", "preview", "label"}
        assert isinstance(c["page"], int)
        assert isinstance(c["score"], float)
        assert c["preview"].startswith("/api/slidesuche/preview/")


def test_suggest_pflicht_gruppe(auth_client, monkeypatch):
    """Slot-Semantik (#64): Frame-Kategorien als EIGENE Gruppen in
    DECK-Reihenfolge — COVER zuerst, KONTAKT zuletzt, Gänge dazwischen
    (zwischen CREW und PERSONAL). Ersetzt die alte Sammel-Pflicht-Gruppe."""
    import backend.routers.designer as d
    _prep_ranking(d, monkeypatch)
    r = auth_client.post("/api/designer/suggest",
                         json={"offer": _OFFER_MD})
    assert r.status_code == 200
    groups = r.json()["groups"]
    kinds = [g["kind"] for g in groups]
    labels = [g["label"] for g in groups]
    assert kinds[0] == "cover" and labels[0] == "COVER"
    assert labels[-1] == "KONTAKT"
    assert kinds.count("pflicht") >= 4             # Crew/Personal/Ausst./Wert./Kontakt
    gang_idx = [i for i, k in enumerate(kinds) if k == "gang"]
    crew_idx = labels.index("DEINE CATERING- & EVENT-CREW IM NORDEN")
    personal_idx = labels.index("PERSONAL")
    assert gang_idx and crew_idx < gang_idx[0] and gang_idx[-1] < personal_idx
    for g in groups:
        assert g["candidates"]                     # kein leerer Slot


def test_suggest_embed_fail_502(auth_client, monkeypatch):
    """embed wirft → 502 gekürzte Meldung (EARS 3)."""
    import backend.routers.designer as d
    monkeypatch.setattr(d, "ENGINE_OK", True)
    monkeypatch.setattr(d, "_korpus_ok", lambda: True)

    def _boom(texts):
        raise RuntimeError("gemini down " + "x" * 500)
    monkeypatch.setattr(d, "embed", _boom)
    r = auth_client.post("/api/designer/suggest",
                         json={"offer": _OFFER_MD})
    assert r.status_code == 502
    assert len(r.json()["error"]) <= 240           # gekürzt


def test_designer_uses_bundle_layer():
    """statisch: designer.py ohne np.load, mit bundle-Import (EARS 4)."""
    import os
    src = os.path.join(os.path.dirname(__file__), "..", "routers",
                       "designer.py")
    code = open(src, encoding="utf-8").read()
    assert "np.load" not in code
    assert "import bundle" in code



# Bug #60 — Regression: request.form() liefert STARLETTE-UploadFiles;
# isinstance gegen die FastAPI-Subklasse war immer False → JEDER echte
# multipart-Upload bekam 400 "kein PDF im Upload". Der US-061-Test
# deckte den Upload-Zweig nie mit files= ab (Testlücke).
def test_suggest_pdf_upload_multipart(auth_client, monkeypatch):
    import assemble
    import compose_offer
    import backend.routers.designer as d
    _prep_ranking(d, monkeypatch)
    monkeypatch.setattr(assemble, "parse_header",
                        lambda src, **kw: ("Upload GmbH", "1. Juli 2026"))
    monkeypatch.setattr(compose_offer, "parse_offer_dishes",
                        lambda src, **kw: [("Vorspeise",
                                            [("Suppe", "klar")])])
    r = auth_client.post(
        "/api/designer/suggest",
        files={"file": ("angebot.pdf", b"%PDF-1.4 fake",
                        "application/pdf")})
    assert r.status_code != 400, r.text   # Bug #60: 400 "kein PDF im Upload"
    assert r.status_code == 200, r.text
    assert r.json()["offer"]["kunde"] == "Upload GmbH"


# Bug #62 — Pauschal-Angebote (0 Menü-Gänge) bekamen nur die Pflicht-
# Gruppe. Fallback: EINE kind=konzept-Gruppe aus Speisen-Positionen +
# Cateringkonzept, gleiche Ranking-Maschinerie.
def test_suggest_pauschal_konzept_fallback(auth_client, monkeypatch):
    import assemble
    import compose_offer
    import backend.routers.designer as d
    _prep_ranking(d, monkeypatch)
    monkeypatch.setattr(assemble, "parse_header",
                        lambda src, **kw: ("Howden GmbH", "11. Juni 2025"))
    monkeypatch.setattr(compose_offer, "parse_offer_dishes",
                        lambda src, **kw: [])          # Pauschal: 0 Gänge
    monkeypatch.setattr(d, "_konzept_text",
                        lambda src: "Einweihungsfeier Flying Dinner",
                        raising=False)
    r = auth_client.post(
        "/api/designer/suggest",
        files={"file": ("angebot.pdf", b"%PDF-1.4 fake",
                        "application/pdf")})
    assert r.status_code == 200, r.text
    kinds = [g["kind"] for g in r.json()["groups"]]
    assert "konzept" in kinds, kinds          # Bug #62: nur ["pflicht"]
    kg = [g for g in r.json()["groups"] if g["kind"] == "konzept"][0]
    assert kg["candidates"], "Konzept-Gruppe ohne Kandidaten"
    assert "konzept" not in r.json()["offer"], "internes Feld geleakt"


# #66 — Texte-Editor: Ist-Texte + Auto-Overrides aus dem Angebot.
def test_designer_texts_endpoint(auth_client):
    r = auth_client.post("/api/designer/texts", json={
        "slides": [{"deck": "kf-ausstattung-location", "page": 1}],
        "offer": None})
    assert r.status_code == 200
    sl = r.json()["slides"][0]
    assert sl["texts"], "Ist-Texte fehlen"
    assert any("Ausstattung" in t["text"] for t in sl["texts"])


def test_designer_texts_requires_auth(client):
    r = client.post("/api/designer/texts", json={"slides": []})
    assert r.status_code == 401


def test_designer_texts_gang_suggestions(auth_client):
    gang = {"label": "Hauptgang", "dishes": [
        {"name": "Rinderfilet", "desc": "mit Jus"},
        {"name": "Gemüse", "desc": ""}]}
    r = auth_client.post("/api/designer/texts", json={
        "slides": [{"deck": "10-182-raumkarussell-gmbh-12-09-2026",
                    "page": 2, "kind": "gang", "gang": gang}],
        "offer": None})
    assert r.status_code == 200
    sug = r.json()["slides"][0]["suggestions"]
    assert sug, "keine Auto-Overrides"
    vals = " | ".join(sug.values())
    assert "HAUPTGANG" in vals
    assert "Rinderfilet — mit Jus" in vals


def test_download_applies_overrides(auth_client):
    """E2E (#66): Override-Text landet wirklich in der PPTX (XML-Check)."""
    import base64
    import io
    import shutil
    import zipfile

    import pytest as _pytest
    if not shutil.which("node"):
        _pytest.skip("node fehlt")
    marker = "JAN OVERRIDE TESTTEXT"
    r = auth_client.post("/api/slidesuche/download", json={"slides": [
        {"deck": "kf-ausstattung-location", "page": 1,
         "overrides": {"5": marker}}]})
    # Override auf irgendein Text-Element — Index 5 muss kein Text sein;
    # robust: alle Text-Indizes durchprobieren bis der Marker drin ist.
    if r.status_code == 200:
        raw = base64.b64decode(r.json()["pptx"].split(",", 1)[1])
        xml = b""
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for n in z.namelist():
                if n.startswith("ppt/slides/") and n.endswith(".xml"):
                    xml += z.read(n)
        if marker.encode() in xml:
            return
    tx = auth_client.post("/api/designer/texts", json={
        "slides": [{"deck": "kf-ausstattung-location", "page": 1}]})
    idx = str(tx.json()["slides"][0]["texts"][0]["i"])
    r = auth_client.post("/api/slidesuche/download", json={"slides": [
        {"deck": "kf-ausstattung-location", "page": 1,
         "overrides": {idx: marker}}]})
    assert r.status_code == 200, r.text
    raw = base64.b64decode(r.json()["pptx"].split(",", 1)[1])
    xml = b""
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for n in z.namelist():
            if n.startswith("ppt/slides/") and n.endswith(".xml"):
                xml += z.read(n)
    assert marker.encode() in xml, "Override nicht in der PPTX"
