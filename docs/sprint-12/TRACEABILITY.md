# TRACEABILITY — kochfabrik Sprint 12

> Sprint-Schnitt aus [[EPIC-004]] (M4–M7) + [[EPIC-009]] (B1–B3).
> Projekt-weite Abdeckung: `docs/epics/TRACEABILITY.md`.
> **Stand:** 2026-06-10.

## WP → Story (7/7 Sprint-WPs geschnitten)

| WP | Story(s) | Artefakt |
|---|---|---|
| M4 | US-053 + US-054 | backend/routers/*, app.py <200 Z. |
| M5 | US-055 (Bundle-Schicht, ADR-003) + US-056 (Tooling-Split) | engine/scripts/bundle.py, engine/tooling/, TOOLING-SPLIT.md |
| M6 | US-057 | Sim-Gate-DB-Block, ALEMBIC-VERIFY.md |
| M7 | US-059 | CLAUDE.md |
| B1 | US-052 | Host-Cron + BACKUP-CYCLE.md |
| B2 | US-058 (Teil) | RESTORE-RUNBOOK.md §Korpus |
| B3 | US-058 (Teil) | RESTORE-RUNBOOK.md §Proben-Protokoll |

Zusatz (kein WP): US-060 = ADR-002-Konsequenz (Engine-Repo archivieren).

## R-ID → Story

| R-ID | Story | R-ID | Story |
|---|---|---|---|
| R-REF-4 | US-053, US-054, US-056 | R-BAK-1 | US-052 |
| R-REF-3 (Datenpfad) | US-055 | R-BAK-2 | US-058 |
| R-REF-5 | US-059 | R-BAK-3 | US-058 |
| R-REF-1 (Abschluss) | US-060 | R-NF-3 | Boundaries (Never) |
| R-QA-3 (F-E-03, F-S-01) | US-055, US-057 | R-REF-6 | Querschnitt (Routen-Inventar-/Gold-Diffs) |

## Epic-Akzeptanzkriterien → Story

| Kriterium | Story(s) | Stand nach Sprint 12 |
|---|---|---|
| EPIC-004 Nr. 3 (Tests grün/Verhalten gleich) | alle Ketten-Verifies | laufend |
| EPIC-004 Nr. 4 (Alembic sauber, kein rc≠0) | US-057 | erfüllt |
| EPIC-004 Nr. 5 (Docs/Techstack an einem Ort) | US-059 | erfüllt |
| EPIC-009 Nr. 1 (Auto-Zyklus, off-host nachweisbar) | US-052 | erfüllt |
| EPIC-009 Nr. 2 (Volume gesichert/Wiederaufbau dokumentiert) | US-058 | erfüllt |
| EPIC-009 Nr. 3 (Restore-Probe im Runbook) | US-058 | erfüllt |

→ Nach diesem Sprint sind **EPIC-004 und EPIC-009 vollständig** —
beide gehen im Review auf DONE.

## Carry-Over-Abdeckung (aus Sprint 11)

| Item | Story |
|---|---|
| M4–M7 inkl. ADR-003-Bundle-Schicht + Alembic-Verify + Docs | US-053…US-057, US-059 |
| EPIC-009 B1-Zyklus + B3-Restore-Probe | US-052, US-058 |
| Engine-Repo read-only archivieren | US-060 |
| Issue #21 schließen + Footer-Hygiene | ✅ bereits im Review 2026-06-10 erledigt (kein Story-Bedarf) |

**Summe: 7/7 WPs, 10/10 sprint-relevante R-IDs, 6/6 offene
Epic-Kriterien, 4/4 Carry-Over-Items. Nichts verloren.**
