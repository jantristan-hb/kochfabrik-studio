"""US-036 — EARS-Gate für die Bug-Analyse kochfabrik-studio.

WHEN die Studio-Analyse abgeschlossen ist THE SYSTEM SHALL
docs/sprint-10/FINDINGS-STUDIO.md liefern, in dem jeder Finding eine
ID (## F-S-NN: …), eine **Beleg:**-Zeile und eine **Zuordnung:**-Zeile
trägt. Doc-only-Sprint: dieser Test prüft NUR das Artefakt, nicht den
Produktiv-Code.
"""
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
_DOC = os.path.join(_ROOT, "docs", "sprint-10", "FINDINGS-STUDIO.md")

_HEAD = re.compile(r"^## F-S-\d{2}: ", re.MULTILINE)
_BELEG = re.compile(r"^\*\*Beleg:\*\*", re.MULTILINE)
_ZUORD = re.compile(r"^\*\*Zuordnung:\*\*", re.MULTILINE)


def _text() -> str:
    assert os.path.isfile(_DOC), f"FINDINGS-STUDIO.md fehlt: {_DOC}"
    with open(_DOC, encoding="utf-8") as f:
        return f.read()


def test_findings_doc_nonempty():
    assert os.path.getsize(_DOC) > 0, "FINDINGS-STUDIO.md ist leer"


def test_min_five_findings():
    n = len(_HEAD.findall(_text()))
    assert n >= 5, f"erwarte >=5 Findings, gefunden {n}"


def test_beleg_per_finding():
    t = _text()
    assert len(_HEAD.findall(t)) == len(_BELEG.findall(t)), (
        "jeder Finding braucht genau eine **Beleg:**-Zeile")


def test_zuordnung_per_finding():
    t = _text()
    assert len(_HEAD.findall(t)) == len(_ZUORD.findall(t)), (
        "jeder Finding braucht genau eine **Zuordnung:**-Zeile")
