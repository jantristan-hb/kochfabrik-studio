# Sprint 12 — Retrospektive (2026-06-11)

## Was lief gut
- **Die Boundary-Eskalation hat eine Prod-Regression verhindert:** Der
  Ketten-Agent wies per Import-Graph nach, dass `gen_fiktiv.py` Runtime
  ist (engine_glue:349, angebot_chat:18) — das TEST.md-Sample hätte es
  per Namensraten nach tooling/ verschoben → ENGINE_OK=False → alle
  /api/angebot/* auf 503. EARS schlug Test-Sample (Option A).
- Beweis-Disziplin durchgängig maschinell: Routen-Inventar-Diff (leer,
  30 Routen byte-gleich), Ranking-Gold-Diff (bit-identisch, als
  dauerhafter Regressionstest), Sim-Gate inkl. neuem DB-Block.
- **Crash-Resilienz:** cmux-Absturz mitten in US-056 kostete keine
  Arbeit — gestageter Stand war vollständig + verifizierbar, Lead
  schloss inline ab (Artefakt-Check → Verify-Kette → Commit).
- Agent-Wiederverwendung in der Kette (US-053→055 ein Agent) + saubere
  Recovery-Spawns danach.

## Was lief schlecht / hätte besser sein können
- **Drei meiner Verify-/Test-Vorgaben waren selbst defekt** und wurden
  von Agents falsifiziert: (1) `r.methods` crasht auf Starlette-Mounts
  (getattr nötig), (2) selbst-matchende grep-Ketten (Testdatei enthält
  Suchstring), (3) gen_fiktiv-Fehlklassifikation. Muster: Verify-Design
  am Schreibtisch ohne Ausführung gegen den Ist-Stand.
- Nachrichten-Kreuzungen (Re-Assignment-Echos) weiterhin — kosten
  Lead-Aufmerksamkeit, aber keine Arbeit; Ownership-vor-Spawn hat die
  Phantom-RE-RUNS verhindert, nicht die Echos.
- Stummer Idle früh in US-053 (einmal Weckruf nötig).

## Plan-vs-Reality

### Implementierungs-Matrix
| Story | Geplant | Status | Abweichung |
|-------|---------|--------|------------|
| US-052 | Backup-Zyklus | ✅ | — |
| US-053 | Router auth+bildgenerator | ✅ | 🔄 getattr-Fix im Routen-Dump (Spec-Defekt) |
| US-054 | Router angebot+praes, <200 Z. | ✅ | — (91 Z.) |
| US-055 | Bundle-Schicht | ✅ | 🔄 tests/-Ausschluss im Loader-Grep (Spec-Defekt); + Gold-Fixture committet |
| US-056 | Tooling-Split | ✅ | 🔄 Option A: gen_fiktiv+build_angebot_template Runtime (Test-Sample korrigiert); Crash-Recovery durch Lead |
| US-057 | Alembic-Abnahme | ✅ | — (rc=0, Stamp 0003) |
| US-058 | Restore-Probe | ✅ | — (Rowcounts bewiesen) |
| US-059 | CLAUDE.md | ✅ | 🔄 faktentreu: 4 Router (nicht 5), Backup-Verweis auf Spec statt docs/ops (Branch-Sicht) — Review fixt Verweis |
| US-060 | Engine-Repo archiviert | ✅ | — |

### Plan-Qualität
| Metrik | Plan | Realität |
|--------|------|----------|
| Umsetzungsrate | 9 Stories | 9/9 DONE (100%) |
| Effort | Kette M, Rest S–M | Akkurat |
| Dependencies | Wave1 ∥ Kette ∥ Wave3 | Korrekt, 0 Merge-Konflikte |
| Scope | 9 (über Soll-8, begründet) | Passend — zwei Epics komplett |

## Learnings (übertragbar)
- **Verify-Vorgaben gegen den Ist-Stand AUSFÜHREN bevor sie in Stories
  landen** — drei Schreibtisch-Verifies waren defekt; ein 30-Sekunden-
  Probelauf beim Planen hätte alle drei gefangen. → sprint-plan-Praxis.
- **grep-basierte Gates brauchen tests/-Ausschluss by default** (Testdatei
  enthält zwangsläufig die Suchstrings).
- **Import-Graph > Namen** ist jetzt zweifach belegt (gen_fiktiv,
  build_angebot_template) — als Architektur-Regel in CLAUDE.md verankert.
- Crash-Recovery-Muster bewährt: Artefakt-Check → gestageten Stand
  verifizieren → inline abschließen, NICHT neu spawnen.

## Spec-Erfüllung (EARS/Tests)
- EARS ohne grünen Verify: — (11/11; FEATURE-006 Nr. 1–4 maschinell
  bewiesen, FEATURE-007 Nr. 1–3 mit Protokollen, FEATURE-008 Nr. 1–2)
- Pitfalls-Gegenprobe: sauber (Ports 15432/15433, kein timeout-Binary,
  keine Dumps im Tree, cron mit User+PATH+Newline, README-vor-Archive)
- Tests die sich als falsch herausstellten: test_tooling_split-Sample
  (gen_fiktiv) + zwei Verify-Einzeiler — alle dokumentiert korrigiert
- Tests die fehlten: — (Suite wuchs 107→113)

## Spec-Sync (Code → Spec, aus E8.0)
- Specs auf `implemented`: KOCHFABRIK-FEATURE-006/007/008
- TRACEABILITY (Sprint + Projekt) + EPIC-004/009 → DONE nachgezogen
- CLAUDE.md-Backup-Verweis auf docs/ops/ im Review-Fixup korrigiert

## Offene technische Schulden
- F-E-02 (Open Sans im Docker-Image) → EPIC-005/T3 (Sprint 14)
- Alt-Ordner-Archivierung inkl. lokalem ../pptxgenerator_v2 —
  Jan-Entscheid (ADR-002-Inventar), blockiert nichts
