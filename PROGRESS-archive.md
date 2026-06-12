# PROGRESS Archive — kochfabrik-studio

> Ausgelagert von /sprint-review 2026-06-09 (Rolling Window: max 5 Sprints in PROGRESS.md).

## Sprint 5 — EPIC-002 v2 Backend-Skelett (2026-05-20) — **DONE**

| Story | Titel | Status |
|-------|-------|--------|
| US-022 | praesentation_v2 APIRouter + Health/Suggestions/Slide/Render-Stub | DONE |
| US-023 | Models PraesV2Slide/PraesV2OfferSlide + Migration 0002 (idempotent) | DONE |
| US-024 | praesentation_v2_store: suggestions/set/get/clear/seed_default | DONE |
| US-025 | 19 pytest-Tests (Kategorien/Router/HTTP/Migration-File) | DONE |

**Live-verifiziert (master 7df66f1):** /api/praesentation_v2/health
gerouted (401 auth = Middleware-Schutz aktiv = Route erkannt), DB-Tabellen
`praes_v2_slide` + `praes_v2_offer_slide` per create_all angelegt. /api/
angebot/health bit-identisch (kein Regression). 66 Backend-Tests grün.
**Tech-Debt erkannt:** alembic.ini fehlt im Container — alembic upgrade
head läuft seit Sprint 1 graceful auf rc=255. Funktional kein Schaden
(create_all macht idempotent), aber Versionstracking ist drift.

---


## Sprint 4 — OAuth2 (Microsoft/Google) — **DONE**

| Story | Titel | Status |
|-------|-------|--------|
| US-018 | OAuth-Provider-Konfiguration (env-gated) | DONE |
| US-019 | OAuth-Routes (login/callback) + Auto-Registrierung | DONE |
| US-020 | valid_cookie um DB-User erweitern (ZERO-REGRESSION) | DONE |
| US-021 | login.html Provider-Buttons (konditional) | DONE |

**Live-verifiziert (master 6784307):** Binding-Gate Graceful-Fallback:
`providers()={}` ohne ENV, `/api/oauth/google/login`→404, **KF_USERS-
Cookie weiter gültig** (`valid_cookie=True`, Short-Circuit), `/api/stats`
mit Cookie funktioniert (S3 intakt). **Playwright login.html:** 0
OAuth-Buttons (providers leer), Passwort-Login unverändert → **Zero-
Regression bestätigt.** Externe Abhängigkeit: Live-OAuth-Roundtrip
braucht vom User registrierte Azure/Google-Apps + `KF_OAUTH_*`-ENV.

---

## Sprint 3 — Dashboard + Bibliothek + Kunden-CRM (2026-05-19) — **DONE**

| Story | Titel | Status |
|-------|-------|--------|
| US-012 | Stats/Aggregat-Endpoint (owner-scoped) | DONE |
| US-013 | Kunden-Endpoints + Store (1 Kunde : n Angebote) | DONE |
| US-014 | Angebote-Liste Such-/Status-Filter | DONE |
| US-015 | index.html Dashboard (echte KPIs) | DONE |
| US-016 | bibliothek.html suchbares Archiv | DONE |
| US-017 | kunden.html Kunden-CRM (Liste + Detail) | DONE |

**Live + Playwright-verifiziert (master 52196cd, deployed):** Backend-
Smoke (stats {1,1,1234.50}, get_customer, Tenant-Isolation, Filter) +
Playwright-E2E auf Live-Prod: Dashboard echte KPIs („1.234,50 €"),
Bibliothek Suche-Treffer/Empty-State, Kunden-CRM Liste→Detail→Reopen
`chat.html?offer=` (S2). Nur favicon-404 (benign). Smoke-Daten
bereinigt. client.html unangetastet (git-diff).

**Keine neuen Tabellen / keine Migration** (reine Lese-Aggregation auf
S1/S2-Schema). **Neue Seite:** `web/kunden.html`. client.html bleibt
unangetastet (anderes Feature). Letzter Funktions-Sprint (S4 OAuth
„später"). Waves: 1=US-012/013/014 (Backend, seq) · 2=US-015/016/017
(UI). Docs: `docs/sprint-3/*`. Nächster: `/sprint-execute kochfabrik-studio 3`.

---

## Sprint 2 — Chat-History + Exakte Wiederherstellung + Tenant-Härtung (2026-05-19) — **DONE**

| Story | Titel | Status |
|-------|-------|--------|
| US-006 | Chat-Turns je Angebot persistieren | DONE |
| US-007 | Angebot + Chat-Verlauf laden (owner-scoped) | DONE |
| US-008 | chat.html exaktes Wiederöffnen (State + Verlauf) | DONE |
| US-009 | Multi-Tenant-Härtung + Regression (inkl. Chat) | DONE |
| US-010 | Echtes Alembic-Setup (Carry-Over S1) | DONE |
| US-011 | pytest gegen Test-Postgres + CI-fähig (Carry-Over S1) | DONE |

**Live-verifiziert (master 69a6e8a, deployed):** `migrate: Alembic
gestampt auf 0001_baseline (kein Re-Create)` — Live-DB-Schema+Daten
intakt; `alembic_version=['0001_baseline']`; Chat-Smoke
save→add_chat(me/bot)→get_offer_full ok; **Tenant-Write geblockt
(TenantError)**, cross-tenant get→None; `/api/health db=true` (keine
Regression). chat.html-Restore JS-valide + Marker (URLSearchParams/
replaceState/offer_id).
**Plan-vs-Reality:** 6/6 DONE. Carry-Over S1 (Alembic/pytest-CI)
abgearbeitet. Hinweis: store.* binden zur Importzeit an DATABASE_URL
→ CI beide Vars auf Test-PG; Binding-Gate bleibt Live-Smoke.

**Nutzt (S1-Schema):** `chat_message`. Keine neuen Tabellen.
**Carry-Over S1 → konsumiert:** Alembic (US-010), pytest-CI (US-011).
**Docs:** `docs/sprint-2/{USER-STORIES,FEATURE-ARCH,FEATURE-IMPL,
FEATURE-SHEET-CHAT-HISTORY-RESTORE,BDD,TEST,EXECUTE}.md`. Waves:
1=US-006/010/011 · 2=US-007/009 · 3=US-008. Sequentiell (geteilte
app.py/store.py). Nächster Schritt: `/sprint-execute kochfabrik-studio 2`.

---

## Sprint 1 — DB-Fundament + Angebot-Persistenz + Nummernsequenz (2026-05-19) — **DONE**

| Story | Titel | Status |
|-------|-------|--------|
| US-001 | Postgres-Container + graceful Async-DB-Layer | DONE |
| US-002 | DB-Schema + idempotente Migration | DONE |
| US-003 | Atomare Nummernsequenzen (100001-A + KF-{Jahr}-{n}) | DONE |
| US-004 | Owner-scoped Repository/Service-Layer | DONE |
| US-005 | API-Endpoints + Integration Angebot-Generierung | DONE |

**Neue Tabellen (live in `kf-studio-pg`):** app_user, customer, offer,
chat_message, seq_counter
**Neuer Service:** Coolify Postgres `kf-studio-pg`
(UUID `tqg2xzsx9zau68jlhmuwyffj`, running:healthy)
**Live-verifiziert (master b0c7f36, deployed):** Migration idempotent,
DB_OK=true, Nummern `100001-A`/`KF-2026-0001`, Tenant-Isolation
bestätigt (owner-B sieht fremde Angebote NICHT), `/api/health` db:true.
**Plan-vs-Reality:** 5/5 DONE. Abweichung: Alembic → idempotentes
`create_all` (lean, Greenfield-äquivalent; echtes Alembic ab erstem
ALTER in S2+). Tests: Graceful/Format-Unit lokal grün; DB-Integration
**live gegen realen Postgres** verifiziert (repräsentativer als Mock).

## Carry-Over → Sprint 2
<!-- auto-generated by sprint-review-äquivalent 2026-05-19 -->
| ID | Titel | Typ | Quelle |
|----|-------|-----|--------|
| — | Echtes Alembic-Setup einführen | DEFERRED | S1 lean-Abweichung (bei erstem Schema-ALTER) |
| — | pytest-Suite gegen Test-PG in CI | DEFERRED | S1: DB-Test war live statt CI |

_(Keine FAILED-Stories — Sprint 1 vollständig.)_


## Bekannte Lücken (nicht in S1)
- Chat-History-Restore (S2) · Dashboard/Bibliothek-UI (S3) · OAuth2 (S4)
- Such/Filter, RBAC — bewusst out-of-scope

## Aktueller Zustand (2026-05-19)
| Metrik | Wert |
|--------|------|
| DB | keine (S1 führt Postgres ein) |
| Auth | KF_USERS-Env + signiertes Cookie (kf_sess) |
| Persistenz | keine (Angebot nur client-seitig) — S1 behebt das |

## Sprint 6 — EPIC-002 v2 Frontend (2026-05-20) — **DONE**

| Story | Titel | Status |
|-------|-------|--------|
| US-022a | web/praesentation_v2/index.html (Drei-Spalten CSS-Grid) | DONE |
| US-022b | assets/editor.js (State, API-Wrapper, Live-Edit-Debounce, Kat-Picker) | DONE |
| US-022c | Slide-Vorschlags-Karten (Klick = Auswahl, persistiert) | DONE |
| US-022d | 15 FE-Smoke-Tests (Layout-Marker, 7 Kategorien, kein Alt-API-Leak) | DONE |


## Sprint 7 — EPIC-002 v2 Kohärenz + Chat (2026-05-20) — **DONE**

| Story | Titel | Status |
|-------|-------|--------|
| US-026 | praesentation_v2_coherence: offer_context, defaults_for (7 Kat), merge_overrides | DONE |
| US-027 | GET /api/praesentation_v2/offer/{id}/context Endpoint | DONE |
| US-028 | POST /api/praesentation_v2/chat (Anthropic LLM, graceful) | DONE |
| US-029 | FE editor.js: Offer-Context-Merge + Chat-Endpunkt + Form-Refresh | DONE |

**Akzeptanzkriterium 5 erfüllt:** Slide-Overrides werden mit Offer-Defaults
(Kunde/Anlass/Konzept/Block-Bullets) gemergt — Präsentation matched das
verknüpfte Angebot.


## Sprint 8 — EPIC-002 v2 FE-Switch (2026-05-20) — **DONE**

| Story | Titel | Status |
|-------|-------|--------|
| US-030 | Alle Nav-Items (9 FE-Files) auf /praesentation_v2/ umgebogen | DONE |
| US-031 | praesentationsgenerator.html: LEGACY-Badge + Gold-Banner zum neuen Editor | DONE |
| US-032 | 7 Switch-Tests (Nav, Banner, kein Alt-href, v2-Route distinct) | DONE |


## Sprint 9 — EPIC-002 v2 Refactor (2026-05-20) — **DONE**

| Story | Titel | Status |
|-------|-------|--------|
| US-033 | web/praesentationsgenerator.html → web/_legacy/ verschoben | DONE |
| US-034 | REFACTOR-NOTES.md: Shared-Code-Analyse + Sprint-9-Backlog | DONE |
| US-035 | Tests aktualisiert (Legacy-Archiv statt aktiv) | DONE |

**Backend bleibt unverändert** für Rollback. `/api/praesentation/*` weiter
aktiv. **111 Tests grün.**

