"""Sprint 5 / AK3 — Angebotsgenerator-Chat: freie Event-Beschreibung
→ Angebot-JSON (LLM) → pixelgenaues KOCHfabrik-Angebots-PDF.

Schließt den Epic-Loop: Chat rein → fertiges Angebots-PDF raus, ohne
manuelle Nacharbeit. Single-Shot (interaktiv, kein Batch).

Run: python3 angebot_chat.py "Sommerfest, 120 Gäste, Hamburg, Street Food, 5. Juli" -o /tmp/a.pdf
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from angebot_model import Angebot, Veranstaltung, Positionsblock, \
    Position, Footer, dump                                        # noqa
from angebot_render import render_pdf                             # noqa
from gen_fiktiv import MODEL, SCHEMA, _key, _extract              # noqa


def beschreibung_zu_angebot(text: str) -> Angebot:
    from anthropic import Anthropic
    c = Anthropic(api_key=_key())
    msg = c.messages.create(
        model=MODEL, max_tokens=4000,
        messages=[{"role": "user", "content":
                   "Wandle diese Event-Beschreibung in EIN striktes "
                   "KOCHfabrik-Angebot-JSON (nur JSON). Fehlende "
                   "Angaben plausibel ergänzen, KOCHfabrik-typische "
                   "Positionen/Preise, Sub-Header (is_header) + "
                   "preisbehaftete Positionen, Zwischensumme je Block, "
                   "Footer NICHT setzen.\n\nBeschreibung:\n" + text
                   + "\n\nSchema:\n" + SCHEMA}])
    d = json.loads(_extract("".join(b.text for b in msg.content
                                    if b.type == "text")))
    v = d.get("veranstaltung", {})
    bl = []
    for b in d.get("bloecke", []):
        bl.append(Positionsblock(
            typ=b.get("typ", "pos"), titel=b.get("titel", ""),
            positionen=[Position(**{k: p[k] for k in
                        ("bezeichnung", "menge", "einzelpreis",
                         "gesamt", "is_header") if k in p})
                        for p in b.get("positionen", [])],
            zwischensumme=b.get("zwischensumme", 0.0)))
    return Angebot(
        kunde=d.get("kunde", ""), adresse=d.get("adresse", ""),
        angebots_nr=d.get("angebots_nr", ""), datum=d.get("datum", ""),
        kundennr=d.get("kundennr", ""),
        lieferdatum=d.get("lieferdatum", ""),
        ansprechpartner=d.get("ansprechpartner", ""),
        veranstaltung=Veranstaltung(
            anlass=v.get("anlass", ""), datum=v.get("datum", ""),
            beginn=v.get("beginn", ""),
            personen=int(v.get("personen", 0) or 0),
            ort=v.get("ort", ""), konzept=v.get("konzept", "")),
        bloecke=bl, footer=Footer())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("beschreibung")
    ap.add_argument("-o", "--out", default="angebot.pdf")
    ap.add_argument("--json", help="Angebot-JSON zusätzlich ablegen")
    a = ap.parse_args()
    try:
        ang = beschreibung_zu_angebot(a.beschreibung)
        if a.json:
            open(a.json, "w").write(dump(ang))
        out = render_pdf(ang, a.out)
    except Exception as e:
        print(f"FEHLER: {e}")
        sys.exit(1)
    print(f"OK: {out}  ({os.path.getsize(out)} bytes) | "
          f"Kunde={ang.kunde!r} Anlass={ang.veranstaltung.anlass!r}")


if __name__ == "__main__":
    main()
