#!/usr/bin/env python3
"""Font-Extraktor über den Referenz-Korpus (Sprint 10, US-038).

Liest die 200 Kunden-PDFs unter ``<cache>/{slug}/assets/*.pdf`` (READ-ONLY) und
schreibt ein font-report.json (Schema: FEATURE-FONT-REPORT §3).

Kernregel (EARS §8 Nr. 2): pt-Größen kommen EXAKT aus der Text-Rendering-Matrix
— PyMuPDF ``span["size"]`` aus ``page.get_text("dict")``. Das ist genau die
Größe, die der PDF-Producer gesetzt hat; KEIN Glyph-Bbox-Maß, KEIN
Korrekturfaktor (der pdfminer-Bbox-Ansatz erzwang in der Engine einen Fudge —
hier bewusst vermieden).

CLI:
    font_report.py [--out PATH] [--cache PATH] [--verify]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import fitz  # PyMuPDF

# Korpus-Pfad relativ zum Repo-Root (dieses File liegt in tools/).
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CACHE = REPO_ROOT / ".." / "pptxgenerator_v2" / "phase0" / "data" / "cache"
DEFAULT_OUT = REPO_ROOT / "docs" / "sprint-10" / "font-report.json"

# Subset-Präfix wie "ABCDEF+OpenSans-Bold" → "OpenSans-Bold". Pitfall §12.2:
# ohne Strippen zerfällt die Font-Verteilung in lauter Einzel-Subsets.
SUBSET_PREFIX = re.compile(r"^[A-Z]{6}\+")

# PyMuPDF span flags (Bit-Feld, siehe PyMuPDF-Doku "TextPage.extractDICT"):
#   Bit 1 (2)  = italic, Bit 4 (16) = bold/serifed-bold.
FLAG_ITALIC = 1 << 1  # 2
FLAG_BOLD = 1 << 4    # 16


def strip_subset(font: str) -> str:
    return SUBSET_PREFIX.sub("", font)


def family_of(font: str) -> str:
    """Font-Familie ohne Stil-Suffix — für das fonts-Aggregat (grobe Verteilung)."""
    base = strip_subset(font)
    return base.split("-", 1)[0].split(",", 1)[0]


def color_hex(color_int: int) -> str:
    """PyMuPDF liefert sRGB als int (0xRRGGBB)."""
    return "#{:06x}".format(int(color_int) & 0xFFFFFF)


def detect_bold(font: str, flags: int) -> bool:
    name = strip_subset(font).lower()
    by_name = "bold" in name or "black" in name or "heavy" in name or "semibold" in name
    return bool(by_name or (flags & FLAG_BOLD))  # Font-Name ist führend, Flag ergänzt


def detect_italic(font: str, flags: int) -> bool:
    name = strip_subset(font).lower()
    by_name = "italic" in name or "oblique" in name
    return bool(by_name or (flags & FLAG_ITALIC))


def extract_pdf(pdf_path: Path):
    """Liefert (pages, spans_aggregiert, wingdings_glyph_counter) für ein PDF.

    spans_aggregiert: Liste {font, size_pt, color, bold, italic, count}, dedupliziert
    über (font, size_pt, color, bold, italic) mit aufsummiertem Zeichen-count.
    """
    doc = fitz.open(pdf_path)
    try:
        pages = doc.page_count
        agg: Counter = Counter()
        meta: dict = {}
        wingdings: Counter = Counter()
        for page in doc:
            data = page.get_text("dict")
            for block in data["blocks"]:
                if block.get("type") != 0:  # nur Text-Blöcke
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span.get("text", "")
                        if text == "":
                            continue
                        font = strip_subset(span["font"])
                        size_pt = round(float(span["size"]), 2)
                        color = color_hex(span["color"])
                        flags = int(span.get("flags", 0))
                        bold = detect_bold(font, flags)
                        italic = detect_italic(font, flags)
                        key = (font, size_pt, color, bold, italic)
                        n_chars = len(text)
                        agg[key] += n_chars
                        meta[key] = (font, size_pt, color, bold, italic)
                        # Pitfall §3-Schema: Wingdings-Glyphen einzeln zählen.
                        if "wingdings" in font.lower():
                            for ch in text:
                                wingdings["{:04x}".format(ord(ch))] += 1
        spans = [
            {
                "font": meta[k][0],
                "size_pt": meta[k][1],
                "color": meta[k][2],
                "bold": meta[k][3],
                "italic": meta[k][4],
                "count": agg[k],
            }
            for k in agg
        ]
        spans.sort(key=lambda s: (-s["count"], s["font"], s["size_pt"]))
        return pages, spans, wingdings
    finally:
        doc.close()


def find_pdfs(cache: Path):
    """Genau ein Eintrag pro slug: das (erste) PDF unter <slug>/assets/."""
    found = []
    for slug_dir in sorted(p for p in cache.iterdir() if p.is_dir()):
        assets = slug_dir / "assets"
        if not assets.is_dir():
            continue
        pdfs = sorted(assets.glob("*.pdf"))
        if pdfs:
            found.append((slug_dir.name, pdfs[0]))
    return found


def build_report(cache: Path) -> dict:
    cache = cache.resolve()
    entries = find_pdfs(cache)
    pdfs_out = []
    errors = []
    fonts_agg: Counter = Counter()
    sizes_agg: Counter = Counter()
    wingdings_agg: Counter = Counter()

    for slug, pdf_path in entries:
        try:
            pages, spans, wingdings = extract_pdf(pdf_path)
        except Exception as exc:  # Pitfall §12.3: Fehler ausweisen, nicht überspringen
            errors.append({"slug": slug, "reason": f"{type(exc).__name__}: {exc}"})
            # PDF zählt weiterhin als gefunden → Eintrag mit leeren spans halten,
            # damit len(pdfs)==pdf_count und der 200/200-Nachweis bestehen bleibt.
            pdfs_out.append({"slug": slug, "pages": 0, "spans": []})
            continue
        pdfs_out.append({"slug": slug, "pages": pages, "spans": spans})
        for s in spans:
            fonts_agg[family_of(s["font"])] += s["count"]
            sizes_agg["{:.2f}".format(s["size_pt"])] += s["count"]
        wingdings_agg.update(wingdings)

    return {
        "generated_for": f"{cache} (Stand: kochfabrik-studio Sprint 10, US-038)",
        "pdf_count": len(entries),
        "pdfs": pdfs_out,
        "errors": errors,
        "aggregate": {
            "fonts": dict(fonts_agg.most_common()),
            "sizes_pt": dict(sorted(sizes_agg.items(), key=lambda kv: float(kv[0]))),
            "wingdings_glyphs": dict(wingdings_agg.most_common()),
        },
    }


def verify(out_path: Path) -> int:
    try:
        d = json.loads(out_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"VERIFY FAIL: {out_path} fehlt", file=sys.stderr)
        return 1
    ok = True
    if d.get("pdf_count") != 200:
        print(f"VERIFY FAIL: pdf_count={d.get('pdf_count')} != 200", file=sys.stderr)
        ok = False
    if len(d.get("pdfs", [])) != 200:
        print(f"VERIFY FAIL: len(pdfs)={len(d.get('pdfs', []))} != 200", file=sys.stderr)
        ok = False
    agg = d.get("aggregate", {})
    for key in ("fonts", "sizes_pt", "wingdings_glyphs"):
        if key not in agg:
            print(f"VERIFY FAIL: aggregate.{key} fehlt", file=sys.stderr)
            ok = False
    if ok:
        print(f"VERIFY OK: pdf_count=200, pdfs=200, aggregate komplett ({out_path})")
        return 0
    return 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Font-Extraktor über den Referenz-Korpus")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--verify", action="store_true", help="Report laden + prüfen, kein Lauf")
    args = parser.parse_args(argv)

    if args.verify:
        return verify(args.out)

    cache = args.cache
    if not cache.is_dir():
        print(f"FEHLER: Korpus-Pfad nicht gefunden: {cache.resolve()}", file=sys.stderr)
        return 1

    report = build_report(cache)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    agg_fonts = report["aggregate"]["fonts"]
    top = list(agg_fonts.items())[:3]
    print(f"font-report.json geschrieben: {args.out}")
    print(f"  pdf_count={report['pdf_count']}  errors={len(report['errors'])}")
    print(f"  Top-Fonts: {', '.join(f'{f} ({c})' for f, c in top)}")
    if report["errors"]:
        for e in report["errors"]:
            print(f"  ERROR {e['slug']}: {e['reason']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
