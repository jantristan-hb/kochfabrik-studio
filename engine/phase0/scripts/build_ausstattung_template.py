"""build_ausstattung_template.py — LOCATION/AUSSTATTUNG-Platzhalter.

Kein Archetyp möglich (18 distinkte Volltexte, location-spezifisch) →
analog zum Cover EIN gewähltes Static-Template:
Basis = `er-ffnung-stetson-store::9` (KOCHfabriks eigene Blanko-Slide:
Titel „AUSTATTUNG" + Body „TEXT SCHREIBEN!" + Bildfläche).

Regeln (= Cover-Logik):
- großes Inhaltsbild (Deckung >= 50%) raus → leerer Bild-Slot, später
  aus dem Bildgenerator-Projekt befüllbar
- Vollseiten-Dunkel-Basis → weiß; Gold-Rahmen bleibt
- Titel bleibt; Body-Text → Platzhalter {LOCATION_AUSSTATTUNG}
  (Assembler füllt aus dem „Event Ausstattung"/Location-Block)

Artefakte: ausstattung_template.elements.json (Assembler) + .pptx
(Demo); static_slide-Zeile category='AUSSTATTUNG' (tier T, bedingt,
skel_pos 0.78).

Usage: python3 build_ausstattung_template.py [--sample "..."]
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

import psycopg2
from psycopg2.extras import execute_values

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _deckpipe import cached_deck, slugify                     # noqa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SPIKE = os.path.join(ROOT, "spike-pptxgenjs")
CORPUS = "/home/jrudat/Nextcloud/Kochfabrik Dokumente/AKARA_Präsentationen"
DSN = dict(host="localhost", port=5434, user="postgres",
           password="pptxgen", dbname="pptxgen")
BASE_SLUG = "er-ffnung-stetson-store"
BASE_PAGE = 9
PLACEHOLDER = "{LOCATION_AUSSTATTUNG}"
IMG_COVER = 0.50                  # >= 50% Seite = Inhaltsbild → leerer Slot
DARKISH = ("1B0000", "000000", "1A1A1A", "0B0B0B")
BLUE = "0070C0"                   # blaues Inhalts-Panel → raus (wie Cover)


def build(seq, meta, body_text):
    """Großbild raus, Dunkel-Basis→weiß, Titel bleibt, Body→Platzhalter."""
    W = meta.get("w_pt", 960) / 72.0
    H = meta.get("h_pt", 540) / 72.0

    def msz(e):
        return max((l["size"] for l in e["lines"]), default=0)

    txt_els = [e for e in seq if e["t"] == "text" and e.get("lines")]
    title_el = max(txt_els, key=msz) if txt_els else None
    body_els = [e for e in txt_els if e is not title_el]
    body_el = max(body_els, key=lambda e: e["w"] * e["h"]) \
        if body_els else None

    out, body_done = [], False
    for e in seq:
        if e["t"] == "image" and (e["w"] * e["h"]) / (W * H) >= IMG_COVER:
            continue                                  # Inhaltsbild → Slot
        if e["t"] == "rect" and e.get("fill") == BLUE:
            continue                                  # blaues Panel raus
        if e["t"] == "rect" and e.get("fill") in DARKISH \
                and e["w"] >= 0.95 * W and e["h"] >= 0.95 * H:
            e = dict(e, fill="FFFFFF")                # Basis → weiß
        if e is body_el and not body_done:
            st = e["lines"][0]
            e = dict(e, lines=[{k: st[k] for k in
                                ("size", "color", "weight", "italic")
                                if k in st} | {"txt": body_text}])
            body_done = True
        out.append(e)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", default="Opernloft im alten Fährterminal "
                    "Altona · Mischbestuhlung · Lounge-Möbel · Bar-Setup")
    a = ap.parse_args()

    src = next((os.path.join(CORPUS, p) for p in os.listdir(CORPUS)
                if p.lower().endswith(".pdf")
                and slugify(p) == BASE_SLUG), None)
    if not src:
        sys.exit(f"Basis-PDF für {BASE_SLUG} nicht gefunden")
    shared = tempfile.mkdtemp(prefix="ausst_")
    slug, el, logos = cached_deck(src, shared)
    meta = el.get("_meta", {"w_pt": 960, "h_pt": 540})
    seq = el[str(BASE_PAGE)]

    tmpl = build(seq, meta, PLACEHOLDER)
    json.dump({"1": tmpl, "_meta": dict(meta, deck="ausstattung-template")},
              open(os.path.join(DATA, "ausstattung_template.elements.json"),
                   "w"), ensure_ascii=False)

    demo = build(seq, meta, a.sample)
    json.dump({"1": demo, "_meta": dict(meta, deck="ausstattung-template")},
              open(os.path.join(shared, "elements.json"), "w"))
    json.dump(logos, open(os.path.join(shared, "logos.json"), "w"))
    out = os.path.join(DATA, "ausstattung_template.pptx")
    subprocess.run(["node", os.path.join(SPIKE, "reconstruct.js"),
                    "elements.json", out], cwd=shared,
                   capture_output=True, check=True, timeout=120)

    imgs = [e for e in seq if e["t"] == "image"]
    W = meta["w_pt"] / 72.0
    H = meta["h_pt"] / 72.0
    rm = [e for e in imgs if (e["w"]*e["h"])/(W*H) >= IMG_COVER]
    print(f"Ausstattung-Template aus {slug}::{BASE_PAGE}")
    print(f"  Bilder {len(imgs)} → {len(rm)} raus (Inhaltsbild→leerer "
          f"Slot) | Basis→weiß | Body→{PLACEHOLDER} | "
          f"Elemente {len(tmpl)} (von {len(seq)})")
    print(f"  → {DATA}/ausstattung_template.elements.json (Assembler)")
    print(f"  → {out} (Demo: '{a.sample[:50]}…')")

    cx = psycopg2.connect(**DSN)
    cu = cx.cursor()
    cu.execute("DELETE FROM static_slide WHERE category='AUSSTATTUNG'")
    execute_values(cu,
                   "INSERT INTO static_slide (category,rank,cnt,tier,"
                   "skel_pos,inclusion,deck,src_pdf,page,full_text,"
                   "is_golden) VALUES %s",
                   [("AUSSTATTUNG", 0, 0, "T", 0.78, "bedingt", slug,
                     src, BASE_PAGE, PLACEHOLDER, True)])
    cx.commit()
    cu.execute("SELECT category,tier,inclusion,skel_pos,is_golden "
               "FROM static_slide WHERE category='AUSSTATTUNG'")
    print(f"  static_slide: {cu.fetchone()}")
    cx.close()


if __name__ == "__main__":
    main()
