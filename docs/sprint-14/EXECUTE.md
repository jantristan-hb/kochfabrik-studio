# Sprint 14 — kochfabrik-studio (Präsentations-Wizard)

> Übergabe-Prompt für `/sprint-execute` nach `/clear`.
> Referenzieren mit: @docs/sprint-14/EXECUTE.md

**Pfad:** /Users/janrudat/work/02 AKARA Solutions GmbH/kochfabrik/kochfabrik-studio
**Sprint:** 14 · **Erstellt:** 2026-06-12 · **Provider:** github
**Test:** `tools/.venv/bin/python -m pytest backend/tests -q`
**Gates:** `./tools/sim_gate.sh` (US-072 + US-077) · Suite-Baseline: 153 passed/5 skipped/0 failed
**Branch-Konvention:** Ketten `sprint-14-api` / `sprint-14-wizard`, Solos `sprint-14-us069-notext` / `sprint-14-us073-imgbundle`

## Sprint-Docs

- Stories: `docs/sprint-14/USER-STORIES.md` (Story-Gate + Boundaries!)
- Specs: `FEATURE-KORPUS-ASSETS.md` (013) · `FEATURE-OVERLAY-BACKEND.md` (014) · `FEATURE-WIZARD-UI.md` (015)
- Test-Stubs: `docs/sprint-14/TEST.md` — **Testdatei-Ownership strikt:** tooling=US-069 · bundle=US-073 · test_sprint14.py=API-Kette · test_sprint14_fe.py=Wizard-Kette
- Traceability: `docs/sprint-14/TRACEABILITY.md`

## Story↔Issue-Tabelle (VERBINDLICH für `Closes #N`)

| Story | Issue | Titel | Strang |
|-------|-------|-------|--------|
| US-069 | #67 | Textfreie Korpus-Renders | Solo (sprint-14-us069-notext) |
| US-073 | #68 | Bild-Embeddings + rank_mixed | Solo (sprint-14-us073-imgbundle) |
| US-070 | #69 | Geometrie-API + Notext-Route | API-Kette 1/3 |
| US-071 | #71 | Bild-Overrides im Download | API-Kette 2/3 |
| US-072 | #72 | Formulieren + Ranking-Mix | API-Kette 3/3 (braucht US-073!) |
| US-074 | #70 | Wizard-Gerüst + Navigation | Wizard-Kette 1/4 |
| US-075 | #73 | Alternativen + Auswahl | Wizard-Kette 2/4 |
| US-076 | #74 | Overlay-Editor | Wizard-Kette 3/4 (braucht API-Merge!) |
| US-077 | #75 | Filmstreifen + Download + E2E | Wizard-Kette 4/4 |

## Stränge / Wartepunkte

### Wave 1 (4 parallel)
| Issue | Story | Worktree | Branch |
|-------|-------|----------|--------|
| #67 | US-069 | `../ks14-wt-notext` | sprint-14-us069-notext |
| #68 | US-073 | `../ks14-wt-imgbundle` | sprint-14-us073-imgbundle |
| #69 | US-070 | `../ks14-wt-api` | sprint-14-api |
| #70 | US-074 | `../ks14-wt-wizard` | sprint-14-wizard |

### Ketten danach (Agent-Wiederverwendung)
- **API-Kette:** US-070 → US-071 → **[WARTEPUNKT 1: US-073 DONE →
  Lead merged origin/sprint-14-us073-imgbundle in sprint-14-api]** → US-072
- **Wizard-Kette:** US-074 → US-075 → **[WARTEPUNKT 2: US-072 DONE →
  Lead merged origin/sprint-14-api in sprint-14-wizard]** → US-076 → US-077
- US-069 ist unabhängig (Vorlagen-PNGs; US-070 hat skipif-Fallback)

## Lead-Regeln (Sprint-13-Lehren — PFLICHT in jedem Ketten-Prompt)

1. Ownership VOR Spawn; **Agents reagieren NUR auf Lead-Briefings,
   Board-Auto-Assignments werden ignoriert** (Klausel in jeden Prompt!).
2. Tasks erst NACH TeamCreate anlegen (Scope-Falle Sprint 13).
3. Background-Bash VERBOTEN; Meilenstein-Meldungen Pflicht.
4. Stumm: Artefakt-Check → 1 Weckruf → Lead inline (US-056-Muster).
5. Rest-Ketten „in einem Rutsch nach USER-STORIES.md/TEST.md"
   delegieren, je Story eigener Commit + DONE-Meldung mit SHA.
6. LLM-Boundary: echte Gemini-/Anthropic-Calls NUR in den dokumentierten
   Sample-/Live-Smoke-Schritten (US-069/072/073), NIE in der Suite;
   Voll-Korpus-Läufe + Volume-Sync sind Ask-first → NICHT im Sprint.
7. Gold-Test-Wache: test_bundle_ranking_gold + test_sprint13*-Bestand
   müssen in JEDER Story grün bleiben.
8. Abschluss: Draft-PRs (Label sprint-14): us069→Closes #67,
   us073→Closes #68, sprint-14-api→Closes #69 #71 #72,
   sprint-14-wizard→Closes #70 #73 #74 #75; CHANGELOG-Branch+PR;
   Team-Shutdown; Abschluss-Tabelle. Merge macht /sprint-review.

## Auftrag

/sprint-execute liest diese Datei und führt alle Stränge aus.
Agent Teams Modus (Default). Sequentiell: `--sequential`.
