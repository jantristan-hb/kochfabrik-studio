"""US-019 — Regression: End-to-End Render-Konformität + Pixel-Gate.

Schließt die US-012-Adaption: jetzt ECHTES PDF (nicht PPTX-Text-Proxy).
(a) angebot_render(example) → PDF → pdftotext → kf_classify ist
    KOCHfabrik + 'angebot' + 6 Labels + Bankblock.
(b) Referenz-Self-Round-Trip (angebot_gate) max-score <= TOL.
Run: python3 tests/test_angebot_render.py
"""
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from angebot_model import load                                   # noqa
from angebot_render import render_pdf                             # noqa
from kf_classify import is_kochfabrik, classify                   # noqa
from angebot_gate import run_one, REFERENZ, TOL                   # noqa

FIX = os.path.join(os.path.dirname(__file__), "..", "fixtures",
                   "angebot_example.json")
LABELS = ["Veranstaltungsanlass", "Veranstaltungsdatum",
          "Veranstaltungsbeginn", "Personenanzahl",
          "Veranstaltungsort", "Cateringkonzept"]
f = 0


def chk(name, cond):
    global f
    print(("  ok  " if cond else "  FAIL") + " " + name)
    f += 0 if cond else 1


wd = tempfile.mkdtemp(prefix="us019_")
pdf = os.path.join(wd, "ex.pdf")
render_pdf(load(FIX), pdf)
chk("PDF erzeugt (>10KB)", os.path.getsize(pdf) > 10000)
txt = subprocess.run(["pdftotext", "-layout", pdf, "-"],
                     capture_output=True, text=True).stdout
chk("is_kochfabrik (Letterhead/Footer verbatim)", is_kochfabrik(txt))
chk("classify == 'angebot'", classify(txt, 0) == "angebot")
chk("alle 6 Veranstaltungsinformationen-Labels",
    all(L in txt for L in LABELS))
chk("Bankblock erhalten (GENODEF1PIN/Planungsfabrik)",
    "GENODEF1PIN" in txt or "Planungsfabrik" in txt)
chk("Kundenwert gerendert (RAUMKARUSSELL)", "RAUMKARUSSELL" in txt)

ref = run_one(REFERENZ, wd)
chk(f"Referenz-Pixel-Gate max={ref['max']:.4f} <= TOL {TOL}",
    ref["max"] <= TOL)

print(f"\n{'ALLE TESTS GRÜN' if f == 0 else str(f)+' FEHLER'}")
raise SystemExit(1 if f else 0)
