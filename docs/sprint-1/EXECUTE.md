# Sprint 1 — kochfabrik-studio (EPIC-001)

> Übergabe-Prompt für `/sprint-execute`. @docs/sprint-1/EXECUTE.md

**Pfad:** /home/jrudat/work/03 AKARA Solutions GmbH/kochfabrik/kochfabrik-studio
**Sprint:** 1 · **Branch-Konvention:** `sprint-1-us{NR}-{slug}` (GitHub, kein glab)
**Build/Run:** `pip install -r requirements.txt`; lokal Postgres via Docker
**Test:** `pytest -q`
**Deploy:** Coolify force (UUID yu2fqx0twmtqcp6zyx2e59si), atomar
**Repo:** GitHub `master` (Deploy-Repo, Direkt-Merge zu master OK nach Review)

## Sprint-Docs
- Stories: `docs/sprint-1/USER-STORIES.md`
- Architektur: `docs/sprint-1/FEATURE-ARCH.md` (Nummernformat fixiert!)
- BDD: `docs/sprint-1/BDD.md` · Tests: `docs/sprint-1/TEST.md`

## Waves (sequenziell — DB-Fundament-Kette)

| Wave | Story | Titel | Blocked-by |
|------|-------|-------|------------|
| 1 | US-001 | Postgres-Container + graceful Async-DB-Layer | — |
| 2 | US-002 | DB-Schema + Alembic-Migrationen | US-001 |
| 3 | US-003 | Atomare Nummernsequenzen (100001-A + Angebot) | US-002 |
| 4 | US-004 | Owner-scoped Repository/Service-Layer | US-002,US-003 |
| 5 | US-005 | API-Endpoints + Integration Angebot-Generierung | US-004 |

## Auftrag
**Modus: sequentiell** (`--sequential`) — jede Story baut auf der
vorigen, Agent-Teams brächten keinen Parallel-Gewinn und Konflikt-Risiko
in app.py/db.py. Pro Story: Tests aus TEST.md rot → implementieren →
`pytest -q` grün → Branch → Commit → (GitHub) Merge zu master nach
Verify. Graceful-DB-Pflicht (DB_OK-Muster) in JEDER Story.

**Prod-Sicherheit:** US-001 Coolify-Postgres ist additiv. Erst nach
grünem `pytest` + lokalem Smoke deployen. Atomarer Coolify-Build
schützt die Live-Frontend-Funktionen.
