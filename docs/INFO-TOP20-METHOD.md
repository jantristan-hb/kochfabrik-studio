# Methode: Die 20 absolut häufigsten mehrfach-vorkommenden Info-Slides

> Exakt reproduzierbare Doku zu `phase0/data/info_top20.pptx`.
> Skript: `phase0/scripts/build_info_top20.py`. Stand 2026-05-19.
> Datenbasis: warmer Element-Cache aller 199 Korpus-Decks.

## Korrektur-Historie (wichtig)

**v1 (verworfen): Kategorie = Headline (größtes Text-Element).** Bug:
buckelt verschiedene event-spezifische Einzel-Slides unter dieselbe
Headline → Fake-Frequenzen. Beweis (von Jan gefunden): Headline
`VERANSTALTUNG INKL. AUF- & ABBAU` zeigte „7 Decks", war aber **7
distinkte Volltexte je 1×** (Personal-/Kostentabellen mit
event-spezifischen Uhrzeiten). → Headline als Identität ist falsch.

**v2 (gültig): Identität = exakter normalisierter Volltext.** Nur so
ist „häufig" = wirklich derselbe Slide. Event-spezifisches fällt
automatisch auf count 1 und damit raus.

## Definitionen (exakt)

- **Slide-Identität** = gesamter Text der Seite (alle Text-Run-`txt`),
  Whitespace kollabiert, UPPER.
- **Absolute Häufigkeit** = Anzahl Vorkommen genau dieses Volltexts im
  Korpus (Slide-Zählung, nicht Deck-Distinct).
- **Mehrfach** = Häufigkeit ≥ 2 (Singletons = event-spezifisch → raus).
- **Repräsentant** = erste Fundstelle `(deck,page)` (deterministisch).

## Filter (vor dem Ranking)

1. `page == 1` → Cover/Titel raus (datengetrieben pro Event).
2. `(deck,page)` ∈ `menu_composition` → Food raus (eigener Pfad).
3. Volltext < 12 Zeichen → text-arm raus.
4. Häufigkeit < 2 → raus (nur mehrfach-vorkommende).
   **Kein** Headline-/JUNK-Regex-Filter (würde z. B. „GMBH" in der
   KONTAKT-Seite treffen; count≥2 trennt Event-spezifisches sauber).

## Auswahl & Reihenfolge

1. Alle verbleibenden Seiten nach exaktem Volltext gruppieren.
2. Gruppen mit count ≥ 2, **absteigend nach absoluter Häufigkeit**
   sortieren, **Top 20**.
3. pptx in **genau dieser Reihenfolge** (häufigster Slide zuerst).
4. Slide-Elemente je Repräsentant aus dem Cache → `reconstruct.js`.
   Notiz je Slide `deck::page`; Manifest = `{rank,count,type,deck,page}`.

## Ergebnis (Deck-Reihenfolge = Häufigkeit absteigend)

| Rang | Count | Typ |
|---|---|---|
| 1 | 155 | WERTSCHÄTZUNG IST DER SCHLÜSSEL |
| 2 | 155 | KONTAKT (Die KOCHfabrik GmbH …) |
| 3 | 150 | DEINE CATERING- & EVENT-CREW IM NORDEN (seit 15 Jahren) |
| 4 | 144 | PERSONAL (unsere Crew besteht aus echten Eventrockstars) |
| 5 | 11 | LOUNGE FACTORY |
| 6–11 | 6 | ALLGEMEINE GESCHÄFTSBEDINGUNGEN + Klausel-Folgeseite (AGB, mehrere angebot-Decks) |
| 12 | 5 | WERTSCHÄTZUNG (älteres Phrasing „unser Anspruch ist") |
| 13–14 | 4 | AGB (weitere) |
| 15 | 3 | EURE VISION UNSER NERVENKITZEL |
| 16 | 3 | CRAZY KITCHEN DESSERT (Food-Leak, s. Caveat) |
| 17 | 3 | KONTAKT (Variante) |
| 18 | 3 | DEINE CATERING- & EVENT-CREW (Variante „seit über 15") |
| 19–20 | 3 | AGB (weitere) |

**Scharfe Kante:** nur 4 Typen ≥144 (Big-4 = das echte Pflicht-
Skelett), danach Absturz auf ≤11. Ab Rang 5 = seltener wiederkehrend
(Lounge Factory, AGB) bzw. Phrasing-Varianten der Big-4.

## Bekannte Caveats (ehrlich)

- **Food-Leakage:** Food/Info-Split via `menu_composition` (1010
  *kuratierte*). Nicht-kuratierte Food-Slides (z. B. `CRAZY KITCHEN
  DESSERT`) leaken in den Info-Komplement. Schärferer Split offen.
- **AGB-Seiten** sind legitime Mehrfach-Slides (Standard-Terms), aber
  inhaltlich kein „Präsentations-Frame" — je nach Zweck filterbar.
- **Big-4 Tier-Unterschied** (Session-Befund): KONTAKT/WERTSCHÄTZUNG =
  byte-identisch (verbatim nutzbar); PERSONAL/CREW = Text/Layout fix,
  Fotos event-spezifisch (→ Hand-Kür der schönen Foto-Instanz).

## Reproduzieren

```
cd phase0/scripts
python3 build_info_top20.py --n 20
# → phase0/data/info_top20.pptx (+ .manifest.json)
```
Deterministisch bei unverändertem Cache + `menu_composition`.
