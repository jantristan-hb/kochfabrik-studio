# Sprint 15 — Retrospektive (2026-06-15)

## Was lief gut
- **CI lebt + master ist geschützt** — erster grüner Pipeline-Lauf auf
  Ubuntu, Branch-Protection mit Pflicht-Checks ci+fidelity. Das Gate hat
  beim ersten echten Einsatz sofort gegriffen (FastAPI-Dep-Drift gefangen,
  s.u.).
- **Treue ist eine Zahl** — fidelity-Metrik + eingefrorene Baseline (Ø
  total 0.612, font=0.0 = F-E-02 quantifiziert) + Regressions-Gate
  (künstliche Regression Δ0.098 nachweislich gefangen). EPIC-005 hat jetzt
  sein Lineal.
- **Voll-Korpus-Batches** durchgezogen: 201/201 Notext-Renders aufs
  Volume, imgbundle 2087 Slides/201 Decks. Embed-Härtung (Checkpoint+Retry)
  nach realem Gemini-503 rettete den zweiten Lauf.
- 4 Stränge (CI-Kette, Treue-Kette, Lead-Batches, + Wizard-Bugfix)
  parallel, Board-Ignorier-Klausel hielt die Agents sauber.

## Was lief schlecht / hätte besser sein können
- **Branch-Protection-Bootstrap-Falle:** required ci+fidelity gesetzt,
  bevor der Workflow in master war → Folge-PRs (#93/#94/#96) hingen auf
  "wartet auf ci". Gelöst: #91/#92 via grüne Checks, Betriebs-/Doc-PRs via
  Admin-Bypass, Wizard-Code durch die echte Pipeline. Lehre: required
  checks erst aktivieren, NACHDEM der Workflow auf dem Default-Branch ist.
- **Ungepinnte FastAPI:** `fastapi>=0.110` zog im CI eine neuere Starlette,
  deren app.routes _IncludedRouter ohne .path liefert → Routen-Inventar-
  Tests (sprint2/3/12) rot. Erst beim ersten echten CI-Lauf sichtbar. Fix:
  fastapi/starlette exakt gepinnt. Lehre: Test-/Runtime-kritische Deps
  pinnen, sonst tickt eine Zeitbombe bis zum nächsten Upstream-Release.
- **CHANGELOG-Merge-Verlust:** Beim Merge master→Wizard-Branch ging der
  [Unreleased]-Eintrag still verloren (beide Seiten am Kopf) — gefangen
  beim Review, wiederhergestellt.
- Wizard-Bugs (#95) waren Sprint-14-Defekte, die der gemockte E2E nicht
  fing — siehe eigene Bug-Retro im PR.

## Plan-vs-Reality
| Metrik | Plan | Realität |
|--------|------|----------|
| Umsetzung | 7 Stories | 7/7 DONE (100%) + Wizard-Bugfix #95 |
| Effort | 3 Stränge | akkurat; Batches als Tages-Langläufer |
| Dependencies | 2 Wartepunkte | korrekt, 0 Code-Konflikte |
| Scope | EPIC-007+008 | beide DONE (V5-Schwellen = Jan offen) |

## Learnings (übertragbar)
- required CI-Checks NIE vor dem Workflow-Merge auf den Default-Branch
  aktivieren (Bootstrap-Henne-Ei).
- Runtime-/Introspektions-kritische Dependencies (FastAPI/Starlette)
  pinnen — der erste CI-Lauf ist der ehrlichste Integrationstest.
- Batch-Tooling von Anfang an mit Checkpoint/Resume bauen (Gemini-503
  killte 1043 Calls, bevor die Härtung griff).

## Spec-Erfüllung
- EARS: FEATURE-009 (1–4) + FEATURE-016 (1–4) grün. V5/R-FID-5
  (Schwellen-Abnahme) offen markiert = Jan-Entscheid.
- Pitfalls-Gegenprobe: sauber (Gold-Test grün, kein np.load außerhalb
  bundle.py, kein timeout-Binary, Cache read-only).

## Spec-Sync (Code → Spec)
- FEATURE-009/016 → implemented; EPIC-007/008 → DONE; TRACEABILITY
  nachgezogen.

## Offene technische Schulden
- V5 Treue-Schwellen (Jan), Vertrag-Rest (Dialog-Edit, DNA-Doku),
  EPIC-005 Font-Treue, EPIC-010 Security, Wizard-Feinschliff, Alt-Ordner.
