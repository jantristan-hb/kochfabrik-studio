# EPIC-001 Implementation Log — Persistenz, Multi-Tenant & CRM

> Headless-Run gestartet 2026-05-19. Observer protokolliert plan/execute/review je Sprint.
> (Observer-Agent war one-shot → Lead pflegt das LOG direkt weiter.)

## Sprint 1 — 2026-05-19

### /sprint-plan
- Commit: kochfabrik-studio master `ca14d49`
- Stories (5, sequenziell — DB-Fundament-Kette):
  - US-001: PostgreSQL-Container (Coolify `kf-studio-pg`) + graceful Async-DB-Layer (DB_OK-Muster wie ENGINE_OK), `/api/health` db-Flag
  - US-002: DB-Schema + Alembic-Migrationen (app_user, customer, offer, chat_message, seq_counter), idempotent
  - US-003: Atomare Nummernsequenzen — Kundennummer `100001-A` (A=AI) + Angebotsnummer `KF-{Jahr}-{n}`
  - US-004: Owner-scoped Repository/Service-Layer (save/get/list, Tenant-Isolation)
  - US-005: API-Endpoints (save/list/load) + Integration in `/api/angebot/pdf` (persistieren + Nummern ins PDF)
- Scope: DB-Persistenzfundament. Lean-adaptiert (FastAPI/pytest, GitHub kein glab). Sicherheits-Design: DB graceful, Postgres additiv, Migrationen idempotent.
- Docs: `docs/sprint-1/{USER-STORIES,FEATURE-ARCH,FEATURE-IMPL,FEATURE-SHEET-DB-PERSISTENZ,BDD,TEST,EXECUTE}.md` + `PROGRESS.md`.

### /sprint-execute (sequentiell, Lead — User-OK „voll headless")
- US-001 DONE: Coolify-Postgres `kf-studio-pg` (UUID tqg2xzsx9zau68jlhmuwyffj, running:healthy) + `backend/db.py` graceful (DB_OK/ping) + `/api/health` db-Feld + DATABASE_URL-ENV gesetzt
- US-002 DONE: `backend/models.py` 5 Tabellen + `migrate.py` idempotent (create_all; Alembic deferred) + Dockerfile CMD migrate→serve
- US-003 DONE: `backend/numbering.py` atomar (UPDATE..RETURNING) — `100001-A` + `KF-{Jahr}-{n}`
- US-004 DONE: `backend/store.py` owner-scoped save/get/list, Tenant-Isolation
- US-005 DONE: `backend/app.py` `_owner`-Helper + `/api/angebot/save|/angebote|/{id}` + `/pdf` persistiert+merged Nummern; alles graceful
- Probleme: keine FAILED. Lean-Abweichung Alembic→create_all (Carry-Over DEFERRED). asyncpg lokal fehlend → DB-Test live statt CI.

### /sprint-review + /integrate (lean-Outcomes)
- Plan-vs-Reality: 5/5 DONE, 1 bewusste Abweichung (Alembic). 
- Branch `sprint-1-db-fundament` → merged master **b0c7f36**, gepusht. CHANGELOG + PROGRESS + Epic aktualisiert.
- **Live-Verify (binding gate, realer Postgres):** Container neu „Up", `migrate: Schema OK (idempotent)`, Tabellen [app_user,chat_message,customer,offer,seq_counter], `DB_OK=True`, Smoke save→`{offer_id:1, KF-2026-0001, 100001-A}`, get OK, **Tenant-Isolation: owner-B sieht 0**, `/api/health db:true`. ✅
- Sprint 1 Status: **DONE**.

### Nächster Sprint
- Sprint 2 (Chat-History + Multi-Tenant-Scoping + Restore) — via `/sprint-plan kochfabrik-studio` in frischem Kontext fortsetzen (Loop ist per-Sprint resumierbar; PROGRESS+LOG tragen den State). Begründung: 3-Sprint-Prod-Epic nicht sicher in einem erschöpften Kontext one-shot-bar; Epic-Design ist genau dafür sequenziell+integrate-gated.
