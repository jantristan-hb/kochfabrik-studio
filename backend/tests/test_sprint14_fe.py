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
