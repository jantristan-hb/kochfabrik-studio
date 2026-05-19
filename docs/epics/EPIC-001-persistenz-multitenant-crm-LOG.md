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

### /sprint-execute
- ⏸ GATE: noch nicht gestartet. Prod-Infra-Bestätigung beim User offen (neuer Postgres-Container + DB-Migration auf Live-App, headless ohne Zwischen-Review = hart-irreversibel).
