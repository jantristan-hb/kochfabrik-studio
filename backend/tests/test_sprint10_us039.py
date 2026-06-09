"""US-039 — FONT-REPORT.md aus font-report.json (Sprint 10, Doc-only-Analyse).

Verify-Kriterien (Story US-039): die lesbare Auswertung MUSS die Abdeckung
200/200 explizit nennen, das Wingdings-Inventar enthalten und einen
Histogramm-/Verteilungs-Abschnitt führen.
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_MD = REPO_ROOT / "docs" / "sprint-10" / "FONT-REPORT.md"


def _text():
    assert REPORT_MD.exists(), f"FONT-REPORT.md fehlt: {REPORT_MD}"
    return REPORT_MD.read_text(encoding="utf-8")


def test_states_full_coverage():
    assert "200/200" in _text()


def test_mentions_wingdings():
    assert re.search(r"wingdings", _text(), re.IGNORECASE)


def test_has_histogram_or_distribution_section():
    assert re.search(r"histogramm|verteilung", _text(), re.IGNORECASE)


def test_mentions_epic_005_consequences():
    # Story verlangt einen Abschnitt "Konsequenzen für EPIC-005 T1–T4".
    assert re.search(r"epic-?005", _text(), re.IGNORECASE)
