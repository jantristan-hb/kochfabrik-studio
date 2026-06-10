# Sprint 11 — kochfabrik

> Übergabe-Prompt für `/sprint-execute` nach `/clear`.
> Referenzieren mit: @docs/sprint-11/EXECUTE.md

**Pfad:** /Users/janrudat/work/02 AKARA Solutions GmbH/kochfabrik/kochfabrik-studio
**Sprint:** 11 (EPIC-004 M1–M3 + EPIC-009/B1 vorgezogen — Monorepo-Schnitt nach ADR-002)
**Erstellt:** 2026-06-09
**Build:** `docker build -t kf-studio-sim .` (ab US-049)
**Test:** `tools/.venv/bin/python -m pytest backend/tests -q` (venv: Homebrew-Python ≥3.10)
**Branch-Konvention:** Wave 1: `sprint-11-us{NR}-{slug}` · Waves 2–4: EIN gemeinsamer Branch `sprint-11-monorepo`
**Provider:** github (gh authentifiziert als jantristan-hb)

## ⚠️ Sicherheits-Kern (jedem Teammate injizieren)

- **master-Push = Auto-Deploy auf Prod** (Coolify). NIEMALS auf master
  pushen/mergen. Cutover = PR-Merge im /sprint-review, NACH grünem
  `tools/sim_gate.sh` + vorhandenem Backup (US-044).
- Engine-Repo `../pptxgenerator_v2` (Branch `main`) ist NICHT
  deploy-gebunden — Commits/Pushes dort erlaubt (US-045).
- `data/cache/` + `pgbundle.npz`: read-only. Alt-Ordner: nicht anfassen.
- macOS: kein GNU `timeout`; Polling max ~40s; Pfade mit Leerzeichen quoten.
- Verhalten strikt erhalten (R-REF-6): kein „nebenbei verbessern".

## Sprint-Docs

- Stories: `docs/sprint-11/USER-STORIES.md` (Story-Gate + Boundaries)
- Feature-Specs: `docs/sprint-11/FEATURE-MONOREPO-MERGE.md` (Merge-Mechanik:
  Engine-main, gitignorte data/node_modules retten!), `FEATURE-DEPLOY-CUTOVER.md` (Infra-Fakten)
- Test-Stubs: `docs/sprint-11/TEST.md` · Traceability: `docs/sprint-11/TRACEABILITY.md`
- Entscheidungsgrundlage: `docs/adr/ADR-002-monorepo-schnitt.md` (accepted)

## Waves

### Wave 1 (parallel, 3 Teammates, eigene Branches/Worktrees)
| Issue | Story | Titel |
|-------|-------|-------|
| #20 | US-044 | Backup vor Cutover erstellen + verifizieren |
| #21 | US-045 | Engine-Repo konsolidieren (Mac-Diff + F-E-10 Env-Konfig) |
| #22 | US-046 | Charakterisierungs-Tests + Suite lokal 100% grün |

### Waves 2–4 (SEQUENTIELL — ein Agent, ein Branch `sprint-11-monorepo`)
| Issue | Story | Titel | Blocked-by |
|-------|-------|-------|------------|
| #23 | US-047 | Engine via subtree + Layout flachziehen | US-045 |
| #24 | US-048 | Backend-Pfade repo-intern + vendor.sh weg | US-046, US-047 |
| #25 | US-049 | Dockerfile Monorepo-Layout + alembic.ini | US-048 |
| #26 | US-050 | Sim-Gate-Skript + Container-Smoke | US-049 |
| #27 | US-051 | Cutover-Runbook + Live-Verify-Skript | US-044, US-050 |

> **Bewusste Abweichung vom Parallel-Default:** US-047–US-051 bauen
> aufeinander auf denselben Dateien auf (FEATURE-004 §12 Pitfall 5) —
> ein Agent arbeitet sie sequentiell auf `sprint-11-monorepo` ab
> (US-051 erst nachdem US-044-DONE gemeldet ist). Ergebnis: 4 Branches,
> 4 Draft-PRs (3× Wave 1 + 1× Monorepo-Branch).

## Auftrag

/sprint-execute liest diese Datei: Wave 1 als Agent-Team (3 parallel,
Worktrees), danach EIN Agent für US-047→US-051 auf `sprint-11-monorepo`.
Cutover (Merge nach master) NICHT im Execute — erst /sprint-review
(Reihenfolge: Backup ✓ → Sim-Gate ✓ → Merge = Deploy → live_verify.sh,
siehe CUTOVER-RUNBOOK.md aus US-051).
