"""US-015 — PDF-Diff-Harness.

Rendert zwei PDFs seitenweise (pdftoppm) und misst pro Seite den
Anteil signifikant abweichender Pixel (Graustufe, Per-Pixel-Toleranz).
Dependency-arm: nur PIL + pdftoppm. Basis für das Pixel-Diff-Gate
(US-016, analog Phase-B des Präsentationsgenerators, aber per-Seite).

Run: python3 pdf_diff.py a.pdf b.pdf [--dpi 150] [--max 0.02] [--tol 0.06]
Exit 0 wenn max Seiten-Score <= --max (und Seitenzahl gleich), sonst 1.
"""
import argparse
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageChops


def render_pages(pdf, dpi, workdir):
    pre = os.path.join(workdir, os.path.basename(pdf).replace(".", "_"))
    subprocess.run(["pdftoppm", "-png", "-r", str(dpi), pdf, pre],
                   capture_output=True, check=True)
    pngs = sorted(f for f in os.listdir(workdir)
                  if f.startswith(os.path.basename(pre))
                  and f.endswith(".png"))
    return [Image.open(os.path.join(workdir, p)).convert("L")
            for p in pngs]


def page_score(a, b, tol):
    """Anteil Pixel mit |Δ| > tol*255. b wird auf a-Größe skaliert."""
    if b.size != a.size:
        b = b.resize(a.size)
    diff = ImageChops.difference(a, b)
    thr = int(tol * 255)
    hist = diff.histogram()                 # 256 Werte (Graustufe)
    over = sum(hist[thr + 1:])
    total = a.size[0] * a.size[1]
    return over / total if total else 0.0


def diff_pdfs(a_pdf, b_pdf, dpi=150, tol=0.06):
    """→ (max_score, [(seite, score)], n_a, n_b)."""
    with tempfile.TemporaryDirectory() as wd:
        A = render_pages(a_pdf, dpi, wd)
        B = render_pages(b_pdf, dpi, wd)
        n = max(len(A), len(B))
        scores = []
        for i in range(n):
            if i >= len(A) or i >= len(B):
                scores.append((i + 1, 1.0))         # fehlende Seite
            else:
                scores.append((i + 1, page_score(A[i], B[i], tol)))
        mx = max((s for _, s in scores), default=0.0)
        return mx, scores, len(A), len(B)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--max", type=float, default=0.02,
                    help="max erlaubter Seiten-Score")
    ap.add_argument("--tol", type=float, default=0.06,
                    help="Per-Pixel-Δ-Toleranz (Anteil von 255)")
    a = ap.parse_args()
    mx, scores, na, nb = diff_pdfs(a.a, a.b, a.dpi, a.tol)
    print(f"Seiten: {na} vs {nb} | dpi={a.dpi} tol={a.tol} "
          f"max-erlaubt={a.max}")
    for pg, sc in scores:
        flag = "" if sc <= a.max else "  > MAX"
        print(f"  Seite {pg}: score={sc:.4f}{flag}")
    ok = (na == nb) and (mx <= a.max)
    print(f"=> max-score={mx:.4f}  {'PASS' if ok else 'FAIL'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
