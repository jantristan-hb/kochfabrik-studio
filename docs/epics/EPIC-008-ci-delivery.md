---
id: EPIC-008
title: "CI/Delivery: Tests + Treue-Gate vor jedem Merge"
status: DONE
created: 2026-06-09
completed: 2026-06-15
project: kochfabrik-studio
sprints: [15]
---

# EPIC-008: CI/Delivery

> **Typ:** EPIC. Klammer über Sprints — kein Detail-Spec. `/sprint-plan`
> schneidet die WPs in Stories. Status: `OPEN → IN_PROGRESS → DONE`.

## Beschreibung

Es gibt keine CI: die 111 Tests laufen nur lokal, Coolify deployt
direkt von master. Damit ist jedes Qualitäts-Gate — insbesondere das
Treue-Regressions-Gate aus [[EPIC-007]]/V3 — zahnlos: nichts erzwingt,
dass es vor einem Merge läuft. Dieses Epic zieht eine schlanke
GitHub-Actions-Pipeline ein und schützt master, sodass nur grüne
Stände deployen.

## Scope

### Was drin ist

- **C1** GitHub-Actions-Pipeline: Lint + pytest (Backend + FE-Smoke)
  auf jedem PR und auf master
- **C2** Sample-Treue-Gate in CI: der schnelle Harness-Lauf
  (EPIC-007/V3-Sample-Set) als Pflicht-Check
- **C3** Branch-Protection auf master (PR-Pflicht, grüne Checks)
  + Doku des Delivery-Flows (PR → CI → Merge → Coolify)

### Was NICHT drin ist

- Der Treue-Harness selbst → [[EPIC-007]]
- Staging-Umgebung / Preview-Deploys — bewusst nicht (ein internes
  Kunden-Tool, ein Deploy-Target; bei Bedarf Backlog)
- Release-Versionierung/Changelog-Automatik — Backlog

## Sprint-Zuordnung (grob)

| Sprint | Scope | Aufwand |
|--------|-------|---------|
| Sprint 13 (Teil) | C1 + C3 (Pipeline + Protection) | S |
| Sprint 13 (Teil) | C2 (nach V3 einhängen) | S |

> **Fortschritt:** wird von /sprint-review aktualisiert.

## Akzeptanzkriterien

1. Jeder PR zeigt Lint + Test-Checks; ein roter Check blockiert den
   Merge (Branch-Protection aktiv).
2. Das Sample-Treue-Gate läuft als CI-Check und fängt eine künstlich
   eingebaute Treue-Regression im PR.
3. Delivery-Flow ist dokumentiert; Coolify deployt nur noch
   master-Stände, die durch CI gegangen sind.

## Referenzen

- **REQUIREMENTS:** R-CI-1, R-CI-2, R-CI-3
- **Audit:** [[TRACEABILITY]] → WP C1–C3

## Abhängigkeiten

Blockiert von: EPIC-004/M1 (Monorepo — CI gegen das Ziel-Repo),
EPIC-007/V3 für C2. Blockiert: verlässliche Abnahme aller späteren
Epics (Gate-Enforcement).
