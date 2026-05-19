"""US-008 — Angebots-Datenmodell (EPIC-001).

Striktes, JSON-roundtrip-stabiles Schema als Single Source für den
Renderer (Sprint 3) und den Chat (Sprint 5). Bildet alle Felder echter
KOCHfabrik-Angebote ab (Referenz: GEN-2-Muster RAUMKARUSSELL).

Preise sind reine Strukturfelder — KEINE KOCHfabrik-Kalkulationslogik
(Epic Non-Goal). dump(load(x)) == x  (kanonisch, indent=2, utf-8).

Run: python3 -c "from angebot_model import example,dump; print(dump(example())[:120])"
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field


@dataclass
class Position:
    bezeichnung: str
    menge: float = 1
    einzelpreis: float = 0.0
    gesamt: float = 0.0


@dataclass
class Positionsblock:
    typ: str                       # speisen|getraenke|personal|logistik
    titel: str = ""                # Anzeige-Überschrift im PDF
    positionen: list[Position] = field(default_factory=list)
    zwischensumme: float = 0.0


@dataclass
class Veranstaltung:
    anlass: str = ""
    datum: str = ""
    beginn: str = ""
    personen: int = 0
    ort: str = ""
    konzept: str = ""


@dataclass
class Footer:
    """Invarianter KOCHfabrik-Bank-/Standortblock — Defaults = verbatim
    aus echtem Muster, wird beim Rendern unverändert ausgegeben."""
    firma: str = "Die KOCHfabrik GmbH"
    strasse: str = "Peiner Hag 9a"
    plz_ort: str = "25497 Prisdorf"
    standorte: str = ("Planungsfabrik Hamburg · Restaurant "
                      "Goldschätzchen · Speisenmacherei")
    bic: str = "GENODEF1PIN"
    amtsgericht: str = "AG Pinneberg"
    steuernummer: str = "18/298/24168"


@dataclass
class Angebot:
    kunde: str = ""
    adresse: str = ""
    angebots_nr: str = ""
    datum: str = ""
    kundennr: str = ""
    lieferdatum: str = ""
    ansprechpartner: str = ""           # KOCHfabrik-Seite
    veranstaltung: Veranstaltung = field(default_factory=Veranstaltung)
    bloecke: list[Positionsblock] = field(default_factory=list)
    footer: Footer = field(default_factory=Footer)


# ---- (De)Serialisierung — roundtrip-stabil ----
def dump(a: Angebot) -> str:
    return json.dumps(asdict(a), indent=2, ensure_ascii=False)


def _pos(d):
    return Position(**d)


def _blk(d):
    d = dict(d)
    d["positionen"] = [_pos(p) for p in d.get("positionen", [])]
    return Positionsblock(**d)


def load(path: str) -> Angebot:
    d = json.load(open(path, encoding="utf-8"))
    d = dict(d)
    d["veranstaltung"] = Veranstaltung(**d.get("veranstaltung", {}))
    d["bloecke"] = [_blk(b) for b in d.get("bloecke", [])]
    d["footer"] = Footer(**d.get("footer", {}))
    return Angebot(**d)


def example() -> Angebot:
    """Echte RAUMKARUSSELL-Referenz (GEN 2) — Felder + Beispiel-Positionen."""
    return Angebot(
        kunde="RAUMKARUSSELL GmbH",
        adresse="Frau Claudia Kiesel, Ernst-Merck-Straße 12-14, "
                "20099 Hamburg",
        angebots_nr="10182",
        datum="15. Juli 2025",
        kundennr="4502",
        lieferdatum="12.09.2026",
        ansprechpartner="Jule Wiegers",
        veranstaltung=Veranstaltung(
            anlass="Sommerfest Regio Kliniken",
            datum="12. September 2026",
            beginn="19:00 Uhr - 01:00 Uhr",
            personen=500,
            ort="Edelfettwerk, Schnackenburgallee 202, 22525 Hamburg",
            konzept="Street Food"),
        bloecke=[
            Positionsblock(
                typ="speisen", titel="Speisen",
                positionen=[
                    Position("1x Live Cooking/BBQ Station im Beach & "
                             "1 Foodtruck", 1, 0.0, 0.0)],
                zwischensumme=0.0),
            Positionsblock(
                typ="logistik", titel="Logistik & Mobiliar",
                positionen=[
                    Position("Mobiles Grillequipment ab 100 PAX",
                             1, 195.00, 195.00),
                    Position("3 vintage Gerüstbohlen für Ihr Buffet",
                             3, 39.90, 119.70)],
                zwischensumme=314.70),
        ])


if __name__ == "__main__":
    print(dump(example()))
