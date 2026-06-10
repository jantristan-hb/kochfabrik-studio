"""compose_demo.py — Composer-KERN (Proof, hand-gefüttert).

Nimmt (PDF, Seite)-Paare, extrahiert je Deck via pdftohtml+extract.py,
und baut EIN kombiniertes elements.json (ausgewählte Kompositionen als
Slides 1..N) → reconstruct.js → ein editierbares Deck.

NICHT der fertige Composer: kein Prompt→model.json, kein Auto-Match,
kein Text-Swap — die Kompositionen behalten ihren Originaltext. Beweist
nur: Korpus → Kompositionen wählen → cross-deck assemblen → editierbar.

Usage: compose_demo.py <out.pptx> "<pdfA>::pageA" "<pdfB>::pageB" ...
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

SPIKE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "spike-pptxgenjs")
import re


def slug(p):
    return re.sub(r"[^a-z0-9]+", "-",
                  os.path.splitext(os.path.basename(p))[0].lower()
                  ).strip("-") or "deck"


def main():
    out = os.path.abspath(sys.argv[1])
    picks = [(s.rsplit("::", 1)[0], int(s.rsplit("::", 1)[1]))
             for s in sys.argv[2:]]
    work = tempfile.mkdtemp(prefix="compose_")
    combined = {}
    meta = None
    page_no = 0
    try:
        for pdf, pg in picks:
            sl = slug(pdf)
            shutil.copy(pdf, os.path.join(work, sl + ".pdf"))
            subprocess.run(["pdftohtml", "-xml", "-zoom", "1",
                            sl + ".pdf", sl + ".xml"],
                           cwd=work, capture_output=True, check=True)
            subprocess.run([sys.executable, os.path.join(SPIKE, "extract.py"),
                            sl + ".pdf", sl + ".json"],
                           cwd=work, capture_output=True, check=True)
            el = json.load(open(os.path.join(work, sl + ".json")))
            if meta is None:
                meta = el["_meta"]
            page_no += 1
            combined[str(page_no)] = el.get(str(pg), [])
            print(f"  + {sl} S{pg} → Slide {page_no} "
                  f"({len(combined[str(page_no)])} Elemente)", file=sys.stderr)
        meta = dict(meta or {"w_pt": 960, "h_pt": 540})
        meta["deck"] = "compose-demo"          # keine Deck-Overrides
        combined["_meta"] = meta
        json.dump(combined, open(os.path.join(work, "elements.json"), "w"))
        subprocess.run(["node", os.path.join(SPIKE, "reconstruct.js"),
                        "elements.json", out],
                       cwd=work, capture_output=True, check=True)
        print(f"OK: {out} ({page_no} Slides)")
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
