# Sprint 2 — Chat-History + Exakte Wiederherstellung + Tenant-Härtung

> EPIC-001 Sprint 2. Baut auf Sprint 1 (DB-Fundament, master 46075c7):
> `backend/{db,models,store,numbering}.py` + `offer.state` JSONB +
> `chat_message`-Tabelle (S1 nur Schema, **S2 nutzt sie**). Cookie-Auth
> `_owner(request)`. Stack: FastAPI + PostgreSQL + SQLAlchemy 2 async.
> Tests: pytest. GitHub → kein glab. Graceful-DB-Pflicht (DB_OK-Muster).
>
> Carry-Over aus S1 (DEFERRED, eingeplant): echtes Alembic (US-010),
> pytest gegen Test-PG (US-011).

## Phasen
Persistenz (US-006) → Laden (US-007) → Frontend-Restore (US-008) →
Tenant-Härtung (US-009) · parallel Tech-Debt (US-010, US-011).

---

### US-006: Chat-Turns je Angebot persistieren

**Context:** Chat-Verlauf geht heute verloren. Jeder Turn muss
offer-scoped gespeichert werden, damit S2-Restore exakt aufsetzt.

**Input:** `backend/app.py` `/api/angebot/chat` (Z.449 `def
angebot_chat`, sync) + `_chat_patch`; `backend/store.py` (`save_offer`,
`_owner`); `chat_message`-Model (S1).

**Task:**
1. `/api/angebot/chat` → `async def`, `request: Request`. owner via
   `_owner`; 401 wenn keiner.
2. Offer sicherstellen: hat `r.angebot` kein `_offer_id` → `save_offer`
   (legt Offer/Nummern an), `_offer_id` ins zurückgegebene Angebot.
3. `backend/store.py`: `async def add_chat(owner, offer_id, role,
   content)` — owner-Check auf Offer, dann `chat_message` insert.
4. Nach erfolgreichem `_chat_patch`: User-Message (`role="me"`) + Bot-
   Antwort (`role="bot"`) via `add_chat` speichern. Graceful: DB-Ausfall
   → Chat funktioniert weiter, nur ohne Persistenz (Warnung im Resp).
5. Response zusätzlich `offer_id` zurückgeben.

**Output:** `backend/app.py` (chat-Endpoint async + persist),
`backend/store.py` (`add_chat`)

**BDD:** → `BDD.md#us-006-chat-turns-persistieren`
**Test-Stubs:** → `TEST.md#us-006-chat-turns-persistieren`

**Verify:**
```bash
python3 -c "import ast,glob;[ast.parse(open(f).read()) for f in glob.glob('backend/*.py')];print('syntax OK')"
pytest backend/tests/test_sprint2.py -q -k chat   # live-PG-Pfad s. US-011
```
**Blocked-by:** —

---

### US-007: Angebot + Chat-Verlauf laden (owner-scoped)

**Context:** Wiederöffnen braucht state UND Chat-Verlauf in einem Zug.

**Input:** US-006; `store.get_offer` (S1); `chat_message`.

**Task:**
1. `backend/store.py`: `async def get_offer_full(owner, offer_id) ->
   dict|None` → `{angebot: state, chat: [{role,content,ts}...]}`
   (ts ISO, chronologisch). Owner-Check (fremd → None).
2. `GET /api/angebot/{id}` liefert jetzt `{angebot, chat}` (statt nur
   angebot) — abwärtskompatibel: `angebot` bleibt Top-Level-Key.
3. Graceful + 404 bei fremd/fehlt.

**Output:** `backend/store.py` (`get_offer_full`), `backend/app.py`
(`/api/angebot/{id}`)

**BDD:** → `BDD.md#us-007-angebot-chat-laden`
**Test-Stubs:** → `TEST.md#us-007-angebot-chat-laden`

**Verify:**
```bash
pytest backend/tests/test_sprint2.py -q -k load
```
**Blocked-by:** US-006

---

### US-008: chat.html — exaktes Wiederöffnen (State + Verlauf)

**Context:** „An exakt gleicher Stelle weitermachen" — Editor-State
UND Chat-Stream beim Öffnen rekonstruieren.

**Input:** US-007 (`GET /api/angebot/{id}` → {angebot,chat});
`web/chat.html` (`A`, `renderForm()`, `add(role,txt)`, `#stream`).

**Task:**
1. Beim Laden: `?offer={id}` aus `location.search` lesen. Falls
   gesetzt → `fetch('/api/angebot/'+id)` → `A=d.angebot`,
   `A.veranstaltung||{}`, `A.bloecke||[]`, `renderForm()` +
   `collect();syncTotals()` (S1-Konsistenz).
2. Chat-Verlauf: `d.chat` chronologisch via `add(m.role, esc(content))`
   in `#stream` abspielen (kein Re-Request an den Bot).
3. Nach jeder Bot-Antwort `A._offer_id` aus Response übernehmen; URL
   per `history.replaceState` auf `?offer={id}` setzen (Reload-fest).
4. Kein Offer-Param → unverändertes Verhalten (neues Angebot).

**Output:** `web/chat.html`

**BDD:** → `BDD.md#us-008-chat-html-wiederoeffnen`
**Test-Stubs:** → `TEST.md#us-008-chat-html-wiederoeffnen`

**Verify:**
```bash
python3 - <<'PY'
import re;h=open('web/chat.html').read()
open('/tmp/c.js','w').write('\n'.join(re.findall(r'<script>(.*?)</script>',h,re.S)))
PY
node --check /tmp/c.js && echo "JS OK"
```
**Blocked-by:** US-007

---

### US-009: Multi-Tenant-Härtung + Regression (inkl. Chat)

**Context:** Chat-Persistenz darf keine neue Cross-Tenant-Lücke
öffnen. Alle Offer/Chat-Pfade owner-geprüft.

**Input:** US-006/007; `backend/store.py`.

**Task:**
1. `add_chat` + `get_offer_full` + chat-Endpoint: vor JEDEM
   chat_message-Read/Write Offer-Ownership prüfen (Offer.owner_email
   == owner), sonst Abbruch (None/403).
2. Regressionstest: User B kann weder Chat von A's Offer schreiben
   noch lesen; `get_offer_full` für fremd → None.
3. Audit: grep alle `chat_message`/`Offer`-Queries → jede hat
   owner-Scope.

**Output:** `backend/store.py` (Härtung), `backend/tests/test_sprint2.py`

**BDD:** → `BDD.md#us-009-tenant-haertung`
**Test-Stubs:** → `TEST.md#us-009-tenant-haertung`

**Verify:**
```bash
pytest backend/tests/test_sprint2.py -q -k tenant
```
**Blocked-by:** US-006

---

### US-010: Echtes Alembic-Setup (Carry-Over S1)

**Context:** S1 nutzt idempotentes `create_all` (lean). Ab jetzt echte
Migrations-Historie für künftige ALTERs (ohne Datenverlust auf der
Live-DB mit bestehendem Schema).

**Input:** `backend/models.py`, `backend/migrate.py`, Dockerfile-CMD.

**Task:**
1. Alembic init (`backend/alembic/`, `alembic.ini`), `env.py` async
   (asyncpg) gegen `DATABASE_URL`, `target_metadata = Base.metadata`.
2. Baseline-Revision = aktuelles S1-Schema. Bestehende Live-DB:
   `alembic stamp head` (kein Re-Create — Tabellen existieren schon).
3. `migrate.py`/Entrypoint: `alembic upgrade head` (idempotent, no-op
   wenn auf head) statt `create_all`; Fehler nicht-fatal (graceful).
4. Doku: neue Migration = `alembic revision --autogenerate`.

**Output:** `backend/alembic/`, `alembic.ini`, `backend/migrate.py`,
`Dockerfile`

**BDD:** → `BDD.md#us-010-alembic-setup`
**Test-Stubs:** → `TEST.md#us-010-alembic-setup`

**Verify:**
```bash
alembic -c alembic.ini heads          # genau 1 head
alembic upgrade head && alembic upgrade head   # 2x idempotent
```
**Blocked-by:** —

---

### US-011: pytest gegen Test-Postgres + CI-fähig (Carry-Over S1)

**Context:** S1-DB-Tests waren skip/live. Wiederholbar in CI gegen
eine Test-DB.

**Input:** `backend/tests/conftest.py` (S1), `requirements.txt`.

**Task:**
1. `requirements`-dev: `pytest`, `pytest-asyncio`.
2. `conftest.py`: async `session`/`session_factory`-Fixture gegen
   `TEST_DATABASE_URL` (Docker-PG); je Test Transaktion+Rollback;
   skip sauber wenn nicht gesetzt.
3. S1+S2 DB-Tests (numbering/store/chat/tenant) laufen damit grün.
4. `docs/sprint-2/EXECUTE.md` + README-Snippet: wie lokal/CI ausführen
   (`docker run postgres` → `TEST_DATABASE_URL=… pytest`).

**Output:** `backend/tests/conftest.py`, `requirements.txt`,
`backend/tests/test_sprint2.py`

**BDD:** → `BDD.md#us-011-pytest-test-pg`
**Test-Stubs:** → `TEST.md#us-011-pytest-test-pg`

**Verify:**
```bash
TEST_DATABASE_URL=postgresql+asyncpg://… pytest backend/tests -q
```
**Blocked-by:** —

---

## Dependency-Graph / Waves

| Wave | Stories | Hinweis |
|------|---------|---------|
| 1 | US-006, US-010, US-011 | unabhängig (US-010/011 = Tech-Debt parallel) |
| 2 | US-007, US-009 | beide [US-006] |
| 3 | US-008 | [US-007] |

3 Waves. Headless: Pfad A sequentiell empfohlen (geteilte Dateien
app.py/store.py über US-006/007/009 → Agent-Teams = Konflikt-Risiko).
