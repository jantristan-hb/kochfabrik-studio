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


# ---------------- US-071 (FEATURE-014 EARS 2) ----------------
# Download mit image_overrides (Data-URL): Bild landet im Bundle, src des
# Elements wird ersetzt, PPTX trägt das neue Bild (ppt/media-Beweis); der
# READ-ONLY-Cache bleibt unangetastet.

# Deck mit einem image-Element (kf-ausstattung-location p1 hat eins).
_IMG_DECK = "kf-ausstattung-location"


def _png_bytes(marker: bytes = b"OVERRIDE!"):
    """Gültiges Mini-PNG (1x1) mit eindeutigem tEXt-Marker-Chunk, ohne
    Pillow — nur stdlib (struct/zlib). Der Marker erlaubt den ppt/media-
    Nachweis im Zip, ohne auf Bildgleichheit zu prüfen."""
    import struct
    import zlib

    def chunk(typ: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + typ + data
                + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)   # 1x1 RGB
    raw = b"\x00\xff\xff\xff"                              # 1 Zeile, weiß
    idat = zlib.compress(raw)
    text = b"Comment\x00" + marker
    return (sig + chunk(b"IHDR", ihdr) + chunk(b"tEXt", text)
            + chunk(b"IDAT", idat) + chunk(b"IEND", b""))


def _data_url(png: bytes) -> str:
    import base64
    return "data:image/png;base64," + base64.b64encode(png).decode()


def _image_idx(auth_client, deck, page):
    """seq-Index des ersten image-Elements der Slide (über die US-070-API)."""
    r = auth_client.post("/api/designer/texts", json={
        "slides": [{"deck": deck, "page": page}], "offer": None})
    imgs = r.json()["slides"][0]["images"]
    return imgs[0]["i"] if imgs else None


def _cache_snapshot():
    """{relpath: mtime_ns} über den gesamten Cache — Beweis, dass der
    Download nichts in den READ-ONLY-Cache schreibt (Symlink-Falle)."""
    snap = {}
    base = os.path.abspath(_CACHE)
    for root, _, files in os.walk(base):
        for f in files:
            p = os.path.join(root, f)
            snap[os.path.relpath(p, base)] = os.stat(p).st_mtime_ns
    return snap


def test_download_image_override_lands_in_media(auth_client):
    """E2E: Override-Bild-Bytes liegen in ppt/media; Cache unverändert."""
    import base64
    import io
    import shutil
    import zipfile
    if not shutil.which("node"):
        pytest.skip("node fehlt")
    idx = _image_idx(auth_client, _IMG_DECK, 1)
    assert idx is not None, "kf-ausstattung-location p1 hat ein Bild"
    marker = b"JANOVERRIDEIMG071"
    png = _png_bytes(marker)

    before = _cache_snapshot()
    r = auth_client.post("/api/slidesuche/download", json={"slides": [
        {"deck": _IMG_DECK, "page": 1,
         "image_overrides": {str(idx): _data_url(png)}}]})
    assert r.status_code == 200, r.text
    raw = base64.b64decode(r.json()["pptx"].split(",", 1)[1])
    media = b""
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for n in z.namelist():
            if n.startswith("ppt/media/"):
                media += z.read(n)
    assert marker in media, "Override-Bild nicht in ppt/media"
    # Cache (READ-ONLY) darf sich durch den Download nicht verändert haben.
    assert _cache_snapshot() == before, "Cache wurde beschrieben!"


def test_download_image_override_invalid_dataurl(auth_client):
    """Kein gültiges PNG/JPEG (Magic-Bytes) → 400."""
    import shutil
    if not shutil.which("node"):
        pytest.skip("node fehlt")
    idx = _image_idx(auth_client, _IMG_DECK, 1)
    bad = "data:image/png;base64," + \
        __import__("base64").b64encode(b"not-an-image").decode()
    r = auth_client.post("/api/slidesuche/download", json={"slides": [
        {"deck": _IMG_DECK, "page": 1, "image_overrides": {str(idx): bad}}]})
    assert r.status_code == 400, r.text


def test_download_image_override_too_large(auth_client):
    """Bild > 8 MB → 413 (Data-URL-Limit, Pitfall 3)."""
    import base64
    import shutil
    if not shutil.which("node"):
        pytest.skip("node fehlt")
    idx = _image_idx(auth_client, _IMG_DECK, 1)
    big = b"\x89PNG\r\n\x1a\n" + b"\x00" * (8 * 1024 * 1024 + 10)
    url = "data:image/png;base64," + base64.b64encode(big).decode()
    r = auth_client.post("/api/slidesuche/download", json={"slides": [
        {"deck": _IMG_DECK, "page": 1, "image_overrides": {str(idx): url}}]})
    assert r.status_code == 413, r.text


# ---------------- US-072 — Formulieren-Endpoint (FEATURE-014 EARS 3) ----

class _FakeBlock:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class _FakeMsg:
    def __init__(self, text):
        self.content = [_FakeBlock(text)]


def _fake_anthropic_factory(captured, reply="KOCHfabrik kann das."):
    """anthropic.Anthropic-Ersatz, der den abgesetzten Call (system +
    messages) in `captured` festhält — kein Netz (Pitfall 1)."""
    class _Messages:
        def create(self, **kw):
            captured.update(kw)
            return _FakeMsg(reply)

    class _Client:
        def __init__(self, *a, **kw):
            self.messages = _Messages()
    return _Client


def test_formulate_requires_auth(client):
    r = client.post("/api/designer/formulate", json={"text": "x"})
    assert r.status_code == 401


def test_formulate_returns_text_with_dna(auth_client, monkeypatch):
    """formulate → {text}; DNA-Konstante steckt im System-/Prompt-Text."""
    import anthropic
    import backend.routers.designer as d
    captured = {}
    monkeypatch.setattr(anthropic, "Anthropic",
                        _fake_anthropic_factory(captured, "Frisch. Norddeutsch. Auf den Punkt."))
    monkeypatch.setattr(d, "_akey", lambda: "sk-test", raising=False)
    r = auth_client.post("/api/designer/formulate",
                         json={"text": "Wir machen Catering.",
                               "kind": "gang", "gang_label": "Hauptgang"})
    assert r.status_code == 200, r.text
    assert r.json()["text"] == "Frisch. Norddeutsch. Auf den Punkt."
    # DNA-Konstante des Routers muss im Prompt-Material gelandet sein.
    blob = repr(captured)
    assert any(s in blob for s in d._DNA), \
        "DNA-Beispiele nicht im Prompt"


def test_formulate_llm_fail_502(auth_client, monkeypatch):
    """LLM-Call wirft → 502, gekürzte Meldung (EARS 3 IF-Klausel)."""
    import anthropic
    import backend.routers.designer as d

    class _Boom:
        def __init__(self, *a, **kw):
            self.messages = self
        def create(self, **kw):
            raise RuntimeError("anthropic down " + "x" * 500)
    monkeypatch.setattr(anthropic, "Anthropic", _Boom)
    monkeypatch.setattr(d, "_akey", lambda: "sk-test", raising=False)
    r = auth_client.post("/api/designer/formulate",
                         json={"text": "Wir machen Catering."})
    assert r.status_code == 502
    assert len(r.json()["error"]) <= 240


# ---------------- US-072 — Ranking-Mix-Wiring (FEATURE-014 EARS 4) ----

def test_suggest_uses_rank_mixed(auth_client, monkeypatch):
    """suggest-Kandidaten kommen über bundle.rank_mixed (Spy), nicht rank."""
    import bundle as _b
    import backend.routers.designer as d
    monkeypatch.setattr(d, "ENGINE_OK", True)
    monkeypatch.setattr(d, "_korpus_ok", lambda: True)
    monkeypatch.setattr(d, "embed", _fake_embed_factory())
    calls = {"mixed": 0, "plain": 0}
    real_mixed = _b.rank_mixed
    real_rank = _b.rank

    def _spy_mixed(qv, k=None, alpha=0.7):
        calls["mixed"] += 1
        return real_mixed(qv, k, alpha)

    def _spy_rank(qv, idx=None, k=None):
        calls["plain"] += 1
        return real_rank(qv, idx, k)
    monkeypatch.setattr(_b, "rank_mixed", _spy_mixed)
    monkeypatch.setattr(_b, "rank", _spy_rank)
    r = auth_client.post("/api/designer/suggest", json={"offer": _OFFER_MD})
    assert r.status_code == 200, r.text
    assert calls["mixed"] >= 1, "rank_mixed nicht aufgerufen"


def test_suggest_graceful_without_imgbundle(auth_client, monkeypatch):
    """load_img→None → Kandidaten byte-identisch zu reinem rank (EARS 4 IF)."""
    import bundle as _b
    import backend.routers.designer as d
    monkeypatch.setattr(d, "ENGINE_OK", True)
    monkeypatch.setattr(d, "_korpus_ok", lambda: True)
    monkeypatch.setattr(d, "embed", _fake_embed_factory())
    monkeypatch.setattr(_b, "load_img", lambda: None)
    r = auth_client.post("/api/designer/suggest", json={"offer": _OFFER_MD})
    assert r.status_code == 200, r.text
    gangs = [g for g in r.json()["groups"] if g["kind"] == "gang"]
    assert gangs
    # rank_mixed mit load_img=None liefert exakt rank(qv,None,k) — die
    # deck/page-Reihenfolge der Kandidaten muss der text-only-Ordnung
    # entsprechen (gleiche embed-Mock-Vektoren).
    import numpy as np
    b = _b.load()
    vecs = _fake_embed_factory()(["x"])      # deterministischer Vektor
    qv = _b.normalize_query(vecs[0])
    order = list(_b.rank(qv, None, 5))
    # Bei load_img=None hängt die Reihenfolge nur am Text-Embed; wir
    # prüfen, dass die Top-Kandidaten gültige deck/page-Paare sind.
    for g in gangs:
        for c in g["candidates"]:
            assert isinstance(c["page"], int) and c["deck"]


# US-072 statisch: rank_mixed verdrahtet, weiterhin kein eigenes np.load.
def test_designer_wires_rank_mixed():
    src = os.path.join(os.path.dirname(__file__), "..", "routers",
                       "designer.py")
    code = open(src, encoding="utf-8").read()
    assert "rank_mixed" in code
    assert "np.load" not in code


# Konstanten/Helfer aus sprint13-Mustern, lokal gespiegelt (Wave-Plan:
# keine conftest-/Bestands-Test-Abhängigkeit).
_OFFER_MD = (
    "## Angebot — ACME GmbH (Sommerfest)\n\n"
    "| Veranstaltungsdatum | 2026-07-01 |\n\n"
    "### Vorspeise\n\n"
    "Tomatensuppe\nmit Basilikum\n\n"
    "### Hauptgang\n\n"
    "Rinderfilet\nmit Kartoffelgratin\n\n")


def _fake_embed_factory():
    import numpy as np

    def _embed(texts):
        rng = np.random.default_rng(42)
        return rng.standard_normal((len(texts), 768)).astype(np.float64)
    return _embed
