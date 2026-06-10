"""US-007 — Angebots-Korpus inventarisieren & Layout vermessen.

Klassifiziert den ganzen KOCHfabrik-Korpus (kf_classify), sammelt die
`angebot`-Typen, leitet pro PDF eine STRUKTUR-SIGNATUR ab (vorhandene
Veranstaltungsinformationen-Labels, Positions-Sektionen, Footer-Variante,
Preiszeilen) und clustert daraus Layout-Generationen. Wählt EIN
Referenz-Muster (höchster Vollständigkeits-Score) für die spätere
pixelgenaue Template-Extraktion (US-009).

Run: python3 scan_angebote.py [--limit N] [--json]
"""
import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kf_classify import is_kochfabrik, classify, pdf_text   # noqa
from compose_offer import parse_offer_dishes                 # noqa

CORPUS = os.path.expanduser("~/Nextcloud/Kochfabrik Dokumente")
LABELS = ["Veranstaltungsanlass", "Veranstaltungsdatum",
          "Veranstaltungsbeginn", "Personenanzahl",
          "Veranstaltungsort", "Cateringkonzept"]
SECTIONS = ["Speisen", "Menü", "Getränke", "Personal", "Logistik",
            "Technik", "Mobiliar"]
FOOTER_VARIANTS = {
    "goldschaetzchen": r"Restaurant Goldschätzchen",
    "planungsfabrik": r"Planungsfabrik Hamburg",
    "speisenmacherei": r"Speisenmacherei",
}
PRICE = re.compile(r"\b\d{1,3}(?:\.\d{3})*,\d{2}\b")


def signature(text):
    labels = tuple(L for L in LABELS
                   if re.search(rf"(?im)^\s*{L}\s*:", text))
    sections = tuple(s for s in SECTIONS
                     if re.search(rf"(?im)^\s*{re.escape(s)}\s*$", text))
    footer = tuple(k for k, p in FOOTER_VARIANTS.items()
                   if re.search(p, text))
    has_price = bool(PRICE.search(text))
    has_angnr = bool(re.search(r"(?i)Angebots\s*Nr\.?:", text))
    has_kdnr = bool(re.search(r"(?i)Kundennr\.?:", text))
    score = (len(labels) + len(sections) + len(footer)
             + has_price + has_angnr + has_kdnr)
    return {"labels": labels, "sections": sections, "footer": footer,
            "has_price": has_price, "has_angnr": has_angnr,
            "has_kdnr": has_kdnr, "score": score}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0,
                    help="max Präsentationen scannen (0=alle)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    mus = sorted(glob.glob(f"{CORPUS}/AKARA_Muster_Angebote/*.pdf"))
    pre = sorted(glob.glob(f"{CORPUS}/AKARA_Präsentationen/*.pdf"))
    if a.limit:
        pre = pre[:a.limit]
    pdfs = mus + pre

    kinds = {"angebot": 0, "menue": 0, "kontext": 0, "fremd": 0}
    angebote = []
    for p in pdfs:
        t = pdf_text(p)
        if not is_kochfabrik(t):
            kinds["fremd"] += 1
            continue
        try:
            nc = len(parse_offer_dishes(p, ""))
        except Exception:
            nc = 0
        k = classify(t, nc)
        kinds[k] += 1
        if k == "angebot":
            sig = signature(t)
            angebote.append((os.path.basename(p), sig))

    # Generationen = distinkte (labels, sections-Set, footer)-Signaturen
    gens = {}
    for name, s in angebote:
        key = (s["labels"], tuple(sorted(s["sections"])), s["footer"])
        gens.setdefault(key, []).append((name, s["score"]))

    angebote.sort(key=lambda x: -x[1]["score"])
    ref = angebote[0] if angebote else None

    print(f"Korpus: {len(pdfs)} PDFs "
          f"({len(mus)} Muster + {len(pre)} Präsentationen)")
    print(f"Klassifikation: {kinds}")
    print(f"angebot-Typen: {len(angebote)} | "
          f"Layout-Generationen: {len(gens)}")
    for i, (key, members) in enumerate(sorted(
            gens.items(), key=lambda kv: -len(kv[1])), 1):
        lbl, sec, foo = key
        print(f"\nGEN {i}  ({len(members)} PDFs)  score~{members[0][1]}")
        print(f"  Labels   : {', '.join(lbl) or '—'}")
        print(f"  Sektionen: {', '.join(sec) or '—'}")
        print(f"  Footer   : {', '.join(foo) or '—'}")
        for n, sc in members[:3]:
            print(f"    · {n[:54]}  (score {sc})")
    if ref:
        n, s = ref
        print(f"\n>>> REFERENZ-MUSTER: {n}")
        print(f"    score={s['score']} labels={len(s['labels'])} "
              f"sections={list(s['sections'])} "
              f"price={s['has_price']} angnr={s['has_angnr']}")
    if a.json:
        print(json.dumps({"kinds": kinds,
                          "angebote": [(n, s) for n, s in angebote],
                          "reference": ref[0] if ref else None},
                         ensure_ascii=False, default=list))


if __name__ == "__main__":
    main()
