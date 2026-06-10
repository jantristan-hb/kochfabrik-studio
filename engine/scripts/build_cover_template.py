"""build_cover_template.py — EIN wiederverwendbares Cover-Template.

Basis = Bechtle-Cover (Seite 1, Konverter darauf perfektioniert).
Regel (Jans Vorschlag): Vollbild-Hintergrundbild (Deckung >= 70%)
ENTFERNEN — der Hero-Slot bleibt leer und wird später aus dem
Bildgenerator-Projekt befüllt. Titel-Text (größtes Element) wird zum
Platzhalter `{EVENT_TITEL}` → Assembler text-swappt die Angebot-
Kopfzeile (Kunde/Event/Datum) hinein, Styling/Position bleibt.

Artefakte:
- phase0/data/cover_template.elements.json  (1-Slide-Template für Assembler)
- phase0/data/cover_template.pptx            (Demo mit Beispiel-Titel)
- static_slide-Zeile category='COVER' (tier T, Pflicht, skel_pos 0.0)

Usage: python3 build_cover_template.py [--sample "KUNDE · DATUM"]
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
from _deckpipe import cached_deck                              # noqa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SPIKE = os.path.join(ROOT, "spike-pptxgenjs")
CORPUS = "/Users/janrudat/Nextcloud/Kochfabrik Dokumente/AKARA_Präsentationen"
BECHTLE_PDF = os.path.join(CORPUS, "12.09.2025_KF Bechtle.pdf")
DSN = dict(host="localhost", port=5434, user="postgres",
           password="pptxgen", dbname="pptxgen")
PLACEHOLDER = "{EVENT_TITEL}"
GOLD = "AA8339"                       # Rahmen
DARK = "1B0000"                       # KF-Brand-Basis + Titel-Band
BLUE = "0070C0"                       # blauer BG-Layer → raus


BG_COVER = 0.70                       # >= 70% Seite = Vollbild-Hero → raus
KF_LOGO = "kochfabrik_official"       # logos-Ziel-Marker des KF-Logos


def build(seq, meta, title_text, logos):
    """Cover-Template: NUR Hero-Vollbild + KOCHfabrik-Logo raus
    (Logo exakt via logos-Map erkannt; Badges haben keinen Key →
    bleiben). Blaues BG-RECT raus. Titel-Band bis zur Gold-Rahmen-
    Innenkante wachsen lassen. Titel = Platzhalter.
    """
    W = meta.get("w_pt", 960) / 72.0
    H = meta.get("h_pt", 540) / 72.0
    lg = logos or {}

    def is_kf_logo(e):
        # KF-Logo: logos-Ziel == kochfabrik_official.png.
        # Badges: Identitäts-Mapping (Ziel == Quelle) → bleiben.
        return KF_LOGO in os.path.basename(str(lg.get(e.get("src"), "")))

    def msz(e):
        return max((l["size"] for l in e["lines"]), default=0)

    # Gold-Rahmen-Innenkanten aus den vertikalen Gold-Rects
    vgold = [e for e in seq if e["t"] == "rect" and e.get("fill") == GOLD
             and e["h"] > e["w"]]
    if vgold:
        lf = min(vgold, key=lambda e: e["x"])
        rf = max(vgold, key=lambda e: e["x"])
        inx0, inx1 = lf["x"] + lf["w"], rf["x"]
    else:                                             # Fallback 0.2in
        inx0, inx1 = 0.2, W - 0.2

    txt_els = [e for e in seq if e["t"] == "text" and e.get("lines")]
    title_el = max(txt_els, key=msz) if txt_els else None

    out, title_done = [], False
    for e in seq:
        if e["t"] == "image":
            cov = (e["w"] * e["h"]) / (W * H)
            if cov >= BG_COVER or is_kf_logo(e):
                continue                  # Hero-Vollbild ODER KF-Logo raus
            # Badges (Identitäts-Mapping) bleiben
        if e["t"] == "rect" and e.get("fill") == BLUE:
            continue                                  # blauer BG-Layer raus
        if e["t"] == "rect" and e.get("fill") == DARK:
            if e["w"] >= 0.95 * W and e["h"] >= 0.95 * H:
                e = dict(e, fill="FFFFFF")    # Vollseiten-Basis → weiß
            else:
                # Titel-Band (dunkel, nicht Vollseite) → bis Gold stretchen
                e = dict(e, x=round(inx0, 4), w=round(inx1 - inx0, 4))
        if e is title_el and not title_done:
            st = e["lines"][0]
            e = dict(e, lines=[{k: st[k] for k in
                                ("size", "color", "weight", "italic")
                                if k in st} | {"txt": title_text}])
            title_done = True
        out.append(e)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", default="RISK.IDENT GMBH · 18. SEPTEMBER 2025")
    a = ap.parse_args()

    shared = tempfile.mkdtemp(prefix="cover_")
    slug, el, logos = cached_deck(BECHTLE_PDF, shared)
    meta = el.get("_meta", {"w_pt": 960, "h_pt": 540})
    seq1 = el["1"]

    # 1) Template (tokenisiert) für den Assembler
    tmpl = build(seq1, meta, PLACEHOLDER, logos)
    tmpl_doc = {"1": tmpl, "_meta": dict(meta, deck="cover-template")}
    json.dump(tmpl_doc, open(os.path.join(DATA,
              "cover_template.elements.json"), "w"), ensure_ascii=False)

    # 2) Demo-pptx mit Beispiel-Titel
    demo = build(seq1, meta, a.sample, logos)
    dd = {"1": demo, "_meta": dict(meta, deck="cover-template")}
    json.dump(dd, open(os.path.join(shared, "elements.json"), "w"))
    json.dump(logos, open(os.path.join(shared, "logos.json"), "w"))
    out = os.path.join(DATA, "cover_template.pptx")
    subprocess.run(["node", os.path.join(SPIKE, "reconstruct.js"),
                    "elements.json", out], cwd=shared,
                   capture_output=True, check=True, timeout=120)

    W = meta["w_pt"] / 72.0
    H = meta["h_pt"] / 72.0
    lg = logos or {}
    imgs = [e for e in seq1 if e["t"] == "image"]
    rm = [e for e in imgs if (e["w"]*e["h"])/(W*H) >= BG_COVER
          or KF_LOGO in os.path.basename(str(lg.get(e.get("src"), "")))]
    blue = sum(1 for e in seq1 if e["t"] == "rect"
               and e.get("fill") == BLUE)
    print(f"Cover-Template aus {slug}::1")
    print(f"  Bilder: {len(imgs)} gesamt → {len(rm)} raus "
          f"(Hero+KF-Logo), {len(imgs)-len(rm)} Badges bleiben | "
          f"{blue} blaues RECT raus | Band→Gold | "
          f"Elemente {len(tmpl)} (von {len(seq1)})")
    print(f"  Titel-Platzhalter: {PLACEHOLDER}")
    print(f"  → {DATA}/cover_template.elements.json (Assembler)")
    print(f"  → {out} (Demo: '{a.sample}')")

    # 3) In static_slide registrieren (category COVER)
    cx = psycopg2.connect(**DSN)
    cu = cx.cursor()
    cu.execute("DELETE FROM static_slide WHERE category='COVER'")
    execute_values(cu,
                   "INSERT INTO static_slide (category,rank,cnt,tier,"
                   "skel_pos,inclusion,deck,src_pdf,page,full_text,"
                   "is_golden) VALUES %s",
                   [("COVER", 0, 0, "T", 0.0, "pflicht", slug,
                     BECHTLE_PDF, 1, PLACEHOLDER, True)])
    cx.commit()
    cu.execute("SELECT category,tier,inclusion,skel_pos,is_golden "
               "FROM static_slide WHERE category='COVER'")
    print(f"  static_slide: {cu.fetchone()}")
    cx.close()


if __name__ == "__main__":
    main()
