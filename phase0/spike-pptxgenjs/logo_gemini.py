"""Logo-Freistellung via Gemini: jpg/png rein -> transparentes png zurueck.
KEIN Generieren — Hintergrund entfernen, Logo unveraendert lassen.

Usage: python3 logo_gemini.py assets/ref-1_1.png assets/ref-1_4.jpg ...
Output: assets/logos/<name>.png  + Eintrag in logos.json
"""
import io
import json
import os
import sys
from google import genai
from PIL import Image

KEY = next(l.split("=", 1)[1].strip().strip('"')
           for l in open(os.path.expanduser("~/work/.env"))
           if l.startswith("GEMINI_API_KEY="))
client = genai.Client(api_key=KEY)
MODEL = "gemini-2.5-flash-image"
PROMPT = ("Remove the background completely and make it fully transparent. "
          "Return ONLY this exact logo/badge, pixel-identical, no recoloring, "
          "no redrawing, no added elements. Output a PNG with alpha channel.")

os.makedirs("assets/logos", exist_ok=True)
mapping = json.load(open("logos.json")) if os.path.exists("logos.json") else {}

for src in sys.argv[1:]:
    img = Image.open(src)
    r = client.models.generate_content(model=MODEL, contents=[PROMPT, img])
    saved = False
    for part in r.candidates[0].content.parts:
        d = getattr(part, "inline_data", None)
        if d and d.data:
            out = "assets/logos/" + os.path.splitext(os.path.basename(src))[0] + ".png"
            Image.open(io.BytesIO(d.data)).convert("RGBA").save(out)
            mapping[src] = out
            print("OK", src, "->", out)
            saved = True
            break
    if not saved:
        print("KEIN Bild zurueck:", src)

json.dump(mapping, open("logos.json", "w"), indent=1)
