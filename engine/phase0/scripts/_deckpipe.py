"""_deckpipe.py — geteilter Per-Deck-Pipeline-Helper für Composer/Demos.

Fährt PRO Deck die VOLLE Pipeline (inkl. Logo-Transparenz +
offizielles Gold-Logo) isoliert wie convert.py, und legt das Ergebnis
deck-genamespaced in ein gemeinsames Workdir, damit Cross-Deck-Decks
das transparente KOCHfabrik-Logo behalten und Bild-Namen nicht kollidieren.

process_deck(pdf, shared) -> (slug, elements_dict, logos_map)
  - elements: image-src und logos-Keys auf "<slug>/assets/..." umgeschrieben
  - shared/<slug>/assets/...  enthält alle Bild-/Logo-Dateien
reconstruct.js mit cwd=shared findet logos.json (gemerged) + Dateien.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

SPIKE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "spike-pptxgenjs")


def slugify(pdf):
    return re.sub(r"[^a-z0-9]+", "-",
                  os.path.splitext(os.path.basename(pdf))[0].lower()
                  ).strip("-") or "deck"


def process_deck(pdf, shared):
    """Volle Pipeline isoliert; Ergebnis namespaced nach shared/<slug>/."""
    slug = slugify(pdf)
    iso = tempfile.mkdtemp(prefix="deck_")
    assets = os.path.join(iso, "assets")
    os.makedirs(assets)
    try:
        shutil.copy(pdf, os.path.join(assets, "ref.pdf"))
        srcl = os.path.join(SPIKE, "assets", "logo_src")
        if os.path.isdir(srcl):
            shutil.copytree(srcl, os.path.join(assets, "logo_src"))
        run = lambda c: subprocess.run(c, cwd=iso, capture_output=True,
                                       check=True, timeout=240)
        run(["pdftohtml", "-xml", "-zoom", "1",
             "assets/ref.pdf", "assets/ref.xml"])
        run([sys.executable, os.path.join(SPIKE, "extract_logos.py")])
        run([sys.executable, os.path.join(SPIKE, "apply_official_logo.py")])
        run([sys.executable, os.path.join(SPIKE, "extract.py"),
             "assets/ref.pdf", "elements.json"])

        el = json.load(open(os.path.join(iso, "elements.json")))
        logos = {}
        lp = os.path.join(iso, "logos.json")
        if os.path.isfile(lp):
            logos = json.load(open(lp))

        # nach shared/<slug>/ kopieren + Pfade namespacen
        dst = os.path.join(shared, slug)
        shutil.copytree(os.path.join(iso, "assets"),
                        os.path.join(dst, "assets"))
        pref = slug + "/"

        def nsp(p):  # "assets/..." -> "<slug>/assets/..."
            return pref + p if p and p.startswith("assets/") else p

        for pg, seq in el.items():
            if pg == "_meta":
                continue
            for e in seq:
                if e.get("t") == "image":
                    e["src"] = nsp(e["src"])
        logos = {nsp(k): nsp(v) for k, v in logos.items()}
        return slug, el, logos
    finally:
        shutil.rmtree(iso, ignore_errors=True)


CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "data", "cache")


def cached_deck(pdf, shared):
    """Drop-in für process_deck mit persistentem Cache (phase0/data/cache/
    <slug>/: elements.json + logos.json + assets/). Lazy: erster Zugriff
    extrahiert + persistiert, danach reine Kopie (keine Extraktion).
    Reproduziert das shared/<slug>/assets-Layout → reconstruct unverändert.
    """
    slug = slugify(pdf)
    cdir = os.path.join(CACHE, slug)
    el_p = os.path.join(cdir, "elements.json")
    ass = os.path.join(cdir, "assets")
    if os.path.isfile(el_p) and os.path.isdir(ass):
        shutil.copytree(ass, os.path.join(shared, slug, "assets"))
        el = json.load(open(el_p))
        lp = os.path.join(cdir, "logos.json")
        logos = json.load(open(lp)) if os.path.isfile(lp) else {}
        return slug, el, logos
    # Cache-Miss → extrahieren und persistieren
    slug, el, logos = process_deck(pdf, shared)
    os.makedirs(cdir, exist_ok=True)
    src_ass = os.path.join(shared, slug, "assets")
    if os.path.isdir(src_ass) and not os.path.isdir(ass):
        shutil.copytree(src_ass, ass)
    json.dump(el, open(el_p, "w"))
    json.dump(logos, open(os.path.join(cdir, "logos.json"), "w"))
    return slug, el, logos
