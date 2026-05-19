"""assemble.py — hocheffizienter End-to-End-Assembler.

Angebot (PDF/md) → vollständiges editierbares KOCHfabrik-Deck:
  1. Header parsen → Kunde + Datum  (→ Cover-Titel)
  2. Cover: cover_template.elements.json, {EVENT_TITEL} text-swappen
  3. Food: 1 Gemini-Batch-Embed ALLER Gänge → pro Gang pgvector-ANN
     gegen menu_composition → beste Komposition → Text-Swap Gerichte
  4. Frame: static_slide WHERE is_golden AND inclusion='pflicht'
     (Crew/Personal/Wertschätzung/Kontakt) verbatim aus Cache
  5. Reihenfolge nach skel_pos (Cover 0 → Crew .10 → Food → Personal
     .76 → Wertschätzung .89 → Kontakt 1.0) → 1× reconstruct.js

Effizienz: 1 Embed-Batch, 1 DB-Connection (K kleine ANN + 1 Frame-
Query), nur Cache-Reads (KEINE PDF-Extraktion zur Laufzeit), 1
reconstruct. Typisch wenige Sekunden (Netzwerk-dominiert: 1 Embed).

Usage:
  python3 assemble.py "<angebot.pdf>" [-o out.pptx]
  python3 assemble.py ../fixtures/fiktive_angebote.md --offer Nordlicht
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time

import psycopg2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _deckpipe import cached_deck, slugify                     # noqa
from compose_offer import (embed, parse_offer_dishes, text_swap,  # noqa
                           DSN, SPIKE, CORPUS_DIR)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
COVER_TMPL = os.path.join(DATA, "cover_template.elements.json")
AUSST_TMPL = os.path.join(DATA, "ausstattung_template.elements.json")
PLACEHOLDER = "{EVENT_TITEL}"
PH_AUSST = "{LOCATION_AUSSTATTUNG}"
BECHTLE_SLUG = "12-09-2025-kf-bechtle"
AUSST_SLUG = "er-ffnung-stetson-store"


def parse_header(path, offer=""):
    """Kunde + Datum aus dem Angebot (PDF: pdftotext; md: Fixture)."""
    if path.lower().endswith((".md", ".txt")):
        lines = open(path, encoding="utf-8").read().splitlines()
        take, kunde, datum = False, "", ""
        for ln in lines:
            if ln.startswith("## "):
                if take:
                    break
                take = (offer or "").lower() in ln.lower()
                if take:
                    m = re.search(r"—\s*(.+?)\s*\(", ln)
                    kunde = m.group(1).strip() if m else ln[3:].strip()
            elif take and "Veranstaltungsdatum" in ln:
                datum = ln.split("|")[2].strip() if "|" in ln else ""
        return kunde, datum
    txt = subprocess.run(["pdftotext", "-layout", path, "-"],
                          capture_output=True, text=True).stdout
    datum = ""
    m = re.search(r"Veranstaltungsdatum:\s*(.+)", txt)
    if m:
        datum = m.group(1).strip()
    kunde = ""
    for ln in txt.splitlines()[:25]:
        s = re.split(r"\s{2,}", ln.strip())[0].strip()
        low = s.lower()
        if re.search(r"\b(GmbH|AG|KG|SE|GbR|e\.V\.|mbH)\b", s) \
                and not any(x in low for x in ("kochfabrik", "koch-fabrik",
                            "prisdorf", "peiner hag")) \
                and 3 < len(s) < 60:
            kunde = s
            break
    return kunde, datum


def parse_location(path, offer=""):
    """Veranstaltungsort (→ LOCATION/AUSSTATTUNG-Platzhalter)."""
    if path.lower().endswith((".md", ".txt")):
        lines = open(path, encoding="utf-8").read().splitlines()
        take = False
        for ln in lines:
            if ln.startswith("## "):
                if take:
                    break
                take = (offer or "").lower() in ln.lower()
            elif take and "Veranstaltungsort" in ln and "|" in ln:
                return ln.split("|")[2].strip()
        return ""
    txt = subprocess.run(["pdftotext", "-layout", path, "-"],
                          capture_output=True, text=True).stdout
    m = re.search(r"Veranstaltungsort:\s*(.+)", txt)
    return re.split(r"\s{2,}", m.group(1).strip())[0].strip() if m else ""


def swap_ph(seq, token, value):
    """Element dessen Text das Token enthält → value (Stil bleibt)."""
    out, done = [], False
    for e in seq:
        if (not done and e.get("t") == "text"
                and any(token in l.get("txt", "")
                        for l in e.get("lines", []))):
            st = e["lines"][0]
            e = dict(e, lines=[{k: st[k] for k in
                                ("size", "color", "weight", "italic")
                                if k in st} | {"txt": value}])
            done = True
        out.append(e)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("offer")
    ap.add_argument("--offer", dest="sec", default="")
    ap.add_argument("-o", default=os.path.join(DATA, "assembled.pptx"))
    a = ap.parse_args()
    a.o = os.path.abspath(a.o)            # reconstruct läuft mit cwd=shared
    t0 = time.time()

    kunde, datum = parse_header(a.offer, a.sec)
    ort = parse_location(a.offer, a.sec)
    title = re.sub(r"\s+", " ", f"{kunde} {datum}").strip().upper()
    courses = parse_offer_dishes(a.offer, a.sec)         # [(name,[dishes])]
    print(f"Angebot: Kunde='{kunde}' Datum='{datum}' Ort='{ort[:40]}' | "
          f"{len(courses)} Gänge → Titel '{title}'")

    cx = psycopg2.connect(**DSN)
    cu = cx.cursor()

    # ---- Food: 1 Embed-Batch, pro Gang 1 ANN ----
    qtext = [f"{c} — {' '.join(n + ' ' + d for n, d in ds)}"
             for c, ds in courses]
    qv = embed(qtext) if qtext else []
    picks = []                                # (pos, slug, page, dishes)
    fpos = (0.30, 0.72)
    for i, ((c, ds), v) in enumerate(zip(courses, qv)):
        q = "[" + ",".join(f"{x:.6f}" for x in v) + "]"
        cu.execute("SELECT deck,page,src_pdf FROM menu_composition "
                   "ORDER BY embedding<=>%s::vector LIMIT 1", (q,))
        deck, pg, src = cu.fetchone()
        p = fpos[0] + (fpos[1] - fpos[0]) * (i / max(len(courses) - 1, 1))
        picks.append((p, deck, int(pg), src, c, ds))
        print(f"  Food «{c[:24]}» → {deck[:24]}::{pg}")

    # ---- Frame: golden, pflicht, verbatim ----
    cu.execute("SELECT deck,page,src_pdf,category,skel_pos FROM "
               "static_slide WHERE is_golden AND inclusion='pflicht' "
               "AND category<>'COVER' ORDER BY skel_pos")
    frame = cu.fetchall()
    cx.close()

    # ---- alle Quell-Decks EINMAL in shared cachen (kein Extrakt) ----
    shared = tempfile.mkdtemp(prefix="asm_")
    smap = {slugify(p): os.path.join(CORPUS_DIR, p)
            for p in os.listdir(CORPUS_DIR) if p.lower().endswith(".pdf")}
    el_cache, logos, meta = {}, {}, None

    def load(slug, src):
        if slug in el_cache:
            return
        s2, el, lg = cached_deck(src or smap.get(slug, ""), shared)
        logos.update(lg)
        el_cache[s2] = el

    cov = json.load(open(COVER_TMPL))
    aus = json.load(open(AUSST_TMPL)) if os.path.isfile(AUSST_TMPL) else None
    meta = cov.get("_meta", {"w_pt": 960, "h_pt": 540})
    # Template-Badges referenzieren ihre Basis-Deck-Assets → cachen
    load(BECHTLE_SLUG, smap.get(BECHTLE_SLUG))           # Cover
    if aus:
        load(AUSST_SLUG, smap.get(AUSST_SLUG))           # Ausstattung
    for _, deck, pg, src, _, _ in picks:
        load(deck, src)
    for deck, pg, src, _, _ in frame:
        load(deck, src)

    # ---- Slides in skel_pos-Reihenfolge bauen ----
    items = []                                # (pos, seq)
    items.append((0.0, swap_ph(cov["1"], PLACEHOLDER, title)))
    if aus:                                   # AUSSTATTUNG (bedingt, 0.78)
        loc = ort or "Location & Ausstattung"
        items.append((0.78, swap_ph(aus["1"], PH_AUSST, loc)))
    for p, deck, pg, src, c, ds in picks:
        seq = el_cache.get(deck, {}).get(str(pg))
        if seq:
            items.append((p, text_swap([dict(e) for e in seq], ds)))
    for deck, pg, src, cat, sp in frame:
        seq = el_cache.get(deck, {}).get(str(pg))
        if seq:
            items.append((float(sp), seq))
    items.sort(key=lambda t: t[0])

    combined, notes = {}, {}
    for i, (_, seq) in enumerate(items, 1):
        combined[str(i)] = seq
        notes[str(i)] = f"slide{i}"
    mm = dict(meta)
    mm["deck"], mm["notes"] = "assembled", notes
    combined["_meta"] = mm
    json.dump(combined, open(os.path.join(shared, "elements.json"), "w"))
    json.dump(logos, open(os.path.join(shared, "logos.json"), "w"))
    r = subprocess.run(["node", os.path.join(SPIKE, "reconstruct.js"),
                        "elements.json", a.o], cwd=shared,
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        print("reconstruct.js FEHLER:\n" + (r.stderr or r.stdout)[-1500:])
        print(f"(shared={shared})")
        sys.exit(1)
    print(f"\nOK → {a.o} — {len(items)} Slides "
          f"(1 Cover + {len(picks)} Food + {len(frame)} Frame + "
          f"{1 if aus else 0} Ausstattung) in {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
