"""Regression — Wizard-Editor-Bugfix (#95).

Vier Prod-Defekte (vom gemockten Sprint-14-E2E nicht gefangen):
1. Auto-Override nur angezeigt, nie committet → PPTX behielt Originaltext.
2. Bild-Overlays überdeckten die Textfelder (CSS-Schichtung).
3. Generiertes Cover in der Stage nicht sichtbar (gleiche Schichtung).
4. coverPrompt listete Gänge → Gemini erzeugte Essen statt Titelbild.
"""
import os

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


def _read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as fh:
        return fh.read()


# --- Backend: Anlass/Ort als Cover-Prompt-Quelle (additiv) ---------------

def test_offer_meta_extracts_anlass_ort(tmp_path):
    import sys
    sys.path.insert(0, os.path.join(ROOT, "engine", "scripts"))
    from backend.routers.designer import _offer_meta
    md = tmp_path / "o.md"
    md.write_text(
        "Veranstaltungsanlass: Sommerfest Regio Kliniken\n"
        "Veranstaltungsort: Edelfettwerk, Hamburg\n"
        "Veranstaltungsdatum: | | 12. September 2026\n",
        encoding="utf-8")
    anlass, ort = _offer_meta(str(md))
    assert anlass == "Sommerfest Regio Kliniken", anlass
    assert "Edelfettwerk" in ort, ort


def test_parse_offer_md_carries_anlass():
    """offer-Dict trägt anlass/ort (Bestandsfelder unberührt)."""
    from backend.routers import designer as dz
    offer = dz._parse_offer_md(
        "## Angebot — Test GmbH (x)\n"
        "Veranstaltungsanlass: Jubiläum\n"
        "Veranstaltungsort: Loft\n")
    assert "anlass" in offer and "ort" in offer
    assert offer["anlass"] == "Jubiläum"
    assert "kunde" in offer and "gaenge" in offer  # additiv, nichts weg


# --- Frontend: die vier Fix-Marker im ausgelieferten Code ----------------

def test_wizard_commits_auto_suggestion():
    """#1: Suggestion wird beim Render in textOverrides committet."""
    js = _read("web", "assets", "wizard.js")
    # nach fieldValue muss ein setTextOverride-Commit der Suggestion stehen
    assert "val !== t.text" in js
    assert "setTextOverride(cand.deck, cand.page, t.i, val)" in js


def test_wizard_cover_prompt_drops_dishes():
    """#4: coverPrompt nutzt Anlass/Ort, listet keine Gänge mehr."""
    js = _read("web", "assets", "wizard.js")
    assert "o.anlass" in js and "o.ort" in js
    assert "Menü/Konzept:" not in js          # Gang-Auflistung raus
    assert "kein Speisen-Close-up" in js


def test_wizard_css_layering():
    """#2/#3: Textfelder über Bild-Overlays, Bild-Boxen klick-durchlässig."""
    html = _read("web", "wizard.html")
    assert "pointer-events:none" in html      # .wz-iov fängt keine Klicks
    assert ".wz-iov-btn" in html and "pointer-events:auto" in html
    # Text-Overlay-Ebene über Bild-Overlay-Ebene
    assert "z-index:4" in html and "z-index:2" in html
