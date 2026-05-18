"""Eine Extraktion, echte Mal-Reihenfolge. pdfminer liefert pro Seite
ALLE Elemente (Rect / Bild / Text) in Dokument-/Paint-Order. Genau diese
Reihenfolge wird spaeter 1:1 in pptxgenjs emittiert -> korrekte z-Order
ohne Heuristik (kein covered-skip, kein isBorder, kein fg-Flag).

- rect : gefuelltes Rechteck         -> Shape
- image: k-tes Bild der Seite        -> pdftohtml-Datei (+ Logo-Transparenz)
- text : Textzeile (Unicode dekodiert -> loest &amp; etc.)

Koordinaten: Zoll, Ursprung oben-links. Seitenmaß aus dem PDF (pdfminer
page.width/height) -> kein Hardcode. Output: <out.json> mit "_meta".

Usage: extract.py <input.pdf> [out.json] [--xml <pdftohtml.xml>]
"""
import argparse
import html
import json
import os
import re
from pdfminer.high_level import extract_pages
from pdfminer.layout import (LTRect, LTLine, LTCurve, LTImage, LTFigure,
                             LTTextLineHorizontal, LTTextBoxHorizontal,
                             LTTextContainer, LTChar)

U = 72.0

ap = argparse.ArgumentParser()
ap.add_argument("pdf", help="Input-PDF")
ap.add_argument("out", nargs="?", default="elements.json", help="Output-JSON")
ap.add_argument("--xml", default=None,
                help="pdftohtml-XML (default: <pdf-basename>.xml daneben)")
A = ap.parse_args()
XML_PATH = A.xml or (os.path.splitext(A.pdf)[0] + ".xml")


def hexc(c):
    if c is None:
        return None
    if isinstance(c, (int, float)):
        v = max(0, min(255, int(round(float(c) * 255))))
        return f"{v:02X}{v:02X}{v:02X}"
    if len(c) == 1:
        v = int(round(c[0] * 255)); return f"{v:02X}{v:02X}{v:02X}"
    if len(c) == 3:
        return "".join(f"{max(0,min(255,int(round(x*255)))):02X}" for x in c)
    if len(c) == 4:
        cy, m, y, k = c
        return "".join(f"{int(255*(1-a)*(1-k)):02X}" for a in (cy, m, y))
    return None


def box(e, ph):
    x0, y0, x1, y1 = e.bbox
    return {"x": round(x0 / U, 4), "y": round((ph - y1) / U, 4),
            "w": round((x1 - x0) / U, 4), "h": round((y1 - y0) / U, 4)}


# pdftohtml-Bild-Quellen pro Seite, in Lesereihenfolge (fuer Pixel)
xml = open(XML_PATH, encoding="utf-8", errors="ignore").read()
srcs_by_page = []
for c in xml.split("</page>"):
    if "<image" in c or "<text" in c:
        srcs_by_page.append(re.findall(r'<image[^>]*src="([^"]+)"', c))


def first_char(o):
    for e in o:
        if isinstance(e, LTChar):
            return e
        if hasattr(e, "__iter__"):
            r = first_char(e)
            if r:
                return r
    return None


pages = list(extract_pages(A.pdf))
out = {"_meta": {"w_pt": round(pages[0].width, 2),
                 "h_pt": round(pages[0].height, 2)} if pages
       else {"w_pt": 960.0, "h_pt": 540.0}}

for pi, page in enumerate(pages):
    seq = []
    img_k = 0
    ph = page.height                       # Seitenhöhe je Seite (y-Flip)
    srcs = srcs_by_page[pi] if pi < len(srcs_by_page) else []

    def walk(obj):
        global img_k
        for e in obj:
            if isinstance(e, (LTRect, LTLine, LTCurve)):
                f = hexc(getattr(e, "non_stroking_color", None))
                b = box(e, ph)
                # nur Sub-2px-Hairlines raus; dünne Seitenränder behalten
                if f and b["w"] >= 0.03 and b["h"] >= 0.03:
                    seq.append({"t": "rect", "fill": f, **b})
            elif isinstance(e, LTImage):
                src = srcs[img_k] if img_k < len(srcs) else None
                img_k += 1
                if src:
                    seq.append({"t": "image", "src": src, **box(e, ph)})
            elif isinstance(e, LTFigure):
                walk(e)
            elif isinstance(e, LTTextBoxHorizontal):
                # EIN editierbares Textfeld pro Block; Zeilen = Rich-Text-Runs
                lines = []
                for ln in e:
                    if not isinstance(ln, LTTextLineHorizontal):
                        continue
                    t = html.unescape(ln.get_text()).strip()
                    if not t:
                        continue
                    ch = first_char(ln)
                    gs = getattr(ch, "graphicstate", None)
                    fn = (ch.fontname or "") if ch else ""
                    wt = fn.split("-")[-1] if "-" in fn else "Regular"
                    lines.append({
                        "txt": t,
                        "size": round(ch.size, 2) if ch else 12,
                        "color": (hexc(gs.ncolor) if gs else None) or "FFFFFF",
                        "weight": wt.replace("Italic", "") or "Regular",
                        "italic": "Italic" in wt,
                    })
                if lines:
                    seq.append({"t": "text", **box(e, ph), "lines": lines})
            elif isinstance(e, LTTextContainer):
                walk(e)

    walk(page)
    out[str(pi + 1)] = seq

json.dump(out, open(A.out, "w"), indent=1)
pages_only = {k: v for k, v in out.items() if k != "_meta"}
print(f"{A.out}: {len(pages_only)} Slides, Maß "
      f"{out['_meta']['w_pt']}x{out['_meta']['h_pt']}pt |",
      {k: len(v) for k, v in pages_only.items()})
