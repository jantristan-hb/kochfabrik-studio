# Sprint 12 — kochfabrik

> Übergabe-Prompt für `/sprint-execute` nach `/clear`.
> Referenzieren mit: @docs/sprint-12/EXECUTE.md

**Pfad:** /Users/janrudat/work/02 AKARA Solutions GmbH/kochfabrik/kochfabrik-studio
**Sprint:** 12 (EPIC-004 M4–M7 + EPIC-009 B1–B3 — schließt BEIDE Epics ab)
**Erstellt:** 2026-06-10
**Build:** `docker build -t kf-studio-sim .`
**Test:** `tools/.venv/bin/python -m pytest backend/tests -q` (Baseline: 112 passed, 0 failed)
**Branch-Konvention:** Wave 1/3: `sprint-12-us{NR}-{slug}` · Code-Kette: EIN Branch `sprint-12-code`
**Provider:** github (gh authentifiziert)

## ⚠️ Sicherheits-Kern (jedem Teammate injizieren)

- **master = Prod-Stand** (Deploy ist manueller Coolify-Trigger, aber
  master bleibt heilig): NIEMALS master pushen. Integration im Review.
- Verhalten strikt erhalten (R-REF-6): Routen-Inventar-Diff + Ranking-
  Gold-Diff sind die Beweise, nicht Bauchgefühl.
- Lokale Wegwerf-Postgres NUR Ports 15432/15433 (nie 5432/5434 —
  5434 ist Jans Build-Korpus-DB!). Prod-DB nie beschreiben.
- Host-Writes NUR die in US-052 explizit gelisteten (cron.d + /data/backups).
- macOS: kein GNU `timeout`; Pfade mit Leerzeichen quoten.

## Story↔Issue-Mapping (VERBINDLICH für Commit-Footer — Learning S11)

| US-052 | US-053 | US-054 | US-055 | US-056 | US-057 | US-058 | US-059 | US-060 |
|--------|--------|--------|--------|--------|--------|--------|--------|--------|
| #33 | #34 | #35 | #36 | #37 | #38 | #39 | #40 | #41 |

## Sprint-Docs

- Stories: `docs/sprint-12/USER-STORIES.md` · Specs: `FEATURE-CODE-ORDNUNG.md`,
  `FEATURE-BACKUP-RESTORE.md`, `FEATURE-PROJEKT-ABSCHLUSS.md`
- Test-Stubs: `docs/sprint-12/TEST.md` (pytest synchron, kein Async-Plugin;
  Fixture `routes_baseline.txt` gehört US-053)
- Traceability: `docs/sprint-12/TRACEABILITY.md`

## Waves

### Wave 1 (parallel, 2 Stränge)
| Issue | Story | Titel | Strang |
|-------|-------|-------|--------|
| #33 | US-052 | Backup-Zyklus auf Host (cron + Rotation + Pull) | eigener Branch |
| #34 | US-053 | Router auth + bildgenerator extrahieren | Kette `sprint-12-code` |

### Code-Kette (SEQUENTIELL, ein Agent, Branch `sprint-12-code`)
| Issue | Story | Titel | Blocked-by |
|-------|-------|-------|------------|
| #35 | US-054 | Router angebot + praesentation (app.py <200 Z.) | US-053 |
| #36 | US-055 | Eine Bundle-Schicht (ADR-003) | US-054 |
| #37 | US-056 | Engine-Tooling-Split | US-055 |
| #38 | US-057 | Alembic-Container-Abnahme (Sim-Gate-DB-Block) | US-056 |

### Wave 3 (parallel, nach Kette)
| Issue | Story | Titel | Blocked-by |
|-------|-------|-------|------------|
| #39 | US-058 | Restore-Probe + Runbook | US-052, US-056 |
| #40 | US-059 | Projekt-CLAUDE.md | US-057 |
| #41 | US-060 | Engine-Repo archivieren | US-056 |

> Wave-3-Hinweis: US-059 dokumentiert den KETTEN-ENDSTAND — Inputs via
> `git show origin/sprint-12-code:<pfad>` falls Worktree von master zieht;
> besser: Worktree direkt von `origin/sprint-12-code` stacken (GESTACKT).
> US-058/060 sind repo-arm (docs/ops bzw. extern) — von master, Inputs
> (Tooling-Pfade) via git show aus der Kette.

## Auftrag

/sprint-execute: Wave 1 = 2 parallele Agents; danach Kette sequentiell
(Agent-Wiederverwendung wie Sprint 11); End-Wave 3 parallel.
Integration + EPIC-004/009-DONE im /sprint-review (Deploy danach
manuell triggern + live_verify — siehe CUTOVER-RUNBOOK-Korrektur).
