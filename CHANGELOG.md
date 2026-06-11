# Changelog — kochfabrik-studio

Format: [Keep a Changelog](https://keepachangelog.com/de/1.1.0/)

## [Unreleased]

### Bugfixes
- **Fixed:** Designer-PDF-Upload lieferte immer 400 (isinstance gegen FastAPI-UploadFile-Subklasse; request.form() liefert Starlette-Instanzen) (#60)

## [Sprint 13] — 2026-06-11 — Präsentationsdesigner (EPIC-006)

### Hinzugefügt
- **US-061/062: Designer-Vorschlags-API** — `POST /api/designer/suggest`: Angebot (PDF-Upload, gespeichert oder JSON) → pro Gang Top-5 Slide-Kandidaten (1 Embed-Batch + bundle-Ranking, ADR-003-konform) + Pflicht-Slide-Gruppe, je mit Score und Preview-URL; Live-Smoke semantisch bewiesen (Vorspeise→„Finger Bites" 0.869 …)
- **US-063: Designer-Seite** — `web/designer.html` + `designer.js` (Design-2, 3-Bereichs-Layout), Nav-Eintrag auf allen Seiten
- **US-065: Storyboard** — Klick-Übernahme, Reorder (↑/↓), Entfernen, Duplikat-Schutz, sessionStorage-Persistenz (`kfDesigner.v1`, reload-fest)
- **US-064: Vorschlags-Karten** — Upload/Angebots-Auswahl → Vorschlags-Spalten mit PNG-Karten (404→Platzhalter), „im Deck"-Markierung
- **US-066: Freitext-Suche im Designer** — Slidesuche-Treffer als gleichartige Karten neben den Vorschlägen, gleiche Board-Übernahme
- **US-067: PPTX-Download + E2E** — Storyboard → `/api/slidesuche/download`; E2E-Beweis suggest→Kandidat→Download→valide PPTX (reconstruct.js, 2,4 MB)
- **US-068: live_verify Deep-Check** — `LIVE_DEEP=1` prüft engine/korpus hinter dem Auth-Gate (Nacharbeit Korpus-Mount-Incident 2026-06-11)

## [Sprint 12] — 2026-06-11 — EPIC-004-Abschluss + EPIC-009

### Hinzugefügt
- **US-052:** Täglicher Backup-Zyklus auf dem Host (Cron 03:30, 14-Tage-Rotation, Off-Host-Pull) → `docs/ops/BACKUP-CYCLE.md`
- **US-055:** `engine/scripts/bundle.py` — die EINE pgbundle-Schicht (ADR-003); Ranking bit-identisch, als Gold-Regressionstest festgenagelt
- **US-057:** Alembic-Container-Abnahme — Migrations-Schritt rc=0 + `alembic_version`-Stamp bewiesen, `SIM_GATE_DB=1`-Block im Sim-Gate (F-S-01 endgültig zu)
- **US-058:** Restore-Probe real durchgespielt (alle Kern-Tabellen + Rowcounts) + Korpus-Wiederaufbau-Doku → `docs/ops/RESTORE-RUNBOOK.md`
- **US-059:** Projekt-`CLAUDE.md` (Stack, Gates, Deploy-Wahrheit „kein Auto-Deploy", Architektur-Regeln, Sprint-Tabelle)

### Geändert
- **US-053/054:** Backend modularisiert — `backend/routers/{auth,bildgenerator,angebot,praesentation}.py` + `engine_glue.py`; `app.py` 936→91 Zeilen, Routen-Inventar byte-identisch
- **US-056:** Engine-Tooling-Split per Import-Graph — 13 Runtime-Module bleiben `engine/scripts/`, 33 Build-Tools nach `engine/tooling/` (inkl. Anti-Namensraten-Befunde gen_fiktiv + build_angebot_template)
- **US-060:** Engine-Repo `pptxgenerator_v2` auf GitHub archiviert (read-only, Verweis aufs Monorepo)

## [Sprint 11] — 2026-06-10 — EPIC-004 Monorepo-Schnitt (M1–M3)

### Hinzugefügt
- **US-044:** Erst-Backup vor Cutover — pg_dump `kf-studio-pg` off-host (Integrität verifiziert) + Korpus-Volume-Inventar (201 Decks, 5,2 GB) → `docs/sprint-11/BACKUP-VERIFY.md`
- **US-046:** `backend/tests/test_charakterisierung.py` — TestClient-Verhaltens-Netz (DB-los); Suite erstmals lokal 0 failed (Alembic-Namespace-Fix)
- **US-050:** `tools/sim_gate.sh` — Container-Smoke-Gate (Build, Health, Engine-Import, reconstruct.js-Probe), Pflicht vor jedem Cutover
- **US-051:** `tools/live_verify.sh` + `docs/sprint-11/CUTOVER-RUNBOOK.md` — Prod-Health-Check + Cutover-/Rollback-Ablauf

### Geändert
- **US-045:** Engine-Repo konsolidiert — Mac-Migrations-Diff committet; Build-DSN + CORPUS_DIR env-übersteuerbar (F-E-10), Defaults identisch
- **US-047:** Engine via `git subtree` ins Studio-Repo (Historie erhalten, 26 Commits), Layout flachgezogen (`engine/scripts` statt `engine/phase0/…`), `data/` + `node_modules` aus vendored Stand gerettet
- **US-048:** Backend-Pfade repo-intern (`_VEND/_SIB`-Heuristik entfernt), `vendor.sh` gelöscht, README auf Monorepo-Workflow
- **US-049:** Dockerfile auf Monorepo-Layout + `COPY alembic.ini` (behebt rc=255-Migrations-Drift im Container, F-S-01) + `.dockerignore`

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
