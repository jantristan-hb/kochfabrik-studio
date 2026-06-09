# TEST.md — kochfabrik Sprint 10 (TDD-Stubs aus EARS)

> Stubs abgeleitet aus den EARS-Kriterien der FEATURE-Specs — initial
> ROT. `/sprint-execute` legt sie als `backend/tests/test_sprint10.py`
> an (Stack: pytest, vgl. pytest.ini) und macht sie über die
> Story-Outputs grün. Doc-only-Sprint → die Tests prüfen Artefakte.

```python
"""Sprint-10-Artefakt-Tests — EARS-Bindung siehe Kommentare."""
import json
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
S10 = os.path.join(ROOT, "docs", "sprint-10")
ADR = os.path.join(ROOT, "docs", "adr")


def _read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


# FEATURE-001 EARS 1 — Findings Studio: Schema vollständig
def test_findings_studio_schema():
    md = _read(os.path.join(S10, "FINDINGS-STUDIO.md"))
    ids = re.findall(r"^## F-S-\d{2}: ", md, re.M)
    assert len(ids) >= 5
    assert len(ids) == len(re.findall(r"^\*\*Beleg:\*\*", md, re.M))
    assert len(ids) == len(re.findall(r"^\*\*Zuordnung:\*\*", md, re.M))


# FEATURE-001 EARS 2 — Findings Engine: Schema + Pflicht-Kandidaten
def test_findings_engine_kandidaten():
    md = _read(os.path.join(S10, "FINDINGS-ENGINE.md"))
    assert len(re.findall(r"^## F-E-\d{2}: ", md, re.M)) >= 5
    assert "SIZE_K" in md


# FEATURE-001 EARS 3 — Test-Baseline mit realem Collect-Count
def test_baseline_count_und_luecken():
    md = _read(os.path.join(S10, "TEST-BASELINE.md"))
    assert re.search(r"\*\*Test-Count \(pytest collect\):\*\* \d+", md)
    assert "## Lücken" in md


# FEATURE-002 EARS 1 — JSON deckt 200/200 PDFs ab
def test_font_report_json_vollstaendig():
    d = json.load(open(os.path.join(S10, "font-report.json"),
                       encoding="utf-8"))
    assert d["pdf_count"] == 200
    assert len(d["pdfs"]) == 200
    assert "fonts" in d["aggregate"]
    assert "wingdings_glyphs" in d["aggregate"]


# FEATURE-002 EARS 2 — exakte pt-Werte, kein Korrekturfaktor
def test_font_report_exakte_groessen():
    d = json.load(open(os.path.join(S10, "font-report.json"),
                       encoding="utf-8"))
    sizes = d["aggregate"]["sizes_pt"]
    assert sizes, "pt-Histogramm darf nicht leer sein"
    src = _read(os.path.join(ROOT, "tools", "font_report.py"))
    assert "SIZE_K" not in src, "kein Fudge-Faktor im Extraktor"


# FEATURE-002 EARS 3 — Report weist Abdeckung + Inventar aus
def test_font_report_md():
    md = _read(os.path.join(S10, "FONT-REPORT.md"))
    assert "200/200" in md
    assert re.search(r"wingdings", md, re.I)


# FEATURE-003 EARS 1+2 — drei ADRs, Template-konform, proposed
@pytest.mark.parametrize("name", [
    "ADR-001-pptx-font-embedding.md",
    "ADR-002-monorepo-schnitt.md",
    "ADR-003-pgbundle-vs-postgres.md",
])
def test_adr_format(name):
    md = _read(os.path.join(ADR, name))
    assert "status: proposed" in md
    for sec in ("## Kontext", "## Entscheidung", "## Alternativen",
                "## Konsequenzen"):
        assert sec in md, f"{name}: {sec} fehlt"
    assert "{…}" not in md
```

**Arbeitsauftrag für /sprint-execute:** Datei als
`backend/tests/test_sprint10.py` anlegen (Wave 1, mit US-036 oder
US-038 — wer zuerst startet), initial rot laufen lassen, durch die
Story-Outputs grün machen. Achtung: erst NACH Anlage der Artefakte
in die Suite aufnehmen, sonst bricht der Bestand (111 Tests grün).
