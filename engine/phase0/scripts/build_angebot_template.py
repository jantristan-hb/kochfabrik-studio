"""US-009 — Pixelgenaues Angebots-Template aus dem Referenz-Muster.

Faithful-Extraktion (cached_deck, Engine UNVERÄNDERT) des GEN-2-Referenz-
Musters → tokenisiertes, parametrisierbares Template:
  • Skalar-Felder (Kopf/Metadaten/Veranstaltungsinformationen) → {TOKEN}
    Mapping gekoppelt an angebot_model.example() (US-008-Referenzwerte)
  • Positionsblöcke → NICHT gerendert (Sprint-3-Scope, FEATURE-ARCH):
    Positions-Elemente werden vermessen → _meta.repeater-Band-Spec
  • Letterhead/Bank/Footer → verbatim (keine Tokens)

Out: phase0/data/angebot_template.elements.json (regenerierbar, wie
cover_template/ausstattung_template; phase0/data ist gitignored).

Run: python3 build_angebot_template.py
"""
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _deckpipe import cached_deck                               # noqa
from angebot_model import example                               # noqa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SPIKE = os.path.join(ROOT, "spike-pptxgenjs")
REF_PDF = ("/home/jrudat/Nextcloud/Kochfabrik Dokumente/"
           "AKARA_Muster_Angebote/# 10_182_RAUMKARUSSELL GmbH_"
           "12_09_2026.pdf")


def token_map():
    """(such-string, token) — längste zuerst (Kollisions-Schutz).
    Werte = echte Referenzstrings (US-008 example() + PDF-Zeilen)."""
    a = example()
    pairs = [
        (a.kunde, "{KUNDE}"),
        ("Frau Claudia Kiesel", "{ADRESSE_NAME}"),
        ("Ernst-Merck-Straße 12-14", "{ADRESSE_STRASSE}"),
        ("20099 Hamburg", "{ADRESSE_ORT}"),
        (a.veranstaltung.ort, "{ORT}"),
        ("Edelfettwerk , Schnackenburgallee 202, 22525 Hamburg", "{ORT}"),
        (a.veranstaltung.anlass, "{ANLASS}"),
        (a.veranstaltung.beginn, "{BEGINN}"),
        (a.veranstaltung.datum, "{V_DATUM}"),
        ("500 Personen", "{PERSONEN}"),
        (a.veranstaltung.konzept, "{KONZEPT}"),
        (a.ansprechpartner, "{ANSPRECHPARTNER}"),
        (a.lieferdatum, "{LIEFERDATUM}"),
        (a.datum, "{DATUM}"),
        (a.angebots_nr, "{ANGEBOTS_NR}"),
        (a.kundennr, "{KUNDENNR}"),
    ]
    # längste Suchstrings zuerst ersetzen
    return sorted([(s, t) for s, t in pairs if s],
                  key=lambda st: -len(st[0]))


def main():
    shared = tempfile.mkdtemp(prefix="angtmpl_")
    slug, el, logos = cached_deck(REF_PDF, shared)
    tmap = token_map()
    pos_strings = []
    for b in example().bloecke:
        for p in b.positionen:
            pos_strings.append(p.bezeichnung)
            for v in (p.einzelpreis, p.gesamt):
                if v:
                    pos_strings.append(f"{v:.2f}".replace(".", ","))

    n_tok = 0
    pos_boxes = []                                # (page,x,y,w,h)
    ref_elcount = 0
    for pg, seq in el.items():
        if pg == "_meta" or not isinstance(seq, list):
            continue
        ref_elcount += len(seq)
        for e in seq:
            if e.get("t") != "text":
                continue
            for ln in e.get("lines", []):
                txt = ln.get("txt", "")
                for s, tok in tmap:                # Skalar-Tokens
                    if s and s in txt:
                        txt = txt.replace(s, tok)
                        n_tok += 1
                ln["txt"] = txt
                if any(ps and ps in ln.get("txt", "")
                       for ps in pos_strings):     # Positions-Element
                    pos_boxes.append((pg, e.get("x", 0), e.get("y", 0),
                                      e.get("w", 0), e.get("h", 0)))

    # Positions-Repeater-Band (best-effort aus den getroffenen Boxen;
    # exakte Zeilen-Vorlage = US-011, Rendering = Sprint 3)
    rep = None
    if pos_boxes:
        pg = pos_boxes[0][0]
        ys = [b[2] for b in pos_boxes if b[0] == pg]
        hs = [b[4] for b in pos_boxes if b[0] == pg] or [0]
        rep = {"positionen": {"page": pg, "y0": min(ys),
                              "y1": max(ys), "row_h": max(hs)}}
    meta = dict(el.get("_meta", {}))
    meta["deck"] = "angebot-template"
    meta["repeater"] = rep
    out = {k: v for k, v in el.items() if k != "_meta"}
    out["_meta"] = meta

    os.makedirs(DATA, exist_ok=True)
    tpath = os.path.join(DATA, "angebot_template.elements.json")
    json.dump(out, open(tpath, "w"), ensure_ascii=False, indent=1)
    json.dump(logos, open(os.path.join(shared, "logos.json"), "w"))
    json.dump(out, open(os.path.join(shared, "elements.json"), "w"),
              ensure_ascii=False)

    # Demo-Render zur Verifikation (rc==0, kein Engine-Fehler)
    r = subprocess.run(
        ["node", os.path.join(SPIKE, "reconstruct.js"),
         "elements.json", "/tmp/angebot_template_demo.pptx"],
        cwd=shared, capture_output=True, text=True)
    pages = sum(1 for k in out if k != "_meta")
    print(f"Referenz: {slug}")
    print(f"Template: {tpath}")
    print(f"  Seiten={pages}  Elemente={ref_elcount}  "
          f"Skalar-Tokens injiziert={n_tok}")
    print(f"  Positions-Elemente getroffen={len(pos_boxes)}  "
          f"repeater={rep}")
    print(f"  reconstruct.js rc={r.returncode} "
          f"({'OK' if r.returncode == 0 else r.stderr[-200:]})")
    if n_tok == 0 or r.returncode != 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
