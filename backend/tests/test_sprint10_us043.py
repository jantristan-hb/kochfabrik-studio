"""US-043 — ADR-003 pgbundle vs. Postgres (Doc-only-Analyse).

Prüft NUR die Artefakt-Konformität des ADR (MADR-artig, Status proposed) —
kein Produktiv-Code. Passt zum Doc-only-Sprint 10 / EPIC-003.
"""
import os
import re

ADR = os.path.join(
    os.path.dirname(__file__), "..", "..",
    "docs", "adr", "ADR-003-pgbundle-vs-postgres.md")


def _read():
    with open(ADR, encoding="utf-8") as f:
        return f.read()


def test_adr_existiert_und_nicht_leer():
    assert os.path.isfile(ADR), "ADR-003 fehlt"
    assert os.path.getsize(ADR) > 0, "ADR-003 ist leer"


def test_status_proposed():
    """Frontmatter-Status im ADR-Lifecycle (proposed→accepted)."""
    # ADR-Lifecycle proposed→accepted; accepted seit 2026-06-09 (4713b2a).
    assert re.search(r"^status: (proposed|accepted)$", _read(),
                     re.MULTILINE), \
        "status: proposed|accepted fehlt"


def test_alternativen_abschnitt():
    assert re.search(r"^## Alternativen", _read(), re.MULTILINE), \
        "Abschnitt '## Alternativen' fehlt"


def test_konsequenzen_abschnitt():
    assert re.search(r"^## Konsequenzen", _read(), re.MULTILINE), \
        "Abschnitt '## Konsequenzen' fehlt"


def test_keine_template_platzhalter():
    """Kein unausgefüllter '{…}'-Platzhalter aus TEMPLATE-ADR.md."""
    assert "{…}" not in _read(), "Template-Platzhalter '{…}' nicht ersetzt"
