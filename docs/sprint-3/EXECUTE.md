# Sprint 3 — kochfabrik-studio (EPIC-001)

> Übergabe für `/sprint-execute`. @docs/sprint-3/EXECUTE.md

**Pfad:** /home/jrudat/work/03 AKARA Solutions GmbH/kochfabrik/kochfabrik-studio
**Sprint:** 3 · **Branch:** `sprint-3-dashboard-crm` (GitHub, kein glab)
**Test:** `pytest -q` (DB-Tests: `TEST_DATABASE_URL=…`)
**Deploy:** Coolify force (UUID yu2fqx0twmtqcp6zyx2e59si), atomar
**Repo:** GitHub `master` (Deploy-Repo; Merge→master via review/integrate)
**Basis:** S1+S2 DONE @ master 50f5c33 (store owner-scoped, chat.html
?offer Wiederöffnen, _owner, graceful, Alembic).

## Sprint-Docs
- Stories: `docs/sprint-3/USER-STORIES.md` · Arch: `FEATURE-ARCH.md`
- BDD: `docs/sprint-3/BDD.md` · Tests: `docs/sprint-3/TEST.md`

## Waves

| Wave | Story | Titel | Blocked-by |
|------|-------|-------|------------|
| 1 | US-012 | Stats/Aggregat-Endpoint | — |
| 1 | US-013 | Kunden-Endpoints + Store | — |
| 1 | US-014 | Angebote Such-/Status-Filter | — |
| 2 | US-015 | index.html Dashboard (echte KPIs) | US-012 |
| 2 | US-016 | bibliothek.html suchbares Archiv | US-014 |
| 2 | US-017 | kunden.html Kunden-CRM | US-013 |

## Auftrag
**Modus: sequentiell** (`--sequential`) — US-012/013/014 teilen
store.py/app.py. Reihenfolge: 012 → 013 → 014 → 015 → 016 → 017.
Pro Story: Tests (TEST.md) → impl → `pytest -q`/JS-check → Branch-
Commit. Graceful-DB-Pflicht. **Keine Migration/keine neuen Tabellen**
(reine Lese-Aggregation). client.html NICHT anfassen (anderes
Feature). Merge→master + Coolify-Deploy erst nach grünem Verify;
atomarer Build schützt Live.
