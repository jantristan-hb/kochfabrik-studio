"""Element-Extraktion: gefuellte Vektor-Rechtecke je Seite via pdfminer.
Das ist die Design-Schicht (Panels, Faerbungen, Raender), die pdftohtml
NICHT liefert. Output: rects.json  -> { "1":[{x,y,w,h,fill}], ... }
Koordinaten in Zoll, Ursprung oben-links (PPTX-Konvention).
"""
import json
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTRect, LTFigure, LTImage

PAGE_H = 540.0
U = 72.0


def to_hex(c):
    if c is None:
        return None
    if isinstance(c, (int, float)):
        v = int(round(float(c) * 255)); return f"{v:02X}{v:02X}{v:02X}"
    if len(c) == 1:
        v = int(round(c[0] * 255)); return f"{v:02X}{v:02X}{v:02X}"
    if len(c) == 3:
        return "".join(f"{int(round(x*255)):02X}" for x in c)
    if len(c) == 4:  # CMYK
        cy, m, y, k = c
        r = 255 * (1 - cy) * (1 - k)
        g = 255 * (1 - m) * (1 - k)
        b = 255 * (1 - y) * (1 - k)
        return f"{int(r):02X}{int(g):02X}{int(b):02X}"
    return None


def collect(obj, out):
    for e in obj:
        if isinstance(e, LTRect):
            fill = to_hex(getattr(e, "non_stroking_color", None))
            x0, y0, x1, y1 = e.bbox
            if fill and (x1 - x0) > 1 and (y1 - y0) > 1:
                out.append({
                    "x": round(x0 / U, 4),
                    "y": round((PAGE_H - y1) / U, 4),
                    "w": round((x1 - x0) / U, 4),
                    "h": round((y1 - y0) / U, 4),
                    "fill": fill,
                })
        elif isinstance(e, LTFigure):
            collect(e, out)


pages = {}
for i, pg in enumerate(extract_pages("assets/ref.pdf"), 1):
    rects = []
    collect(pg, rects)              # Dokumentreihenfolge = Mal-Reihenfolge
    pages[str(i)] = rects

json.dump(pages, open("rects.json", "w"), indent=1)
print("rects.json:", {k: len(v) for k, v in pages.items()})
