---
key: KOCHFABRIK-FEATURE-008
status: approved
title: "Projekt-Docs (CLAUDE.md) + Engine-Repo-Archivierung"
created: 2026-06-10
project: kochfabrik
---

# KOCHFABRIK-FEATURE-008: Projekt-Abschluss M7 + Archivierung

> **Typ:** FEATURE (doc/ops). Sprint 12 / EPIC-004 M7 +
> ADR-002-Konsequenz (Engine-Repo read-only).

## 1. Vision

Das Monorepo hat ein vollständiges Projekt-CLAUDE.md (Techstack an
genau einem Ort, Befehle, Architektur-Regeln, Sprint-Tabelle), und
das alte Engine-Repo ist auf GitHub archiviert — eine Quelle der
Wahrheit, keine Verwechslungsgefahr.

## 4. Inhalte

**CLAUDE.md (Projekt-Root):** Session-Start-Reihenfolge (CLAUDE →
PROGRESS → REQUIREMENTS → Sprint-Docs), Tech-Stack-Tabelle (FastAPI/
Postgres/SQLAlchemy2-async/Alembic · Engine: Python-Skripte +
pptxgenjs/node + LibreOffice/poppler · pgbundle.npz read-only),
Befehle (venv-Tests, `tools/sim_gate.sh`, `tools/live_verify.sh`,
Deploy-Trigger manuell via Coolify-API!, docker build), Architektur-
Regeln (Router-Struktur nach M4, eine Bundle-Schicht nach ADR-003,
graceful-Degradation-Muster, Boundaries: data/cache read-only,
master = Deploy nur nach Sim-Gate), Sprint-Tabelle (1–12).

**Engine-Archivierung:** Abschieds-Commit ins Engine-Repo-README
(„ARCHIVIERT 2026-06-10 — Code lebt im Monorepo kochfabrik-studio
unter engine/, Historie via subtree erhalten") → push →
`gh repo archive jantristan-hb/pptxgenerator_v2 -y`.

## 8. Akzeptanzkriterien (EARS)

1. WHEN ein neuer Agent das Projekt betritt THE SYSTEM SHALL ihm via
   CLAUDE.md Stack, Befehle (inkl. der zwei Gates + manuellem
   Deploy-Trigger) und Architektur-Regeln auf dem Sprint-12-Stand
   liefern — ohne `{…}`-Platzhalter, mit korrekten Pfaden
   (stichprobenhaft gegen die Codebase geprüft).
2. WHEN die Archivierung abgeschlossen ist THE SYSTEM SHALL das
   GitHub-Repo pptxgenerator_v2 als archived/read-only zeigen
   (`gh repo view --json isArchived` = true) und dessen README SHALL
   auf das Monorepo verweisen.

## 9. Abgrenzung (Nicht-Teil)

- Lokales Engine-Verzeichnis `../pptxgenerator_v2` bleibt liegen
  (Jan-Entscheid über Alt-Ordner steht aus — ADR-002-Inventar)
- Keine README-Vollsanierung — nur Drift-Fixes

## 9a. Boundaries (3-Tier)

- ✅ **Always:** CLAUDE.md/README im Branch; Engine-Repo README-Commit
  + push auf main; `gh repo archive` (explizit Task-gedeckt)
- ⚠️ **Ask-first (headless → BLOCKED):** weitere GitHub-Settings
  (Branch-Protection, Visibility); Löschen von irgendetwas
- 🚫 **Never:** lokales `../pptxgenerator_v2` verschieben/löschen;
  Monorepo-master pushen

## 11. Implementierungs-Anker (Ist)

Kein `CLAUDE.md` im Repo (verifiziert 2026-06-10). README.md auf
Monorepo-Stand (US-048). Engine-Repo `jantristan-hb/pptxgenerator_v2`
@ main 0336866, clean. CLAUDE.md-Strukturvorgabe: sprint-plan-Skill
§Greenfield-CLAUDE.md (Session-Start/Stack/Befehle/Regeln/Sprints).
Router-Struktur nach US-052/053: `backend/routers/*` (erst NACH der
Kette dokumentieren — Story läuft in der End-Wave!).

## 12. Bekannte Pitfalls

1. **CLAUDE.md vor dem Umbau geschrieben = sofort stale** — Story
   läuft NACH der Code-Ordnungs-Kette (Blocked-by), dokumentiert den
   End-Stand.
2. **„Auto-Deploy"-Folklore:** Das Runbook-Learning (KEIN Webhook,
   Deploy = manueller API-Trigger) MUSS in die Befehle — sonst merged
   jemand und wundert sich.
3. **Archivieren vor letztem Push** — erst README-Hinweis pushen,
   DANN archivieren (archived = read-only, auch für uns).

## Referenzen
- implements → REQUIREMENTS R-REF-5, R-REF-2 (Teil), R-REF-1 (Abschluss)
- relates_to → [[EPIC-004]] M7 · [[KOCHFABRIK-ADR-002]] (Engine read-only)

## Referenziert von
— USER-STORIES Sprint 12 (US-059, US-060)
