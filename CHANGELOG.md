# Changelog — kochfabrik-studio

Format: [Keep a Changelog](https://keepachangelog.com/de/1.1.0/)

## [Sprint 10] — 2026-06-09 — EPIC-003 Analyse-Fundament (doc-only)

### Hinzugefügt
- **US-036:** `docs/sprint-10/FINDINGS-STUDIO.md` — 12 belegte Studio-Findings (3 HIGH/3 MEDIUM/4 LOW, 2 VERWORFEN)
- **US-037:** `docs/sprint-10/FINDINGS-ENGINE.md` — 13 Engine-Findings, F-E-02 CRITICAL: Open Sans fehlt im Docker-Image
- **US-038:** `tools/font_report.py` + `docs/sprint-10/font-report.json` — exakte Font-/pt-Daten über 200/200 Referenz-PDFs (PyMuPDF-Spans, kein SIZE_K)
- **US-039:** `docs/sprint-10/FONT-REPORT.md` — Verteilung (Open Sans 72,8%), pt-Histogramm (14pt+8pt = 83%), Wingdings-Inventar, T1–T4-Konsequenzen; SIZE_K=0.78 als größenabhängig falsch belegt
- **US-040:** `docs/sprint-10/TEST-BASELINE.md` — realer Collect-Count 63 (PROGRESS behauptete 111), Lücken-Karte als EPIC-004-Refactoring-Gate
- **US-041:** `docs/adr/ADR-001-pptx-font-embedding.md` (proposed) — Empfehlung Server-Treue statt Embedding
- **US-042:** `docs/adr/ADR-002-monorepo-schnitt.md` (proposed) — Monorepo via git-subtree, vendor.sh entfällt, Coolify bleibt am Repo
- **US-043:** `docs/adr/ADR-003-pgbundle-vs-postgres.md` (proposed) — Hybrid: pgbundle read-only hinter EINER Bundle-Schicht

## [Sprint 4] — 2026-05-19 — EPIC-001 OAuth2 (Microsoft/Google) — **EPIC DONE**

### Hinzugefügt
- **US-018:** `backend/oauth.py` — stdlib-only, env-gated Provider-
  Config (Google + Microsoft). Ohne ENV `providers()={}`.
- **US-019:** `/api/oauth/providers`, `/api/oauth/{p}/login`,
  `/api/oauth/{p}/callback` — Authorization-Code-Flow, state-Cookie
  (CSRF), Auto-Registrierung in `app_user`, setzt identische
  `kf_sess`-Session wie Passwort-Login. PUBLIC erweitert.
- **US-021:** `login.html` Provider-Buttons (konditional, nur wenn
  aktiv); `?err=oauth` zeigt Hinweis.
- `store.ensure_user` (graceful) für OAuth-Auto-Registrierung.

### Geändert (ZERO-REGRESSION-Kern)
- **US-020:** `valid_cookie` erweitert — KF_USERS-Pfad bleibt
  ERSTER Short-Circuit (kein DB-Hit, bitidentisch). DB-Check
  `_db_user_ok` (psycopg2, TTL 60s, 2s-Timeout) NUR für Nicht-
  KF_USERS-User, **exception-safe** → False bei jedem Fehler.

### Externe Abhängigkeit
- Live-OAuth-Roundtrip braucht User-seitig registrierte Azure-AD- +
  Google-OAuth-Apps + Coolify-ENV `KF_OAUTH_*`. Bis dahin: OAuth
  inaktiv, Passwort-Login unverändert.

## [Sprint 3] — 2026-05-19 — EPIC-001 Dashboard + Bibliothek + Kunden-CRM

### Hinzugefügt
- **US-012:** `store.stats` + `GET /api/stats` — owner-scoped KPIs
  (Angebote, Kunden, Volumen Σ Zwischensummen, letzte 5).
- **US-013:** `store.list_customers`/`get_customer` + `GET /api/kunden`,
  `GET /api/kunde/{id}` (1 Kunde : n Angebote, owner-scoped, 404 fremd).
- **US-016:** `bibliothek.html` — durchsuchbares/filterbares
  Angebots-Archiv (q + Status, debounced).
- **US-017:** `web/kunden.html` (neu) — Kunden-CRM Liste + Detail;
  Nav-Link „Kunden" in Dashboard + Bibliothek.

### Geändert
- **US-014:** `list_offers(q, status)` + `/api/angebote?q=&status=`
  (additiv, abwärtskompatibel).
- **US-015:** `index.html` zeigt echte KPIs + zuletzt bearbeitete
  Angebote (Platzhalter-Daten entfernt); Listen-Zeilen öffnen
  `chat.html?offer={id}` (S2 exaktes Wiederöffnen).
- Reine Lese-Aggregation: keine Migration, keine neuen Tabellen.
  `client.html` unangetastet.

## [Sprint 2] — 2026-05-19 — EPIC-001 Chat-History + Restore + Tenant-Härtung

### Hinzugefügt
- **US-006: Chat-Persistenz** — `/api/angebot/chat` async + owner-
  scoped; Offer create-or-update + me/bot-Turns in `chat_message`
  (graceful bei DB-Ausfall).
- **US-007: Laden inkl. Verlauf** — `store.get_offer_full`,
  `/api/angebot/{id}` → `{angebot, chat}` (abwärtskompatibel).
- **US-008: Exaktes Wiederöffnen** — `chat.html ?offer={id}`
  rekonstruiert Editor-State + Chat-Stream 1:1, `history.replaceState`
  reload-fest.
- **US-010: Echtes Alembic** — `backend/alembic/` + Baseline 0001;
  `migrate.py` create_all (idempotent) + STAMP statt Re-Create auf
  Live-DB (droppt NIE), sonst `upgrade head`.
- **US-011: Test-Infra** — `conftest` async session/Test-PG-Fixtures
  + `pytest.ini` (`asyncio_mode=auto`).

### Geändert / Behoben
- **US-009: Multi-Tenant-Härtung** — `TenantError` + `_owned_offer`
  Owner-Check vor jedem `chat_message` Read/Write (Regressionstest).
- `requirements.txt`: psycopg2-binary, pytest, pytest-asyncio.

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
