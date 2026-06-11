"""analyze_structure.py — typischer Präsentations-Aufbau (Hauptstruktur).

Liest den Element-Cache (phase0/data/cache/<slug>/elements.json — alle
Seiten je Deck) READ-ONLY. Headline = größtes Text-Element je Seite
(= Kategorie). Liefert:
  - Deck-Länge-Verteilung (Slides/Deck: min/Median/Schnitt/max + Histogr.)
  - Headline-Häufigkeit global (welche Kategorie wie oft)
  - Positions-Profil je Headline (rel. Position 0=Anfang .. 1=Ende)
    → kanonisches Skelett (Reihenfolge der Slide-Typen)
  - Food/Non-Food-Mix je Deck (via menu_composition) → Umfangs-Modell
Output: docs/REPORT-structure.md + Konsolen-Summary.

Voraussetzung: Cache vorgewärmt. Usage: python3 analyze_structure.py
"""
import glob
import json
import os
import re
import statistics as st
import sys
import tempfile
from collections import Counter, defaultdict

import psycopg2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# US-056: Tooling lebt jetzt unter engine/tooling/ — Runtime-Module
# (engine/scripts/) zusätzlich auf den Pfad (KEINE Logikänderung).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "scripts"))
from _deckpipe import cached_deck, slugify                     # noqa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "cache")
REPORT = os.path.join(ROOT, "..", "docs", "REPORT-structure.md")
CORPUS = "/Users/janrudat/Nextcloud/Kochfabrik Dokumente/AKARA_Präsentationen"
DSN = dict(host="localhost", port=5434, user="postgres",
           password="pptxgen", dbname="pptxgen")


def deck_elements(pdf):
    """el je Deck: Cache-Hit → direkt elements.json laden (kein Asset-
    Copy); Miss → cached_deck extrahiert+persistiert. Über ALLE Korpus-
    PDFs (Jan: alle ~200), inkl. der ~34 ohne Food."""
    slug = slugify(pdf)
    cp = os.path.join(CACHE, slug, "elements.json")
    if os.path.isfile(cp):
        return slug, json.load(open(cp))
    sh = tempfile.mkdtemp(prefix="ana_")
    try:
        slug, el, _ = cached_deck(pdf, sh)
        return slug, el
    finally:
        import shutil
        shutil.rmtree(sh, ignore_errors=True)


def headline(seq):
    best, bs = "", -1.0
    for e in seq:
        if e.get("t") != "text" or not e.get("lines"):
            continue
        mx = max(l["size"] for l in e["lines"])
        if mx > bs:
            bs = mx
            best = " ".join(l["txt"] for l in e["lines"]).strip()
    return re.sub(r"\s+", " ", best).strip().upper()


def main():
    cx = psycopg2.connect(**DSN)
    cu = cx.cursor()
    cu.execute("SELECT deck, page FROM menu_composition")
    food = {(d, int(p)) for d, p in cu.fetchall()}
    cx.close()

    pdfs = sorted(glob.glob(os.path.join(CORPUS, "*.pdf")))
    lens, hcount = [], Counter()
    pos = defaultdict(list)                 # headline -> [rel_pos]
    first_h, last_h = Counter(), Counter()
    food_per, info_per = [], []
    ndeck, fails = 0, []
    for i, pdf in enumerate(pdfs, 1):
        try:
            slug, el = deck_elements(pdf)
        except Exception as ex:
            fails.append(os.path.basename(pdf))
            print(f"  skip {os.path.basename(pdf)[:40]}: "
                  f"{str(ex).splitlines()[-1][:70]}", file=sys.stderr)
            continue
        ndeck += 1
        if i % 25 == 0 or i == len(pdfs):
            print(f"  [{i}/{len(pdfs)}] ok={ndeck}", file=sys.stderr)
        pages = sorted((int(k) for k in el if k != "_meta"))
        if not pages:
            continue
        n = len(pages)
        lens.append(n)
        fc = ic = 0
        for idx, pg in enumerate(pages):
            h = headline(el[str(pg)]) or "<leer>"
            hcount[h] += 1
            pos[h].append(idx / max(n - 1, 1))
            if idx == 0:
                first_h[h] += 1
            if idx == n - 1:
                last_h[h] += 1
            if (slug, pg) in food:
                fc += 1
            else:
                ic += 1
        food_per.append(fc)
        info_per.append(ic)

    def dist(v):
        v = sorted(v)
        return (min(v), st.median(v), round(st.mean(v), 1), max(v))

    lo, md, av, hi = dist(lens)
    out = []
    out.append("# Präsentations-Hauptstruktur — Analyse\n")
    out.append(f"_{ndeck} von {len(pdfs)} Korpus-PDFs analysiert"
               + (f" ({len(fails)} übersprungen)" if fails else "") + "._\n")
    out.append("## Deck-Länge (Slides/Deck)\n")
    out.append(f"min {lo} · Median {md} · Schnitt {av} · max {hi}\n")
    hb = Counter(min(x // 5 * 5, 40) for x in lens)
    out.append("Histogramm (5er-Buckets):")
    for b in sorted(hb):
        out.append(f"  {b:>2}-{b+4}: {'#'*hb[b]} ({hb[b]})")
    out.append(f"\nFood-Slides/Deck: {dist(food_per)} · "
               f"Non-Food/Deck: {dist(info_per)}")
    fr = sum(food_per) / max(sum(food_per) + sum(info_per), 1)
    out.append(f"Food-Anteil gesamt: {fr*100:.0f}% "
               f"→ Umfangs-Faustregel: ~{md} Slides, "
               f"davon ~{round(md*fr)} Food / ~{round(md*(1-fr))} Rahmen.\n")

    out.append("## Häufigste Headlines/Kategorien (Top 30)\n")
    out.append("| Headline | Vorkommen | Decks-Anteil | Ø Position |")
    out.append("|---|---|---|---|")
    for h, c in hcount.most_common(30):
        rp = st.mean(pos[h])
        loc = ("Anfang" if rp < .25 else "früh" if rp < .45
               else "Mitte" if rp < .65 else "spät" if rp < .85 else "Ende")
        out.append(f"| {h[:40]} | {c} | {c*100//max(ndeck,1)}% "
                   f"| {rp:.2f} ({loc}) |")

    out.append("\n## Kanonisches Skelett (nach Ø-Position)\n")
    skel = sorted(((st.mean(pos[h]), h, len(pos[h]))
                   for h, c in hcount.items() if c >= max(3, ndeck // 20)),
                  key=lambda x: x[0])
    for rp, h, c in skel:
        out.append(f"  {rp:.2f}  {h[:46]:46} ({c}×)")
    out.append("\n## Typischer Opener (Seite 1)\n")
    for h, c in first_h.most_common(6):
        out.append(f"  {c:4d}  {h[:50]}")
    out.append("\n## Typischer Closer (letzte Seite)\n")
    for h, c in last_h.most_common(6):
        out.append(f"  {c:4d}  {h[:50]}")

    txt = "\n".join(out) + "\n"
    open(REPORT, "w").write(txt)
    print(txt)
    print(f"→ {REPORT}")


if __name__ == "__main__":
    main()
