"""build_category_samples.py — Top-Kategorien als Sampler.

Nimmt die häufigsten Info-Kategorien (Identität = exakter Volltext,
gruppiert über die Headline = größtes Text-Element als Kategorie-Label)
und legt je Kategorie 2–3 BEWUSST VARIIERENDE Instanzen ins Deck:
verschiedene Decks, verschiedene Volltext-Varianten und — wichtig für
Tier-B (PERSONAL/CREW) — verschiedene Foto-Sets (Bild-md5). So sieht
man je Kategorie die Spannweite und kann die goldene Instanz küren.

Reihenfolge: Kategorien nach Häufigkeit absteigend; je Kategorie die
häufigste (kanonische) Instanz zuerst, dann die variierenden.

Output: phase0/data/category_samples.pptx (+ .manifest.json).
Usage: python3 build_category_samples.py [--top 5] [--per 3]
"""
import argparse
import glob
import hashlib
import json
import os
import re
import subprocess
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
from analyze_structure import deck_elements, headline           # noqa
from dedup_exact import CACHE                                   # noqa

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


def img_sig(slug, seq):
    hs = []
    for e in seq:
        if e.get("t") != "image":
            continue
        p = os.path.join(CACHE, slug, e["src"].split("/", 1)[-1])
        try:
            hs.append(hashlib.md5(open(p, "rb").read()).hexdigest()[:8])
        except Exception:
            hs.append("NA")
    return tuple(sorted(hs))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--per", type=int, default=3)
    a = ap.parse_args()

    cx = psycopg2.connect(**DSN)
    cu = cx.cursor()
    cu.execute("SELECT deck, page FROM menu_composition")
    food = {(d, int(p)) for d, p in cu.fetchall()}
    cx.close()

    # cat (Headline) -> list of (slug,page,full_text,img_sig)
    cat = defaultdict(list)
    for pdf in sorted(glob.glob(os.path.join(CORPUS, "*.pdf"))):
        try:
            slug, el = deck_elements(pdf)
        except Exception:
            continue
        for k, seq in el.items():
            if k == "_meta":
                continue
            pg = int(k)
            if pg == 1 or (slug, pg) in food:
                continue
            ft = full_text(seq)
            if len(ft) < 12:
                continue
            h = headline(seq)
            if not h:
                continue
            cat[h].append((slug, pg, ft, img_sig(slug, seq)))

    # Kategorie-Häufigkeit = max exakt-Volltext-Count darin (robust
    # gegen Headline-Bucket-Inflation: nur echt wiederkehrender Inhalt)
    scored = []
    for h, inst in cat.items():
        tc = Counter(ft for _, _, ft, _ in inst)
        scored.append((tc.most_common(1)[0][1], h, inst, tc))
    scored.sort(key=lambda r: -r[0])
    top = scored[:a.top]
    print(f"Top {len(top)} Kategorien (max exakt-Volltext-Count):")

    chosen = []                       # (cat, rank_in_cat, slug, pg, cnt, why)
    for cnt, h, inst, tc in top:
        print(f"\n■ {h[:46]}  (kanonisch {cnt}×, {len(inst)} Instanzen)")
        # #1 = häufigster Volltext, erste Fundstelle
        dom = tc.most_common(1)[0][0]
        dom_inst = next(i for i in inst if i[2] == dom)
        picks = [(dom_inst, f"kanonisch {cnt}×")]
        seen_txt = {dom}
        seen_img = {dom_inst[3]}
        # variierende: anderer Volltext ODER anderes Foto-Set, anderes Deck
        for slug, pg, ft, ig in inst:
            if len(picks) >= a.per:
                break
            if (slug, pg) == (dom_inst[0], dom_inst[1]):
                continue
            new_txt = ft not in seen_txt
            new_img = ig not in seen_img
            if new_txt or new_img:
                why = ("Text-Variante" if new_txt else "anderes Foto-Set")
                picks.append(((slug, pg, ft, ig), f"{why} ({tc[ft]}×)"))
                seen_txt.add(ft)
                seen_img.add(ig)
        # Fallback: Varianten erschöpft → mit weiteren Instanzen aus
        # anderen Decks auffüllen, bis --per erreicht
        used = {(s, p) for (s, p, _, _), _ in picks}
        used_decks = {s for (s, p, _, _), _ in picks}
        for slug, pg, ft, ig in inst:
            if len(picks) >= a.per:
                break
            if (slug, pg) in used or slug in used_decks:
                continue
            picks.append(((slug, pg, ft, ig), f"weiteres Deck ({tc[ft]}×)"))
            used.add((slug, pg))
            used_decks.add(slug)
        for slug, pg, ft, ig in inst:           # letzter Fallback: irgendein
            if len(picks) >= a.per:
                break
            if (slug, pg) in used:
                continue
            picks.append(((slug, pg, ft, ig), f"weitere Instanz ({tc[ft]}×)"))
            used.add((slug, pg))
        for (slug, pg, ft, ig), why in picks:
            chosen.append((h, slug, pg, tc[ft], why))
            print(f"   {slug[:22]:22}::{pg:<3} {why:22} {ft[:38]}")

    smap = {slugify(p): os.path.join(CORPUS, p)
            for p in os.listdir(CORPUS) if p.lower().endswith(".pdf")}
    shared = tempfile.mkdtemp(prefix="catsamp_")
    cel, logos, meta = {}, {}, None
    for h, slug, pg, c, why in chosen:
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
    for h, slug, pg, c, why in chosen:
        el = cel.get(slug)
        seq = el.get(str(pg)) if el else None
        if not seq:
            print(f"  warn fehlt {slug}::{pg}", file=sys.stderr)
            continue
        n += 1
        combined[str(n)] = seq
        notes[str(n)] = f"{slug}::{pg}"
        manifest[str(n)] = {"category": h[:70], "count": c,
                            "variant": why, "deck": slug, "page": pg}

    mm = dict(meta or {"w_pt": 960, "h_pt": 540})
    mm["deck"], mm["notes"] = "category-samples", notes
    combined["_meta"] = mm
    json.dump(combined, open(os.path.join(shared, "elements.json"), "w"))
    json.dump(logos, open(os.path.join(shared, "logos.json"), "w"))
    out = os.path.join(DATA, "category_samples.pptx")
    json.dump(manifest, open(out + ".manifest.json", "w"),
              ensure_ascii=False, indent=1)
    subprocess.run(["node", os.path.join(SPIKE, "reconstruct.js"),
                    "elements.json", out], cwd=shared,
                   capture_output=True, check=True, timeout=600)
    print(f"\nOK → {out} — {n} Slides ({len(top)} Kategorien × bis "
          f"{a.per}, nach Häufigkeit gruppiert)")


if __name__ == "__main__":
    main()
