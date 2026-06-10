# TRACEABILITY — kochfabrik Sprint 11

> Sprint-Schnitt aus [[EPIC-004]] (M1–M3) + Cross-Epic-Pull
> [[EPIC-009]]/B1. Projekt-weite Abdeckung: `docs/epics/TRACEABILITY.md`.
> **Stand:** 2026-06-09.

## WP → Story (4/4 Sprint-WPs geschnitten)

| WP | Story(s) | Artefakt |
|---|---|---|
| M1 | US-045 (Vorbedingung F-E-10) + US-046 (Gate) + US-047 + US-048 | engine/ subtree, repo-interne Pfade, vendor.sh weg |
| M2 | US-048 (Teil: vendor.sh) + US-049 + US-050 | Dockerfile, .dockerignore, tools/sim_gate.sh |
| M3 | US-051 | CUTOVER-RUNBOOK.md, tools/live_verify.sh (Cutover selbst: /sprint-review nach Sim-Gate) |
| B1 (EPIC-009, vorgezogen) | US-044 | Off-Host-Dump + Volume-Inventar, BACKUP-VERIFY.md |

## R-ID → Story (Sprint-relevant)

| R-ID | Story | R-ID | Story |
|---|---|---|---|
| R-REF-1 | US-047, US-048 | R-NF-2 | US-044, US-049, US-050, US-051 |
| R-REF-4 (Teil) | US-048 | R-BAK-1 (Teil, Erst-Dump) | US-044 |
| R-REF-6 | US-045, US-046 (Gate), US-048 | R-BAK-2 (Teil, Inventar) | US-044 |
| R-QA-3 (Fixes F-E-10, F-S-01-Vorauss., E2) | US-045, US-046, US-049 | R-QA-4 | US-046 |
| R-NF-1 | US-050 (graceful-Pfade im Gate) | R-NF-3 | Boundaries (Never) |

Offen markiert: R-BAK-1/2 vollständig (Zyklus + Restore-Probe) →
EPIC-009 Sprint 12; R-REF-2/3/5 + M4–M7 → Sprint 12.

## Epic-Akzeptanzkriterien (EPIC-004) → Story

| Kriterium | Story(s) | Stand nach Sprint 11 |
|---|---|---|
| 1 — Ein Repo, kein vendor.sh, repo-interne Pfade | US-047, US-048 | erfüllt (nach Cutover) |
| 2 — Coolify-Deploy aus Monorepo grün | US-049, US-050, US-051 + Cutover im Review | erfüllt nach M3-Verify |
| 3 — Tests grün / Verhalten gleich | US-046 (Netz) + alle Verifies | laufend gesichert |
| 4 — Alembic sauber (kein rc=255) | US-049 (alembic.ini ins Image — Voraussetzung) | TEILWEISE — voller M6-Fix Sprint 12 |
| 5 — Docs/Techstack an einem Ort | — | Sprint 12 (M7) |

## Session-Absprachen

| # | Absprache (2026-06-09) | WP |
|---|---|---|
| 1 | „mach weiter, solang es sicher und SOTA is" → ADR-Abnahme delegiert, Sicherheits-Gates verpflichtend | Boundaries + US-044/050/051 |
| 2 | Backup VOR Cutover (vorgezogen aus EPIC-009/B1) | US-044 (im EPIC-009-Doc annotiert) |
| 3 | Alt-Ordner nicht anfassen (Jan-Entscheid steht aus) | Boundary (Never) |
| 4 | Planen heute, Execute morgen | EXECUTE.md liegt bereit, kein Auto-Start |

**Summe: 4/4 WPs, 11/11 sprint-relevante R-IDs, 5/5 Kriterien
adressiert (2 bewusst teilweise → Sprint 12). Nichts verloren.**

## Erfüllungs-Stand (Review 2026-06-10)

8/8 Stories DONE. Alle EARS-Verifies grün (Agents + Lead-Re-Check);
Sim-Gate grün @ f1f8fa1 (Delta bis c3c67a8 doc-only), Live-Verify
Pre-Cutover gegen Prod grün. Cutover ausgeführt im Review (PR #31).
Offen → Sprint 12: M4–M7, B1-Zyklus + B3-Restore-Probe,
Engine-Repo read-only archivieren (ADR-002-Konsequenz).
