"""US-021 — Korpus-Batch-Renderer.

Alle data/fiktiv/*.json → angebot_render → data/fiktiv_korpus/*.pdf.
Fehler pro Datei isoliert + Report. Kern-Deliverable: 20–30 fiktive
Original-Stil-PDFs.

Run: python3 build_korpus.py [--src ../data/fiktiv] [--out ../data/fiktiv_korpus]
"""
import argparse
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# US-056: Tooling lebt jetzt unter engine/tooling/ — Runtime-Module
# (engine/scripts/) zusätzlich auf den Pfad (KEINE Logikänderung).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "scripts"))
from angebot_model import load                                   # noqa
from angebot_render import render_pdf                             # noqa


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="../data/fiktiv")
    ap.add_argument("--out", default="../data/fiktiv_korpus")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    js = sorted(glob.glob(os.path.join(a.src, "*.json")))
    ok, fail = 0, []
    for j in js:
        name = os.path.splitext(os.path.basename(j))[0]
        try:
            render_pdf(load(j), os.path.join(a.out, name + ".pdf"))
            ok += 1
        except Exception as e:
            fail.append((name, str(e)[:90]))
    print(f"Korpus: {ok}/{len(js)} PDFs → {a.out}")
    for n, e in fail:
        print(f"  FAIL {n}: {e}")
    sys.exit(0 if ok >= max(1, int(len(js) * 0.8)) else 1)


if __name__ == "__main__":
    main()
