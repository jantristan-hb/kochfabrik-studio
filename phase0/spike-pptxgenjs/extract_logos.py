"""Transparente Logos/Badges: poppler isoliert Bild + Soft-Mask sauber
(gleiche object-ID), PIL fuegt Alpha zusammen. Deterministisch, KEIN
Generieren. Reihenfolge-Mapping: k-tes <image> in pdftohtml-xml == k-te
'image'-Zeile in pdfimages -list (beide poppler, gleiche Seitentraversierung).

Output:
  assets/logos/<pdftohtml-basename>.png   (RGBA, nur wenn Soft-Mask existiert)
  logos.json  -> { "assets/ref-1_1.png": "assets/logos/ref-1_1.png", ... }
"""
import glob
import json
import os
import re
import subprocess
from PIL import Image

os.makedirs("assets/raw", exist_ok=True)
os.makedirs("assets/logos", exist_ok=True)

subprocess.run(["pdfimages", "-png", "-p", "assets/ref.pdf", "assets/raw/r"],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
listing = subprocess.run(["pdfimages", "-list", "assets/ref.pdf"],
                          capture_output=True, text=True).stdout.splitlines()

# pdfimages -list -> pro Seite geordnete (num,type,obj)
rows_by_page = {}
for ln in listing[2:]:
    p = ln.split()
    if len(p) < 11:
        continue
    page, num, typ, obj = int(p[0]), int(p[1]), p[2], p[10]
    rows_by_page.setdefault(page, []).append((num, typ, obj))


def rawfile(page, num):
    hits = glob.glob(f"assets/raw/r-*{page}-*{num}.png") + \
           glob.glob(f"assets/raw/r-{page:03d}-{num:03d}.png")
    for h in sorted(set(hits)):
        if re.search(rf"-0*{page}-0*{num}\.png$", h):
            return h
    return None


xml = open("assets/ref.xml", encoding="utf-8", errors="ignore").read()
chunks = [c for c in xml.split("</page>") if "<image" in c or "<text" in c]

mapping = {}
for pidx, c in enumerate(chunks, 1):
    srcs = re.findall(r'<image[^>]*src="([^"]+)"', c)
    rows = rows_by_page.get(pidx, [])
    images = [r for r in rows if r[1] == "image"]
    smask_by_obj = {obj: num for (num, typ, obj) in rows if typ == "smask"}
    for k, src in enumerate(srcs):
        if k >= len(images):
            break
        num, _, obj = images[k]
        sm = smask_by_obj.get(obj)
        if sm is None:
            continue  # kein Alpha -> Original (opak) behalten
        bf, mf = rawfile(pidx, num), rawfile(pidx, sm)
        if not bf or not mf:
            continue
        base = Image.open(bf).convert("RGBA")
        mask = Image.open(mf).convert("L").resize(base.size)
        base.putalpha(mask)
        out = f"assets/logos/{os.path.basename(src)}"
        out = os.path.splitext(out)[0] + ".png"
        base.save(out)
        mapping[src] = out

json.dump(mapping, open("logos.json", "w"), indent=1)
print("logos.json:", len(mapping), "transparente Logos")
