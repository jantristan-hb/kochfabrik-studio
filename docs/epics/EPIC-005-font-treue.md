---
id: EPIC-005
title: "Font-Treue: exakte Schriftarten + Größen aus den Referenz-PDFs"
status: OPEN
created: 2026-06-09
project: kochfabrik-studio
sprints: []
---

# EPIC-005: Font-Treue

> **Typ:** EPIC. Klammer über Sprints — kein Detail-Spec. `/sprint-plan`
> schneidet die WPs in Stories. Status: `OPEN → IN_PROGRESS → DONE`.

## Beschreibung

Generierte Präsentationen sollen **exakt** die Schriftarten und
Schriftgrößen der 200 Referenz-PDFs tragen. Entschieden (2026-06-09):
**Open Sans ist kanonisch**; Ausreißer-Fonts (Arial/Calibri/Helvetica/
Candara, ~15% der PDFs) werden normalisiert.

Ist-Zustand der Pipeline (PDF → extract.py/pdfminer → elements.json →
reconstruct.js/pptxgenjs → PPTX → soffice): Schriftgrößen kommen aus
der Glyph-Bbox der ersten Glyphe pro Zeile und werden mit einem visuell
kalibrierten Fudge-Faktor `SIZE_K = 0.78` korrigiert; Weight/Italic
werden nur pro Zeile gesampelt; im Docker-Image fehlt Open Sans
komplett (nur DejaVu + Liberation) — LibreOffice substituiert beim
PDF/PNG-Render. Dieses Epic ersetzt Heuristik durch exakte Extraktion
und macht Font-Treue dauerhaft testbar.

## Scope

### Was drin ist

- **T1** Exakte pt-Größen-Extraktion (z.B. PyMuPDF-Spans /
  Text-Rendering-Matrix statt pdfminer-Glyph-Bbox); `SIZE_K`,
  `LINE_K`, `Y_OFF_K`-Heuristiken eliminieren bzw. exakt herleiten
- **T2** Run-genaue Weight/Style-Treue: Bold/Italic/ExtraBold pro
  Text-Run statt erster Glyphe pro Zeile; Open-Sans-Face-Mapping
  vervollständigen (inkl. Semibold/Light)
- **T3** Open-Sans-Fontdateien ins Docker-Image + Render-Verify:
  kein Substitutions-Fallback bei soffice-Renders
- **T4** Wingdings-/Bullet-Glyphen-Mapping (Inventar aus EPIC-003/Q3)
- **T6** Bestands-Preview-PNGs im Coolify-Volume re-rendern
  (`render_previews.py --force`) nach T1–T3

### Was NICHT drin ist

- Treue-Messung/Regressions-Gate (ehem. T5) → [[EPIC-007]]
  Render-Treue-Harness; die Abnahme dieses Epics läuft darüber
- PPTX-Font-Embedding für Kunden-Rechner — nur falls das ADR aus
  EPIC-003/Q5 es fordert; dann eigenes Folge-Epic
- Layout-/Positions-Treue jenseits der Schrift → wird vom Harness
  (EPIC-007) gemessen; Verbesserungen sind Folge-Arbeit

## Sprint-Zuordnung (grob)

| Sprint | Scope | Aufwand |
|--------|-------|---------|
| Sprint 14 | T1–T4 (Font-Kern, gemessen am Harness aus EPIC-007) | M |
| Sprint 15 (Teil) | T6 (Preview-Re-Render) | S |

> **Fortschritt:** wird von /sprint-review aktualisiert.

## Akzeptanzkriterien

1. Rekonstruierte Decks verwenden ausschließlich Open-Sans-Faces;
   pdffonts auf dem gerenderten PDF zeigt keine Substitutions-Fonts.
2. Extrahierte pt-Größen stimmen exakt mit den Referenz-PDFs überein
   (Abgleich gegen den Q3-Report) — kein globaler Korrekturfaktor
   mehr im Code.
3. Mischformatierung innerhalb einer Zeile bleibt erhalten
   (Run-genauer Roundtrip-Test).
4. Treue-Score (EPIC-007-Harness) verbessert sich messbar gegenüber
   der Baseline; Font-Diff-Anteil der Metrik ist null Substitutionen.
5. Slidesuche-Previews im Volume sind mit korrekten Fonts re-rendert.

## Referenzen

- **REQUIREMENTS:** R-FONT-1, R-FONT-2, R-FONT-3, R-FONT-4, R-FONT-5,
  R-FONT-6 (ADR-abhängig), R-FONT-7, R-NF-3
- **ADR:** PPTX-Embedding (aus EPIC-003/Q5)
- **Audit:** [[TRACEABILITY]] → WP T1–T4, T6 (Treue-Gate: [[EPIC-007]])

## Abhängigkeiten

Blockiert von: EPIC-003 (Q3-Report, Q5-Embedding-ADR), EPIC-004
(Monorepo — Font-Arbeit nur einmal, nicht doppelt im Vendoring),
EPIC-007/V1–V3 (Abnahme läuft über den Harness — erst messen, dann
verbessern). Blockiert: EPIC-006/D3 nur indirekt (Builder liefert
verbatim Slides, profitiert von T6-Previews).
