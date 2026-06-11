"""build_menu_deck.py — EINE pptx aller Menü-Kandidaten aus ALLEN PDFs,
nach Ähnlichkeit sortiert + mit Manifest/Slide-Notizen für DB-Rückmapping.

- volle Per-Deck-Pipeline via _deckpipe → transparentes/Gold-Logo bleibt
- Struktur-Signatur je Slide → gleiche Archetypen liegen AM STÜCK
  (Block-Löschen statt Einzeljagd beim Kuratieren)
- jede Slide bekommt unsichtbare Notiz "deck::page" (übersteht Löschen/
  Umsortieren) + `<out>.manifest.json` (slide_no → deck/page/src_pdf)
- Kuratierung: Falsch-Slides löschen → überlebende Slide-Notizen lesen =
  exakte (deck,page)-Menge für menu_composition.

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
# US-056: Tooling lebt jetzt unter engine/tooling/ — Runtime-Module
# (engine/scripts/) zusätzlich auf den Pfad (KEINE Logikänderung).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "scripts"))
from _deckpipe import process_deck                                  # noqa
from ingest_compositions import classify, is_content_photo          # noqa

SPIKE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "spike-pptxgenjs")
CORPUS = "/Users/janrudat/Nextcloud/Kochfabrik Dokumente/AKARA_Präsentationen"


def signature(seq, W, H):
    """Struktur-Fingerprint → gleiche Archetypen sortieren benachbart."""
    photos = [e for e in seq
              if e["t"] == "image" and is_content_photo(e, W, H)]
    photos.sort(key=lambda e: (round(e["y"], 1), round(e["x"], 1)))
    grid = ";".join(
        f"{round(e['x']/W*8)},{round(e['y']/H*8)},"
        f"{round(e['w']/W*8)},{round(e['h']/H*8)}" for e in photos)
    ntext = sum(1 for e in seq if e["t"] == "text")
    sizes = [ln["size"] for e in seq if e["t"] == "text"
             for ln in e["lines"]]
    title_b = int(max(sizes) // 8) if sizes else 0
    return (len(photos), grid, ntext, title_b)


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
logos = {}
meta = None
items = []                       # (sig, slug, src_pdf, page, seq)
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
    for pg, seq in ((k, v) for k, v in el.items() if k != "_meta"):
        nphoto = sum(1 for e in seq
                     if e["t"] == "image" and is_content_photo(e, W, H))
        lines = [ln for e in seq if e["t"] == "text" for ln in e["lines"]]
        if classify(int(pg), lines, nphoto)[0] != "menu":
            continue
        items.append((signature(seq, W, H), slug, pdf, int(pg), seq))

if not items:
    sys.exit("Keine Menü-Kandidaten.")

items.sort(key=lambda t: t[0])           # ähnliche Slides benachbart
combined, notes, manifest = {}, {}, {}
for n, (_sig, slug, src, pg, seq) in enumerate(items, 1):
    combined[str(n)] = seq
    notes[str(n)] = f"{slug}::{pg}"
    manifest[str(n)] = {"deck": slug, "page": pg, "src_pdf": src}

mm = dict(meta or {"w_pt": 960, "h_pt": 540})
mm["deck"] = "all-menus"
mm["notes"] = notes                      # reconstruct.js → addNotes je Slide
combined["_meta"] = mm
json.dump(combined, open(os.path.join(shared, "elements.json"), "w"))
json.dump(logos, open(os.path.join(shared, "logos.json"), "w"))
json.dump(manifest, open(out + ".manifest.json", "w"), indent=1)
subprocess.run(["node", os.path.join(SPIKE, "reconstruct.js"),
                "elements.json", out], cwd=shared,
               capture_output=True, check=True, timeout=2400)
print(f"\nOK: {out} — {len(items)} Menü-Kandidaten aus {ok_decks} Decks "
      f"({len(fails)} fehlgeschlagen), ähnlichkeits-sortiert.")
print(f"Manifest: {out}.manifest.json | Slide-Notizen: 'deck::page'")
print("Kuratieren: Falsch-Slides löschen → überlebende Notizen = "
      "menu_composition-Ground-Truth.")
