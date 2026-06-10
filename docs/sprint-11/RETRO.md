# Sprint 11 — Retrospektive (2026-06-10)

## Was lief gut
- **Erst messen/sichern, dann schneiden** hat getragen: Backup +
  Charakterisierungs-Netz + Engine-Konsolidierung VOR dem Subtree-Merge —
  der heikelste Umbau des Projekts lief ohne einen einzigen FAILED.
- Sequentielle Kette (US-047→051, ein Agent, ein Branch) statt
  Parallel-Gewürge auf geteilten Dateien: null Merge-Konflikte; die
  Kontext-Kontinuität des Agenten zahlte sich pro Folge-Story aus.
- Meilenstein-Meldungen + Ownership-vor-Spawn: Lead sah jeden
  Subtree-Schritt live; Phantom-Re-Runs aus Sprint 10 traten nicht mehr
  als Arbeits-, nur noch als Nachrichtenproblem auf.
- Zwei saubere BLOCKED-/Klärungs-Eskalationen statt Alleingängen
  (ADR-Lifecycle-Tests; ungültiges KF_USERS-Format → Cookie-Minting im
  Container).
- Agent-Verifikation schlug Lead-Annahme: der vorgegebene
  Postgres-Container-Kandidat war falsch (flinkbase-db) — der
  Verifikations-Schritt im Task hat die Fehlbackup-Falle abgefangen.

## Was lief schlecht / hätte besser sein können
- **Issue-Footer-Drift:** Der Ketten-Agent leitete Issue-Nummern aus
  Story-Nummern ab (#47–#49 statt #23–#25), trotz Mapping im Auftrag —
  harmlos (Nummern existieren nicht), aber PR #31 musste die Closes
  übernehmen; Issue #21 bleibt manuell zu schließen.
- **Nachrichten-Kreuzung:** Idle-Agent + neue Aufträge erzeugten
  wiederholt „bereits DONE"-Echos und „schick mir den Auftrag"-Loops —
  kostete Lead-Aufmerksamkeit. Muster: Inbox-Verarbeitung hinkt den
  DONE-Meldungen hinterher.
- Lead hat den Ketten-Worktree einmal zu früh ge-force-removed (nach
  Shutdown-Request, vor finaler Agent-Bestätigung) — ging gut, weil
  alles gepusht war, ist aber ein vermeidbares Risiko.

## Plan-vs-Reality

### Implementierungs-Matrix
| Story | Geplant | Status | Abweichung |
|-------|---------|--------|------------|
| US-044 | Backup vor Cutover | ✅ | Container-Kandidat des Leads korrigiert (Verifikation griff) |
| US-045 | Engine konsolidieren | ✅ | — (Dirty-Diff exakt wie vorhergesagt) |
| US-046 | Charakterisierung | ✅ | 🔄 +3 ADR-Lifecycle-Tests angepasst (Freigabe, Baseline war 4 statt 1 failed) |
| US-047 | Subtree + Flachziehen | ✅ | — (26 Engine-Commits, Rettung vollständig) |
| US-048 | Pfade + vendor.sh | ✅ | — |
| US-049 | Dockerfile | ✅ | — (Image 1,46 GB, Inhalt im Container verifiziert) |
| US-050 | Sim-Gate | ✅ | 🔄 Cookie-Minting statt KF_USERS-Login (Format-Realität) |
| US-051 | Runbook + Live-Verify | ✅ | — (Pre-Cutover-Referenz grün: 200/401/401/401/200) |

### Plan-Qualität
| Metrik | Plan | Realität |
|--------|------|----------|
| Umsetzungsrate | 8 Stories | 8/8 DONE (100%) |
| Effort | US-047 L, Rest S–M | Akkurat; Kette lief in ~35 min Wall-Clock |
| Dependencies | Wave 1 parallel + 5er-Kette | Korrekt; Lead-Merge der us046-Basis konfliktfrei |
| Scope | 8 Stories | Passend; Sicherheits-Auflagen (Backup/Gates) haben sich direkt ausgezahlt |

## Learnings (übertragbar)
- **Sequentielle Ein-Branch-Kette mit Agent-Wiederverwendung** ist das
  richtige Muster für Struktur-Refactorings auf geteilten Dateien —
  in /sprint-execute als expliziten Modus beibehalten.
- **Verifikations-Schritte in Tasks sind keine Höflichkeit:** Zwei
  Lead-Vorgaben (Postgres-Container, KF_USERS-Format) waren falsch und
  wurden nur durch die eingebauten Verify-/Eskalations-Schritte gefangen.
- Issue-Nummern gehören als **Tabelle in den EXECUTE.md-Kontext-Kern**,
  nicht nur in einzelne Aufträge — Agents memorieren Story↔Issue sonst
  falsch.
- Doc-only-Deltas nach grünem Gate (f1f8fa1→c3c67a8) per `git diff --stat`
  beweisen statt Gate-Re-Run — spart Minuten ohne Risikoverlust.

## Spec-Erfüllung (EARS/Tests)
- EARS ohne grünen Verify: — (9/9 über Story-Verifies; FEATURE-005 Nr. 4
  Post-Cutover-Teil wird in E9 mit live_verify auf der neuen Revision bewiesen)
- Pitfalls-Gegenprobe: sauber — kein `timeout`-Binary in tools/*.sh,
  keine Secrets/Dumps im Tree, `data/cache`/pgbundle unangetastet,
  kein master-Push durch Agents
- Tests die sich als falsch herausstellten: 3× `test_status_proposed`
  (Sprint-10-Artefakt-Tests froren ADR-Lifecycle-Momentaufnahme ein) —
  mit Freigabe auf `proposed|accepted` korrigiert
- Tests die fehlten: Engine-Skripte weiterhin ohne eigene Suite im
  Studio-Kontext (engine/tests läuft separat) → EPIC-004/M5-Thema

## Spec-Sync (Code → Spec, aus E8.0)
- Specs auf `implemented`: KOCHFABRIK-FEATURE-004, KOCHFABRIK-FEATURE-005
- Abweichungen eingearbeitet: — (keine Spec-relevanten; Cookie-Minting
  ist Implementierungsdetail des Gates)
- TRACEABILITY (Sprint + Projekt + Epics) nachgezogen

## Offene technische Schulden (→ Carry-Over Sprint 12)
- M4–M7 (app.py entzerren, Engine-Skripte ordnen inkl. ADR-003-
  Bundle-Schicht, Alembic-Versionstracking-Verify im Container, Docs/CLAUDE.md)
- EPIC-009: B1-Zyklus automatisieren + B3 Restore-Probe
- Engine-Repo `pptxgenerator_v2` auf GitHub archivieren (read-only)
- Issue #21 manuell schließen; Issue-Footer-Hygiene
