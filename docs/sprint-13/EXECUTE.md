# Sprint 13 — kochfabrik-studio (Präsentationsdesigner)

> Übergabe-Prompt für `/sprint-execute` nach `/clear`.
> Referenzieren mit: @docs/sprint-13/EXECUTE.md

**Pfad:** /Users/janrudat/work/02 AKARA Solutions GmbH/kochfabrik/kochfabrik-studio
**Sprint:** 13 · **Erstellt:** 2026-06-11 · **Provider:** github
**Test:** `tools/.venv/bin/python -m pytest backend/tests -q`
**Gates:** `./tools/sim_gate.sh` · `./tools/live_verify.sh` (US-068: +LIVE_DEEP)
**Branch-Konvention:** `{issue-nr}-{slug}` · Ketten-Branches: `sprint-13-api`, `sprint-13-ui`

## Sprint-Docs

- Stories: `docs/sprint-13/USER-STORIES.md` (Story-Gate + Boundaries!)
- Specs: `FEATURE-DESIGNER-API.md` (011) · `FEATURE-DESIGNER-UI.md` (012)
- Test-Stubs: `docs/sprint-13/TEST.md` (API-Kette: test_sprint13.py · UI-Kette: test_sprint13_fe.py — getrennte Dateien, getrennte Ownership!)
- Traceability: `docs/sprint-13/TRACEABILITY.md`

## Story↔Issue-Tabelle (VERBINDLICH für Commit-Footer `Closes #N`)

| Story | Issue | Titel | Strang |
|-------|-------|-------|--------|
| US-061 | #47 | Designer-Router + Angebots-Parsing | API-Kette (Start) |
| US-062 | #50 | Vorschlags-Ranking Top-N + Pflicht | API-Kette (Ende) |
| US-063 | #48 | Designer-Seite Grundgerüst + Nav | UI-Kette (Start) |
| US-065 | #52 | Storyboard (Reorder/Remove/Session) | UI-Kette |
| US-064 | #51 | Quelle + Vorschlags-Karten | UI-Kette (braucht US-062!) |
| US-066 | #53 | Freitext-Suche im Designer | UI-Kette |
| US-067 | #54 | Download + E2E-Beweis | UI-Kette (Ende) |
| US-068 | #49 | live_verify Deep-Check (Incident) | Solo |

## Waves / Stränge

### Wave 1 (3 parallel)
| Issue | Story | Strang/Worktree |
|-------|-------|-----------------|
| #47 | US-061 | API-Kette, Worktree `../ks13-wt-api`, Branch `sprint-13-api` |
| #48 | US-063 | UI-Kette, Worktree `../ks13-wt-ui`, Branch `sprint-13-ui` |
| #49 | US-068 | Solo, Worktree `../ks13-wt-us068`, Branch `sprint-13-us068-live-deep` |

### Ketten danach (Agent-Wiederverwendung, Sprint-11/12-Muster)
- **API-Kette:** US-061 → US-062 (gleicher Agent, gleicher Branch)
- **UI-Kette:** US-063 → US-065 → **[WARTEPUNKT: US-062 DONE → Lead merged
  `sprint-13-api` in `sprint-13-ui`]** → US-064 → US-066 → US-067
- US-067-Ende = volle Suite + Sim-Gate auf dem vereinten Stand

## Lead-Regeln (aus Sprint 11/12 gelernt)

1. Ownership VOR Spawn (TaskUpdate owner) — keine Phantom-Re-Runs.
2. Background-Bash für Teammates VERBOTEN; Meilenstein-Meldungen Pflicht.
3. Stummer Agent: Artefakt-Check (`git log`/`status` im Worktree) VOR
   jeder Aktion; 1 Weckruf, dann Lead inline (Crash-Muster US-056).
4. Verify-Vorgaben sind gegen den Ist-Stand zu prüfen — bei Konflikt
   Spec/EARS > Test-Sample (gen_fiktiv-Lehre); Eskalation als BLOCKED.
5. Boundaries: echte Gemini-Calls nur im dokumentierten Live-Smoke
   (US-062/067), NIE in der Suite; assemble/compose_offer-Logik
   unangetastet; master nie.
6. Nach Abschluss: Draft-PRs (Label sprint-13): `sprint-13-api`
   (Closes #47, #50), `sprint-13-ui` (Closes #48, #51, #52, #53, #54),
   `sprint-13-us068-live-deep` (Closes #49). Dann CHANGELOG-Branch+PR,
   Team-Shutdown, Abschluss-Tabelle. Merge macht /sprint-review.

## Auftrag

/sprint-execute liest diese Datei und führt alle Stränge aus.
Agent Teams Modus (Default). Sequentiell: `--sequential`.
