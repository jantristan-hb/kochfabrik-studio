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
    import datetime
    MON = ("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
           "August", "September", "Oktober", "November", "Dezember")
    h = datetime.date.today()
    heute = f"{h.day}. {MON[h.month - 1]} {h.year}"
    c = Anthropic(api_key=_key())
    msg = c.messages.create(
        model=MODEL, max_tokens=4000,
        messages=[{"role": "user", "content":
                   "Wandle diese Event-Beschreibung in EIN striktes "
                   "KOCHfabrik-Angebot-JSON (nur JSON). KOCHfabrik-"
                   "typische Positionen/Preise, Sub-Header (is_header) "
                   "+ preisbehaftete Positionen, Zwischensumme je "
                   "Block, Footer NICHT setzen.\n\n"
                   f"HEUTE ist der {heute}. REGELN (strikt):\n"
                   f"- Alle Datumswerte im deutschen Format "
                   f"'T. Monat JJJJ' (z.B. '{heute}'), NIEMALS ISO/"
                   f"JJJJ-MM-TT. Jahre = {h.year} oder später, nie in "
                   f"der Vergangenheit.\n"
                   "- Unbekannte Angaben LEER lassen (\"\"). KEINE "
                   "Platzhalter erfinden — kein 'Max Mustermann', "
                   "keine 'KF-JJJJ-…'-Nummern, keine Fake-Mail/-Tel. "
                   "Nur aus der Beschreibung ableitbare Werte "
                   "ergänzen.\n"
                   "- FELDER: 'kunde' = Firmenname. 'adresse' = "
                   "Postanschrift OHNE die Firma (die steht schon in "
                   "'kunde' — NICHT wiederholen!), Format "
                   "'[Ansprechpartner-Name, ]Straße Nr, PLZ Ort'. "
                   "'veranstaltung.ort' = Event-LOCATION/Venue — "
                   "NICHT die Kundenadresse/-PLZ. 'ansprechpartner' = "
                   "KOCHfabrik-Sachbearbeiter (Name) — NICHT der "
                   "Kunde. Kunden-PLZ/-Ort gehört AUSSCHLIESSLICH in "
                   "'adresse'.\n"
                   "- KALKULATION (KOCHfabrik-Standard, strikt). P = "
                   "Gästezahl (veranstaltung.personen).\n"
                   "  * PERSONAL: je Rolle 1 Position. bezeichnung = "
                   "'<Rolle>*in <von> - <bis> Uhr (<Gesamtstd> Std.)'. "
                   "menge = Personenanzahl dieser Rolle, einzelpreis = "
                   "Stundensatz, gesamt = menge × Schichtstunden × "
                   "einzelpreis. Die '(… Std.)' im Text sind die "
                   "GESAMT-Personenstunden = menge × Schichtstunden "
                   "(NICHT die Schichtlänge!). Beispiel: 5 Personen, "
                   "Schicht 17:00-23:00 (6 Std) → bezeichnung endet "
                   "'(30 Std.)', menge=5, ep=37,50, gesamt=1.125,00. "
                   "Mindestabnahme 5 Std./Mitarbeiter. "
                   "Stundensätze: Serviceleiter*in 46,00 · "
                   "Servicemitarbeiter*in/Barmitarbeiter*in/Food "
                   "Helfer*in 37,50 · Küchenchef*in 60,00 · "
                   "Speisemacher*in 49,00 · Logistiker*in 36,00 · "
                   "Eventmanager*in 54,00. Personalumfang grob aus P "
                   "ableiten (Faustregel ~1 Service je 25 Gäste).\n"
                   "  * PFLICHT-Positionen, IMMER vorhanden, skaliert "
                   "mit P: 'Müllentsorgung pro Person' (menge=P, "
                   "einzelpreis 0,60, gesamt=P×0,60) und "
                   "'Servicepauschale (Geschirr, Besteck, Gläser, "
                   "Servietten, Endreinigung)' (menge=P, einzelpreis "
                   "≈12,90, gesamt=P×einzelpreis). NIE weglassen.\n"
                   "  * LOGISTIK pauschal (menge 1, gesamt=einzelpreis): "
                   "'Logistikpauschale Transporter Hin- und "
                   "Rücktransport' 220,00 (bei LKW 450,00); "
                   "'Küchenequipmentpauschale' ≈800,00.\n"
                   "  * gesamt MUSS arithmetisch stimmen: pauschal → "
                   "gesamt=einzelpreis; pro Person → "
                   "gesamt=menge×einzelpreis; Personal → "
                   "gesamt=menge×Schichtstunden×einzelpreis. "
                   "zwischensumme je Block = Summe der gesamt. KEINE "
                   "Position weglassen oder kürzen.\n\nBeschreibung:\n"
                   + text + "\n\nSchema:\n" + SCHEMA}])
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


def angebot_to_offer_md(d: dict) -> str:
    """Angebot-dict → Offer-md, das assemble.parse_offer_dishes/
    parse_header/parse_location konsumiert (Übergabe Angebots- →
    Präsentationsgenerator, statt Hand-Paste). Pro Positionsblock ein
    `### {Titel}`-Gang; Positionsbezeichnung = Gericht-Zeile,
    Leerzeile trennt. Kategorie-Lock matcht die Gänge gegen den Korpus.
    """
    v = d.get("veranstaltung", {}) or {}
    kunde = (d.get("kunde") or "Kunde").strip()
    anlass = (v.get("anlass") or "Angebot").strip()
    out = [f"## Angebot — {kunde} ({anlass})", "",
           f"| Veranstaltungsdatum | {v.get('datum','')} |",
           f"| Veranstaltungsort | {v.get('ort','')} |", ""]
    for b in d.get("bloecke", []) or []:
        titel = (b.get("titel") or b.get("typ") or "MENÜ").strip()
        pos = [p for p in (b.get("positionen") or [])
               if str(p.get("bezeichnung", "")).strip()]
        if not pos:
            continue
        out.append(f"### {titel}")
        out.append("")
        for p in pos:                       # je Gericht: Name + Leerzeile
            out.append(str(p["bezeichnung"]).strip())
            out.append("")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    main()
