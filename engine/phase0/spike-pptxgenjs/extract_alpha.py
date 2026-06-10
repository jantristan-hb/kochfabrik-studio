"""Transparente Logo/Badge-Extraktion: Bild + Soft-Mask -> RGBA-PNG.
Deterministisch via PyMuPDF, KEIN Generieren. Platzierung kommt weiter aus
pdftohtml (validiert); hier nur Pixel+Position zum Matchen.

Output:
  assets/alpha/p<page>_<xref>.png   (RGBA)
  images_alpha.json  -> { "1": [ {x,y,w,h,file} (Zoll, oben-links) ] }
"""
import json
import os
import fitz  # PyMuPDF

U = 72.0
os.makedirs("assets/alpha", exist_ok=True)
doc = fitz.open("assets/ref.pdf")
out = {}

for pno in range(len(doc)):
    page = doc[pno]
    entries = []
    for img in page.get_images(full=True):
        xref, smask = img[0], img[1]
        base = fitz.Pixmap(doc, xref)
        if smask:                          # Alpha aus Soft-Mask anwenden
            try:
                pix = fitz.Pixmap(base, fitz.Pixmap(doc, smask))
            except Exception:
                pix = base
        else:
            pix = base                     # opak (z.B. großes Foto) -> egal
        if pix.n > 4:                      # CMYK -> RGB(A)
            pix = fitz.Pixmap(fitz.csRGB, pix)
        fn = f"assets/alpha/p{pno+1}_{xref}.png"
        pix.save(fn)
        has_alpha = bool(smask)
        for r in page.get_image_rects(xref):
            entries.append({
                "x": round(r.x0 / U, 4), "y": round(r.y0 / U, 4),
                "w": round(r.width / U, 4), "h": round(r.height / U, 4),
                "file": fn, "alpha": has_alpha,
            })
    out[str(pno + 1)] = entries

json.dump(out, open("images_alpha.json", "w"), indent=1)
print("images_alpha.json:", {k: len(v) for k, v in out.items()})
