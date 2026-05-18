"""build_menu_deck.py — EINE pptx mit ALLEN Menü-Kandidaten aus ALLEN PDFs.

Mensch-kuratierter Ground-Truth statt Klassifikator-Perfektion:
inklusiv sammeln (lieber zu viel), Jan löscht die Falschen von Hand.
Volle Per-Deck-Pipeline via _deckpipe → transparentes/Gold-Logo bleibt,
Bild-Namen deck-genamespaced, gemergte logos.json.

Usage (aus spike-pptxgenjs/):
  python3 ../scripts/build_menu_deck.py /tmp/all_menus.pptx [--limit N]
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _deckpipe import process_deck                                  # noqa
from ingest_compositions import classify, is_content_photo          # noqa

SPIKE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "spike-pptxgenjs")
CORPUS = "/home/jrudat/Nextcloud/Kochfabrik Dokumente/AKARA_Präsentationen"

ap = argparse.ArgumentParser()
ap.add_argument("out", nargs="?", default="/tmp/all_menus.pptx")
ap.add_argument("--limit", type=int, default=0, help="0 = alle Decks")
a = ap.parse_args()
out = os.path.abspath(a.out)

pdfs = [p for p in sorted(glob.glob(os.path.join(CORPUS, "*.pdf")))
        if not os.path.basename(p).startswith("Angebot #")]
if a.limit:
    pdfs = pdfs[:a.limit]

shared = tempfile.mkdtemp(prefix="allmenus_")
combined, logos, meta, n = {}, {}, None, 0
ok_decks, fails = 0, []

for i, pdf in enumerate(pdfs, 1):
    name = os.path.basename(pdf)
    print(f"[{i}/{len(pdfs)}] {name[:46]}", file=sys.stderr)
    try:
        slug, el, lg = process_deck(pdf, shared)
    except Exception as ex:
        fails.append(name)
        print(f"  skip: {str(ex).splitlines()[-1][:90]}", file=sys.stderr)
        continue
    ok_decks += 1
    logos.update(lg)
    m = el.get("_meta", {"w_pt": 960, "h_pt": 540})
    if meta is None:
        meta = m
    W, H = m["w_pt"] / 72.0, m["h_pt"] / 72.0
    for pg, seq in sorted(((k, v) for k, v in el.items() if k != "_meta"),
                          key=lambda kv: int(kv[0])):
        nphoto = sum(1 for e in seq
                     if e["t"] == "image" and is_content_photo(e, W, H))
        lines = [ln for e in seq if e["t"] == "text" for ln in e["lines"]]
        kind, _ = classify(int(pg), lines, nphoto)
        if kind != "menu":
            continue
        n += 1
        combined[str(n)] = seq

if n == 0:
    sys.exit("Keine Menü-Kandidaten — Klassifikator/Filter prüfen.")

mm = dict(meta or {"w_pt": 960, "h_pt": 540})
mm["deck"] = "all-menus"            # keine Deck-Overrides
combined["_meta"] = mm
json.dump(combined, open(os.path.join(shared, "elements.json"), "w"))
json.dump(logos, open(os.path.join(shared, "logos.json"), "w"))
subprocess.run(["node", os.path.join(SPIKE, "reconstruct.js"),
                "elements.json", out], cwd=shared,
               capture_output=True, check=True, timeout=1800)
print(f"\nOK: {out} — {n} Menü-Kandidaten aus {ok_decks} Decks "
      f"({len(fails)} Decks fehlgeschlagen)")
print("Kuratieren: Falsch-Slides in PowerPoint/Impress von Hand löschen.")
