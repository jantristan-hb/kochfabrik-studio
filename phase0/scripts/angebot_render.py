"""US-014 — End-to-End Renderer-CLI: Angebot-JSON → pixelgenaues PDF.

load(angebot.json) → angebot_fill.fill (Skalar-Tokens) →
angebot_positions.render (Positions-Repeater) → elements.json+logos in
Workdir (cached_deck materialisiert Assets) → reconstruct.js → pptx →
soffice → PDF. Kernprodukt des Sprints; schließt die US-012-Adaption
(echte PDF-Pipeline statt PPTX-Text-Proxy). Engine UNVERÄNDERT.

Run: python3 angebot_render.py <angebot.json> -o out.pdf
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _deckpipe import cached_deck                                # noqa
from angebot_model import load                                   # noqa
from angebot_fill import fill, TEMPLATE                           # noqa
from angebot_positions import render                              # noqa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPIKE = os.path.join(ROOT, "spike-pptxgenjs")
SCRIPTS = os.path.join(ROOT, "scripts")
REF_PDF = ("/Users/janrudat/Nextcloud/Kochfabrik Dokumente/"
           "AKARA_Muster_Angebote/# 10_182_RAUMKARUSSELL GmbH_"
           "12_09_2026.pdf")


def render_pdf(angebot, out_pdf: str) -> str:
    """Angebot-Instanz → PDF unter out_pdf. Gibt out_pdf zurück."""
    if not shutil.which("soffice"):
        raise RuntimeError("soffice (LibreOffice) fehlt — für pptx→pdf")
    if not os.path.isfile(TEMPLATE):
        subprocess.run([sys.executable,
                        os.path.join(SCRIPTS, "build_angebot_template.py")],
                       check=True, capture_output=True)
    sh = tempfile.mkdtemp(prefix="angrender_")
    _, _, logos = cached_deck(REF_PDF, sh)            # Assets in sh
    el = render(fill(angebot), angebot)
    json.dump(el, open(os.path.join(sh, "elements.json"), "w"),
              ensure_ascii=False)
    json.dump(logos, open(os.path.join(sh, "logos.json"), "w"))
    r = subprocess.run(["node", os.path.join(SPIKE, "reconstruct.js"),
                        "elements.json", "out.pptx"], cwd=sh,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("reconstruct.js: " + (r.stderr or "")[-300:])
    c = subprocess.run(["soffice", "--headless", "--convert-to", "pdf",
                        "--outdir", sh, os.path.join(sh, "out.pptx")],
                       capture_output=True, text=True, timeout=180)
    src = os.path.join(sh, "out.pdf")
    if not os.path.isfile(src):
        raise RuntimeError("soffice pptx→pdf fehlgeschlagen: "
                           + (c.stderr or c.stdout or "")[-300:])
    os.makedirs(os.path.dirname(os.path.abspath(out_pdf)), exist_ok=True)
    shutil.copyfile(src, out_pdf)
    return out_pdf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("angebot", help="Angebot-JSON (angebot_model)")
    ap.add_argument("-o", "--out", default="angebot.pdf")
    a = ap.parse_args()
    try:
        out = render_pdf(load(a.angebot), a.out)
    except Exception as e:
        print(f"FEHLER: {e}")
        sys.exit(1)
    print(f"OK: {out}  ({os.path.getsize(out)} bytes)")


if __name__ == "__main__":
    main()
