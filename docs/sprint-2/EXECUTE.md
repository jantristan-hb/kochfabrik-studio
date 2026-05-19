# Sprint 2 — kochfabrik-studio (EPIC-001)

> Übergabe-Prompt für `/sprint-execute`. @docs/sprint-2/EXECUTE.md

**Pfad:** /home/jrudat/work/03 AKARA Solutions GmbH/kochfabrik/kochfabrik-studio
**Sprint:** 2 · **Branch:** `sprint-2-chat-history` (GitHub, kein glab)
**Test:** `pytest -q` (DB-Tests: `TEST_DATABASE_URL=…` s. US-011)
**Deploy:** Coolify force (UUID yu2fqx0twmtqcp6zyx2e59si), atomar
**Repo:** GitHub `master` (Deploy-Repo; Merge→master via review/integrate)
**Basis:** Sprint 1 DONE @ master 46075c7 (db/models/store/numbering,
`chat_message`-Tabelle existiert, `_owner`, graceful DB).

## Sprint-Docs
- Stories: `docs/sprint-2/USER-STORIES.md`
- Architektur: `docs/sprint-2/FEATURE-ARCH.md`
- BDD: `docs/sprint-2/BDD.md` · Tests: `docs/sprint-2/TEST.md`

## Waves

| Wave | Story | Titel | Blocked-by |
|------|-------|-------|------------|
| 1 | US-006 | Chat-Turns persistieren | — |
| 1 | US-010 | Echtes Alembic-Setup (Carry-Over) | — |
| 1 | US-011 | pytest gegen Test-PG (Carry-Over) | — |
| 2 | US-007 | Angebot+Chat laden (owner-scoped) | US-006 |
| 2 | US-009 | Multi-Tenant-Härtung + Regression | US-006 |
| 3 | US-008 | chat.html exaktes Wiederöffnen | US-007 |

## Auftrag
**Modus: sequentiell** (`--sequential`) — US-006/007/009 teilen
app.py/store.py. Reihenfolge: US-010 → US-011 → US-006 → US-007 →
US-009 → US-008. Pro Story: Tests (TEST.md) rot → impl → `pytest -q`
grün → Branch-Commit. Graceful-DB-Pflicht. **Alembic-Caveat (US-010):
auf der Live-DB `alembic stamp head` (Tabellen existieren aus S1) —
NIE drop/create.** Merge→master + Coolify-Deploy erst nach grünem
Verify; atomarer Build schützt Live-Frontend.
