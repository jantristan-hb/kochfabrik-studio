"""US-017 — Muster→Angebot-Parser.

Echtes KOCHfabrik-Angebots-PDF → `Angebot`-Modell. Für den Round-Trip
des Pixel-Diff-Gates (US-016): Muster → parse → render → diff vs
Original. Kopf/Veranstaltung via kf_classify + compose_offer (bewährt),
Positionsblöcke per Spalten-Regex. Footer = invariante Defaults.

Heuristisch — Rest-Ungenauigkeiten macht das Pixel-Gate (US-016)
sichtbar/kalibrierbar; das ist dessen Zweck.

Run: python3 -c "import angebot_parse as A; a=A.parse('<muster.pdf>'); print(a.kunde, a.veranstaltung.anlass, len(a.bloecke))"
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# US-056: Tooling lebt jetzt unter engine/tooling/ — Runtime-Module
# (engine/scripts/) zusätzlich auf den Pfad (KEINE Logikänderung).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "scripts"))
from kf_classify import pdf_text, extract_event, strip_footer    # noqa
from angebot_model import (Angebot, Veranstaltung, Positionsblock,  # noqa
                           Position)

_FIRMA = re.compile(r"\b(GmbH|AG|KG|GbR|e\.?V\.?|mbH|SE)\b")
_KF = re.compile(r"(?i)kochfabrik|koch-fabrik|prisdorf|peiner hag")


def _kunde(raw: str) -> str:
    """Erste Firmen-Zeile die NICHT KOCHfabrik ist (Empfänger).
    pdftotext -layout hängt die rechte Metadaten-Spalte an → nur das
    linke Segment vor dem Großspalt nehmen."""
    for ln in raw.splitlines():
        seg = re.split(r"\s{2,}", ln.strip())[0].strip()
        if (seg and _FIRMA.search(seg) and not _KF.search(seg)
                and len(seg) < 60):
            return seg
    return ""

# Positionszeile: Bezeichnung  Menge  Einzelpreis  Gesamt (rechtsbündig)
ROW = re.compile(
    r"^\s*(?P<bez>.+?)\s{2,}(?P<menge>\d+(?:,\d+)?)\s+"
    r"(?P<ep>\d{1,3}(?:\.\d{3})*,\d{2})\s+"
    r"(?P<ges>\d{1,3}(?:\.\d{3})*,\d{2})\s*$")
HEADCOLS = re.compile(r"Menge\s+Preis\s*netto\s+Gesamt", re.I)
SUM = re.compile(r"^\s*(\d{1,3}(?:\.\d{3})*,\d{2})\s*$")
SKIP = re.compile(r"(?i)Veranstaltungs|Cateringkonzept|Angebots\s*Nr|"
                  r"Kundennr|Lieferdatum|Ansprechpartner|^Projekt:|"
                  r"^ANGEBOT$|Dieser Preis gilt|^\s*$")


def _eur(s):
    return float(s.replace(".", "").replace(",", "."))


def _val(text, label):
    m = re.search(rf"(?i){label}\s*:?\s*(.+?)\s*$", text, re.M)
    return m.group(1).strip() if m else ""


def parse(path: str) -> Angebot:
    raw = pdf_text(path)
    txt = strip_footer(raw)
    ev = extract_event(raw)
    a = Angebot(
        kunde=_kunde(raw),
        adresse="",
        angebots_nr=_val(txt, r"Angebots\s*Nr\.?"),
        datum=_val(txt, r"Datum\.?"),
        kundennr=_val(txt, r"Kundennr\.?"),
        lieferdatum=_val(txt, r"Lieferdatum"),
        ansprechpartner=_val(txt, r"Ansprechpartner"),
        veranstaltung=Veranstaltung(
            anlass=ev["anlass"], datum=ev["datum"], beginn="",
            personen=int(re.sub(r"\D", "", ev["personen"]) or 0),
            ort=ev["ort"],
            konzept=ev["konzept"]),
        bloecke=[])

    # Positionsblöcke: jeder Gold-Header (… Menge Preis netto Gesamt)
    # öffnet einen Block; Titel = Wort vor "Menge"; Zeilen bis nächster
    # Header / Summen-Zeile.
    lines = txt.splitlines()
    blk = None
    for ln in lines:
        s = ln.strip()
        if HEADCOLS.search(ln):
            m = re.match(r"\s*([A-Za-zÄÖÜäöü&/ ]+?)\s{2,}Menge", ln)
            titel = (m.group(1).strip() if m else "Positionen")
            blk = Positionsblock(typ=titel.lower().split()[0]
                                 if titel else "pos", titel=titel)
            a.bloecke.append(blk)
            continue
        if blk is None or not s:
            continue
        mrow = ROW.match(ln)
        if mrow:
            blk.positionen.append(Position(
                mrow["bez"].strip(),
                float(mrow["menge"].replace(",", ".")),
                _eur(mrow["ep"]), _eur(mrow["ges"])))
        elif SUM.match(s):
            blk.zwischensumme = _eur(s)
            blk = None                       # Block endet bei Summe
        elif not SKIP.search(s) and len(s) > 3:
            blk.positionen.append(Position(s, is_header=True))
    a.bloecke = [b for b in a.bloecke if b.positionen]
    return a


if __name__ == "__main__":
    a = parse(sys.argv[1])
    print(f"Kunde={a.kunde!r} Anlass={a.veranstaltung.anlass!r} "
          f"Blöcke={len(a.bloecke)} "
          f"Positionen={sum(len(b.positionen) for b in a.bloecke)}")
