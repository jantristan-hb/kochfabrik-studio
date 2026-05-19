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

try:
    import psycopg2
except Exception:                       # Container ohne DB-Treiber
    psycopg2 = None

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _deckpipe import cached_deck, slugify, CACHE              # noqa
from compose_offer import (embed, parse_offer_dishes, text_swap,  # noqa
                           slot_count, pick_frame, DSN, SPIKE,
                           CORPUS_DIR)

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
    derived = False
    if not courses and a.offer.lower().endswith(".pdf"):
        from kf_classify import derive_courses
        dc = derive_courses(a.offer)
        if dc:
            courses, derived = dc, True
    src_note = (" (aus Event-Kontext abgeleitet: "
                + ", ".join(h for h, _ in courses) + ")") if derived else ""
    print(f"Angebot: Kunde='{kunde}' Datum='{datum}' Ort='{ort[:40]}' | "
          f"{len(courses)} Gänge{src_note} → Titel '{title}'")

    # DB: echtes Postgres falls verfügbar, sonst vendored pg_shim
    # (DB-frei, originaltreue ANN aus numpy-Bundle). Studio-Container:
    # PPTX_PGSHIM=1 erzwingt Shim (kein Postgres-Connect-Timeout).
    if os.environ.get("PPTX_PGSHIM") == "1" or psycopg2 is None:
        import pg_shim
        cx = pg_shim.connect()
    else:
        try:
            cx = psycopg2.connect(**DSN)
        except Exception:
            import pg_shim
            cx = pg_shim.connect()
    cu = cx.cursor()

    # ---- Food: Kategorie HART locken (Gang-Headline → nächstes
    #      module_label), dann ANN NUR im Modul + Kapazitäts-Tiebreak.
    #      1 Embed-Batch (labels + headlines + headline+dishes). ----
    import numpy as np
    cu.execute("SELECT DISTINCT module_type, module_label FROM "
               "menu_composition WHERE module_label IS NOT NULL "
               "AND module_type IS NOT NULL")
    mods = cu.fetchall()
    labels = [m[1] for m in mods]
    heads = [c for c, _ in courses]
    conts = [f"{c} — {' '.join(n + ' ' + d for n, d in ds)}"
             for c, ds in courses]
    allv = embed(labels + heads + conts) if courses else []
    nL = len(labels)
    # Robust: kein Gang erkannt (z.B. kaufmännisches Angebots-PDF ohne
    # Speisen) → allv leer; asarray wäre 1-D → norm(axis=1) crasht.
    # Dann Food-Block leer lassen, Deck wird ohne Food gebaut.
    if nL and len(allv) >= nL:
        Ln = np.asarray(allv[:nL], float)
        Ln = Ln / (np.linalg.norm(Ln, axis=1, keepdims=True) + 1e-9)
    else:
        Ln = np.zeros((0, 768))
        if not courses:
            print("  ⚠ Keine Speisen/Gänge im Angebot erkannt — Deck "
                  "ohne Food-Slides (Cover + Frame + Ausstattung).")
    Hv = list(allv[nL:nL + len(heads)])
    Cv = list(allv[nL + len(heads):])
    picks = []                                # (pos, slug, page, dishes)
    fpos = (0.30, 0.72)
    for i, ((c, ds), hv, cv) in enumerate(zip(courses, Hv, Cv)):
        hvn = np.asarray(hv, float)
        hvn = hvn / (np.linalg.norm(hvn) + 1e-9)
        mi = int(np.argmax(Ln @ hvn)) if nL else -1
        mt, mlabel = mods[mi] if mi >= 0 else (None, "?")
        q = "[" + ",".join(f"{x:.6f}" for x in cv) + "]"
        if mt is not None:
            cu.execute("SELECT deck,page,src_pdf FROM menu_composition "
                       "WHERE module_type=%s ORDER BY "
                       "embedding<=>%s::vector LIMIT 8", (mt, q))
            cands = cu.fetchall()
        else:
            cands = []
        if not cands:                         # Fallback: global ANN
            cu.execute("SELECT deck,page,src_pdf FROM menu_composition "
                       "ORDER BY embedding<=>%s::vector LIMIT 8", (q,))
            cands = cu.fetchall()
        nd = len(ds)
        # kapazitäts-bewusst: kleinste Slot-Zahl >= #Gerichte (sonst
        # max Slots), bei Gleichstand ANN-Rang (Reihenfolge bleibt)
        best, bestkey = cands[0], None
        for rank, (dk, pgc, sc) in enumerate(cands):
            cp = os.path.join(CACHE, dk, "elements.json")
            try:
                seqc = json.load(open(cp)).get(str(int(pgc)))
                slots = slot_count(seqc) if seqc else 0
            except Exception:
                slots = 0
            fits = slots >= nd
            key = ((rank,) if nd == 0 else          # abgeleitet: bester ANN
                   (0 if fits else 1,
                    slots - nd if fits else -slots, rank))
            if bestkey is None or key < bestkey:
                bestkey, best = key, (dk, pgc, sc)
        deck, pg, src = best
        p = fpos[0] + (fpos[1] - fpos[0]) * (i / max(len(courses) - 1, 1))
        picks.append((p, deck, int(pg), src, c, ds))
        print(f"  Food «{c[:20]}» → {deck[:20]}::{pg} "
              f"[mod:{mlabel[:20]}] ({nd})")

    # ---- Frame: pflicht, je Kategorie kunden-stabil random aus dem
    #      freigegebenen Set (golden + Alternativen), verbatim ----
    cu.execute("SELECT deck,page,src_pdf,category,skel_pos FROM "
               "static_slide WHERE inclusion='pflicht' "
               "AND category<>'COVER'")
    by_cat = {}
    for deck, pg, src, cat, sp in cu.fetchall():
        by_cat.setdefault(cat, []).append((deck, int(pg), src, cat,
                                           float(sp)))
    frame = []
    for cat, opts in by_cat.items():
        opts.sort(key=lambda r: (r[0], r[1]))     # stabile Reihenfolge
        ch = pick_frame(cat, opts, kunde)
        frame.append(ch)
        print(f"  Frame «{cat[:22]}» → {ch[0][:24]}::{ch[1]} "
              f"(aus {len(opts)})")
    frame.sort(key=lambda r: r[4])                 # skel_pos
    cx.close()

    # ---- alle Quell-Decks EINMAL in shared cachen (kein Extrakt) ----
    shared = tempfile.mkdtemp(prefix="asm_")
    # CORPUS_DIR (Nextcloud) fehlt im Container → smap nur Fallback;
    # gemountete CACHE-Hits brauchen die Quell-PDFs nicht.
    smap = ({slugify(p): os.path.join(CORPUS_DIR, p)
             for p in os.listdir(CORPUS_DIR) if p.lower().endswith(".pdf")}
            if os.path.isdir(CORPUS_DIR) else {})
    el_cache, logos, meta = {}, {}, None

    def load(slug, src):
        if slug in el_cache:
            return
        # Cache ist nach dem deck-Slug benannt; slugify ist idempotent.
        # Direkt darüber auflösen → Nextcloud/src_pdf-unabhängig
        # (Container hat nur den gemounteten Cache). Fallback nur wenn
        # der Slug-Cache fehlt; unauflösbar → skip statt Crash.
        arg = (slug if os.path.isdir(os.path.join(CACHE, slug))
               else (src or smap.get(slug, "")))
        if not arg:
            return
        s2, el, lg = cached_deck(arg, shared)
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
            # abgeleiteter Gang (ds leer) → Korpus-Slide verbatim
            # (enthält bereits echte passende KOCHfabrik-Gerichte)
            items.append((p, text_swap([dict(e) for e in seq], ds)
                          if ds else seq))
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
