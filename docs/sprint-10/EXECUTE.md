# Sprint 10 — kochfabrik

> Übergabe-Prompt für `/sprint-execute` nach `/clear`.
> Referenzieren mit: @docs/sprint-10/EXECUTE.md

**Pfad:** /Users/janrudat/work/02 AKARA Solutions GmbH/kochfabrik/kochfabrik-studio
**Sprint:** 10 (EPIC-003 — Analyse-Fundament, doc-only)
**Erstellt:** 2026-06-09
**Build:** — (keine Build-Pipeline; doc-only-Sprint)
**Test:** `tools/.venv/bin/python -m pytest backend/tests -q`
(System-Python auf dem Mac hat kein pytest — venv via US-038/US-040)
**Branch-Konvention:** `sprint-10-{slug}`
**Provider:** github (`jantristan-hb/kochfabrik-studio`; gh CLI NICHT
authentifiziert → keine Issues/PRs via CLI; Branches pushen + PR
manuell oder nach `gh auth login`)

## Sprint-Docs

- Stories: `docs/sprint-10/USER-STORIES.md` (Story-Gate + Boundaries)
- Feature-Specs: `docs/sprint-10/FEATURE-BUG-ANALYSE.md`,
  `FEATURE-FONT-REPORT.md`, `FEATURE-ADR-PAKET.md`
- Test-Stubs: `docs/sprint-10/TEST.md` (aus EARS, initial rot)
- Traceability: `docs/sprint-10/TRACEABILITY.md`
- Engine-Repo (read-only): `../pptxgenerator_v2/phase0/`

## Kontext-Kern (jedem Teammate mitgeben)

- Doc-only-Analyse-Sprint: NICHTS fixen, NUR `docs/sprint-10/`,
  `docs/adr/`, `tools/` schreiben. `data/cache/` ist tabu (R-NF-3).
- Finding-Schema: `## F-{S|E}-NN: Titel` + `**Beleg:**` +
  `**Zuordnung:**` + Severity.
- Font-Extraktion: exakte pt aus PyMuPDF-Spans, KEIN Korrekturfaktor;
  Subset-Präfixe (`ABCDEF+`) strippen.
- ADRs: TEMPLATE-ADR aus `~/work/99 Jan/templates/`,
  `status: proposed`, nie selbst auf accepted setzen.

## Waves

### Wave 1 (parallel, 4 Teammates)
| Story | Titel |
|-------|-------|
| US-036 | Bug-Analyse kochfabrik-studio dokumentieren |
| US-037 | Bug-Analyse pptxgenerator_v2-Engine dokumentieren |
| US-038 | Font-Extraktor + font-report.json über 200 PDFs |
| US-040 | Test-Baseline-Inventur schreiben |

### Wave 2 (parallel, nach Wave 1)
| Story | Titel | Blocked-by |
|-------|-------|------------|
| US-039 | FONT-REPORT.md generieren | US-038 |
| US-041 | ADR-001 PPTX-Font-Embedding | US-038 |
| US-042 | ADR-002 Monorepo-Schnitt | US-036, US-037 |
| US-043 | ADR-003 pgbundle vs. Postgres | US-037 |

## Auftrag

/sprint-execute liest diese Datei und führt alle Waves aus.
Agent Teams Modus (Default): Stories einer Wave parallel, jeder
Teammate eigener Worktree (PFLICHT bei paralleler Arbeit).
Sequentiell: `/sprint-execute kochfabrik 10 --sequential`
