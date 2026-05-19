"""US-010 — Datenmodell → Template Felder-Mapping.

Setzt die Skalar-Felder eines `Angebot` in die Tokens des
`angebot_template.elements.json` ein (Muster: compose_offer.swap_ph).
Positions-Repeater (`_meta.repeater`) + invariante Letterhead/Bank/
Footer-Blöcke bleiben UNBERÜHRT — Positions-Rendering = Sprint 3.

Token-Set deckt exakt die von build_angebot_template.py (US-009)
injizierten Tokens ab.

Run: python3 -c "import angebot_fill,angebot_model as m; \
print(sum(1 for _ in str(angebot_fill.fill(m.example()))))"
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from angebot_model import Angebot, example, load                # noqa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "data", "angebot_template.elements.json")
TOKEN_RE = re.compile(r"\{[A-Z_]+\}")


def _addr(adresse: str):
    p = [x.strip() for x in (adresse or "").split(",")]
    while len(p) < 3:
        p.append("")
    return p[0], p[1], p[2]


def token_values(a: Angebot) -> dict:
    """Token → konkreter Wert aus dem Angebot. Muss die in
    build_angebot_template.token_map() vergebenen Tokens abdecken."""
    an, st, ot = _addr(a.adresse)
    v = a.veranstaltung
    return {
        "{KUNDE}": a.kunde,
        "{ADRESSE_NAME}": an,
        "{ADRESSE_STRASSE}": st,
        "{ADRESSE_ORT}": ot,
        "{ANGEBOTS_NR}": a.angebots_nr,
        "{DATUM}": a.datum,
        "{KUNDENNR}": a.kundennr,
        "{LIEFERDATUM}": a.lieferdatum,
        "{ANSPRECHPARTNER}": a.ansprechpartner,
        "{ANLASS}": v.anlass,
        "{V_DATUM}": v.datum,
        "{BEGINN}": v.beginn,
        "{PERSONEN}": f"{v.personen} Personen" if v.personen else "",
        "{ORT}": v.ort,
        "{KONZEPT}": v.konzept,
    }


def fill(a: Angebot, template_path: str = TEMPLATE) -> dict:
    el = json.load(open(template_path, encoding="utf-8"))
    vals = token_values(a)
    for pg, seq in el.items():
        if pg == "_meta" or not isinstance(seq, list):
            continue
        for e in seq:
            if e.get("t") != "text":
                continue
            for ln in e.get("lines", []):
                t = ln.get("txt", "")
                if "{" not in t:
                    continue
                for tok, val in vals.items():
                    if tok in t:
                        t = t.replace(tok, val)
                ln["txt"] = t
    return el


def open_tokens(el: dict) -> list:
    """Verbleibende {TOKEN} im Text (Repeater in _meta zählt nicht)."""
    out = []
    for pg, seq in el.items():
        if pg == "_meta" or not isinstance(seq, list):
            continue
        for e in seq:
            if e.get("t") != "text":
                continue
            for ln in e.get("lines", []):
                out += TOKEN_RE.findall(ln.get("txt", ""))
    return out


if __name__ == "__main__":
    elx = fill(example())
    rest = open_tokens(elx)
    print(f"offene Tokens nach fill: {rest or '— keine'}")
    sys.exit(1 if rest else 0)
