"""convert.py — Ein-Lauf-Orchestrator: PDF -> editierbares PPTX.

Kapselt die bisher manuell per bash gefahrenen Schritte in einen
deterministischen Lauf. Die verifizierten Spike-Bausteine bleiben
unverändert — convert.py richtet nur die Arbeitsumgebung ein und ruft
sie in der richtigen Reihenfolge.

Pipeline:
  pdftohtml -xml  ->  extract_logos.py  ->  apply_official_logo.py
  ->  extract.py  ->  reconstruct.js

Usage: convert.py <input.pdf> [output.pptx] [--keep]
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

SPIKE = os.path.dirname(os.path.abspath(__file__))


def run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(
            f"FEHLER ({' '.join(cmd[:2])}, rc={r.returncode}): "
            f"{(r.stderr or r.stdout).strip()[-300:]}")
    return r.stdout.strip()


def convert(pdf, out_pptx, keep=False):
    pdf = os.path.abspath(pdf)
    out_pptx = os.path.abspath(out_pptx)
    if not os.path.isfile(pdf):
        raise FileNotFoundError(pdf)

    work = tempfile.mkdtemp(prefix="pptxgen_")
    assets = os.path.join(work, "assets")
    os.makedirs(assets)
    try:
        # Eingabe-PDF als erwarteter Name; feste Assets (offizielles Logo)
        shutil.copy(pdf, os.path.join(assets, "ref.pdf"))
        src_logo = os.path.join(SPIKE, "assets", "logo_src")
        if os.path.isdir(src_logo):
            shutil.copytree(src_logo, os.path.join(assets, "logo_src"))
        # Deck-Overrides (Hand-Kalibrierung) durchreichen falls vorhanden
        ov = os.path.join(SPIKE, "overrides.json")
        if os.path.isfile(ov):
            shutil.copy(ov, os.path.join(work, "overrides.json"))

        run(["pdftohtml", "-xml", "-zoom", "1",
             "assets/ref.pdf", "assets/ref.xml"], work)
        run([sys.executable, os.path.join(SPIKE, "extract_logos.py")], work)
        run([sys.executable, os.path.join(SPIKE, "apply_official_logo.py")],
            work)
        run([sys.executable, os.path.join(SPIKE, "extract.py"),
             "assets/ref.pdf", "elements.json"], work)
        run(["node", os.path.join(SPIKE, "reconstruct.js"),
             "elements.json", out_pptx], work)
        return out_pptx
    finally:
        if keep:
            print(f"[keep] Work-Dir: {work}", file=sys.stderr)
        else:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", help="Input-PDF")
    ap.add_argument("out", nargs="?", default=None,
                    help="Output-PPTX (default: <pdf>.pptx)")
    ap.add_argument("--keep", action="store_true",
                    help="Work-Dir nicht löschen")
    a = ap.parse_args()
    out = a.out or (os.path.splitext(a.pdf)[0] + ".pptx")
    result = convert(a.pdf, out, keep=a.keep)
    print(f"OK: {result}")
