"""US-040 — Test-Baseline-Inventur (Doc-only-Analyse).

EARS: WHEN die Baseline-Inventur abgeschlossen ist THE SYSTEM SHALL
docs/sprint-10/TEST-BASELINE.md liefern mit realer Test-Anzahl
(pytest-Collect), Abdeckungs-Karte pro Modul und expliziter
Lücken-Liste (Engine-Skripte).

Dieser Test prüft NUR die Artefakt-Konformität des Docs (keine
Produktiv-Logik) — passend zum Doc-only-Sprint.
"""
import os
import re

DOC = os.path.join(
    os.path.dirname(__file__), "..", "..",
    "docs", "sprint-10", "TEST-BASELINE.md")


def _read():
    with open(DOC, encoding="utf-8") as f:
        return f.read()


def test_doc_existiert_und_nicht_leer():
    assert os.path.isfile(DOC), "TEST-BASELINE.md fehlt"
    assert os.path.getsize(DOC) > 0, "TEST-BASELINE.md ist leer"


def test_test_count_zeile_mit_zahl():
    """Pflicht-Zeile: **Test-Count (pytest collect):** {N}."""
    m = re.search(r"\*\*Test-Count \(pytest collect\):\*\* (\d+)", _read())
    assert m, "Test-Count-Zeile mit Zahl fehlt"
    assert int(m.group(1)) > 0


def test_luecken_abschnitt_vorhanden():
    assert re.search(r"^## Lücken", _read(), re.MULTILINE), \
        "Abschnitt '## Lücken' fehlt"
