#!/usr/bin/env python3
"""fidelity_run.py — Korpus-Treue-Harness (FEATURE-TREUE-HARNESS §8 Nr. 2, US-082).

Rekonstruiert je Slide eines Sample-Decks aus ``elements.json``, rendert ihn über
dieselbe Container-Pipeline wie ``render_notext.py`` (reconstruct.js → soffice),
konvertiert nach PDF und misst ihn mit ``fidelity.compare`` gegen die zugehörige
``assets/ref.pdf``-Seite (Seiten sind 1:1 nummeriert). Ausgabe: ein
reproduzierbarer JSON-Report je Slide.

EARS §8 Nr. 2: WHEN der Lauf über das Sample läuft THE SYSTEM SHALL einen
reproduzierbaren JSON-Report liefern (zweiter Lauf: identische Scores ±0.005 —
Render-Determinismus-Toleranz; soffice rendert NICHT bit-identisch, Pitfall §12.1).

UNTERSCHIED zu render_notext.py: KEIN Text-Filter (volles Layout inkl. Text),
und soffice konvertiert nach PDF statt PNG (fidelity arbeitet auf PDF-Seiten).

Render-/Mess-Pipeline läuft NUR im Container — der braucht ``node`` + ``soffice``
(kf-studio-sim hat beide). ``fitz`` (PyMuPDF) ist die freigegebene Analyse-Dep,
die NICHT im Runtime-Image steckt (Tooling-Split): dieses Build-Werkzeug stellt
sie bei Bedarf zur Laufzeit selbst bereit (``ensure_fitz``) — die Runtime
(``engine/scripts/``) importiert dieses Modul nie.

CONTAINER-AUFRUF (wie render_notext, SOFFICE via Env):
    docker run --rm \\
      -v "$PWD/engine/data:/app/engine/data" \\
      -v "$PWD/engine/tooling:/app/engine/tooling" \\
      kf-studio-sim \\
      python3 engine/tooling/fidelity_run.py --deck 10-182-raumkarussell-gmbh-12-09-2026

Usage:
    fidelity_run.py --deck SLUG              # alle Seiten eines Decks
    fidelity_run.py --decks SLUG1,SLUG2      # mehrere Decks
    fidelity_run.py --deck SLUG --limit N    # nur erste N Seiten
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Runtime-Module (engine/scripts/) für CACHE/SPIKE auf den Pfad — KEINE
# Logikänderung, identisch zu render_notext.py (US-056).
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
)
from _deckpipe import CACHE, SPIKE  # noqa: E402

SOFFICE = os.environ.get("SOFFICE", "soffice")


def ensure_fitz():
    """fitz importierbar machen; im Container on-demand nachinstallieren.

    fitz darf NICHT ins Runtime-Image (Tooling-Split). Dieses Analyse-Werkzeug
    stellt die Dep daher zur Laufzeit bereit, falls sie fehlt — die Version wird
    von fidelity.py im Output ausgewiesen (FIDELITY pinnt fitz-Version).
    """
    try:
        import fitz  # noqa: F401
    except ImportError:
        # pip-Ausgabe NUR nach stderr — stdout bleibt reines JSON.
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", "pymupdf>=1.24"],
            check=True,
            stdout=sys.stderr,
        )
    # MuPDF schreibt Struktur-Warnungen ("No common ancestor in structure tree")
    # bei soffice-PDFs auf den C-stdout-Deskriptor — abschalten, sonst landet
    # Nicht-JSON auf stdout (Parse-Bruch im Harness/Verify).
    import fitz  # noqa: F811

    if hasattr(fitz, "TOOLS") and hasattr(fitz.TOOLS, "mupdf_display_errors"):
        fitz.TOOLS.mupdf_display_errors(False)


def _load_fidelity():
    """fidelity.py als Modul laden (liegt neben dieser Datei in engine/tooling/)."""
    import importlib.util

    fid_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fidelity.py")
    spec = importlib.util.spec_from_file_location("fidelity", fid_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def list_pages(deck):
    """Alle Seiten eines Decks aus dessen elements.json (DB-los, wie render_notext)."""
    el_path = os.path.join(CACHE, deck, "elements.json")
    if not os.path.isfile(el_path):
        return []
    el = json.load(open(el_path))
    return sorted(int(k) for k in el.keys() if k != "_meta")


def render_slide_pdf(deck, page, work):
    """Rendert 1 Slide (VOLLES Layout, KEIN Text-Filter) → PDF-Pfad oder None.

    Pipeline identisch zu render_notext.render_single bis zum soffice-Schritt,
    nur ohne strip_text und mit --convert-to pdf statt png.
    """
    el_path = os.path.join(CACHE, deck, "elements.json")
    if not os.path.isfile(el_path):
        return None
    el = json.load(open(el_path))
    seq = el.get(str(int(page)))
    if not seq:
        return None

    # 1-Slide-elements.json bauen: meta + nur diese page als "1".
    meta = el.get("_meta", {"w_pt": 960, "h_pt": 540})
    single = {
        "1": seq,
        "_meta": dict(meta, deck=deck, notes={"1": f"{deck}:{page}"}),
    }
    shared = tempfile.mkdtemp(prefix="fidelity_", dir=work)
    lg_src = os.path.join(CACHE, deck, "logos.json")
    if os.path.isfile(lg_src):
        shutil.copy(lg_src, os.path.join(shared, "logos.json"))
    # Asset-Dir symlinken: src-Pfade sind relativ '<deck>/assets/<file>',
    # reconstruct.js läuft mit cwd=shared (identisch render_notext).
    assets_src = os.path.join(CACHE, deck, "assets")
    if os.path.isdir(assets_src):
        os.makedirs(os.path.join(shared, deck), exist_ok=True)
        os.symlink(assets_src, os.path.join(shared, deck, "assets"))
    json.dump(single, open(os.path.join(shared, "elements.json"), "w"))

    pptx = os.path.join(shared, "slide.pptx")
    r = subprocess.run(
        ["node", os.path.join(SPIKE, "reconstruct.js"), "elements.json", pptx],
        cwd=shared,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if r.returncode != 0 or not os.path.isfile(pptx):
        return None

    # soffice headless: PPTX → PDF (eigenes User-Profile-Dir, sonst kollidieren
    # parallele Läufe auf demselben ~/.config/libreoffice — wie render_notext).
    user_profile = os.path.join(shared, "soffice-profile")
    r = subprocess.run(
        [
            SOFFICE,
            "--headless",
            f"-env:UserInstallation=file://{user_profile}",
            "--convert-to",
            "pdf",
            "--outdir",
            shared,
            pptx,
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    pdf = os.path.join(shared, "slide.pdf")
    if r.returncode != 0 or not os.path.isfile(pdf):
        return None
    return pdf


def run_deck(deck, fid, limit=None):
    """Liefert Liste {deck, page, scores} für alle (oder erste N) Seiten."""
    ref_pdf = os.path.join(CACHE, deck, "assets", "ref.pdf")
    if not os.path.isfile(ref_pdf):
        return [], f"ref.pdf fehlt: {ref_pdf}"
    pages = list_pages(deck)
    if limit:
        pages = pages[:limit]
    out = []
    errors = []
    work = tempfile.mkdtemp(prefix="fidelity_deck_")
    try:
        for page in pages:
            pdf = render_slide_pdf(deck, page, work)
            if pdf is None:
                errors.append({"deck": deck, "page": page, "reason": "render-fail"})
                continue
            try:
                scores = fid.compare(ref_pdf, page, pdf, 1)
            except Exception as exc:  # Mess-Fehler ausweisen, nicht verschlucken
                errors.append(
                    {"deck": deck, "page": page, "reason": f"{type(exc).__name__}: {exc}"}
                )
                continue
            out.append({"deck": deck, "page": page, "scores": scores})
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return out, errors


def main(argv=None):
    ap = argparse.ArgumentParser(description="Korpus-Treue-Harness (fidelity_run)")
    ap.add_argument("--deck", help="ein Deck-Slug")
    ap.add_argument("--decks", help="mehrere Deck-Slugs, kommagetrennt")
    ap.add_argument("--limit", type=int, help="nur erste N Seiten je Deck")
    a = ap.parse_args(argv)

    decks = []
    if a.deck:
        decks.append(a.deck)
    if a.decks:
        decks.extend(d.strip() for d in a.decks.split(",") if d.strip())
    if not decks:
        print("FEHLER: --deck oder --decks angeben", file=sys.stderr)
        return 2

    ensure_fitz()
    fid = _load_fidelity()

    slides = []
    all_errors = []
    for deck in decks:
        deck_slides, deck_errors = run_deck(deck, fid, limit=a.limit)
        slides.extend(deck_slides)
        if isinstance(deck_errors, str):
            all_errors.append({"deck": deck, "reason": deck_errors})
        else:
            all_errors.extend(deck_errors)

    report = {
        "metrik_version": fid.FIDELITY_VERSION,
        "fitz_version": fid._fitz_version(),
        "decks": decks,
        "slides": slides,
        "errors": all_errors,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
