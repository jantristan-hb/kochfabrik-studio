---
id: EPIC-003
title: "Analyse-Fundament & Entscheidungen (Bugs, Fonts, ADRs)"
status: OPEN
created: 2026-06-09
project: kochfabrik-studio
sprints: []
---

# EPIC-003: Analyse-Fundament & Entscheidungen

> **Typ:** EPIC. Klammer über Sprints — kein Detail-Spec. `/sprint-plan`
> schneidet die WPs in Stories. Status: `OPEN → IN_PROGRESS → DONE`.

## Beschreibung

Phase 0 der Epic-Landschaft aus [[REQUIREMENTS]] (2026-06-09): bevor
refactored oder an der Font-Pipeline gebaut wird, liegen verifizierte
Fakten und getroffene Entscheidungen vor. Das Projekt ist „hart
gevibecoded" — es gibt keine systematische Bug-Inventur, keinen
Font-Report über die 200 Referenz-PDFs und drei offene
Grundsatzentscheidungen (PPTX-Embedding, Monorepo-Schnitt,
pgbundle vs. Postgres), die EPIC-004/005 blockieren.

Doc-only: dieses Epic ändert keinen Produktiv-Code. Output sind
Findings-Dokumente, ein Font-Datenartefakt und ADRs.

## Scope

### Was drin ist

- **Q1** Bug-Analyse kochfabrik-studio (backend/, web/, Dockerfile,
  Deploy-Pfad) — verifizierte, priorisierte Findings mit Beleg/Repro
- **Q2** Bug-Analyse pptxgenerator_v2-Engine (phase0/scripts/,
  spike-pptxgenjs/) — Findings inkl. bekannter Kandidaten
  (SIZE_K-Widerspruch, fehlende Container-Fonts, pg_shim-Bypass)
- **Q3** Font-/Größen-Report über die 200 Referenz-PDFs:
  pt-Histogramme pro Element-Typ (Titel/Body/Bullet), Weights, Farben,
  Wingdings-Glyphen-Inventar — Report + maschinenlesbares JSON
- **Q4** Test-Baseline-Inventur: was die 111 Bestandstests absichern,
  wo die Engine ungetestet ist — Lücken-Liste als Refactoring-Gate
- **Q5** ADRs zu den offenen ❓: PPTX-Font-Embedding ja/nein,
  Monorepo-Schnitt + Schicksal der Alt-Verzeichnisse,
  pgbundle-Shim vs. echtes Postgres

### Was NICHT drin ist

- Fixes der gefundenen Bugs → EPIC-004 (Struktur/Tech-Debt) bzw.
  EPIC-005 (Font-Pipeline)
- Korpus-Änderungen — `data/cache/` ist read-only (R-NF-3)

## Sprint-Zuordnung (grob)

| Sprint | Scope | Aufwand |
|--------|-------|---------|
| Sprint 10 | Q1–Q5 komplett | M |

> **Fortschritt:** wird von /sprint-review aktualisiert.

## Akzeptanzkriterien

1. Findings-Docs für beide Repos existieren; jeder Finding ist
   verifiziert (Beleg/Repro), priorisiert und einem Folge-Epic/WP
   zugeordnet oder begründet verworfen.
2. Font-Report deckt alle 200 PDFs ab (Vollständigkeits-Zähler im
   Report) und liegt zusätzlich maschinenlesbar (JSON) vor.
3. Drei ADRs sind geschrieben und von Jan abgenommen — EPIC-004/005
   sind dadurch entsperrt.
4. Test-Baseline-Doc benennt abgesicherte Bereiche und Lücken;
   EPIC-004 referenziert es als Refactoring-Gate.

## Referenzen

- **REQUIREMENTS:** R-QA-1, R-QA-2, R-QA-3, R-QA-4; klärt R-FONT-6,
  R-FONT-7, R-REF-1 (❓-Anteile), R-NF-2
- **ADR:** entstehen in Q5 (Embedding, Monorepo-Schnitt, pgbundle)
- **Audit:** [[TRACEABILITY]] → WP Q1–Q5

## Abhängigkeiten

Keine (Wurzel). Blockiert: EPIC-004 (braucht Q4 + Q5-ADRs),
EPIC-005 (braucht Q3 + Q5-Embedding-ADR).
