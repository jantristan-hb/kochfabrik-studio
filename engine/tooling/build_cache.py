"""build_cache.py — Cache einmalig vorwärmen (Step 1, Produktiv-Speed).

Iteriert alle distinkten src_pdf aus menu_composition und ruft
cached_deck → phase0/data/cache/<slug>/ wird gefüllt. Idempotent
(bereits gecachte Decks = instant Cache-Hit, kein Re-Extrakt).
Danach ist JEDES Angebot sofort heiß (Hot-Path ~0.3 s).

Usage: python3 build_cache.py
"""
import os
import sys
import tempfile
import time

import psycopg2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# US-056: Tooling lebt jetzt unter engine/tooling/ — Runtime-Module
# (engine/scripts/) zusätzlich auf den Pfad (KEINE Logikänderung).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "scripts"))
from _deckpipe import cached_deck                              # noqa

DSN = dict(host="localhost", port=5434, user="postgres",
           password="pptxgen", dbname="pptxgen")


def main():
    cx = psycopg2.connect(**DSN)
    cu = cx.cursor()
    cu.execute("SELECT DISTINCT src_pdf FROM menu_composition ORDER BY 1")
    pdfs = [r[0] for r in cu.fetchall()]
    cx.close()
    print(f"{len(pdfs)} Decks vorwärmen", flush=True)
    t0 = time.time()
    ok, fail = 0, []
    for i, src in enumerate(pdfs, 1):
        sh = tempfile.mkdtemp(prefix="warm_")
        try:
            cached_deck(src, sh)
            ok += 1
        except Exception as ex:
            fail.append((os.path.basename(src), str(ex).splitlines()[-1][:80]))
        finally:
            import shutil
            shutil.rmtree(sh, ignore_errors=True)
        if i % 10 == 0 or i == len(pdfs):
            print(f"  [{i}/{len(pdfs)}] ok={ok} fail={len(fail)} "
                  f"{time.time()-t0:.0f}s", flush=True)
    if fail:
        print("Fehlgeschlagen:", flush=True)
        for n, e in fail:
            print(f"  {n}: {e}", flush=True)
    print(f"Cache warm: {ok}/{len(pdfs)} Decks in {time.time()-t0:.0f}s",
          flush=True)


if __name__ == "__main__":
    main()
