"""embed_images.py — Bild-Embeddings je Korpus-Slide → imgbundle.npz.

US-073 / FEATURE-013 §8 Nr. 2. Build-/Analyse-Tooling (engine/tooling/,
läuft NICHT zur Laufzeit). Pipeline je Slide MIT image-Elementen:

  1. Slide-Vorschau-PNG (cache/<deck>/preview/p<page>.png) — der gleiche
     Render, den die Slide-Suche serviert. Fehlt das Preview (noch nicht
     gerendert), Fallback auf das größte eingebettete Foto-Asset der
     Slide (elements.json `src`).
  2. Gemini-Vision (generateContent, inlineData-PNG + Text-Prompt, OHNE
     responseModalities-IMAGE → Text-Antwort; Muster aus
     engine_glue.image_kochfabrik) → kurze deutsche Beschreibung
     (Speisen / Szene / Stimmung).
  3. compose_offer.embed(Beschreibungen) — GLEICHES Gemini-Embedding-
     Modell wie pgbundle (gemini-embedding-001, 768D, SEMANTIC_SIMILARITY),
     sonst ist die Cosinus-Mischung in rank_mixed bedeutungslos (Pitfall 3).
  4. → imgbundle.npz {deck, page, imgemb (float32, L2-normiert), desc}.

Idempotent: vorhandene (deck,page)-Einträge werden geskippt (--force
erzwingt Neu-Embedding aller gesammelten Slides). --limit N begrenzt.

Usage:
  python3 embed_images.py                       # alle image-Slides
  python3 embed_images.py --decks A,B           # nur diese Decks
  python3 embed_images.py --limit 5 --force
"""
import argparse
import base64
import json
import os
import sys
import urllib.request

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Tooling lebt unter engine/tooling/ — Runtime-Module (engine/scripts/)
# zusätzlich auf den Pfad (compose_offer.embed = gleiches Embed-Modell
# wie pgbundle, _deckpipe.CACHE = Cache-Wurzel).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "scripts"))
from compose_offer import embed, _key, MODEL as _EMBED_MODEL    # noqa: E402,F401
from _deckpipe import CACHE                                      # noqa: E402

_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))), "data")
_OUT = os.path.join(_DATA, "imgbundle.npz")

# Vision-Modell: text-fähiges Gemini (KEIN Image-Output). Override via Env.
VISION_MODEL = os.environ.get("KF_VISION_MODEL", "gemini-2.5-flash")

_VISION_PROMPT = (
    "Beschreibe dieses Präsentations-Slide in EINEM kurzen deutschen "
    "Satz: welche Speisen/Gerichte sind zu sehen, welche Szene/Setting, "
    "welche Stimmung. Nur die Beschreibung, keine Einleitung."
)


def collect_image_slides(decks=None):
    """Alle (deck, page, png_src) mit image-Elementen aus den Cache-
    Decks. `decks` = optionale Whitelist von Deck-Slugs. png_src ist das
    Preview-PNG (falls vorhanden), sonst das größte Foto-Asset der Slide."""
    out = []
    if not os.path.isdir(CACHE):
        return out
    deck_dirs = sorted(d for d in os.listdir(CACHE)
                       if os.path.isdir(os.path.join(CACHE, d)))
    if decks:
        want = set(decks)
        deck_dirs = [d for d in deck_dirs if d in want]
    for deck in deck_dirs:
        el_path = os.path.join(CACHE, deck, "elements.json")
        if not os.path.isfile(el_path):
            continue
        try:
            el = json.load(open(el_path, encoding="utf-8"))
        except Exception:
            continue
        for pg, seq in el.items():
            if pg == "_meta" or not isinstance(seq, list):
                continue
            imgs = [x for x in seq if isinstance(x, dict)
                    and x.get("t") == "image" and x.get("src")]
            if not imgs:
                continue
            png = _vision_source(deck, int(pg), imgs)
            if png:
                out.append((deck, int(pg), png))
    return out


def preview_png(deck, page):
    """Pfad zum vorab gerenderten Slide-Preview (Slide-Suche-Render)."""
    return os.path.join(CACHE, deck, "preview", f"p{int(page)}.png")


def _vision_source(deck, page, imgs):
    """Preview-PNG bevorzugen (kompletter Slide-Render); sonst Fallback
    auf das größte eingebettete Foto-Asset (src relativ '<deck>/...')."""
    prev = preview_png(deck, page)
    if os.path.isfile(prev):
        return prev
    best, best_sz = None, -1
    for im in imgs:
        p = os.path.join(CACHE, im["src"])
        if os.path.isfile(p):
            sz = os.path.getsize(p)
            if sz > best_sz:
                best, best_sz = p, sz
    return best


def describe_image(png_path, key):
    """Gemini-Vision: PNG → kurze deutsche Beschreibung. Request-Muster
    wie engine_glue.image_kochfabrik (generateContent, inlineData + Text),
    aber OHNE responseModalities-IMAGE → Text-Antwort."""
    mime = "image/jpeg" if png_path.lower().endswith((".jpg", ".jpeg")) \
        else "image/png"
    data = base64.b64encode(open(png_path, "rb").read()).decode()
    body = {"contents": [{"parts": [
        {"inlineData": {"mimeType": mime, "data": data}},
        {"text": _VISION_PROMPT},
    ]}]}
    url = (f"https://generativelanguage.googleapis.com/v1beta/"
           f"models/{VISION_MODEL}:generateContent?key={key}")
    req = urllib.request.Request(url, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    res = json.loads(urllib.request.urlopen(req, timeout=120).read())
    for p in (res.get("candidates", [{}])[0].get("content", {})
              .get("parts", [])):
        if "text" in p:
            return p["text"].strip()
    return ""


def _load_existing(out_path):
    """(deck,page)→row-dict aus vorhandenem imgbundle (für Idempotenz)."""
    if not os.path.isfile(out_path):
        return {}
    z = np.load(out_path, allow_pickle=True)
    rows = {}
    for i in range(len(z["deck"])):
        rows[(str(z["deck"][i]), int(z["page"][i]))] = {
            "imgemb": z["imgemb"][i].astype(np.float32),
            "desc": str(z["desc"][i]),
        }
    return rows


def run(out_path=_OUT, decks=None, limit=None, force=False, key=None):
    """Sammelt image-Slides, beschreibt + embedet die neuen (oder alle bei
    --force) und schreibt imgbundle.npz. Gibt die Gesamtzahl der Einträge
    im geschriebenen Bundle zurück."""
    key = key or _key()
    slides = collect_image_slides(decks)
    existing = {} if force else _load_existing(out_path)

    todo = [(d, p, png) for (d, p, png) in slides
            if (d, p) not in existing]
    if limit is not None:
        todo = todo[:limit]

    new_rows = {}
    if todo:
        descs = []
        for deck, page, png in todo:
            desc = describe_image(png, key)
            descs.append(desc)
            print(f"  vision {deck}:{page} → {desc[:60]!r}", file=sys.stderr)
        emb = np.asarray(embed(descs), dtype=np.float32)
        emb = emb / (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-9)
        for (deck, page, _png), e, d in zip(todo, emb, descs):
            new_rows[(deck, page)] = {"imgemb": e, "desc": d}

    merged = dict(existing)
    merged.update(new_rows)
    if not merged:
        print("Keine image-Slides gefunden.", file=sys.stderr)
        return 0

    keys = sorted(merged.keys())
    np.savez(
        out_path,
        deck=np.array([k[0] for k in keys], dtype=object),
        page=np.array([k[1] for k in keys], dtype=np.int64),
        imgemb=np.stack([merged[k]["imgemb"] for k in keys]).astype(
            np.float32),
        desc=np.array([merged[k]["desc"] for k in keys], dtype=object),
    )
    print(f"imgbundle.npz: {len(merged)} Slides "
          f"(+{len(new_rows)} neu) → {out_path}", file=sys.stderr)
    return len(merged)


def main():
    ap = argparse.ArgumentParser(description="Bild-Embeddings → imgbundle.npz")
    ap.add_argument("--decks", help="Komma-Liste von Deck-Slugs (Default: alle)")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true",
                    help="alle gesammelten Slides neu embedden")
    ap.add_argument("-o", "--out", default=_OUT)
    a = ap.parse_args()
    decks = [d.strip() for d in a.decks.split(",")] if a.decks else None
    run(out_path=a.out, decks=decks, limit=a.limit, force=a.force)


if __name__ == "__main__":
    main()
