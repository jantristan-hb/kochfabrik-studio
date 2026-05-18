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


def run_batch(in_dir, out_dir, keep):
    import glob
    pdfs = sorted(glob.glob(os.path.join(in_dir, "*.pdf")))
    if not pdfs:
        sys.exit(f"Keine *.pdf in {in_dir}")
    os.makedirs(out_dir, exist_ok=True)
    ok, fail = [], []
    for n, pdf in enumerate(pdfs, 1):
        name = os.path.splitext(os.path.basename(pdf))[0]
        out = os.path.join(out_dir, name + ".pptx")
        print(f"[{n}/{len(pdfs)}] {os.path.basename(pdf)} ...",
              file=sys.stderr)
        try:
            convert(pdf, out, keep=keep)
            ok.append(name)
        except Exception as ex:
            fail.append((name, str(ex).splitlines()[-1][:160]))
    print(f"\n=== Batch: {len(ok)} OK, {len(fail)} Fehler ===")
    for name, err in fail:
        print(f"  FEHLER {name}: {err}")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", nargs="?", default=None, help="Input-PDF")
    ap.add_argument("out", nargs="?", default=None,
                    help="Output-PPTX (default: <pdf>.pptx)")
    ap.add_argument("--batch", metavar="DIR",
                    help="alle *.pdf in DIR konvertieren")
    ap.add_argument("--out", dest="out_dir", metavar="DIR", default="out",
                    help="Batch-Output-Verzeichnis (default: out/)")
    ap.add_argument("--keep", action="store_true",
                    help="Work-Dir nicht löschen")
    a = ap.parse_args()
    if a.batch:
        run_batch(a.batch, a.out_dir, a.keep)
    if not a.pdf:
        ap.error("Input-PDF fehlt (oder --batch DIR nutzen)")
    out = a.out or (os.path.splitext(a.pdf)[0] + ".pptx")
    print(f"OK: {convert(a.pdf, out, keep=a.keep)}")
