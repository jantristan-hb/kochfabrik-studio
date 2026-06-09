"""US-037 — EARS-Akzeptanz-Gate für FINDINGS-ENGINE.md.

WHEN die Engine-Analyse abgeschlossen ist THE SYSTEM SHALL
docs/sprint-10/FINDINGS-ENGINE.md im Schema liefern und die 5
Verdachts-Kandidaten je als Finding oder VERWORFEN führen.

Maschinell verifizierbar: Datei existiert + nicht leer, >=5 Findings im
Schema `## F-E-NN:`, Beleg-Parität (jedes Finding hat genau eine
**Beleg:**-Zeile), Zuordnungs-Parität, und der namentliche
SIZE_K-Kandidat ist belegt.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "sprint-10" / "FINDINGS-ENGINE.md"

FINDING_RE = re.compile(r"^## F-E-[0-9]{2}: ", re.MULTILINE)
BELEG_RE = re.compile(r"^\*\*Beleg:\*\*", re.MULTILINE)
ZUORD_RE = re.compile(r"^\*\*Zuordnung:\*\*", re.MULTILINE)


def _text():
    assert DOC.is_file(), f"{DOC} fehlt"
    t = DOC.read_text(encoding="utf-8")
    assert t.strip(), f"{DOC} ist leer"
    return t


def test_doc_exists_and_nonempty():
    _text()


def test_min_five_findings():
    n = len(FINDING_RE.findall(_text()))
    assert n >= 5, f"nur {n} Findings (>=5 gefordert)"


def test_beleg_parity():
    t = _text()
    assert len(FINDING_RE.findall(t)) == len(BELEG_RE.findall(t)), \
        "Anzahl Findings != Anzahl **Beleg:**-Zeilen"


def test_zuordnung_parity():
    t = _text()
    assert len(FINDING_RE.findall(t)) == len(ZUORD_RE.findall(t)), \
        "Anzahl Findings != Anzahl **Zuordnung:**-Zeilen"


def test_size_k_candidate_present():
    assert "SIZE_K" in _text(), "Kandidat 1 (SIZE_K) nicht referenziert"
