# Assembler-Workflow — Angebot → fertiges Deck (End-to-End)

> **Der produktive Lauf.** Eingabe = ein KOCHfabrik-Angebot (PDF oder
> md-Fixture). Ausgabe = ein vollständiges, editierbares KOCHfabrik-
> PPTX im kanonischen Skelett. Hocheffizient: **~0,7 s**, reiner
> Datenbank-/Cache-Workflow, KEINE PDF-Extraktion zur Laufzeit.
> Skript: `phase0/scripts/assemble.py`. Stand 2026-05-19.

## Verifiziertes Beispiel (Risk.Ident)

```
python3 assemble.py "…/AKARA_Muster_Angebote/# 9_062_Risk_Ident GmbH_18_09_2025.pdf" \
        -o phase0/data/assembled_risk_ident.pptx
→ 9 Slides (1 Cover + 3 Food + 4 Frame + 1 Ausstattung) in 0.7s
```

Ergebnis-Deck (exakt das empirische Skelett aus `REPORT-structure.md`):

| # | Slide | Quelle | Mechanik |
|---|---|---|---|
| 1 | RISK.IDENT GMBH 18. SEPTEMBER 2025 | `cover_template` | Text-Swap `{EVENT_TITEL}` ← Kunde+Datum |
| 2 | DEINE CATERING- & EVENT-CREW IM NORDEN | `static_slide` 0.10 | verbatim (golden) |
| 3 | FRÜHSTÜCK | `menu_composition` | ANN ← „EVENT START-UP", Text-Swap Gerichte |
| 4 | LUNCH | `menu_composition` | ANN ← „LUNCH" |
| 5 | KAFFEEPAUSE II | `menu_composition` | ANN ← „KAFFEEPAUSE" |
| 6 | PERSONAL | `static_slide` 0.76 | verbatim (golden) |
| 7 | AUSTATTUNG | `ausstattung_template` | Text-Swap `{LOCATION_AUSSTATTUNG}` ← Ort |
| 8 | WERTSCHÄTZUNG IST DER SCHLÜSSEL | `static_slide` 0.89 | verbatim (golden) |
| 9 | KONTAKT | `static_slide` 1.00 | verbatim (golden, stets letzte) |

## Pipeline (6 Schritte)

1. **Header parsen** → Kunde + Datum + Veranstaltungsort.
   KOCHfabriks eigener Briefkopf (Prisdorf/Peiner Hag/koch-fabrik)
   wird übersprungen → erster echter Kunde (`Risk.Ident GmbH`).
2. **Cover** — `cover_template.elements.json`, `{EVENT_TITEL}` ←
   `<KUNDE> <DATUM>` (Stil/Position bleiben; Hero-Bildslot leer).
3. **Food** — **1 Gemini-Batch-Embed ALLER Gänge** (effizient, nicht
   pro Slide). Pro Gang **1 pgvector-ANN** gegen
   `menu_composition.embedding` → beste kategorie-kohärente
   Komposition → **Text-Swap** der Angebot-Gerichte (Headline/
   Foto-Set/Layout bleiben).
4. **Frame** — `static_slide WHERE is_golden AND inclusion='pflicht'
   AND category<>'COVER'` (Crew/Personal/Wertschätzung/Kontakt),
   verbatim aus dem Cache (kein Swap).
5. **Ausstattung** (bedingt) — `ausstattung_template.elements.json`,
   `{LOCATION_AUSSTATTUNG}` ← Veranstaltungsort (Bildslot leer).
6. **Reihenfolge nach `skel_pos`** (Cover 0.0 → Crew 0.10 → Food-Block
   0.30–0.72 → Personal 0.76 → Ausstattung 0.78 → Wertschätzung 0.89
   → Kontakt 1.00) → Element-JSONs konkatenieren → **1× reconstruct.js**
   → editierbares PPTX.

## Datenbank-Quellen (Source of Truth)

`pptxgen-pg` · localhost:5434 · db `pptxgen` (→
[[reference_pptxgenerator_v2_postgres]]).

| Tabelle | Inhalt | Rolle im Assembler |
|---|---|---|
| `menu_composition` | 1010 kuratierte Food-Slides + `embedding vector(768)`, 296 Module | ANN-Match je Gang + Text-Swap |
| `static_slide` | 16 Zeilen / 6 Kategorien: COVER(T), CREW(B), PERSONAL(B), AUSSTATTUNG(T), WERTSCHÄTZUNG(B), KONTAKT(B); golden + freigegebene Alternativen | Frame verbatim (golden, pflicht) + Template-Anker (tier T) |
| Element-Cache `phase0/data/cache/<slug>/` | extrahierte `elements.json` + Assets je Deck | reine Assembly, **keine** Laufzeit-Extraktion |

Templates (tier T): `cover_template.elements.json` /
`ausstattung_template.elements.json` in `phase0/data/` — je 1 Slide,
Text-Platzhalter + leerer Bild-Slot (Bildgenerator-Projekt später).

## Effizienz (warum „hocheffizient")

- **1** Gemini-Embed-Batch (alle Gänge), kein Re-Embed des Korpus
- **1** DB-Connection: K kleine ANN-Queries (K=#Gänge) + 1 Frame-Query
- nur Cache-Reads, **0** PDF-Extraktion zur Laufzeit
- **1** `reconstruct.js`
→ ~0,7 s (netzwerk-dominiert durch den einen Embed-Call).

## Reproduzieren

```
cd phase0/scripts
python3 assemble.py "<angebot.pdf>" -o <out.pptx>
python3 assemble.py ../fixtures/fiktive_angebote.md --offer Nordlicht -o <out.pptx>
```

Voraussetzungen: `pptxgen-pg` läuft, `menu_composition` + `static_slide`
befüllt (`db_load.py`/`db_embed.py`/`db_load_static.py`/
`build_cover_template.py`/`build_ausstattung_template.py`), Cache warm
(`build_cache.py`). Deterministisch bei unverändertem Stand.

## Grenzen / offen (ehrlich)

- Food-Fotos sind **kategorie-kohärent**, nicht gericht-literal
  („ungefähr", bewusste Vorgabe). Text = Angebot-Gerichte (Swap).
- Cover/Ausstattung Hero-/Bild-Slot leer → späteres
  Bildgenerator-Projekt (eigenes Vorhaben).
- Ausstattung-Text aktuell = Veranstaltungsort; feinere Befüllung aus
  dem „Event Ausstattung"-Block des Angebots = Ausbaustufe.
- Food-Modul-Reihenfolge linear nach Angebot-Reihenfolge im Block
  0.30–0.72 (kanonische Modul-Sortierung = Ausbaustufe).
