# Changelog — kochfabrik-studio

Format: [Keep a Changelog](https://keepachangelog.com/de/1.1.0/)

## [Sprint 1] — 2026-05-19 — EPIC-001 DB-Fundament + Persistenz + Nummern

### Hinzugefügt
- **US-001: Graceful Async-DB-Layer** — eigener PostgreSQL-Container
  (Coolify `kf-studio-pg`), `backend/db.py` (DB_OK/ping, App bootet
  auch bei DB-Ausfall), `/api/health` meldet `db`.
- **US-002: DB-Schema** — `backend/models.py` (app_user, customer,
  offer/JSONB, chat_message, seq_counter), idempotente Migration
  (`backend/migrate.py`, Dockerfile-CMD migrate→serve).
- **US-003: Atomare Nummernsequenzen** — `backend/numbering.py`,
  Kundennummer `100001-A` (A=AI) + Angebotsnummer `KF-{Jahr}-{n}`,
  kollisionsfrei via `UPDATE..RETURNING`.
- **US-004: Owner-scoped Store** — `backend/store.py` save/get/list,
  strikte Multi-Tenant-Isolation.
- **US-005: API + Integration** — `/api/angebot/save`, `/api/angebote`,
  `/api/angebot/{id}`; `/api/angebot/pdf` persistiert + merged
  Kunden-/Angebotsnummer ins PDF. Alles graceful bei DB-Ausfall.

### Geändert
- `requirements.txt`: sqlalchemy[asyncio], asyncpg, alembic.
- `backend/app.py`: `_owner`-Cookie→Tenant-Abstraktion (OAuth-ready),
  `/api/health` async + db-Feld.
