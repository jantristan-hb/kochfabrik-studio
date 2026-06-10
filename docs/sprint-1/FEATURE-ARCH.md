# FEATURE-ARCH.md — pptxgenerator_v2 · Sprint 1 (Engine Phase A)

## Scope

| Key | Wert |
|---|---|
| **Projekt** | pptxgenerator_v2 |
| **Typ** | CLI / Konverter-Engine |
| **Ein-Satz** | KOCHfabrik-PDF → faithful, element-für-element editierbares PPTX |
| **Zielgruppe** | intern (später: Prompt/Formular-getriebene Präsentationsgenerierung) |
| **Kern-Constraint** | 1:1 faithful (reproduzieren, nicht verschönern); editierbares natives PPTX |

### Goals

| # | Ziel | Metrik | Prio |
|---|---|---|---|
| G1 | Beliebiges PDF konvertierbar (kein Hardcode) | `convert.py <pdf> <pptx>` läuft für ≠Bechtle | Must |
| G2 | Ein-Lauf-Orchestrierung | 0 manuelle bash-Schritte | Must |
| G3 | Batch über Ordner robust | 1 kaputtes Deck killt Batch nicht | Must |
| G4 | Korpus-Fehlerrate gemessen | REPORT-phase-b.md liegt vor | Must |

### Non-Goals (explizit)

- Phase C: Korpus-weite Kalibrier-/Regel-Härtung — erst nach US-006-Daten.
- Prompt/Formular-Eingabe statt PDF — spätere Phase (Architektur-Richtung notiert).
- „Slide als wiederverwendbarer pptxgenjs-Baustein embedden" — spätere Phase.
- GUI, Tests-Framework, CI — kein ROI im Engine-Bootstrap.

## Architecture Overview

```
                 convert.py  (Orchestrator + CLI/Batch + Report)
                      │
   ┌──────────────────┼───────────────────────────────────────┐
   ▼                  ▼                  ▼                      ▼
pdftohtml -xml    pdfimages         extract_logos.py +     extract.py (pdfminer)
(Bild-Assets)   (-list/-png)      apply_official_logo.py   → elements.json
                                  → logos.json                   │
                                                                 ▼
                                                  reconstruct.js + lib/
                                                  {logos,text,frame,overrides}.js
                                                          │
                                                          ▼
                                            natives, editierbares .pptx
                                       (overrides.json: Hand-Korrektur je Deck)
```

Bestehende, **verifizierte** Bausteine (Spike) bleiben unverändert in ihrer
Kernlogik — Sprint 1 macht sie nur parametrisch, orchestriert, robust.

## Data Model (zentrale Artefakte)

- `elements.json` — `{ "<page>": [ {t:rect|image|text, x,y,w,h, ...} ] }` in
  Paint-Order (+ Seitenmaß).
- `logos.json` — `{ "<src>": "<transparente/offizielle Fassung>" }`.
- `overrides.json` — `{ "<deckKey>": { "<page>": [ {match, set} ] } }`.
- `convert-report.json` — `[ {deck, stage, status, error?} ]` (Batch/Skip).

## Risiken (Sprint-relevant)

| Risiko | Mitigation |
|---|---|
| pdfminer Paint-Order/Farbe variiert bei alten Templates | US-006 misst; Phase C fixt |
| Logo-aHash False-Positives auf fremden Badges | US-006 misst Fehlerklasse „Logo" |
| Bild↔Quelle-Reihenfolge bricht (pdfminer ≠ pdftohtml) | US-004 Fallback + US-006 Messung |
| Override-Key-Kollision über Decks | US-005: stabiler Hash/Basename |

## Vision-Alignment

**Adressierte Stufe:** Engine-Bootstrap — der PDF→Element→pptxgenjs-Konverter
ist die Bauteil-Quelle für die spätere Prompt/Formular-getriebene
Präsentationsgenerierung. **Kern-Loop-Schritt:** „Rohinput → editierbares
Deck". **Nächste Iteration (nach Phase B):** Phase C (Korpus-Härtung), danach
Eingabe-Kapselung (Prompt statt Kunden-PDF), Slide-Bausteine wiederverwendbar.
