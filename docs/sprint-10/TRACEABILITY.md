# TRACEABILITY — kochfabrik Sprint 10

> Sprint-Schnitt aus [[EPIC-003]] (Q1–Q5). Projekt-weite Abdeckung:
> `docs/epics/TRACEABILITY.md`. **Stand:** 2026-06-09.

## WP → Story (5/5 WPs geschnitten)

| WP | Story(s) | Artefakt |
|---|---|---|
| Q1 | US-036 | FINDINGS-STUDIO.md |
| Q2 | US-037 | FINDINGS-ENGINE.md |
| Q3 | US-038 + US-039 | font_report.py, font-report.json, FONT-REPORT.md |
| Q4 | US-040 | TEST-BASELINE.md |
| Q5 | US-041 + US-042 + US-043 | ADR-001/002/003 (proposed) |

## R-ID → Story (Sprint-relevant)

| R-ID | Story | R-ID | Story |
|---|---|---|---|
| R-QA-1 | US-036, US-037 | R-FONT-6 ❓ | US-041 (ADR-Vorlage) |
| R-QA-2 | US-038, US-039 | R-REF-1 ❓ | US-042 (ADR-Vorlage) |
| R-QA-3 | US-036, US-037 | R-REF-3 | US-043 (ADR-Vorlage) |
| R-QA-4 | US-040 | R-NF-2 | US-042 (Migrationsplan im ADR) |
| R-NF-3 | Boundaries (Never: cache schreiben) | | |

## Epic-Akzeptanzkriterien → Story (4/4)

| EPIC-003-Kriterium | Story(s) |
|---|---|
| 1 — Findings verifiziert, priorisiert, zugeordnet | US-036, US-037 |
| 2 — Font-Report 200/200 + JSON | US-038, US-039 |
| 3 — 3 ADRs geschrieben (Abnahme: Jan, nach Sprint) | US-041, US-042, US-043 |
| 4 — Test-Baseline-Doc als Refactoring-Gate | US-040 |

## Offen markiert

- ADR-Abnahme (`proposed → accepted`) ist bewusst NICHT Teil des
  Sprints — Jans Entscheidung, Gate vor EPIC-004/M1 und EPIC-005.

## Erfüllungs-Stand (Review 2026-06-09)

Alle 8 Stories DONE (PRs #11–#18), alle Verifies gegen die
Remote-Branches re-geprüft (exit 0), Pitfall-Gegenprobe: kein Branch
ändert Produktiv-Code. 5/5 WPs geliefert; ADR-Abnahme bleibt der
einzige offene Punkt (siehe oben).

**Summe: 5/5 WPs, 9/9 sprint-relevante R-IDs, 4/4 Kriterien
zugeordnet. Nichts verloren.**
