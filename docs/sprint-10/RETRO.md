# Sprint 10 — Retrospektive (2026-06-09)

## Was lief gut
- Agent-Teams-Execution: 2 Waves à 4 parallele Stories, 8/8 DONE, keine
  Merge-Konflikte (disjunkte Output-Dateien per Design — Story-Schnitt
  mit je eigener Test-Datei `test_sprint10_us{NR}.py` hat sich bewährt).
- Wave-2-Wiederverwendung der Wave-1-Agents nach Kontext-Affinität
  (Extraktor-Autor schrieb den Report, Engine-Analyst das Embedding-ADR)
  — schnelle, fundierte Ergebnisse ohne Neukontext.
- Boundaries griffen: Pitfall-Gegenprobe über alle 8 Branches zeigt
  null Produktiv-Code-Änderungen — „Analyse-Sprint fixt nichts nebenbei"
  wurde eingehalten.
- Doc-only + deterministische EARS-Verifies = Review konnte jede Story
  mechanisch gegen die Remote-Branches re-verifizieren.

## Was lief schlecht / hätte besser sein können
- Team-Messaging erzeugte Dubletten-Echos (Agents beantworteten
  Re-Assignment-Notifications als „schon DONE") — kostete Aufmerksamkeit,
  aber keine Arbeit. Ursache: Task-Owner-Updates nach Spawn wirken wie
  neue Zuweisungen.
- `timeout` existiert nicht auf macOS — Workflow-Templates referenzierten
  es (Changelog-Push schlug zuerst fehl); Templates auf Mac-kompatible
  Befehle prüfen.
- PROGRESS.md war doppelt stale (EPIC-001 „IN_PROGRESS", „111 Tests") —
  Docs-Drift entsteht, wenn Sprints ohne /sprint-review abgeschlossen
  werden.

## Plan-vs-Reality

### Implementierungs-Matrix
| Story | Geplant | Status | Abweichung |
|-------|---------|--------|------------|
| US-036 | Bug-Analyse Studio | ✅ | — (12 Findings statt min. 5) |
| US-037 | Bug-Analyse Engine | ✅ | — (13 Findings, F-E-02 CRITICAL) |
| US-038 | Font-Extraktor + JSON | ✅ | — (200/200, errors=0) |
| US-039 | FONT-REPORT.md | ✅ | — (Zusatz: SIZE_K-Falsifikation belegt) |
| US-040 | Test-Baseline | ✅ | Befund: Collect 63 ≠ behauptete 111 |
| US-041 | ADR-001 Embedding | ✅ | — (Empfehlung: Server-Treue) |
| US-042 | ADR-002 Monorepo | ✅ | Bonus-Fund: Pfad-Drift `03 AKARA…` in vendor.sh:12 |
| US-043 | ADR-003 pgbundle | ✅ | Bonus: Schnitt-Blocker F-E-10/11 dokumentiert |

### Plan-Qualität
| Metrik | Plan | Realität |
|--------|------|----------|
| Umsetzungsrate | 8 Stories | 8/8 DONE (100%) |
| Effort-Schätzungen | Q1/Q2 M, Rest S–M | Akkurat — alle Stories in einem Durchgang |
| Dependencies | 2 Waves, 4 Blocked-by-Kanten | Korrekt, keine Konflikte; Wave-2-Inputs via `git show origin/<branch>` gelöst (Worktrees basieren auf master) |
| Scope | 8 Stories | Passend |

## Learnings (übertragbar)
- **Intra-Sprint-Artefakt-Abhängigkeiten** (Wave 2 braucht Wave-1-Output
  vor dem Merge): `git show origin/<branch>:<pfad>` als untracked Input
  funktioniert sauber — als Standard-Muster in /sprint-execute denkbar.
- **Pro-Story-Testdateien** statt einer geteilten TEST-Datei vermeiden
  Cross-Branch-Konflikte vollständig.
- **Messen vor Verbessern zahlt sich aus:** Die Subpixel-Daten aus US-038
  haben die SIZE_K-Hypothese nicht nur bestätigt, sondern verschärft
  (größenabhängiger Fehler) — EPIC-005/T1 hat jetzt ein präzises Ziel.

## Spec-Erfüllung (EARS/Tests)
- EARS-Kriterien ohne grünen Verify: — (11/11 über die 8 Verifies abgedeckt, im Review re-geprüft)
- Pitfalls-Gegenprobe-Findings: — (alle 8 Branches berühren nur `docs/`, `tools/`, `backend/tests/test_sprint10_*`)
- Tests die sich als falsch herausgestellt haben: `test_alembic_baseline_present_and_empty` (Bestand) — brüchig via Namespace-Package (`__file__=None`), dokumentiert in TEST-BASELINE (E2)
- Tests die fehlten: Endpoint-Charakterisierungstests (TestClient), Engine-JS-Pipeline — als Carry-Over/EPIC-004-Gate vorgemerkt

## Spec-Sync (Code → Spec, aus E8.0)
- Specs auf `implemented`: KOCHFABRIK-FEATURE-001/002/003
- Abweichungen eingearbeitet: — (keine 🔄-Stories)
- Neue Pitfalls dokumentiert: — (keine neuen beim Implementieren getroffen; Messaging-/timeout-Beobachtungen sind Prozess-, nicht Feature-Pitfalls)
- TRACEABILITY (Sprint + Projekt) nachgezogen: Erfüllungs-Stand + ADR-Verweise

## Offene technische Schulden
- ADR-001/002/003 Abnahme durch Jan (`proposed → accepted`) — **Gate für EPIC-004 + EPIC-005**
- Python >=3.10-Pin + Alembic-Test-Fix (TEST-BASELINE E1/E2) → EPIC-004/M6
- Build-DSN/CORPUS_DIR hardcodiert (F-E-10) → vor EPIC-004/M1
- Endpoint-Charakterisierungstests vor Refactoring → EPIC-004-Gate
