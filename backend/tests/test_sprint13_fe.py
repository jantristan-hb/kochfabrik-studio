"""Sprint 13 — Frontend-Smoke der Designer-UI-Kette (US-063 ff.).

Marker-basierte FE-Smoke nach Vorbild der Charakterisierungs-Tests
(`test_charakterisierung.py`: TestClient + Auth-Cookie) und der
statischen read_text-Greps (`test_sprint10_us037.py`). DB-los.

US-063 (Vorstufe): die Designer-Seite wird ausgeliefert (200, hinter
dem Auth-Gate wie jede Modul-Seite), traegt die drei Bereichs-Marker
(`designer-source`/`designer-groups`/`designer-board`), das JS-Modul
ist erreichbar (200, /assets ist public) und versioniert den State
unter `kfDesigner.v1`. Die Nav verlinkt designer.html aus mind. 5
bestehenden Seiten. Klick-Verdrahtung folgt in US-064.

DIESE Datei gehoert der UI-Kette (NICHT test_sprint13.py = API-Kette).
"""
import hashlib
import secrets
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"

# Bekannter KF_USERS-Eintrag zum Minten eines gueltigen Session-Cookies
# (gleiche Mechanik wie test_charakterisierung.py).
_EMAIL = "designer@kf.de"
_SALT = "saltsalt"
_PW = "pw-designer"
_HASH = hashlib.sha256((_SALT + _PW).encode()).hexdigest()


@pytest.fixture
def app_module(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("KF_USERS", f"{_EMAIL}|{_SALT}|{_HASH}")
    monkeypatch.setenv("KF_SESSION_SECRET", secrets.token_hex(16))
    import backend.app as app
    return app


@pytest.fixture
def auth_client(app_module):
    """TestClient mit gueltigem Session-Cookie (passiert das Auth-Gate)."""
    c = TestClient(app_module.app, follow_redirects=False)
    c.cookies.set(app_module.COOKIE, app_module.make_cookie(_EMAIL))
    return c


@pytest.fixture
def client(app_module):
    return TestClient(app_module.app, follow_redirects=False)


# --- US-063: Auslieferung + Marker -----------------------------------------

def test_designer_page_served_200(auth_client):
    r = auth_client.get("/designer.html")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_designer_page_gated_without_cookie(client):
    # Modul-Seite hinter dem Auth-Gate (IST: Nicht-API -> 302 /login.html).
    r = client.get("/designer.html")
    assert r.status_code == 302
    assert r.headers["location"] == "/login.html"


def test_designer_page_has_three_area_markers():
    html = (WEB / "designer.html").read_text(encoding="utf-8")
    for marker in ("designer-source", "designer-groups", "designer-board"):
        assert marker in html, f"Bereichs-Marker fehlt: {marker}"


def test_designer_js_served_200(client):
    # /assets ist public (kein Cookie noetig).
    r = client.get("/assets/designer.js")
    assert r.status_code == 200


def test_designer_js_versioned_state_key():
    js = (WEB / "assets" / "designer.js").read_text(encoding="utf-8")
    assert "kfDesigner.v1" in js, "sessionStorage-Key kfDesigner.v1 fehlt"


def test_designer_js_has_login_redirect_pattern():
    # 401 -> Login-Redirect nach chat.html-Muster.
    js = (WEB / "assets" / "designer.js").read_text(encoding="utf-8")
    assert "/login.html" in js


# --- US-063: Navigation aus bestehenden Seiten -----------------------------

def test_at_least_five_pages_link_designer():
    pages = [p for p in WEB.glob("*.html")
             if "designer.html" in p.read_text(encoding="utf-8")]
    assert len(pages) >= 5, (
        f"Nur {len(pages)} Seiten verlinken designer.html (>=5 erwartet)")


# --- US-065: Storyboard (Add/Reorder/Remove/Session) -----------------------
# Marker-basiert (FE-Smoke nach EPIC-002-Muster): die Board-Funktionen
# leben in designer.js. EARS 3 (FEATURE-012): Reorder + Remove + Reload-feste
# Persistenz via sessionStorage unter dem versionierten Key.

def _designer_js():
    return (WEB / "assets" / "designer.js").read_text(encoding="utf-8")


def test_board_persists_to_versioned_session_key():
    js = _designer_js()
    assert "sessionStorage" in js, "Persistenz via sessionStorage fehlt"
    assert "kfDesigner.v1" in js, "versionierter State-Key fehlt"


def test_board_add_remove_reorder_handlers_present():
    js = _designer_js()
    for fn in ("addToBoard", "removeFromBoard", "moveBoardItem"):
        assert fn in js, f"Board-Handler fehlt: {fn}"


def test_board_dedup_by_deck_page():
    # Duplikat-Schutz: gleiche deck/page nur 1× (Identitaet via deck/page).
    js = _designer_js()
    assert "boardKey" in js and "deck" in js and "page" in js


def test_board_renders_into_board_container():
    js = _designer_js()
    assert "dz-board" in js, "Board-Render-Ziel (#dz-board) nicht referenziert"


def test_board_restores_on_load():
    # Restore beim Laden: renderBoard wird im init-Hook aufgerufen.
    js = _designer_js()
    assert "renderBoard" in js


# --- US-064: Quelle + Vorschlags-Karten (FEATURE-012 EARS 1+5) -------------
# Quelle (Upload + Angebots-Dropdown) -> suggest -> klickbare PNG-Karten je
# Gruppe. Karten-Klick dockt via designer:add ans Board (US-065). EARS 5:
# fehlt das Preview-PNG, zeigt die Karte einen Platzhalter (onerror), statt
# den Kandidaten zu verwerfen.

def _designer_html():
    return (WEB / "designer.html").read_text(encoding="utf-8")


def test_designer_js_wires_suggest():
    # designer.js ruft suggest + die Angebots-Liste auf.
    js = _designer_js()
    assert "/api/designer/suggest" in js, "suggest-Endpoint nicht verdrahtet"
    assert "/api/angebote" in js, "Angebots-Liste nicht verdrahtet"


def test_designer_js_preview_fallback_marker():
    # EARS 5: Platzhalter-/onerror-Pfad für fehlende Preview-PNGs.
    js = _designer_js()
    assert "onerror" in js
    assert ("placeholder" in js.lower() or "platzhalter" in js.lower())


def test_designer_js_renders_groups():
    # Vorschlags-Gruppen werden in den Gruppen-Container gerendert.
    js = _designer_js()
    assert "dz-groups" in js, "Gruppen-Render-Ziel (#dz-groups) fehlt"
    assert "renderGroups" in js


def test_designer_source_panel_markers():
    # Quelle-Panel: Upload-Input, Angebots-Dropdown.
    html = _designer_html()
    assert 'id="dz-upload"' in html
    assert 'id="dz-offer"' in html


# --- US-066: Freitext-Suche im Designer (FEATURE-012 EARS 2) ---------------
# Slidesuche-Treffer landen im selben Storyboard, im selben Karten-Format
# wie die Vorschläge (gemeinsame card()-Render-Funktion). Eigener Treffer-
# Bereich, der die Vorschlags-Gruppen nicht ersetzt.

def test_designer_js_wires_search():
    js = _designer_js()
    assert "/api/slidesuche/search" in js, "search-Endpoint nicht verdrahtet"


def test_designer_js_search_renders_results():
    js = _designer_js()
    # Eigener Treffer-Bereich (#dz-results) — koexistiert mit #dz-groups.
    assert "dz-results" in js, "Such-Treffer-Bereich (#dz-results) fehlt"


def test_designer_search_panel_marker():
    html = _designer_html()
    assert 'id="dz-search"' in html


# --- US-067: Download + End-to-End (FEATURE-012 EARS 4 + FEATURE-011 e2e) --
# Storyboard -> PPTX über /api/slidesuche/download (Data-URL-Muster);
# Button disabled bei leerem Board. E2E beweist den Gesamtflow gegen ein
# committetes Cache-Deck: suggest (gemockt) -> Kandidat -> download -> echte
# PPTX (PK-Magic, >10 KB) über reconstruct.js.

# Committetes Cache-Deck (engine/data/cache/) — die einzigen Decks, die
# lokal UND im Sim-Gate-Container ohne Volume rendern.
_E2E_DECK = "kf-ausstattung-location"
_E2E_PAGE = 1


def test_designer_download_wired():
    js = _designer_js()
    assert "/api/slidesuche/download" in js, "download-Endpoint nicht verdrahtet"
    # disabled-Logik am Download-Button (leeres Board -> kein Download).
    assert "disabled" in js


def _node_available():
    import shutil
    return shutil.which("node") is not None


@pytest.mark.skipif(not _node_available(),
                    reason="node/reconstruct.js nicht verfügbar")
def test_e2e_suggest_to_pptx(auth_client, monkeypatch):
    """E2E: suggest (gemockter embed) liefert Kandidaten -> einer davon
    (committetes Cache-Deck) geht durch /api/slidesuche/download -> echte
    PPTX (PK-Magic + >10 KB). Beweist den Designer-Gesamtflow."""
    import base64

    import backend.routers.designer as d

    # suggest mit gemocktem Parsing + embed (Pitfall 1: NIE echte Gemini).
    import numpy as np

    def _fake_embed(texts):
        rng = np.random.default_rng(7)
        return rng.standard_normal((len(texts), 768)).astype(np.float64)

    monkeypatch.setattr(d, "ENGINE_OK", True)
    monkeypatch.setattr(d, "_korpus_ok", lambda: True)
    monkeypatch.setattr(d, "embed", _fake_embed)
    monkeypatch.setattr(
        d, "_parse_offer_md",
        lambda md: {"kunde": "ACME", "datum": "2026-07-01",
                    "gaenge": [{"label": "Vorspeise",
                                "dishes": [{"name": "Suppe", "desc": ""}]}]})

    sug = auth_client.post("/api/designer/suggest",
                           json={"offer": "## Angebot — ACME"})
    assert sug.status_code == 200
    groups = sug.json()["groups"]
    # Front-Hälfte des Flows verifiziert: es kommen Kandidaten zurück.
    assert any(g["candidates"] for g in groups)

    # Download-Hälfte gegen das committete Cache-Deck (rendert real).
    dl = auth_client.post("/api/slidesuche/download",
                          json={"slides": [{"deck": _E2E_DECK,
                                            "page": _E2E_PAGE}]})
    assert dl.status_code == 200, dl.text
    pptx = dl.json()["pptx"]
    assert pptx.startswith("data:application/vnd.openxmlformats")
    raw = base64.b64decode(pptx.split(",", 1)[1])
    assert raw[:2] == b"PK", "kein gültiges PPTX (PK-Magic fehlt)"
    assert len(raw) > 10 * 1024, "PPTX < 10 KB"


# Bug #62 — FE erklärt Pauschal-Angebote statt stumm nur Pflicht zu zeigen.
def test_designer_js_pauschal_hint():
    import os
    root = os.path.join(os.path.dirname(__file__), "..", "..")
    js = open(os.path.join(root, "web", "assets", "designer.js"),
              encoding="utf-8").read()
    assert "Pauschal-Angebot" in js
    assert '"konzept"' in js


# #64 — Slot-Ansicht: nummerierte Slides, max 3 nebeneinander,
# Slot-bewusstes Einsortieren ins Board.
def test_designer_js_slot_view():
    import os
    root = os.path.join(os.path.dirname(__file__), "..", "..")
    js = open(os.path.join(root, "web", "assets", "designer.js"),
              encoding="utf-8").read()
    assert '"Slide " + slot' in js               # Nummerierung
    assert "slice(0, 3)" in js                   # 2-3 nebeneinander
    assert "weitere" in js                       # +N weitere
    assert "b.slot != null && b.slot <= entry.slot" in js  # Board-Einsortierung
    html = open(os.path.join(root, "web", "designer.html"),
                encoding="utf-8").read()
    assert "dz-cards-row" in html


# #65 — Cover-Bild-Generator: Button über dem Storyboard, /api/image-
# Wiring (category=cover), Prompt aus Angebots-Kontext.
def test_designer_js_cover_generator():
    import os
    root = os.path.join(os.path.dirname(__file__), "..", "..")
    js = open(os.path.join(root, "web", "assets", "designer.js"),
              encoding="utf-8").read()
    assert "/api/image" in js
    assert '"cover"' in js and "coverPrompt" in js
    html = open(os.path.join(root, "web", "designer.html"),
                encoding="utf-8").read()
    assert 'id="dz-genbild"' in html
    assert html.index('id="dz-genbild"') < html.index('id="dz-board"')


# #66 — Texte-Editor: Modus-Umschalter, Bild-links/Text-rechts-Layout,
# Auto-Override-Vorbelegung, Download mit Overrides.
def test_designer_js_texts_editor():
    import os
    root = os.path.join(os.path.dirname(__file__), "..", "..")
    js = open(os.path.join(root, "web", "assets", "designer.js"),
              encoding="utf-8").read()
    assert "/api/designer/texts" in js
    assert "toggleTextsMode" in js and "renderTextsEditor" in js
    assert "b.overrides" in js
    html = open(os.path.join(root, "web", "designer.html"),
                encoding="utf-8").read()
    assert 'id="dz-edit-texts"' in html and 'id="dz-texts"' in html
    assert "dz-tx-row" in html                      # Bild links, Texte rechts
