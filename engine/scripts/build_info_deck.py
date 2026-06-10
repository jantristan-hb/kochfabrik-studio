"""build_info_deck.py — EINE pptx aller NICHT-Food-Kandidaten (Step 2).

Nicht-Food = jede (deck,page) der 171 Korpus-Decks, die NICHT in
menu_composition (= die 1010 kuratierten Speisen) ist. Quelle: der
Element-Cache (cached_deck — jede Deck-elements.json hat ALLE Seiten).
Output: /tmp/all_info.pptx + .manifest.json, jede Slide trägt
deck::page-Notiz. Danach bewährter Flow:
  slide_text.py → embed_cluster (cluster) → resort_pptx → Jan kürt je
  Nicht-Food-Typ EINE goldene Instanz (Block-Löschen, Cluster-sortiert).

Voraussetzung: build_cache.py durchgelaufen (sonst lazy = langsam).
Usage: python3 build_info_deck.py [/tmp/all_info.pptx] [--limit N]
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import tempfile

import psycopg2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _deckpipe import cached_deck, slugify                     # noqa

SPIKE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "spike-pptxgenjs")
CORPUS = "/Users/janrudat/Nextcloud/Kochfabrik Dokumente/AKARA_Präsentationen"
DSN = dict(host="localhost", port=5434, user="postgres",
           password="pptxgen", dbname="pptxgen")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", default="/tmp/all_info.pptx")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    out = os.path.abspath(a.out)

    cx = psycopg2.connect(**DSN)
    cu = cx.cursor()
    cu.execute("SELECT deck, page FROM menu_composition")
    food = {(d, int(p)) for d, p in cu.fetchall()}
    cx.close()
    print(f"Food-Set (ausschließen): {len(food)} (deck,page)")

    pdfs = [p for p in sorted(glob.glob(os.path.join(CORPUS, "*.pdf")))
            if not os.path.basename(p).startswith("Angebot #")]
    if a.limit:
        pdfs = pdfs[:a.limit]

    shared = tempfile.mkdtemp(prefix="info_")
    combined, notes, manifest, logos, meta = {}, {}, {}, {}, None
    n, ok, fails = 0, 0, []
    for i, pdf in enumerate(pdfs, 1):
        name = os.path.basename(pdf)
        print(f"[{i}/{len(pdfs)}] {name[:44]}", file=sys.stderr)
        try:
            slug, el, lg = cached_deck(pdf, shared)
        except Exception as ex:
            fails.append(name)
            print(f"  skip: {str(ex).splitlines()[-1][:80]}", file=sys.stderr)
            continue
        ok += 1
        logos.update(lg)
        if meta is None:
            meta = el.get("_meta", {"w_pt": 960, "h_pt": 540})
        for pg, seq in ((k, v) for k, v in el.items() if k != "_meta"):
            if (slug, int(pg)) in food:
                continue                       # Food bleibt bei Speisen
            n += 1
            combined[str(n)] = seq
            notes[str(n)] = f"{slug}::{pg}"
            manifest[str(n)] = {"deck": slug, "page": int(pg),
                                "src_pdf": pdf}

    if not combined:
        sys.exit("Keine Nicht-Food-Kandidaten.")
    mm = dict(meta or {"w_pt": 960, "h_pt": 540})
    mm["deck"], mm["notes"] = "all-info", notes
    combined["_meta"] = mm
    json.dump(combined, open(os.path.join(shared, "elements.json"), "w"))
    json.dump(logos, open(os.path.join(shared, "logos.json"), "w"))
    json.dump(manifest, open(out + ".manifest.json", "w"), indent=1)
    subprocess.run(["node", os.path.join(SPIKE, "reconstruct.js"),
                    "elements.json", out], cwd=shared,
                   capture_output=True, check=True, timeout=2400)
    print(f"\nOK: {out} — {n} Nicht-Food-Slides aus {ok} Decks "
          f"({len(fails)} fehlgeschlagen)")
    print(f"Manifest: {out}.manifest.json | Notizen: deck::page")
    print("Weiter: slide_text.py → embed_cluster cluster → resort_pptx "
          "→ je Typ EINE goldene Instanz küren.")


if __name__ == "__main__":
    main()
