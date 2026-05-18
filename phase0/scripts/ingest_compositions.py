"""ingest_compositions.py — Schritt 1: Kompositions-Tabelle aus den PDFs.

Pro Deck: pdftohtml -xml + extract.py (vorhandene Engine-Bausteine) →
elements.json. Pro Seite mit Content-Fotos → eine `composition`-Zeile
(das kuratierte Foto-SET) + `image`-Zeilen. Gericht-Text der Seite als
`dishes`. Stichprobe zuerst (--n), dann skalieren.

Usage (aus phase0/spike-pptxgenjs/):
  python3 ../scripts/ingest_compositions.py --n 20
  python3 ../scripts/ingest_compositions.py --all
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import psycopg2

CORPUS = "/home/jrudat/Nextcloud/Kochfabrik Dokumente/AKARA_Präsentationen"
SPIKE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "spike-pptxgenjs")
DSN = dict(host="localhost", port=5434, user="postgres",
           password="pptxgen", dbname="pptxgen")


def is_content_photo(im, W, H):
    """Food-Foto-Set-Member: groß genug, nicht Furniture, nicht Voll-BG."""
    w, h = im["w"], im["h"]
    if min(w, h) < 1.2 or w * h < 3.0:
        return False
    if w >= 0.95 * W and h >= 0.95 * H:        # Voll-BG
        return False
    return True


def slugify(pdf):
    return re.sub(r"[^a-z0-9]+", "-",
                  os.path.splitext(os.path.basename(pdf))[0].lower()
                  ).strip("-") or "deck"


def elements_for(pdf, work):
    # eindeutiger Deck-Slug als Dateiname → extract.py leitet korrekten
    # _meta.deck ab (sonst hieße jedes Deck "ref" → Key-Kollision)
    slug = slugify(pdf)
    base = os.path.join(work, slug)
    shutil.copy(pdf, base + ".pdf")
    subprocess.run(["pdftohtml", "-xml", "-zoom", "1",
                    slug + ".pdf", slug + ".xml"],
                   cwd=work, capture_output=True, check=True, timeout=120)
    subprocess.run([sys.executable, os.path.join(SPIKE, "extract.py"),
                    slug + ".pdf", "elements.json"],
                   cwd=work, capture_output=True, check=True, timeout=180)
    return json.load(open(os.path.join(work, "elements.json")))


def sample(n, take_all):
    pdfs = [p for p in sorted(glob.glob(os.path.join(CORPUS, "*.pdf")))
            if not os.path.basename(p).startswith("Angebot #")]
    if take_all:
        return pdfs
    step = max(1, len(pdfs) // n)
    return pdfs[::step][:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    decks = sample(a.n, a.all)

    conn = psycopg2.connect(**DSN)
    conn.autocommit = False
    cur = conn.cursor()
    ncomp = nimg = nfail = 0

    for i, pdf in enumerate(decks, 1):
        name = os.path.splitext(os.path.basename(pdf))[0]
        print(f"[{i}/{len(decks)}] {name[:48]}", file=sys.stderr)
        work = tempfile.mkdtemp(prefix="ingest_")
        try:
            el = elements_for(pdf, work)
            meta = el.get("_meta", {"deck": name, "w_pt": 960, "h_pt": 540})
            deck = meta.get("deck") or name
            W, H = meta["w_pt"] / 72.0, meta["h_pt"] / 72.0
            # re-ingestion idempotent: Deck vorher leeren
            cur.execute("DELETE FROM composition WHERE deck=%s", (deck,))
            for pg, seq in el.items():
                if pg == "_meta":
                    continue
                photos = [e for e in seq
                          if e["t"] == "image" and is_content_photo(e, W, H)]
                if not photos:
                    continue
                dishes = []
                for e in seq:
                    if e["t"] == "text":
                        for ln in e["lines"]:
                            t = ln["txt"].strip()
                            if t and t not in dishes:
                                dishes.append(t)
                cur.execute(
                    "INSERT INTO composition(deck,page,n_photos,dishes) "
                    "VALUES(%s,%s,%s,%s) RETURNING id",
                    (deck, int(pg), len(photos), dishes[:60]))
                cid = cur.fetchone()[0]
                ncomp += 1
                for ph in photos:
                    cur.execute(
                        "INSERT INTO image(comp_id,file,x,y,w,h) "
                        "VALUES(%s,%s,%s,%s,%s,%s)",
                        (cid, os.path.basename(ph["src"]),
                         ph["x"], ph["y"], ph["w"], ph["h"]))
                    nimg += 1
            conn.commit()
        except Exception as ex:
            conn.rollback()
            nfail += 1
            print(f"  FEHLER {name}: {str(ex).splitlines()[-1][:140]}",
                  file=sys.stderr)
        finally:
            shutil.rmtree(work, ignore_errors=True)

    cur.close()
    conn.close()
    print(f"\n=== Ingest: {len(decks)-nfail}/{len(decks)} Decks OK | "
          f"{ncomp} Kompositionen, {nimg} Bilder | {nfail} Fehler ===")


if __name__ == "__main__":
    main()
