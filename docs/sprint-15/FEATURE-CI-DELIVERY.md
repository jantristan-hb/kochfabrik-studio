---
key: KOCHFABRIK-FEATURE-009
status: approved
title: "CI/Delivery: GitHub Actions, Branch-Protection, Treue-Gate-Verdrahtung"
created: 2026-06-11
project: kochfabrik
---

# KOCHFABRIK-FEATURE-009: CI/Delivery (EPIC-008 C1–C3)

> **Typ:** FEATURE (Brownfield-Delta). Sprint 13 / EPIC-008. Macht die
> Sprint-11/12-Gates verbindlich: ohne CI ist jedes Gate freiwillig.

## 1. Vision

Jede Änderung läuft vor dem Merge durch eine Pipeline (Lint + Tests +
Build); master ist geschützt (PR-Pflicht + grüne Checks); das
Treue-Sample-Gate (FEATURE-010) ist als Pflicht-Check verdrahtet —
„super nah am PDF" wird vom Merge-Prozess erzwungen, nicht erhofft.

## 4. Flows / Pipeline-Design

```
.github/workflows/ci.yml — Trigger: pull_request + push auf master
  Job "ci":      ruff check --select E9,F63,F7,F82 (Baseline sauber,
                 verifiziert 2026-06-11) → pytest backend/tests
                 (Ubuntu, Python 3.12 wie Container; DB-gated Tests
                 skippen by design) → docker build (Image baut)
  Job "fidelity" (US-067): Sample-Treue-Gate gegen das committete
                 Referenz-Deck (engine/data/cache/10-182-…, ref.pdf +
                 elements.json im Repo) — Render im frisch gebauten
                 Image, Score gegen eingefrorene Baseline
Branch-Protection master: PR-Pflicht + required checks [ci, fidelity];
enforce_admins=false (dokumentierter Admin-Bypass für Doc-Hotfixes —
bewusst, weil Review-Doc-Commits sonst PR-Zwang hätten; Disziplin via
CLAUDE.md). Delivery-Flow: docs/ops/DELIVERY-FLOW.md.
```

## 8. Akzeptanzkriterien (EARS)

1. WHEN ein PR geöffnet/aktualisiert wird THE SYSTEM SHALL die
   Pipeline (Lint, Tests, Build) ausführen und ein roter Check SHALL
   den Merge blockieren (Branch-Protection mit required checks aktiv).
2. WHEN die Pipeline auf master läuft THE SYSTEM SHALL grün sein
   (Erst-Lauf bewiesen, kein rotes master-Badge als Dauerzustand).
3. WHEN das Fidelity-Gate als Pflicht-Check verdrahtet ist THE SYSTEM
   SHALL einen PR mit künstlich verschlechterter Treue (Test-Regression)
   nachweislich blockieren (Beweis-Lauf dokumentiert).
4. THE SYSTEM SHALL den Delivery-Flow dokumentieren (PR → CI → Merge →
   manueller Deploy-Trigger + live_verify) inkl. Admin-Bypass-Regel.

## 9. Abgrenzung (Nicht-Teil)

- Voll-Korpus-Lauf im CI (200 Decks liegen nicht im Repo — Sample = 1
  committetes Deck; Voll-Lauf bleibt lokal/manuell, FEATURE-010)
- Auto-Deploy — bleibt bewusst manuell (CUTOVER-RUNBOOK)
- Coverage-/Quality-Gates jenseits Lint+Tests (Goldplating)

## 9a. Boundaries (3-Tier)

- ✅ **Always:** `.github/workflows/`, `docs/ops/DELIVERY-FLOW.md`,
  `pyproject.toml`/ruff-Konfig im Branch; gh-API-READS;
  **explizit Task-gedeckt (US-062/067):** Branch-Protection via
  `gh api repos/.../branches/master/protection` setzen/aktualisieren
- ⚠️ **Ask-first (headless → BLOCKED):** andere Repo-Settings
  (Visibility, Webhooks, Secrets); enforce_admins=true
- 🚫 **Never:** master pushen; CI-Secrets im Klartext; Tests/Lint
  aufweichen, um die Pipeline grün zu machen

## 10. Abgrenzung zum Ist

- Keine CI (verifiziert: kein `.github/`) → Pipeline + Protection
- Gates (sim_gate/fidelity) nur lokal-freiwillig → CI-erzwungen
- master ungeschützt (direkte Pushes möglich/praktiziert) → PR-Pflicht
  mit dokumentiertem Admin-Bypass

## 11. Implementierungs-Anker (Ist)

`tools/.venv/bin/ruff check --select E9,F63,F7,F82 backend engine/scripts`
= sauber (2026-06-11). Suite: 113 passed/5 skipped (DB-gated via
fehlender DATABASE_URL — läuft im CI identisch). `Dockerfile` baut auf
Ubuntu-Runnern (kein Mac-Spezifikum). Repo privat, gh-Token mit
repo-Scope (Protection-API ok). Tests brauchen Python ≥3.10 (PEP 604,
README §Tests lokal) — CI nimmt 3.12 (Container-Parität).

## 12. Bekannte Pitfalls

1. **CI ≠ lokal:** Ubuntu + frisches venv — Test-Deps explizit
   installieren (pytest, httpx, requirements.txt); KEIN tools/.venv-Pfad
   im CI verwenden, sondern systemweites pip im Runner.
2. **Required-Check-Namen müssen exakt matchen** (Job-Name = Check-Name);
   Protection erst NACH erstem grünen Lauf setzen, sonst sperrt man sich
   mit einem nie-gelaufenen Check aus.
3. **docker build im CI ohne Cache** dauert (LibreOffice-Layer ~3-5 min)
   — akzeptiert; kein Cache-Tuning in diesem Sprint (Goldplating).
4. **Branch-Protection sperrt den eigenen Workflow:** Review-Doc-Pushes
   auf master brauchen danach Admin-Bypass oder PR — in DELIVERY-FLOW.md
   + CLAUDE.md festschreiben, sonst stolpert der nächste /sprint-review.
5. **fidelity-Job braucht das Image** — Job-Dependency (needs: ci bzw.
   eigener Build-Step), nicht parallel blind starten.

## Referenzen
- implements → REQUIREMENTS R-CI-1, R-CI-2, R-CI-3, R-FID-3 (CI-Teil)
- depends_on → [[KOCHFABRIK-FEATURE-010]] (Sample-Gate) · tools/sim_gate.sh
- relates_to → [[EPIC-008]] C1–C3 · [[EPIC-007]] V3

## Referenziert von
— USER-STORIES Sprint 13 (US-061, US-062, US-067)
