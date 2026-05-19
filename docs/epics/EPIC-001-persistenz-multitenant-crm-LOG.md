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

## Sprint 2 — 2026-05-19

### /sprint-plan
- 6 Stories US-006..011: US-006 Chat-Turns persistieren · US-007 Angebot+Chat laden (owner-scoped) · US-008 chat.html exaktes Wiederöffnen · US-009 Multi-Tenant-Härtung+Regression · US-010 echtes Alembic (Carry-Over S1) · US-011 pytest gegen Test-PG (Carry-Over S1)
- Nutzt S1-`chat_message` (keine neuen Tabellen). Carry-Over S1 konsumiert (Alembic, pytest-CI).
- Waves: 1=US-006/010/011 · 2=US-007/009 · 3=US-008. Sequentiell empfohlen.
- Docs: docs/sprint-2/* committed. Status: PLAN. Nächster: /sprint-execute kochfabrik-studio 2.

### /sprint-execute + review/integrate (Sprint 2, headless+sequentiell)
- US-006..011 DONE. Branch `sprint-2-chat-history` → merged master **69a6e8a**.
- **Live-Verify (binding gate, realer Postgres):** neuer Build „Up", migrate-Log `Schema OK` + **`Alembic gestampt auf 0001_baseline (kein Re-Create)`** (Live-DB intakt, alembic_version=['0001_baseline'], 6 Tabellen), Chat-Smoke save→me/bot→get_offer_full ok, **Tenant-Write geblockt (TenantError)** + cross-tenant get→None, `/api/health db=true`. chat.html-Restore JS-valide. ✅
- Mode-Hinweis: „headless"-Arg → Skill-Default Agent-Teams, ABER EXECUTE.md schrieb sequentiell vor (US-006/007/009 teilen store.py/app.py) → headless+sequentiell gefahren (Pushback dokumentiert).
- Sprint 2 Status: **DONE**.

### Nächster Sprint
- Sprint 3 (Dashboard KPIs + Bibliothek suchbares Archiv + Kunden-CRM) — letzter Funktions-Sprint (S4 OAuth „später"). Via `/sprint-plan kochfabrik-studio` in frischem Kontext fortsetzen. Begründung wie S1: per-Sprint resumierbar, Kontext nach diesem Umfang erschöpft.

## Sprint 3 — 2026-05-19

### /sprint-plan
- 6 Stories US-012..017: US-012 Stats-Endpoint · US-013 Kunden-Endpoints+Store · US-014 Angebote Such-/Status-Filter · US-015 index.html Dashboard (echte KPIs) · US-016 bibliothek.html suchbares Archiv · US-017 kunden.html Kunden-CRM (neu).
- Reine Lese-Aggregation auf S1/S2-Schema — KEINE Migration, keine neuen Tabellen. client.html unangetastet. Letzter Funktions-Sprint (S4 OAuth „später").
- Carry-Over: keine (S1-DEFERRED Alembic/pytest in S2 erledigt). Waves: 1=US-012/013/014 (Backend, seq) · 2=US-015/016/017 (UI). Validierung grün (Refs ok, kunden.html neu, Dep-Graph azyklisch).
- Docs: docs/sprint-3/* committed. Status: PLAN. Nächster: /sprint-execute kochfabrik-studio 3.

### /sprint-execute + review/integrate (Sprint 3, headless+sequentiell)
- US-012..017 DONE. Branch `sprint-3-dashboard-crm` → merged master **52196cd**, deployed.
- **Live-Verify:** Backend-Smoke (stats {angebote1,kunden1,volumen1234.50}, get_customer, Tenant-Isolation→None, list_offers-Filter). **Playwright-E2E (Live-Prod, Cookie für jr@dangerously.ai gemintet):** Dashboard echte KPIs/„1.234,50 €" + Reopen-Link, Bibliothek Suche-Treffer + Empty-State, Kunden-CRM Liste→Detail→Angebot-Reopen `chat.html?offer=3`. Nur favicon-404 (benign). Smoke-Daten bereinigt, client.html unangetastet.
- Sprint 3 Status: **DONE**. EPIC-001 funktional komplett (S1+S2+S3). Verbleibend: S4 OAuth.

## Sprint 4 — 2026-05-19 (EPIC-Abschluss)

### /sprint-plan + /sprint-execute + integrate (headless+sequentiell)
- 4 Stories US-018..021 DONE. Branch `sprint-4-oauth` → merged master **6784307**, deployed.
- **Binding-Gate live-verifiziert (Zero-Regression):**
  - `providers()=={}` ohne ENV (env-gated, korrekt inaktiv)
  - `/api/oauth/google/login` → HTTP 404 (Provider inaktiv)
  - `valid_cookie(KF_USERS-User)` = **True** (Short-Circuit, kein DB-Hit, bitidentisch zu vor S4)
  - `/api/stats` mit KF_USERS-Cookie liefert {} — S3-Funktionalität intakt
  - **Playwright login.html:** 0 OAuth-Buttons (providers leer), Passwort-Input + Login-Button vorhanden → exakt heutiges Verhalten
- Externe Abhängigkeit dokumentiert: Live-OAuth-Roundtrip braucht vom User registrierte Azure-AD + Google-OAuth-Apps + Coolify-ENV (`KF_OAUTH_GOOGLE_ID/_SECRET`, `KF_OAUTH_MS_ID/_SECRET/_TENANT`, `KF_OAUTH_REDIRECT_BASE`). Bis dahin: Code ready, OAuth inaktiv, kein Schaden.

### EPIC-001 — DONE (S1 ✅ S2 ✅ S3 ✅ S4 ✅)
Persistenz, Multi-Tenant & CRM für den Angebotsgenerator funktional komplett:
DB-Fundament (Postgres `kf-studio-pg`) + atomare Nummern (`100001-A` /
`KF-{Jahr}-{n}`) + Chat-History + exaktes Wiederöffnen + Dashboard +
Bibliothek + Kunden-CRM + OAuth2 (env-gated, zero-regression).
Headless durchgezogen, je Sprint live gegen den realen Postgres
verifiziert, sequentiell + integrate-gated, atomare Coolify-Builds.
