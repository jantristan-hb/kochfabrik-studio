"""US-042 — Gate für ADR-002 Monorepo-Schnitt.

Doc-only-Sprint (R-REF-6): prüft NUR das ADR-Artefakt, nicht
Produktiv-Code. Anforderungen aus der Story:
- Frontmatter `status: proposed` (NIE accepted in diesem Sprint)
- Abschnitt `## Alternativen` (Optionen-Vergleich)
- Coolify-Migration adressiert (case-insensitiv 'coolify')
- keine offenen Template-Platzhalter ('{…}') mehr im Dokument
"""
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
_DOC = os.path.join(_ROOT, "docs", "adr",
                    "ADR-002-monorepo-schnitt.md")


def _text() -> str:
    assert os.path.isfile(_DOC), f"ADR-002 fehlt: {_DOC}"
    with open(_DOC, encoding="utf-8") as f:
        return f.read()


def test_status_proposed():
    # ADR-Lifecycle proposed→accepted; accepted seit 2026-06-09 (4713b2a).
    assert re.search(r"^status: (proposed|accepted)\s*$", _text(),
                     re.MULTILINE), \
        "Frontmatter 'status: proposed|accepted' fehlt"


def test_has_alternativen_section():
    assert re.search(r"^## Alternativen\s*$", _text(),
                     re.MULTILINE), "Abschnitt '## Alternativen' fehlt"


def test_mentions_coolify():
    assert re.search(r"coolify", _text(), re.IGNORECASE), \
        "Coolify-Migration nicht adressiert"


def test_no_open_placeholder():
    assert "{…}" not in _text(), \
        "offener Template-Platzhalter '{…}' im Dokument"
