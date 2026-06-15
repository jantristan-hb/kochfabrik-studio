"""Sprint 14 — Frontend-Smoke der Wizard-UI-Kette (US-074 ff.).

Marker-basierte FE-Smoke nach Vorbild der Designer-UI-Kette
(`test_sprint13_fe.py`: TestClient + Auth-Cookie, statische read_text-Greps).
DB-los.

US-074: das Wizard-Gerüst wird ausgeliefert (200, hinter dem Auth-Gate wie
jede Modul-Seite), trägt die vier Bereichs-Marker (`wizard-progress`/
`wizard-step`/`wizard-alts`/`wizard-stage`), das JS-Modul ist erreichbar
(200, /assets ist public) und versioniert den State unter `kfWizard.v1`.
Die Nav verlinkt wizard.html aus mind. 5 bestehenden Seiten. Schritt 0
(Angebot wählen) verdrahtet suggest; die Schritt-Maschine läuft in
Server-Reihenfolge der suggest-Gruppen (FEATURE-015 §8 Nr. 6 + Nr. 1).

DIESE Datei gehört der Wizard-Kette (NICHT test_sprint14.py = API-Kette).
"""
import hashlib
import secrets
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"

# Bekannter KF_USERS-Eintrag zum Minten eines gültigen Session-Cookies
# (gleiche Mechanik wie test_sprint13_fe.py).
_EMAIL = "wizard@kf.de"
_SALT = "saltsalt"
_PW = "pw-wizard"
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
    """TestClient mit gültigem Session-Cookie (passiert das Auth-Gate)."""
    c = TestClient(app_module.app, follow_redirects=False)
    c.cookies.set(app_module.COOKIE, app_module.make_cookie(_EMAIL))
    return c


@pytest.fixture
def client(app_module):
    return TestClient(app_module.app, follow_redirects=False)


def _wizard_html():
    return (WEB / "wizard.html").read_text(encoding="utf-8")


def _wizard_js():
    return (WEB / "assets" / "wizard.js").read_text(encoding="utf-8")


# --- US-074: Auslieferung + Marker -----------------------------------------

def test_wizard_page_served_200(auth_client):
    r = auth_client.get("/wizard.html")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_wizard_page_gated_without_cookie(client):
    # Modul-Seite hinter dem Auth-Gate (IST: Nicht-API -> 302 /login.html).
    r = client.get("/wizard.html")
    assert r.status_code == 302
    assert r.headers["location"] == "/login.html"


def test_wizard_page_has_area_markers():
    html = _wizard_html()
    for marker in ("wizard-progress", "wizard-step", "wizard-alts",
                   "wizard-stage"):
        assert marker in html, f"Bereichs-Marker fehlt: {marker}"


def test_wizard_js_served_200(client):
    # /assets ist public (kein Cookie nötig).
    r = client.get("/assets/wizard.js")
    assert r.status_code == 200


def test_wizard_js_versioned_state_key():
    js = _wizard_js()
    assert "kfWizard.v1" in js, "sessionStorage-Key kfWizard.v1 fehlt"


def test_wizard_js_has_login_redirect_pattern():
    # 401 -> Login-Redirect nach designer.js-Muster.
    js = _wizard_js()
    assert "/login.html" in js


# --- US-074: Navigation aus bestehenden Seiten -----------------------------

def test_at_least_five_pages_link_wizard():
    pages = [p for p in WEB.glob("*.html")
             if "wizard.html" in p.read_text(encoding="utf-8")]
    assert len(pages) >= 5, (
        f"Nur {len(pages)} Seiten verlinken wizard.html (>=5 erwartet)")


# --- US-074: Schritt-0 + State-Maschine ------------------------------------

def test_wizard_js_wires_suggest():
    # Schritt 0: Angebot -> suggest (Muster designer.js).
    js = _wizard_js()
    assert "/api/designer/suggest" in js, "suggest-Endpoint nicht verdrahtet"
    assert "/api/angebote" in js, "Angebots-Liste nicht verdrahtet"


def test_wizard_js_step_machine_present():
    # Schritt-Maschine: stepIndex + Weiter/Zurück + Restore.
    js = _wizard_js()
    assert "stepIndex" in js, "stepIndex (Schritt-Zeiger) fehlt"
    for fn in ("nextStep", "prevStep", "renderStep"):
        assert fn in js, f"Schritt-Maschinen-Funktion fehlt: {fn}"


def test_wizard_js_groups_drive_steps_in_server_order():
    # Pitfall 4: Gruppen = Schritte in Server-Reihenfolge; FE sortiert NICHT.
    js = _wizard_js()
    assert "groups" in js, "groups (Server-Reihenfolge) fehlt"


def test_wizard_js_images_not_persisted():
    # Pitfall 3: Bild-Overrides NICHT in sessionStorage (MB-Data-URLs).
    # Nur Schritt/Auswahl/Text-Overrides werden persistiert.
    js = _wizard_js()
    assert "imageOverrides" in js, "imageOverrides (in-memory) fehlt"
    assert "saveState" in js, "saveState (persistierter Teil-State) fehlt"


def test_wizard_step0_panel_markers():
    # Schritt-0-Panel: Upload-Dropzone + Angebots-Dropdown.
    html = _wizard_html()
    assert 'id="wz-upload"' in html, "Upload-Dropzone fehlt"
    assert 'id="wz-offer"' in html, "Angebots-Dropdown fehlt"


def test_wizard_nav_buttons_present():
    # Zurück/Weiter-Steuerung.
    html = _wizard_html()
    assert 'id="wz-back"' in html
    assert 'id="wz-next"' in html


# --- US-075: Alternativen + Auswahl (FEATURE-015 §8 Nr. 1 + Nr. 4-Teil) -----
# WHEN ein Schritt angezeigt wird THE SYSTEM SHALL 3-4 Alternativen mit dem
# Top-Kandidaten (candidates[0]) vorausgewählt zeigen; Rest hinter "+N weitere".
# Cover-Schritt: "✨ generieren" -> /api/image -> pending image_override.

def test_wizard_js_alts_limit_and_more():
    # Max 4 sichtbar (slice(0, 4)) + "+N weitere"-Mechanik (Pitfall-frei:
    # gleiche Begrenzung wie Designer-Slot-Ansicht).
    js = _wizard_js()
    assert "slice(0, 4)" in js, "Alternativen-Begrenzung slice(0, 4) fehlt"
    assert "weitere" in js, '"+N weitere"-Mechanik fehlt'


def test_wizard_js_alts_render_into_marker():
    # Alternativen werden in den gekennzeichneten Bereich #wizard-alts gerendert.
    js = _wizard_js()
    assert "wizard-alts" in js, "Render-Ziel #wizard-alts nicht referenziert"
    assert "renderAlts" in js, "renderAlts (Alternativen-Render) fehlt"


def test_wizard_js_default_selection_top_candidate():
    # Vorauswahl = Top-Kandidat candidates[0] (EARS Nr. 1).
    js = _wizard_js()
    assert "candidates[0]" in js, "Vorauswahl candidates[0] fehlt"


def test_wizard_js_selection_state_per_group():
    # Klick wechselt state.selections[groupIdx]; Auswahl-Markierung.
    js = _wizard_js()
    assert "selections" in js, "Auswahl-State (selections) fehlt"
    assert "selectAlt" in js, "selectAlt (Auswahl-Wechsel) fehlt"
    assert "wz-alt-on" in js, "Auswahl-Markierung (wz-alt-on) fehlt"


def test_wizard_js_stage_shows_selected_preview():
    # Stage zeigt vorerst das preview-PNG der gewählten Karte groß
    # (Overlay folgt US-076).
    js = _wizard_js()
    assert "renderStage" in js, "renderStage (Stage-Render) fehlt"
    assert "wizard-stage" in js, "Render-Ziel #wizard-stage nicht referenziert"


def test_wizard_js_cover_generate_wiring():
    # Cover-Schritt (kind=="cover"): /api/image mit category "cover".
    js = _wizard_js()
    assert "/api/image" in js, "/api/image nicht verdrahtet"
    assert '"cover"' in js, 'category "cover" fehlt'
    assert "coverPrompt" in js, "coverPrompt (Prompt aus Angebots-Kontext) fehlt"


def test_wizard_js_cover_pending_image_override_in_memory():
    # Pitfall 3: erzeugtes Cover-Bild als pending image_override IN-MEMORY,
    # NICHT in sessionStorage. Persistenz enthält weiterhin keine Bilder.
    js = _wizard_js()
    assert "pendingImageOverride" in js or "imageOverrides" in js, (
        "pending image_override (in-memory) fehlt")
    # Bilder dürfen nicht in den persistierten State wandern.
    save_block = js[js.index("function saveState"):js.index("function saveState") + 600]
    assert "imageOverrides" not in save_block, (
        "imageOverrides darf NICHT persistiert werden (Pitfall 3)")


# --- US-076: Overlay-Editor (FEATURE-015 §8 Nr. 2+3+4) ---------------------
# Stage: texts-API → Notext-Hintergrund + positionierte Text-/Bild-Overlays.
# Pitfall 1: Maßstab relativ aus meta.w_pt/h_pt + ResizeObserver. Pitfall 2:
# contenteditable plain-text (paste-Strip), Enter = \n.

def test_wizard_stage_notext_fallback():
    # Stage-Hintergrund = preview_notext; onerror → normales preview + Badge.
    js = _wizard_js()
    assert "/api/designer/texts" in js, "texts-API nicht verdrahtet"
    assert "preview_notext" in js, "Notext-Hintergrund fehlt"
    assert "onerror" in js, "onerror-Fallback fehlt"
    # Hinweis-Badge beim Fallback aufs normale preview.
    assert ("notext" in js.lower() and "badge" in js.lower()), (
        "Notext-Fallback-Badge fehlt")


def test_wizard_overlay_scaling():
    # Pitfall 1: Positionierung relativ aus meta.w_pt/h_pt + ResizeObserver.
    js = _wizard_js()
    assert "w_pt" in js and "h_pt" in js, "Maßstab aus meta.w_pt/h_pt fehlt"
    assert "ResizeObserver" in js, "ResizeObserver (Nachrechnen) fehlt"


def test_wizard_plaintext_editor():
    # #95b: Editor ist die sichtbare textarea-Feldliste (ersetzt das nicht
    # erkennbare contenteditable-Overlay). <textarea> ist von Natur aus
    # plain-text — der frühere paste-Strip entfällt.
    js = _wizard_js()
    assert 'createElement("textarea")' in js, "textarea-Editor fehlt"
    assert "wz-fields" in js, "sichtbare Feldliste fehlt"


def test_wizard_override_precedence():
    # Vorbelegung: Override > Auto-Suggestion > Ist-Text; Änderung →
    # state.textOverrides[deck::page][idx].
    js = _wizard_js()
    assert "textOverrides" in js, "textOverrides-State fehlt"
    assert "suggestions" in js, "Auto-Suggestion-Vorbelegung fehlt"


def test_wizard_formulate_wiring():
    # ✦ Formulieren je Feld: /api/designer/formulate + Undo.
    js = _wizard_js()
    assert "/api/designer/formulate" in js, "formulate-API nicht verdrahtet"
    assert "Undo" in js or "undo" in js, "Undo-Mechanik fehlt"


def test_wizard_image_generate_wiring():
    # 🖼 Bild generieren je images[]-Element → /api/image (category food),
    # in-memory Override, deckt das Element positionsgenau.
    js = _wizard_js()
    assert '"food"' in js, 'category "food" fehlt'
    assert "imageOverrides" in js, "in-memory imageOverrides fehlt"
    # Cover-pending (US-075) wird hier aufs größte image-Element aufgelöst.
    assert ("largest" in js.lower() or "größt" in js.lower()
            or "biggest" in js.lower()), "größtes image-Element-Auflösung fehlt"


# --- US-077: Abschluss — Filmstreifen + Download + E2E (FEATURE-015 Nr. 5) --
# Abschluss-Schritt: Filmstreifen der gewählten Slides in Reihenfolge,
# "PPTX herunterladen" -> /api/slidesuche/download mit overrides +
# image_overrides; "Von vorn"-Reset.

def test_wizard_download_payload_markers():
    js = _wizard_js()
    assert "/api/slidesuche/download" in js, "download-Endpoint nicht verdrahtet"
    # Payload trägt sowohl Text- als auch Bild-Overrides.
    assert "image_overrides" in js, "image_overrides im Payload fehlt"
    assert "overrides" in js, "overrides im Payload fehlt"
    # Filmstreifen + "Von vorn"-Reset.
    assert "renderFilm" in js or "wz-film" in js, "Filmstreifen-Render fehlt"
    assert ("Von vorn" in js or "resetWizard" in js), '"Von vorn"-Reset fehlt'


def test_wizard_finish_markers():
    html = _wizard_html()
    assert 'id="wz-film"' in html, "Filmstreifen-Container fehlt"
    assert 'id="wz-download"' in html, "Download-Button fehlt"


# E2E: suggest (gemockt) -> Auswahl + Text-Override + 1x1-PNG-image_override
# -> download -> echte PPTX (PK-Magic) + Override-Text im Slide-XML + Bild in
# ppt/media. node-gated (reconstruct.js). Muster:
# test_sprint13_fe.test_e2e_suggest_to_pptx + test_sprint14.image-Override.
_E2E_DECK = "kf-ausstattung-location"
_E2E_PAGE = 1


def _png_with_marker(marker: bytes):
    """Gültiges 1x1-PNG mit tEXt-Marker (stdlib, ohne Pillow) — Muster
    test_sprint14._png_bytes; der Marker beweist das Bild in ppt/media."""
    import struct
    import zlib

    def chunk(typ: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + typ + data
                + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(b"\x00\xff\xff\xff")
    text = b"Comment\x00" + marker
    return (sig + chunk(b"IHDR", ihdr) + chunk(b"tEXt", text)
            + chunk(b"IDAT", idat) + chunk(b"IEND", b""))


def _node_available():
    import shutil
    return shutil.which("node") is not None


@pytest.mark.skipif(not _node_available(),
                    reason="node/reconstruct.js nicht verfügbar")
def test_wizard_e2e_full_flow(auth_client, monkeypatch):
    """E2E des Wizard-Download-Vertrags: suggest (gemockt) liefert Kandidaten;
    eine gewählte Slide (committetes Cache-Deck) geht mit Text-Override +
    1x1-PNG-image_override durch /api/slidesuche/download -> echte PPTX mit
    Override-Text im Slide-XML UND dem Bild in ppt/media."""
    import base64
    import io
    import zipfile

    import numpy as np

    import backend.routers.designer as d

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
    assert any(g["candidates"] for g in groups)

    # Text-Override-Index der E2E-Slide über die texts-API (wie US-066-E2E).
    tx = auth_client.post("/api/designer/texts",
                          json={"slides": [{"deck": _E2E_DECK,
                                            "page": _E2E_PAGE}]})
    sl = tx.json()["slides"][0]
    txt_idx = str(sl["texts"][0]["i"])
    img_idx = str(sl["images"][0]["i"]) if sl["images"] else None

    marker_txt = "WIZARD E2E OVERRIDE"
    marker_img = b"WIZARDE2EIMG077"
    data_url = "data:image/png;base64," + base64.b64encode(
        _png_with_marker(marker_img)).decode()

    slide = {"deck": _E2E_DECK, "page": _E2E_PAGE,
             "overrides": {txt_idx: marker_txt}}
    if img_idx is not None:
        slide["image_overrides"] = {img_idx: data_url}

    dl = auth_client.post("/api/slidesuche/download", json={"slides": [slide]})
    assert dl.status_code == 200, dl.text
    pptx = dl.json()["pptx"]
    assert pptx.startswith("data:application/vnd.openxmlformats")
    raw = base64.b64decode(pptx.split(",", 1)[1])
    assert raw[:2] == b"PK", "kein gültiges PPTX (PK-Magic fehlt)"

    xml = b""
    media = b""
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for n in z.namelist():
            if n.startswith("ppt/slides/") and n.endswith(".xml"):
                xml += z.read(n)
            if n.startswith("ppt/media/"):
                media += z.read(n)
    assert marker_txt.encode() in xml, "Text-Override nicht im Slide-XML"
    if img_idx is not None:
        assert marker_img in media, "Bild-Override nicht in ppt/media"
