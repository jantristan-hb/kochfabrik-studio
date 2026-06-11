"""build_info_top20.py — die 20 absolut häufigsten mehrfach
vorkommenden Info-Slides, EIN Deck, absteigend nach Häufigkeit.

Identität = **exakter normalisierter Volltext der Seite** (NICHT
Headline — Headline-Bucketing blähte event-spezifische Slides auf:
'VERANSTALTUNG INKL. AUF- & ABBAU' = 7 distinkte Volltexte je 1×).
Häufigkeit = absolute Anzahl Vorkommen dieses exakten Volltexts im
Korpus. Nur **mehrfach** (count >= 2). Top 20 nach Häufigkeit,
pptx **absteigend** sortiert (häufigster zuerst). Repräsentant =
erste Fundstelle.

Ausgeschlossen: Cover (Seite 1), Food (menu_composition), text-arm
(<12 Zeichen). Kein Headline-/JUNK-Filter (count>=2 trennt
Event-spezifisches sauber ab).

Output: phase0/data/info_top20.pptx (+ .manifest.json), persistent.
Usage: python3 build_info_top20.py [--n 20]
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict

import psycopg2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# US-056: Tooling lebt jetzt unter engine/tooling/ — Runtime-Module
# (engine/scripts/) zusätzlich auf den Pfad (KEINE Logikänderung).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "scripts"))
from _deckpipe import cached_deck, slugify                     # noqa
from analyze_structure import deck_elements                     # noqa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SPIKE = os.path.join(ROOT, "spike-pptxgenjs")
CORPUS = "/Users/janrudat/Nextcloud/Kochfabrik Dokumente/AKARA_Präsentationen"
DSN = dict(host="localhost", port=5434, user="postgres",
           password="pptxgen", dbname="pptxgen")


def full_text(seq):
    t = " ".join(l.get("txt", "") for e in seq if e.get("t") == "text"
                 for l in e.get("lines", []))
    return re.sub(r"\s+", " ", t).strip().upper()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    a = ap.parse_args()

    cx = psycopg2.connect(**DSN)
    cu = cx.cursor()
    cu.execute("SELECT deck, page FROM menu_composition")
    food = {(d, int(p)) for d, p in cu.fetchall()}
    cx.close()

    grp = defaultdict(list)                    # volltext -> [(slug,page)]
    for pdf in sorted(glob.glob(os.path.join(CORPUS, "*.pdf"))):
        try:
            slug, el = deck_elements(pdf)
        except Exception:
            continue
        for k, seq in el.items():
            if k == "_meta":
                continue
            pg = int(k)
            if pg == 1 or (slug, pg) in food:      # Cover/Food raus
                continue
            ft = full_text(seq)
            if len(ft) >= 12:
                grp[ft].append((slug, pg))

    # mehrfach (>=2), Top-N nach absoluter Häufigkeit, absteigend
    ranked = sorted(((len(v), ft, v[0]) for ft, v in grp.items()
                     if len(v) >= 2), key=lambda r: -r[0])[:a.n]
    print(f"Top {len(ranked)} mehrfach-vorkommende Info-Slides "
          f"(absolute Häufigkeit, absteigend):")
    for c, ft, (slug, pg) in ranked:
        print(f"  {c:4d}×  {slug[:20]:20}::{pg:<3} {ft[:50]}")
    if not ranked:
        sys.exit("Nichts mehrfach vorkommend.")

    smap = {slugify(p): os.path.join(CORPUS, p)
            for p in os.listdir(CORPUS) if p.lower().endswith(".pdf")}
    shared = tempfile.mkdtemp(prefix="top20_")
    cel, logos, meta = {}, {}, None
    for c, ft, (slug, pg) in ranked:
        if slug in cel:
            continue
        src = smap.get(slug)
        if not src:
            continue
        _, el, lg = cached_deck(src, shared)
        logos.update(lg)
        if meta is None:
            meta = el.get("_meta", {"w_pt": 960, "h_pt": 540})
        cel[slug] = el

    combined, notes, manifest, n = {}, {}, {}, 0
    for c, ft, (slug, pg) in ranked:               # bereits absteigend
        el = cel.get(slug)
        seq = el.get(str(pg)) if el else None
        if not seq:
            print(f"  warn fehlt {slug}::{pg}", file=sys.stderr)
            continue
        n += 1
        combined[str(n)] = seq
        notes[str(n)] = f"{slug}::{pg}"
        manifest[str(n)] = {"rank": n, "count": c, "type": ft[:90],
                            "deck": slug, "page": pg}

    mm = dict(meta or {"w_pt": 960, "h_pt": 540})
    mm["deck"], mm["notes"] = "info-top20", notes
    combined["_meta"] = mm
    json.dump(combined, open(os.path.join(shared, "elements.json"), "w"))
    json.dump(logos, open(os.path.join(shared, "logos.json"), "w"))
    out = os.path.join(DATA, "info_top20.pptx")
    json.dump(manifest, open(out + ".manifest.json", "w"),
              ensure_ascii=False, indent=1)
    subprocess.run(["node", os.path.join(SPIKE, "reconstruct.js"),
                    "elements.json", out], cwd=shared,
                   capture_output=True, check=True, timeout=600)
    print(f"\nOK → {out} — {n} Slides, absteigend nach Häufigkeit")


if __name__ == "__main__":
    main()
