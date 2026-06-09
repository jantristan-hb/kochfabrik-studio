---
id: EPIC-007
title: "Render-Treue-Harness: Rekonstruktion messbar nah am Referenz-PDF"
status: OPEN
created: 2026-06-09
project: kochfabrik-studio
sprints: []
---

# EPIC-007: Render-Treue-Harness

> **Typ:** EPIC. Klammer über Sprints — kein Detail-Spec. `/sprint-plan`
> schneidet die WPs in Stories. Status: `OPEN → IN_PROGRESS → DONE`.

## Beschreibung

Jans Kernanforderung (2026-06-09): „die präsentationen, die wir
generieren, sollen super nah an den pdfs sein. alleine dieses testing
ist nen epic." Heute gibt es keinerlei automatisierte Treue-Messung —
ob eine Rekonstruktion dem Referenz-PDF entspricht, wird per Augenmaß
beurteilt (genau so entstand der `SIZE_K`-Fudge-Faktor).

Dieses Epic baut den Mess- und Regressions-Harness: eine definierte
Treue-Metrik (visuell, Text, Geometrie, Font) pro Slide und Deck,
einen reproduzierbaren Korpus-Lauf über die 200 Referenz-Decks, eine
eingefrorene Baseline mit Regressions-Gate und einen Report mit
Diff-Bildern. **Erst messen, dann verbessern:** Die Font-Arbeit
(EPIC-005) wird gegen diesen Harness abgenommen — ihr Fortschritt
wird als Score-Delta sichtbar statt als Bauchgefühl.

## Scope

### Was drin ist

- **V1** Treue-Metrik definieren: Pixel-/SSIM-Diff (Referenz-PDF-Seite
  vs. gerenderte Rekonstruktion), Text-Diff (Inhalt + Reihenfolge),
  Geometrie-Diff (Element-Positionen/Boxen), Font-Diff (Face + pt) —
  aggregierter Score pro Slide und Deck
- **V2** Korpus-Harness: reproduzierbarer Lauf über die 200
  Referenz-Decks (Stufen: Sample-Set für schnelle Läufe, Voll-Lauf),
  Container-identisches Rendering (gleiche Fonts/soffice wie Prod)
- **V3** Baseline + Regressions-Gate: Ist-Treue einfrieren; Gate
  schlägt fehl, wenn ein Lauf schlechter wird als die Baseline;
  Sample-Gate in der Test-Suite, Voll-Lauf manuell/nightly
- **V4** Treue-Report: Worst-Slides-Ranking, Side-by-Side-Diff-Bilder,
  Score-Trend über Läufe — als HTML/Markdown-Artefakt
- **V5** Abnahme-Integration: EPIC-005-Akzeptanz läuft über den
  Harness (Score-Ziele statt Augenmaß); Doku des Workflows

### Was NICHT drin ist

- Die Treue-**Verbesserungen** selbst (Fonts, Größen) → EPIC-005
- Ziel-Schwellen festlegen ohne Baseline — Zahlen kommen aus der
  ersten Messung, Jan nimmt sie ab (R-FID-5 ❓)
- CI-Infrastruktur allgemein (Lint/Unit-Pipeline) → Gap-Vorschlag
  Delivery, eigenes Thema

## Sprint-Zuordnung (grob)

| Sprint | Scope | Aufwand |
|--------|-------|---------|
| Sprint 13 | V1–V3 (Metrik, Harness, Baseline + Gate) | M |
| Sprint 15 (Teil) | V4–V5 (Report, Abnahme-Integration) | S |

> **Fortschritt:** wird von /sprint-review aktualisiert.

## Akzeptanzkriterien

1. Ein Befehl misst die Treue eines rekonstruierten Decks gegen sein
   Referenz-PDF und liefert einen Score pro Slide + Deck.
2. Der Korpus-Lauf über alle 200 Decks läuft reproduzierbar durch;
   Sample-Lauf ist Teil der Test-Suite.
3. Eine Baseline ist eingefroren; eine künstlich eingebaute
   Verschlechterung (z.B. Font-Substitution) lässt das Gate fehlschlagen.
4. Report zeigt Worst-Slides mit Diff-Bildern; Score-Delta zwischen
   zwei Läufen ist ablesbar.
5. Treue-Schwellen („super nah") sind als Zahlen definiert und von
   Jan abgenommen.

## Referenzen

- **REQUIREMENTS:** R-FID-1, R-FID-2, R-FID-3, R-FID-4, R-FID-5 (❓),
  R-NF-3
- **ADR:** Metrik-/Schwellen-Entscheidung wird als ADR festgehalten
- **Audit:** [[TRACEABILITY]] → WP V1–V5

## Abhängigkeiten

Blockiert von: EPIC-004 (Monorepo, Container-identisches Rendering),
EPIC-003/Q3 (Font-Report als Metrik-Input). Blockiert: EPIC-005-Abnahme
(läuft über V5) — T1–T4 können parallel starten, werden aber gegen den
Harness gemessen.
