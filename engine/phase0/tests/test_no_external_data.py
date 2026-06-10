"""Regressiontest: generierte Angebot-PDFs enthalten NUR Kalkulationen
aus dem Angebotsgenerator — keine Raumkarussell-Muster-Reste.

E2E offline (kein LLM/DB): Angebot-Modell → render_pdf → pdftotext →
String-Asserts. Fängt jede künftige Template-Drift (untokenisierte
Literale, ungewollte Verbatim-Seiten) sofort.
"""
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

# Strings die NIE in einem generierten Angebot stehen dürfen
# (Raumkarussell-Muster-Reste oder Raumkarussell-spezifische Beträge).
FORBIDDEN = [
    # Geschirr/Becher-Block (Page 3 alt)
    "Becher / Holzgeschirr", "Nachhaltig & One Way",
    "Zuckerrohr- & Pappverpackungen", "biologisch Abbaubar",
    # Projektmanagement-Block (Page 4 alt)
    "Projektmanagement & Eventplanung",
    "Korrespondenz mit Kunden",
    "Angebots-Erstellung",
    # Speisen/Equipment-Block (Page 2 Restdaten falls Strip nicht greift)
    "Liebe zum Detail", "Food-Truck", "Streetfood",
    "1x Live Cooking/BBQ Station",
    # Raumkarussell-spezifische Beträge
    "19.750,00", "33.771,30", "6.416,54", "40.187,84",
    "3.728,30", "6.548,00",
    # Totals-Page (Page 5 alt)
    "Nettogesamtbetrag", "Gesamtsumme brutto",
    # Adressen-Reste (sollten alle tokenisiert sein)
    "20099  Hamburg", "Ernst-Merck-Straße", "Frau Claudia Kiesel",
    "jwiegers@koch-fabrik.com", "04101-7744545",
    "claudia.kiesel@raumkarussell.de", "Raumkarussell",
]


def _build_angebot():
    from angebot_model import (Angebot, Position, Positionsblock,
                               Veranstaltung)
    return Angebot(
        kunde="Testkunde GmbH",
        adresse="Teststraße 1, 22765 Hamburg",
        angebots_nr="KF-2026-9999", datum="20. Mai 2026",
        kundennr="100099-A", lieferdatum="1. Juli 2026",
        ansprechpartner="",
        veranstaltung=Veranstaltung(
            anlass="Testfest", datum="1. Juli 2026",
            beginn="17:00 Uhr", personen=100,
            ort="Testlocation Hamburg", konzept="Testkonzept lean"),
        bloecke=[
            Positionsblock(typ="speisen", titel="Speisen",
                positionen=[Position("Testgericht A", 100, 10.0,
                                      1000.0)],
                zwischensumme=1000.0),
            Positionsblock(typ="personal", titel="Personal",
                positionen=[Position(
                    "Servicemitarbeiter*in 17-23 (60 Std.)",
                    10, 37.5, 2250.0)],
                zwischensumme=2250.0),
        ])


def _render_text(tmp_path):
    from angebot_render import render_pdf
    if not (subprocess.run(["which", "soffice"],
                            capture_output=True).returncode == 0
            and subprocess.run(["which", "pdftotext"],
                                capture_output=True).returncode == 0):
        pytest.skip("soffice/pdftotext nicht installiert")
    out = str(tmp_path / "angebot.pdf")
    render_pdf(_build_angebot(), out)
    r = subprocess.run(["pdftotext", "-layout", out, "-"],
                        capture_output=True, text=True, timeout=60)
    return r.stdout


def test_no_raumkarussell_residue(tmp_path):
    """Kein Raumkarussell-Muster-Inhalt im generierten Angebot."""
    txt = _render_text(tmp_path)
    leaks = [s for s in FORBIDDEN if s in txt]
    assert not leaks, ("Raumkarussell-Residue gefunden: "
                       + ", ".join(repr(s) for s in leaks))


def test_generator_content_present(tmp_path):
    """Vom Angebotsgenerator erzeugte Werte sind sichtbar im PDF."""
    txt = _render_text(tmp_path)
    must = ["Testkunde GmbH", "KF-2026-9999", "100099-A",
            "20. Mai 2026", "Testfest", "Testgericht A",
            "Servicemitarbeiter*in"]
    missing = [s for s in must if s not in txt]
    assert not missing, ("Pflicht-Inhalt fehlt im PDF: "
                         + ", ".join(repr(s) for s in missing))


def test_agb_pages_preserved(tmp_path):
    """KOCHfabrik-AGB (standardisiert, gilt für alle) bleibt erhalten."""
    txt = _render_text(tmp_path)
    for marker in ("ALLGEMEINE GESCHÄFTSBEDINGUNGEN",
                   "§ 1 Geltungsbereich",
                   "§ 15 Salvatorische"):
        assert marker in txt, f"AGB-Marker fehlt: {marker!r}"
