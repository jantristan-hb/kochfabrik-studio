"""render_notext.py — Textfreie Slide-Vorschau-PNGs (US-069).

Identische Pipeline wie render_previews.py, mit EINEM Unterschied: vor dem
PPTX-Bau werden alle Korpus-Text-Elemente (t == "text") deterministisch aus
der Element-Sequenz gefiltert. Ergebnis ist ein Render des reinen Layouts
(Rects, Bilder, Logos) ohne jeglichen eingebrannten Korpus-Text.

Pro Slide aus menu_composition + static_slide:
  1. elements.json[<page>] aus cache/<deck>/ holen
  2. Text-Elemente filtern (strip_text)
  3. 1-Slide-PPTX via reconstruct.js bauen
  4. soffice --headless --convert-to png → PNG
  5. PIL resize/crop → 800×450
  6. Speichern unter cache/<deck>/preview_notext/p<page>.png

Idempotent: existierende PNGs werden geskippt. --force erzwingt Re-Render.
SOFFICE-Binary via Env SOFFICE (Default "soffice") — Mac hat kein soffice,
Render-Läufe laufen im kf-studio-sim-Container.

Usage:
  python3 render_notext.py                       # alle Slides (braucht DB)
  python3 render_notext.py --deck X --page Y      # nur eine
  python3 render_notext.py --deck X               # alle Seiten eines Decks
  python3 render_notext.py --force                # auch existierende
  python3 render_notext.py --limit N              # nur erste N
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

try:
    import psycopg2
except Exception:
    psycopg2 = None

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# US-056: Tooling lebt jetzt unter engine/tooling/ — Runtime-Module
# (engine/scripts/) zusätzlich auf den Pfad (KEINE Logikänderung).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "scripts"))
from compose_offer import DSN, SPIKE                              # noqa
from _deckpipe import CACHE                                       # noqa

PREVIEW_W = 800
PREVIEW_H = 450
SOFFICE = os.environ.get("SOFFICE", "soffice")


def strip_text(seq):
    """US-069-Filter: alle Korpus-Text-Elemente (t == "text") weglassen,
    Rest (rect/image/…) in unveränderter Reihenfolge behalten. Deterministisch,
    pure — keine Mutation der Eingabe."""
    return [e for e in seq if e.get("t") != "text"]


def render_single(deck, page, force=False):
    """Rendert 1 Slide textfrei → cache/<deck>/preview_notext/p<page>.png.
    Returns: 'ok' | 'skip' | 'no-elements' | 'render-fail'."""
    el_path = os.path.join(CACHE, deck, "elements.json")
    if not os.path.isfile(el_path):
        return "no-elements"
    el = json.load(open(el_path))
    seq = el.get(str(int(page)))
    if not seq:
        return "no-elements"

    preview_dir = os.path.join(CACHE, deck, "preview_notext")
    out_png = os.path.join(preview_dir, f"p{int(page)}.png")
    if not force and os.path.isfile(out_png):
        return "skip"
    os.makedirs(preview_dir, exist_ok=True)

    # US-069: Text-Elemente vor dem PPTX-Bau deterministisch entfernen.
    seq = strip_text(seq)

    # 1-Slide-elements.json bauen: meta + nur diese page als "1"
    meta = el.get("_meta", {"w_pt": 960, "h_pt": 540})
    single = {"1": seq, "_meta": dict(meta, deck=deck,
                                      notes={"1": f"{deck}:{page}"})}
    shared = tempfile.mkdtemp(prefix="notext_")
    # logos.json aus dem Cache mitnehmen (sonst fehlen Asset-Pfade)
    lg_src = os.path.join(CACHE, deck, "logos.json")
    if os.path.isfile(lg_src):
        shutil.copy(lg_src, os.path.join(shared, "logos.json"))
    # Asset-Dir symlinken: src-Pfade in elements.json sind relativ,
    # Form '<deck>/assets/<file>'. reconstruct.js läuft mit cwd=shared,
    # also brauchen wir 'shared/<deck>/assets' → cache/<deck>/assets.
    assets_src = os.path.join(CACHE, deck, "assets")
    if os.path.isdir(assets_src):
        os.makedirs(os.path.join(shared, deck), exist_ok=True)
        os.symlink(assets_src, os.path.join(shared, deck, "assets"))
    json.dump(single, open(os.path.join(shared, "elements.json"), "w"))

    pptx = os.path.join(shared, "slide.pptx")
    r = subprocess.run(["node", os.path.join(SPIKE, "reconstruct.js"),
                        "elements.json", pptx], cwd=shared,
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0 or not os.path.isfile(pptx):
        shutil.rmtree(shared, ignore_errors=True)
        return "render-fail"

    # soffice headless: PPTX → PNG (User-Profile-Dir explizit setzen,
    # sonst kollidieren parallele Läufe auf demselben ~/.config/libreoffice)
    user_profile = os.path.join(shared, "soffice-profile")
    r = subprocess.run(
        [SOFFICE, "--headless",
         f"-env:UserInstallation=file://{user_profile}",
         "--convert-to", "png", "--outdir", shared, pptx],
        capture_output=True, text=True, timeout=120)
    raw_png = os.path.join(shared, "slide.png")
    if r.returncode != 0 or not os.path.isfile(raw_png):
        shutil.rmtree(shared, ignore_errors=True)
        return "render-fail"

    # Resize auf 800×450 (Korpus-Decks sind 16:9 = 960:540)
    try:
        from PIL import Image
        im = Image.open(raw_png).convert("RGB")
        im.thumbnail((PREVIEW_W * 2, PREVIEW_H * 2), Image.LANCZOS)
        im = im.resize((PREVIEW_W, PREVIEW_H), Image.LANCZOS)
        im.save(out_png, "PNG", optimize=True)
    except ImportError:
        shutil.copy(raw_png, out_png)
    shutil.rmtree(shared, ignore_errors=True)
    return "ok"


def list_pages(deck):
    """Alle Seiten eines Decks aus dessen elements.json (DB-los)."""
    el_path = os.path.join(CACHE, deck, "elements.json")
    if not os.path.isfile(el_path):
        return []
    el = json.load(open(el_path))
    pages = sorted(int(k) for k in el.keys() if k != "_meta")
    return [(deck, p) for p in pages]


def list_slides(cx):
    """Alle (deck, page) aus menu_composition + static_slide."""
    cu = cx.cursor()
    cu.execute("SELECT deck, page FROM menu_composition")
    out = [(d, int(p)) for d, p in cu.fetchall()]
    cu.execute("SELECT deck, page FROM static_slide")
    out += [(d, int(p)) for d, p in cu.fetchall()]
    cu.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", help="nur dieser Deck-Slug")
    ap.add_argument("--page", type=int, help="nur diese Seite (mit --deck)")
    ap.add_argument("--force", action="store_true",
                    help="auch existierende PNGs neu rendern")
    ap.add_argument("--limit", type=int, help="nur erste N Slides")
    a = ap.parse_args()

    if a.deck and a.page is not None:
        slides = [(a.deck, a.page)]
    elif a.deck:
        # Deck-weit ohne DB: Seiten direkt aus elements.json ableiten.
        slides = list_pages(a.deck)
    else:
        if psycopg2 is None:
            sys.exit("psycopg2 fehlt — Batch-Mode braucht echte DB")
        cx = psycopg2.connect(**DSN)
        slides = list_slides(cx)
        cx.close()
    if a.limit:
        slides = slides[:a.limit]

    stats = {"ok": 0, "skip": 0, "no-elements": 0, "render-fail": 0}
    for i, (deck, page) in enumerate(slides, 1):
        r = render_single(deck, page, force=a.force)
        stats[r] += 1
        if r != "skip":
            print(f"  [{i}/{len(slides)}] {deck}::{page} → {r}")
    print(f"\nDONE: ok={stats['ok']} skip={stats['skip']} "
          f"no-elements={stats['no-elements']} "
          f"render-fail={stats['render-fail']}")


if __name__ == "__main__":
    main()
