#!/usr/bin/env python3
"""Treue-Metrik (FEATURE-TREUE-HARNESS, KOCHFABRIK-FEATURE-016 §3/§4, Sprint 15 US-081).

Vergleicht zwei PDF-Seiten und liefert vier Teil-Scores + Gesamt-Score in [0, 1]:

- ``text``     normalisierter Token-F1 über ``fitz`` ``get_text`` beider Seiten
- ``geometry`` Span-BBox-Matching, IoU-gewichtet, beste Zuordnung; Koordinaten
               IMMER auf die jeweiligen Seitenmaße normalisiert (Pitfall §12.2 —
               ref.pdf ist A4-Hochkant 595×839, nichts hartkodieren)
- ``font``     Anteil gematchter Spans mit gleicher Größe (±0.5pt) UND Font-Familie
- ``pixel``    Graustufen-Ähnlichkeit der ``fitz``-Pixmaps @192px Breite, ``1 − MAE``
- ``total``    0.35*text + 0.25*geometry + 0.25*font + 0.15*pixel

Dies ist ein **Analyse-/Build-Werkzeug** (``engine/tooling/``). Es lädt NIE zur
Laufzeit und ``engine/scripts/`` darf es nie importieren (TOOLING-SPLIT). ``fitz``
(PyMuPDF) ist eine explizit freigegebene Analyse-Dependency, NICHT im Runtime-Stack.

Span-Extraktion folgt dem Anker-Muster aus ``tools/font_report.py`` (Sprint 10):
pt-Größen kommen EXAKT aus ``span["size"]`` der Text-Rendering-Matrix, Font-Familie
aus dem (subset-bereinigten) Font-Namen.

CLI:
    fidelity.py a.pdf:1 b.pdf:1   → JSON auf stdout
                                     (1-basierte Seitennummern, default :1)
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

import fitz  # PyMuPDF — Analyse-Dep, nicht Runtime

# Versions-Konstante (FEATURE-016 §4). Im Output zusammen mit der fitz-Version.
FIDELITY_VERSION = "1.0"

# Gewichte des Gesamt-Scores (FEATURE-016 §4).
W_TEXT = 0.35
W_GEOMETRY = 0.25
W_FONT = 0.25
W_PIXEL = 0.15

# Pixel-Vergleich: Pixmap auf diese Breite skalieren (Höhe proportional).
PIXEL_WIDTH = 192

# Font-Größentoleranz beim Span-Matching (FEATURE-016 §4).
SIZE_TOL_PT = 0.5

# Subset-Präfix wie "ABCDEF+OpenSans-Bold" → "OpenSans-Bold" (vgl. font_report.py).
SUBSET_PREFIX = re.compile(r"^[A-Z]{6}\+")
# Token-Normalisierung: Unicode-Wortzeichen, kleingeschrieben.
TOKEN_RE = re.compile(r"\w+", re.UNICODE)


# ---------------------------------------------------------------------------
# Span-/Seiten-Extraktion
# ---------------------------------------------------------------------------
def strip_subset(font: str) -> str:
    return SUBSET_PREFIX.sub("", font or "")


def family_of(font: str) -> str:
    """Font-Familie ohne Stil-Suffix (vgl. font_report.family_of)."""
    base = strip_subset(font)
    return base.split("-", 1)[0].split(",", 1)[0].lower()


def _open_page(pdf_path: str, page_no_1based: int):
    """Öffnet das Dokument und liefert (doc, page). page_no ist 1-basiert."""
    doc = fitz.open(pdf_path)
    idx = page_no_1based - 1
    if idx < 0 or idx >= doc.page_count:
        doc.close()
        raise IndexError(
            f"Seite {page_no_1based} außerhalb [1, {doc.page_count}] in {pdf_path}"
        )
    return doc, doc[idx]


def extract_page(page):
    """Liefert (text, spans, (width, height)) einer Seite.

    spans: Liste {text, bbox_norm=(x0,y0,x1,y1) in [0,1], size, family}.
    bbox auf die Seitenmaße normalisiert → seitengrößen-unabhängig (Pitfall §12.2).
    """
    rect = page.rect
    width = float(rect.width) or 1.0
    height = float(rect.height) or 1.0
    spans = []
    texts = []
    data = page.get_text("dict")
    for block in data["blocks"]:
        if block.get("type") != 0:  # nur Text-Blöcke
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = span.get("text", "")
                if text.strip() == "":
                    continue
                x0, y0, x1, y1 = span["bbox"]
                spans.append(
                    {
                        "text": text,
                        "bbox_norm": (
                            x0 / width,
                            y0 / height,
                            x1 / width,
                            y1 / height,
                        ),
                        "size": round(float(span["size"]), 2),
                        "family": family_of(span["font"]),
                    }
                )
                texts.append(text)
    return " ".join(texts), spans, (width, height)


def _tokens(text: str) -> Counter:
    return Counter(t.lower() for t in TOKEN_RE.findall(text))


# ---------------------------------------------------------------------------
# Teil-Scores
# ---------------------------------------------------------------------------
def text_f1(text_a: str, text_b: str) -> float:
    """Normalisierter Token-F1 (Multiset-Schnitt) über beide Seiten."""
    ca, cb = _tokens(text_a), _tokens(text_b)
    if not ca and not cb:
        return 1.0
    if not ca or not cb:
        return 0.0
    overlap = sum((ca & cb).values())
    if overlap == 0:
        return 0.0
    precision = overlap / sum(cb.values())
    recall = overlap / sum(ca.values())
    return 2 * precision * recall / (precision + recall)


def _iou(a, b) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    iw, ih = max(0.0, ix1 - ix0), max(0.0, iy1 - iy0)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(0.0, ax1 - ax0) * max(0.0, ay1 - ay0)
    area_b = max(0.0, bx1 - bx0) * max(0.0, by1 - by0)
    union = area_a + area_b - inter
    if union <= 0:
        return 0.0
    return inter / union


def _greedy_match(spans_a, spans_b):
    """Greedy beste-IoU-Zuordnung normalisierter Span-BBoxes.

    Liefert Liste (i, j, iou) der gematchten Paare (absteigend nach IoU,
    jeder Span höchstens einmal).
    """
    candidates = []
    for i, sa in enumerate(spans_a):
        for j, sb in enumerate(spans_b):
            iou = _iou(sa["bbox_norm"], sb["bbox_norm"])
            if iou > 0.0:
                candidates.append((iou, i, j))
    candidates.sort(reverse=True)
    used_a, used_b = set(), set()
    pairs = []
    for iou, i, j in candidates:
        if i in used_a or j in used_b:
            continue
        used_a.add(i)
        used_b.add(j)
        pairs.append((i, j, iou))
    return pairs


def geometry_score(spans_a, spans_b, pairs) -> float:
    """IoU-gewichtetes BBox-Matching, normalisiert auf die Span-Anzahl.

    Summe der Match-IoUs geteilt durch die größere Span-Menge — fehlende oder
    überzählige Spans drücken den Score (Recall- UND Precision-Seite).
    """
    denom = max(len(spans_a), len(spans_b))
    if denom == 0:
        return 1.0
    return sum(iou for _, _, iou in pairs) / denom


def font_score(spans_a, spans_b, pairs) -> float:
    """Anteil gematchter Spans mit gleicher Größe (±0.5pt) UND Font-Familie.

    Nenner ist die größere Span-Menge, damit unzuordenbare Spans als
    Font-Mismatch zählen (kein künstliches 1.0 bei leerem Match).
    """
    denom = max(len(spans_a), len(spans_b))
    if denom == 0:
        return 1.0
    good = 0
    for i, j, _ in pairs:
        sa, sb = spans_a[i], spans_b[j]
        if abs(sa["size"] - sb["size"]) <= SIZE_TOL_PT and sa["family"] == sb["family"]:
            good += 1
    return good / denom


def pixel_score(page_a, page_b) -> float:
    """1 − MAE der Graustufen-Pixmaps, auf gemeinsame @192px-Breite skaliert."""
    grids = []
    for page in (page_a, page_b):
        rect = page.rect
        width = float(rect.width) or 1.0
        zoom = PIXEL_WIDTH / width
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY, alpha=False)
        grids.append(pix)

    # Auf gemeinsames Raster (min. Breite/Höhe) zuschneiden — Seitenmaße können
    # differieren (A4 vs. 16:9). Wir vergleichen den überlappenden Bereich.
    w = min(grids[0].width, grids[1].width)
    h = min(grids[0].height, grids[1].height)
    if w == 0 or h == 0:
        return 0.0
    sa = grids[0].samples
    sb = grids[1].samples
    stride_a = grids[0].stride
    stride_b = grids[1].stride
    total = 0
    count = w * h
    for y in range(h):
        base_a = y * stride_a
        base_b = y * stride_b
        row_a = sa[base_a : base_a + w]
        row_b = sb[base_b : base_b + w]
        total += sum(abs(pa - pb) for pa, pb in zip(row_a, row_b))
    mae = total / (count * 255.0)
    return 1.0 - mae


# ---------------------------------------------------------------------------
# Öffentliche API
# ---------------------------------------------------------------------------
def compare(ref_pdf: str, ref_page: int, neu_pdf: str, neu_page: int) -> dict:
    """Vergleicht zwei PDF-Seiten und liefert die Teil-Scores + total.

    ref_page/neu_page sind 1-basiert. Koordinaten werden auf Seitenmaße
    normalisiert, sodass unterschiedliche Seitenformate nicht crashen.
    """
    doc_a, page_a = _open_page(ref_pdf, ref_page)
    try:
        doc_b, page_b = _open_page(neu_pdf, neu_page)
        try:
            text_a, spans_a, _ = extract_page(page_a)
            text_b, spans_b, _ = extract_page(page_b)
            pairs = _greedy_match(spans_a, spans_b)

            text = text_f1(text_a, text_b)
            geometry = geometry_score(spans_a, spans_b, pairs)
            font = font_score(spans_a, spans_b, pairs)
            pixel = pixel_score(page_a, page_b)
            total = (
                W_TEXT * text
                + W_GEOMETRY * geometry
                + W_FONT * font
                + W_PIXEL * pixel
            )
            return {
                "text": round(text, 6),
                "geometry": round(geometry, 6),
                "font": round(font, 6),
                "pixel": round(pixel, 6),
                "total": round(total, 6),
            }
        finally:
            doc_b.close()
    finally:
        doc_a.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _parse_arg(arg: str):
    """``path.pdf:3`` → (path, 3); ohne Suffix → Seite 1."""
    if ":" in arg:
        path, _, page = arg.rpartition(":")
        if page.isdigit() and path:
            return path, int(page)
    return arg, 1


def _fitz_version() -> str:
    ver = getattr(fitz, "version", None)
    if isinstance(ver, (tuple, list)) and ver:
        return str(ver[0])
    return str(ver)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print(
            "usage: fidelity.py REF.pdf:PAGE NEU.pdf:PAGE  (PAGE 1-basiert, default 1)",
            file=sys.stderr,
        )
        return 2
    ref_path, ref_page = _parse_arg(argv[0])
    neu_path, neu_page = _parse_arg(argv[1])
    for p in (ref_path, neu_path):
        if not Path(p).is_file():
            print(f"FEHLER: PDF nicht gefunden: {p}", file=sys.stderr)
            return 1
    try:
        scores = compare(ref_path, ref_page, neu_path, neu_page)
    except (IndexError, RuntimeError) as exc:
        print(f"FEHLER: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    out = {
        "fidelity_version": FIDELITY_VERSION,
        "fitz_version": _fitz_version(),
        "ref": {"pdf": ref_path, "page": ref_page},
        "neu": {"pdf": neu_path, "page": neu_page},
        "scores": scores,
        **scores,  # Teil-Scores auch top-level (CLI-/grep-freundlich)
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
