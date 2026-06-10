"""US-041 — Gate für ADR-001 PPTX-Font-Embedding.

Maschinell verifizierbar: ADR existiert, ist `status: proposed` (NICHT
accepted — das ist Jans Entscheidung), trägt die vier Pflicht-Sektionen
und enthält keinen unausgefüllten Template-Platzhalter `{…}`.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADR = ROOT / "docs" / "adr" / "ADR-001-pptx-font-embedding.md"


def _text():
    assert ADR.is_file(), f"{ADR} fehlt"
    t = ADR.read_text(encoding="utf-8")
    assert t.strip(), f"{ADR} ist leer"
    return t


def test_status_proposed():
    # ADR-Lifecycle proposed→accepted; accepted seit 2026-06-09 (4713b2a).
    assert re.search(r"^status: (proposed|accepted)$", _text(),
                     re.MULTILINE), \
        "Frontmatter 'status: proposed|accepted' fehlt"


def test_required_sections():
    t = _text()
    for sec in ("## Kontext", "## Entscheidung", "## Alternativen",
                "## Konsequenzen"):
        assert re.search(rf"^{re.escape(sec)}$", t, re.MULTILINE), \
            f"Sektion '{sec}' fehlt"


def test_no_template_placeholder():
    assert "{…}" not in _text(), "unausgefüllter Platzhalter {…} verblieben"
