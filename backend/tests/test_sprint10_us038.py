"""US-038 — Font-Extraktor + font-report.json (Sprint 10, Doc-only-Analyse).

EARS-Akzeptanzkriterien (FEATURE-FONT-REPORT §8 Nr. 1, 2, 4):
  1. pdf_count == 200 UND genau 200 pdfs-Einträge.
  2. pt-Größen sind exakte Werte aus der Rendering-Matrix — KEIN Korrekturfaktor
     ("SIZE_K" darf in tools/font_report.py nicht vorkommen).
  4. Nicht lesbare PDFs landen unter errors mit Grund (kein stilles Überspringen).

Die Checks lesen den committeten Report (Artefakt des Korpus-Laufs) und die
Extraktor-Quelle. Sie laufen ohne den Korpus selbst.
"""
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT = REPO_ROOT / "docs" / "sprint-10" / "font-report.json"
EXTRACTOR = REPO_ROOT / "tools" / "font_report.py"


def _load_report():
    assert REPORT.exists(), f"font-report.json fehlt: {REPORT}"
    return json.loads(REPORT.read_text(encoding="utf-8"))


def test_report_pdf_count_is_200():
    # EARS §8 Nr. 1
    d = _load_report()
    assert d["pdf_count"] == 200, d["pdf_count"]
    assert len(d["pdfs"]) == 200, len(d["pdfs"])


def test_aggregate_keys_present():
    d = _load_report()
    agg = d["aggregate"]
    for key in ("fonts", "sizes_pt", "wingdings_glyphs"):
        assert key in agg, key
    assert agg["fonts"], "fonts-Aggregat darf nicht leer sein"
    assert agg["sizes_pt"], "sizes_pt-Aggregat darf nicht leer sein"


def test_sizes_are_exact_floats():
    # EARS §8 Nr. 2: pt-Werte exakt (gerundet auf 2 Dezimalen), keine bbox-Heuristik
    d = _load_report()
    seen = False
    for pdf in d["pdfs"]:
        for span in pdf["spans"]:
            s = span["size_pt"]
            assert isinstance(s, (int, float))
            assert round(float(s), 2) == s
            seen = True
    assert seen, "kein einziger Span im Report — Extraktion fehlgeschlagen?"


def test_no_size_k_fudge_factor_in_source():
    # EARS §8 Nr. 2: der String "SIZE_K" darf nicht vorkommen
    assert EXTRACTOR.exists(), EXTRACTOR
    assert "SIZE_K" not in EXTRACTOR.read_text(encoding="utf-8")


def test_errors_field_is_list():
    # EARS §8 Nr. 4: Lesefehler werden ausgewiesen, nicht still verschluckt
    d = _load_report()
    assert isinstance(d["errors"], list)
    for e in d["errors"]:
        assert "slug" in e and "reason" in e


def test_span_schema():
    d = _load_report()
    pdf = d["pdfs"][0]
    assert {"slug", "pages", "spans"} <= set(pdf)
    if pdf["spans"]:
        span = pdf["spans"][0]
        assert {"font", "size_pt", "color", "bold", "italic", "count"} <= set(span)
        assert re.fullmatch(r"#[0-9a-fA-F]{6}", span["color"]), span["color"]
