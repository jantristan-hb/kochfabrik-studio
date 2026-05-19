"""db_embed.py — menu_composition.embedding füllen (Step 4).

Embeddet "headline — body" je Zeile EXAKT wie compose_offer.cmd_match
die Korpus-Seite (gemini-embedding-001, SEMANTIC_SIMILARITY, dim 768),
damit Offer-Query-Vektoren vergleichbar sind. Cache in
phase0/data/menu_emb.npz → re-runnable ohne API.

Usage: python3 db_embed.py
"""
import os
import sys

import numpy as np
import psycopg2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compose_offer import embed                                # noqa

DATA = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "data")
NPZ = os.path.join(DATA, "menu_emb.npz")
DSN = dict(host="localhost", port=5434, user="postgres",
           password="pptxgen", dbname="pptxgen")


def main():
    cx = psycopg2.connect(**DSN)
    cu = cx.cursor()
    cu.execute("SELECT id, headline, body FROM menu_composition ORDER BY id")
    rows = cu.fetchall()
    ids = [r[0] for r in rows]
    texts = [f"{r[1]} — {r[2]}" for r in rows]
    print(f"{len(rows)} Zeilen zu embedden")

    if os.path.isfile(NPZ):
        d = np.load(NPZ)
        if list(d["ids"]) == ids:
            vecs = d["emb"]
            print("  Cache-Hit (npz)")
        else:
            vecs = None
    else:
        vecs = None
    if vecs is None:
        vecs = embed(texts)
        np.savez(NPZ, emb=vecs, ids=np.array(ids))
        print(f"  embedded → {NPZ}")

    payload = [("[" + ",".join(f"{x:.6f}" for x in v) + "]", i)
               for v, i in zip(vecs, ids)]
    cu.executemany(
        "UPDATE menu_composition SET embedding=%s::vector WHERE id=%s",
        payload)
    cx.commit()
    cu.execute("SELECT count(*) FROM menu_composition "
               "WHERE embedding IS NOT NULL")
    print(f"Persistiert: {cu.fetchone()[0]} / {len(rows)} embeddings")
    cx.close()


if __name__ == "__main__":
    main()
