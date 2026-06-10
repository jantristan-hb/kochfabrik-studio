"""embed_cluster.py — Slides semantisch clustern (Content-Tags).

Phasen (getrennt, damit Tuning ohne Re-Embed läuft):
  embed   : slides.json → Gemini-Embeddings (batch, gecacht als .npz)
  cluster : .npz → mean-zentrieren + L2 → AgglomerativeClustering(cosine)
            → Histogramm + tags.json (no,deck,page,headline,cluster)

Embedding-Geometrie liegt im engen Band → Zentrieren+Normalisieren
spreizt sie, average-linkage cosine findet die relative Struktur.
taskType SEMANTIC_SIMILARITY (empirisch beste Trennung).

Usage (aus spike-pptxgenjs/ oder scripts/):
  python3 embed_cluster.py embed   /tmp/all_menus.slides.json
  python3 embed_cluster.py cluster /tmp/all_menus.slides.json --th 0.12
"""
import argparse
import json
import os
import sys
import time
import urllib.request

import numpy as np

MODEL = "gemini-embedding-001"
DIM = 768
TASK = "SEMANTIC_SIMILARITY"
BATCH = 100


def _key():
    k = os.environ.get("GEMINI_API_KEY")
    if k:
        return k
    for ln in open(os.path.expanduser("~/work/.env")):
        if ln.startswith("GEMINI_API_KEY="):
            return ln.split("=", 1)[1].strip().strip('"')
    sys.exit("GEMINI_API_KEY fehlt")


def _post(url, payload):
    req = urllib.request.Request(
        url, json.dumps(payload).encode(),
        {"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())


def embed(slides_json, with_body=False):
    rows = json.load(open(slides_json))
    npz = slides_json + ".emb.npz"
    # Headline-only ist Default: identische Headline → identischer Vektor
    # → wiederkehrende Module clustern garantiert. Body fragmentiert
    # gleichen Modultyp (per-Event-Gerichte) → nur opt-in.
    if with_body:
        texts = [f"{r['headline']} — {r['body']}".strip(" —") for r in rows]
    else:
        texts = [r["headline"] or " " for r in rows]
    key = _key()
    url = (f"https://generativelanguage.googleapis.com/v1beta/"
           f"models/{MODEL}:batchEmbedContents?key={key}")
    vecs = []
    for i in range(0, len(texts), BATCH):
        chunk = texts[i:i + BATCH]
        body = {"requests": [
            {"model": f"models/{MODEL}",
             "content": {"parts": [{"text": t or " "}]},
             "taskType": TASK, "outputDimensionality": DIM}
            for t in chunk]}
        for attempt in range(4):
            try:
                res = _post(url, body)
                break
            except Exception as ex:
                if attempt == 3:
                    raise
                print(f"  retry {i} ({ex})", file=sys.stderr)
                time.sleep(2 * (attempt + 1))
        vecs.extend(e["values"] for e in res["embeddings"])
        print(f"  embedded {min(i + BATCH, len(texts))}/{len(texts)}",
              file=sys.stderr)
    arr = np.asarray(vecs, dtype=np.float32)
    np.savez(npz, emb=arr, no=[r["no"] for r in rows])
    print(f"{arr.shape[0]} Vektoren (dim {arr.shape[1]}) → {npz}")


def cluster(slides_json, th):
    from collections import Counter

    from sklearn.cluster import AgglomerativeClustering
    rows = json.load(open(slides_json))
    d = np.load(slides_json + ".emb.npz")
    X = d["emb"].astype(np.float64)
    X = X - X.mean(axis=0)                       # zentrieren
    X /= np.linalg.norm(X, axis=1, keepdims=True) + 1e-9   # L2
    lab = AgglomerativeClustering(
        n_clusters=None, distance_threshold=th,
        metric="cosine", linkage="average").fit_predict(X)
    for r, c in zip(rows, lab):
        r["cluster"] = int(c)
    out = slides_json.replace(".slides.json", ".tags.json")
    json.dump(rows, open(out, "w"), ensure_ascii=False, indent=0)

    sizes = Counter(lab)
    big = sizes.most_common()
    sing = sum(1 for _, c in sizes.items() if c == 1)
    print(f"th={th}  →  {len(sizes)} Cluster | "
          f"Singletons: {sing} | größter: {big[0][1]}")
    print("== Top 30 Cluster (Größe | häufigste Headline | 2 Beispiele) ==")
    by_c = {}
    for r in rows:
        by_c.setdefault(r["cluster"], []).append(r)
    for cid, n in big[:30]:
        mem = by_c[cid]
        hl = Counter(m["headline"] for m in mem).most_common(1)[0][0]
        ex = " / ".join(sorted({m["headline"] for m in mem})[:2])
        print(f"  c{cid:<4} {n:3d}  {hl[:34]:34}  [{ex[:50]}]")
    print(f"\ntags.json → {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["embed", "cluster"])
    ap.add_argument("slides_json", nargs="?",
                    default="/tmp/all_menus.slides.json")
    ap.add_argument("--th", type=float, default=0.12,
                    help="cosine distance_threshold (cluster)")
    ap.add_argument("--with-body", action="store_true",
                    help="Headline+Body embedden statt nur Headline")
    a = ap.parse_args()
    if a.phase == "embed":
        embed(a.slides_json, a.with_body)
    else:
        cluster(a.slides_json, a.th)


if __name__ == "__main__":
    main()
