"""US-024 — Korpus-Konformitäts-Gate.

Jedes fiktiv_korpus/*.pdf → pdftotext → kf_classify: is_kochfabrik +
classify=='angebot' + Label-/Bankblock. Aggregat + KORPUS-GATE.md.
Belegt Epic-Akzeptanzkriterium 2 (strukturell ununterscheidbar).

Run: python3 korpus_gate.py [--src ../data/fiktiv_korpus]
"""
import argparse
import glob
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# US-056: Tooling lebt jetzt unter engine/tooling/ — Runtime-Module
# (engine/scripts/) zusätzlich auf den Pfad (KEINE Logikänderung).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "scripts"))
from kf_classify import is_kochfabrik, classify                  # noqa

PROJ = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
LABELS = ["Veranstaltungsanlass", "Veranstaltungsdatum",
          "Personenanzahl", "Veranstaltungsort", "Cateringkonzept"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="../data/fiktiv_korpus")
    a = ap.parse_args()
    pdfs = sorted(glob.glob(os.path.join(a.src, "*.pdf")))
    rows, okc = [], 0
    for p in pdfs:
        t = subprocess.run(["pdftotext", "-layout", p, "-"],
                           capture_output=True, text=True).stdout
        kf = is_kochfabrik(t)
        ang = classify(t, 0) == "angebot"
        lab = sum(1 for L in LABELS if L in t)
        bank = ("GENODEF1PIN" in t or "Planungsfabrik" in t)
        good = kf and ang and lab >= 3 and bank
        okc += good
        rows.append((os.path.basename(p), kf, ang, lab, bank, good))
    n = len(pdfs)
    lines = ["# US-024 — Korpus-Konformitäts-Gate", "",
             f"{okc}/{n} PDFs konform "
             f"(is_kochfabrik + classify=='angebot' + ≥3 Labels + "
             f"Bankblock)", "",
             "| PDF | KF | angebot | Labels | Bank | OK |",
             "|-----|----|---------|--------|------|----|"]
    for nm, kf, ang, lab, bk, g in rows:
        lines.append(f"| {nm} | {'✓' if kf else '✗'} | "
                     f"{'✓' if ang else '✗'} | {lab}/5 | "
                     f"{'✓' if bk else '✗'} | "
                     f"{'✅' if g else '❌'} |")
    rp = os.path.join(PROJ, "docs", "sprint-4", "KORPUS-GATE.md")
    os.makedirs(os.path.dirname(rp), exist_ok=True)
    open(rp, "w").write("\n".join(lines) + "\n")
    print(f"Korpus-Gate: {okc}/{n} konform → {rp}")
    sys.exit(0 if n and okc == n else 1)


if __name__ == "__main__":
    main()
