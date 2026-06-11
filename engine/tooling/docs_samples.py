"""docs_samples.py — Referenz-Sample-Decks nach docs/samples/.

- cover.pptx       : das Cover-Template (Kopie)
- info_static.pptx : die golden/pflicht Static-Frame-Slides
                     (Crew/Personal/Wertschätzung/Kontakt) verbatim
- food_sample.pptx : ein Repräsentant je größtem embedded
                     menu_composition-Modul (Top 25 Cluster)

Alles aus dem warmen Cache (keine Extraktion), je 1 reconstruct.
Usage: python3 docs_samples.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

import psycopg2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# US-056: Tooling lebt jetzt unter engine/tooling/ — Runtime-Module
# (engine/scripts/) zusätzlich auf den Pfad (KEINE Logikänderung).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "scripts"))
from _deckpipe import cached_deck, slugify                     # noqa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SPIKE = os.path.join(ROOT, "spike-pptxgenjs")
SAMPLES = os.path.join(ROOT, "..", "docs", "samples")
CORPUS = "/Users/janrudat/Nextcloud/Kochfabrik Dokumente/AKARA_Präsentationen"
DSN = dict(host="localhost", port=5434, user="postgres",
           password="pptxgen", dbname="pptxgen")


def render(rows, out, label):
    """rows: [(deck,page,src_pdf,note)] → ein Deck via Cache."""
    shared = tempfile.mkdtemp(prefix="smp_")
    smap = {slugify(p): os.path.join(CORPUS, p)
            for p in os.listdir(CORPUS) if p.lower().endswith(".pdf")}
    elc, logos, meta = {}, {}, None
    for deck, pg, src, _ in rows:
        if deck not in elc:
            _, el, lg = cached_deck(src or smap.get(deck, ""), shared)
            logos.update(lg)
            elc[deck] = el
            if meta is None:
                meta = el.get("_meta", {"w_pt": 960, "h_pt": 540})
    combined, notes, n = {}, {}, 0
    for deck, pg, src, note in rows:
        seq = elc.get(deck, {}).get(str(pg))
        if not seq:
            continue
        n += 1
        combined[str(n)] = seq
        notes[str(n)] = note
    mm = dict(meta or {"w_pt": 960, "h_pt": 540})
    mm["deck"], mm["notes"] = label, notes
    combined["_meta"] = mm
    json.dump(combined, open(os.path.join(shared, "elements.json"), "w"))
    json.dump(logos, open(os.path.join(shared, "logos.json"), "w"))
    subprocess.run(["node", os.path.join(SPIKE, "reconstruct.js"),
                    "elements.json", out], cwd=shared,
                   capture_output=True, check=True, timeout=300)
    print(f"  {label}: {n} Slides → {out}")


def cslug(c):
    import re
    return re.sub(r"[^a-z0-9]+", "-", c.lower()).strip("-")[:32] or "cat"


def main():
    os.makedirs(SAMPLES, exist_ok=True)
    # 1) Cover (= COVER-Golden)
    src = os.path.join(DATA, "cover_template.pptx")
    if os.path.isfile(src):
        shutil.copy(src, os.path.join(SAMPLES, "golden_cover.pptx"))
        print(f"  golden_cover.pptx → {SAMPLES}/ (Kopie Cover-Template)")

    cx = psycopg2.connect(**DSN)
    cu = cx.cursor()
    # 2) Golden-Dataset JE Kategorie (golden + freigegebene Alternativen,
    #    golden zuerst) — je ein File zum Sichern/Verschicken
    cu.execute("SELECT DISTINCT category FROM static_slide "
               "WHERE category<>'COVER' ORDER BY category")
    for (cat,) in cu.fetchall():
        cu.execute("SELECT deck,page,src_pdf,is_golden FROM static_slide "
                   "WHERE category=%s ORDER BY is_golden DESC, id", (cat,))
        rows = [(d, p, s, ("GOLDEN" if g else "alt"))
                for d, p, s, g in cu.fetchall()]
        render(rows, os.path.join(SAMPLES, f"golden_{cslug(cat)}.pptx"),
               cslug(cat))
    # 3) Food-Sample: Repräsentant (min id) je Top-25-Modul
    cu.execute("""
      SELECT m.deck,m.page,m.src_pdf,m.module_label FROM menu_composition m
      JOIN (SELECT module_type, count(*) c, min(id) rid
            FROM menu_composition GROUP BY module_type
            ORDER BY c DESC LIMIT 25) t ON m.id=t.rid
      ORDER BY t.c DESC""")
    render([(d, p, s, lbl or "menu") for d, p, s, lbl in cu.fetchall()],
           os.path.join(SAMPLES, "food_sample.pptx"), "food-sample")
    cx.close()
    print(f"\nReferenz-Samples in {SAMPLES}/")


if __name__ == "__main__":
    main()
