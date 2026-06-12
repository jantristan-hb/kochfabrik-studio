# Sprint 15 — kochfabrik-studio (CI/Delivery + Treue-Harness + Korpus-Batches)

> Übergabe-Prompt für `/sprint-execute` nach `/clear`.
> Referenzieren mit: @docs/sprint-15/EXECUTE.md

**Pfad:** /Users/janrudat/work/02 AKARA Solutions GmbH/kochfabrik/kochfabrik-studio
**Sprint:** 15 · **Erstellt:** 2026-06-12 · **Provider:** github
**Test:** `tools/.venv/bin/python -m pytest backend/tests -q` (Baseline 213/5skip)
**Gates:** sim_gate.sh · NEU im Sprint: CI-Pipeline + fidelity-Check
**Branch-Konvention:** Ketten `sprint-15-ci` / `sprint-15-treue`, Lead `sprint-15-us078-batches`

## Sprint-Docs

- Stories: `docs/sprint-15/USER-STORIES.md` (Story-Gate + Boundaries!)
- Specs: `FEATURE-CI-DELIVERY.md` (009) · `FEATURE-TREUE-HARNESS.md` (016)
- Test-Stubs: `docs/sprint-15/TEST.md` — Ownership: test_sprint15.py=CI-Kette · test_sprint15_fidelity.py=Treue-Kette
- Traceability: `docs/sprint-15/TRACEABILITY.md`

## Story↔Issue-Tabelle (VERBINDLICH für `Closes #N`)

| Story | Issue | Titel | Strang |
|-------|-------|-------|--------|
| US-078 | #83 | Voll-Korpus-Batches + Sync + Deploy | **LEAD** (kein Agent!) |
| US-079 | #84 | GitHub-Actions-Pipeline | CI-Kette 1/2 |
| US-080 | #86 | Branch-Protection + Delivery-Flow | CI-Kette 2/2 |
| US-081 | #85 | Treue-Metrik fidelity.py | Treue-Kette 1/4 |
| US-082 | #87 | Korpus-Harness fidelity_run | Treue-Kette 2/4 |
| US-083 | #88 | Baseline + Report + Schwellen | Treue-Kette 3/4 |
| US-084 | #89 | Regressions-Gate + CI-Check | Treue-Kette 4/4 (braucht CI-Merge!) |

## Stränge / Wartepunkte

### Wave 1 (3 parallel)
| Issue | Story | Worktree | Branch |
|-------|-------|----------|--------|
| #83 | US-078 | — (Lead arbeitet im Hauptrepo + eigener Branch für imgbundle) | sprint-15-us078-batches |
| #84 | US-079 | `../ks15-wt-ci` | sprint-15-ci |
| #85 | US-081 | `../ks15-wt-treue` | sprint-15-treue |

### Ketten danach (Agent-Wiederverwendung)
- **CI-Kette:** US-079 → US-080 (gleicher Agent/Branch)
- **Treue-Kette:** US-081 → US-082 → US-083 → **[WARTEPUNKT: US-080
  DONE → Lead merged origin/sprint-15-ci in sprint-15-treue]** → US-084
- **US-078 = LEAD-STORY:** Stunden-Langläufer (render-Voll-Lauf) +
  Prod-Writes — der Lead führt sie selbst nach den Runbooks aus
  (Hintergrund-Lauf mit aktivem Polling erlaubt — NUR für den Lead,
  Teammate-Background-Verbot gilt weiter). Läuft nebenher, blockiert
  keine Kette.

## Lead-Regeln (etabliert S13/S14 — PFLICHT in jedem Ketten-Prompt)

1. Ownership VOR Spawn; **Agents reagieren NUR auf Lead-Briefings,
   Board-Auto-Assignments ignorieren** (Klausel in jeden Prompt).
2. Tasks erst NACH TeamCreate anlegen.
3. Teammate-Background-Bash VERBOTEN; Meilenstein-Meldungen Pflicht;
   CI-Läufe pollen statt warten (max ~8×30s je Runde).
4. Stumm: Artefakt-Check → 1 Weckruf → Lead inline.
5. Schreibende GitHub-Settings-Calls NUR die in US-080/084 exakt
   genannten Protection-PUTs.
6. **ACHTUNG nach US-080:** Branch-Protection ist dann AKTIV — direkte
   master-Pushes (auch Review-Docs) brauchen ab da Admin-Bypass; alle
   Sprint-Branches sind davon unberührt (PRs wie immer).
7. LLM-/Kosten-Boundary: US-078-Gemini-Voll-Lauf nur 1× (idempotent,
   Resume statt Re-Run); keine LLM-Calls in Suiten.
8. Abschluss: Draft-PRs (Label sprint-15): us078→Closes #83,
   sprint-15-ci→Closes #84 #86, sprint-15-treue→Closes #85 #87 #88 #89;
   CHANGELOG-Branch+PR; Shutdown+TeamDelete; Abschluss-Tabelle.
   Merge macht /sprint-review (ab jetzt mit grüner CI als Gate!).

## Auftrag

/sprint-execute liest diese Datei und führt alle Stränge aus.
Agent Teams Modus (Default). Sequentiell: `--sequential`.
