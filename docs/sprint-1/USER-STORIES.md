# Sprint 1 — DB-Fundament + Angebot-Persistenz + Nummernsequenz

> EPIC-001 Sprint 1. Projekt: kochfabrik-studio (FastAPI, GitHub `master`,
> Coolify-Deploy UUID `yu2fqx0twmtqcp6zyx2e59si`). Stack: FastAPI +
> **PostgreSQL (eigener Coolify-Container)** + SQLAlchemy 2 async +
> asyncpg + Alembic. Tests: pytest. Kein glab (GitHub) → USER-STORIES.md
> ist Single Source.
>
> **Sicherheits-Design (Pflicht in allen Stories):** DB-Schicht
> **graceful** wie das `ENGINE_OK`-Muster — bootet die App auch bei
> DB-Ausfall, bestehende Endpoints (chat/pdf/praes) laufen unverändert
> weiter, nur Persistenz degradiert. `/api/health` meldet `db:true|false`.
> Migrationen idempotent. Neuer Postgres-Container ist additiv.

## Phasen
Foundation (US-001) → Schema (US-002) → Numbering (US-003) →
Service (US-004) → API+Integration (US-005). Inhärent sequenziell
(DB-Fundament-Kette).

---

### US-001: PostgreSQL-Container + graceful Async-DB-Layer

**Context:** Studio ist zustandslos. Fundament für jede Persistenz:
eigener Postgres + Connection-Layer, der die App NICHT zum Absturz
bringt wenn die DB (noch) nicht da ist.

**Input:**
- `backend/app.py` (ENGINE_OK-Graceful-Muster ab Zeile 266 als Vorlage)
- `requirements.txt`, `Dockerfile`, Coolify-API (`COOLIFY_TOKEN` aus ~/work/.env)

**Task:**
1. Coolify: neuen PostgreSQL-Service `kf-studio-pg` anlegen (API,
   gleicher Server `yu2fqx0twmtqcp6zyx2e59si`-Projekt). Interne
   Connection-URL als Coolify-ENV `DATABASE_URL` der App setzen.
2. `requirements.txt`: `sqlalchemy[asyncio]>=2`, `asyncpg>=0.29`,
   `alembic>=1.13`.
3. `backend/db.py`: async `engine` + `async_sessionmaker` aus
   `os.environ["DATABASE_URL"]` (psycopg→asyncpg URL-Normalisierung).
   `DB_OK`/`DB_ERR`-Flag analog `ENGINE_OK`; `async def ping()`.
   Import in app.py darf NIE den Boot brechen (try/except).
4. `/api/health`: Feld `db: bool` + `db_error` ergänzen.

**Output:**
- `backend/db.py` — Engine/Session/DB_OK/ping
- `requirements.txt`, `Dockerfile` (falls Build-Deps nötig), `backend/app.py` (health)
- Coolify: Service `kf-studio-pg` + `DATABASE_URL`-ENV

**BDD:** → `BDD.md#us-001-postgres-graceful-db-layer`
**Test-Stubs:** → `TEST.md#us-001-postgres-graceful-db-layer`

**Verify:**
```bash
python -c "import backend.db"                       # kein Import-Crash
curl -s localhost:8000/api/health | python -m json.tool | grep -i '"db"'
```
**Blocked-by:** —

---

### US-002: DB-Schema + Alembic-Migrationen

**Context:** Tabellen für User/Kunde/Angebot/Chat. Chat-Tabelle wird
erst in Sprint 2 genutzt, Schema aber jetzt mit angelegt.

**Input:** `backend/db.py` (US-001), Angebot-Modell-Shape (JS `A`-Objekt
+ engine `angebot_model.Angebot`)

**Task:**
1. `backend/models.py` (SQLAlchemy 2 declarative):
   - `app_user(email PK, created)`
   - `customer(id PK, kundennummer UNIQUE, name, owner_email FK→app_user, created)`
   - `offer(id PK, angebotsnummer UNIQUE, customer_id FK→customer, owner_email FK, state JSONB, status, created, updated)`
   - `chat_message(id PK, offer_id FK→offer, role, content, ts)`
   - `seq_counter(name PK, value)` — für atomare Nummern (US-003)
2. Alembic init (`backend/alembic/`, `alembic.ini`), erste Revision =
   gesamtes Schema. Idempotent (`upgrade head` mehrfach safe).
3. Container-Entrypoint: `alembic upgrade head` vor uvicorn-Start,
   Fehler nicht-fatal (graceful: loggen, App startet trotzdem).

**Output:**
- `backend/models.py`, `backend/alembic/`, `alembic.ini`
- `Dockerfile`/Entrypoint-Skript (migrate→serve, graceful)

**BDD:** → `BDD.md#us-002-db-schema-migrationen`
**Test-Stubs:** → `TEST.md#us-002-db-schema-migrationen`

**Verify:**
```bash
alembic upgrade head && alembic upgrade head   # 2x = idempotent, kein Fehler
python -c "from backend.models import Offer,Customer,ChatMessage,AppUser,SeqCounter"
```
**Blocked-by:** US-001

---

### US-003: Atomare Nummernsequenzen (Kunde 100001-A + Angebot)

**Context:** Fortlaufende, kollisionsfreie Kundennummer `100001-A`
(A=AI) und separate Angebotsnummer — auch bei parallelen Requests.

**Input:** `backend/models.py` (`seq_counter`), US-002

**Task:**
1. `backend/numbering.py`: `async def next_kundennummer(session)` →
   `f"{100000+n:06d}-A"` (Start 100001-A); `async def
   next_angebotsnummer(session)` → fortlaufend (Format
   `KF-{jahr}-{n:04d}` oder reine Sequenz — in FEATURE-ARCH festgelegt).
2. Atomar via `UPDATE seq_counter SET value=value+1 ... RETURNING value`
   (row-lock, kein Race). Counter lazy-init.
3. Idempotenz: dieselbe Funktion liefert NIE zweimal dieselbe Nummer.

**Output:** `backend/numbering.py`

**BDD:** → `BDD.md#us-003-atomare-nummernsequenzen`
**Test-Stubs:** → `TEST.md#us-003-atomare-nummernsequenzen`

**Verify:**
```bash
pytest backend/tests/test_numbering.py -q   # inkl. Nebenläufigkeits-Test
```
**Blocked-by:** US-002

---

### US-004: Owner-scoped Repository/Service-Layer

**Context:** Angebot speichern/laden/listen — strikt auf den
eingeloggten User (owner_email) gescoped (Multi-Tenant-Fundament).

**Input:** US-002, US-003

**Task:**
1. `backend/store.py`:
   - `async def save_offer(owner_email, angebot: dict) -> dict`:
     Customer upsert (per Name+owner), bei Erstanlage
     `next_kundennummer`/`next_angebotsnummer` zuweisen, `offer.state`
     = vollständiges Angebot-JSON, `updated` setzen. Gibt
     `{offer_id, angebotsnummer, kundennummer}` zurück.
   - `async def get_offer(owner_email, offer_id) -> dict|None` (NUR
     eigene; fremde → None).
   - `async def list_offers(owner_email) -> list[dict]` (nur eigene,
     Kurzfelder: id, nummern, kunde, anlass, updated).
2. Alle Queries `WHERE owner_email = :owner` — keine Cross-Tenant-Leaks.

**Output:** `backend/store.py`

**BDD:** → `BDD.md#us-004-owner-scoped-store`
**Test-Stubs:** → `TEST.md#us-004-owner-scoped-store`

**Verify:**
```bash
pytest backend/tests/test_store.py -q   # inkl. Tenant-Isolations-Test
```
**Blocked-by:** US-002, US-003

---

### US-005: API-Endpoints + Integration in Angebot-Generierung

**Context:** Speichern/Listen/Laden über die App; beim PDF-Erzeugen
automatisch persistieren + Kunden-/Angebotsnummer ins Angebot/PDF.

**Input:** `backend/store.py` (US-004), bestehende `/api/angebot/*`
(Cookie-Auth `valid_cookie`, COOKIE `kf_sess`)

**Task:**
1. Auth-Helper: aus Cookie die `owner_email` ableiten
   (`valid_cookie`+Decode); 401 wenn ungültig.
2. `POST /api/angebot/save` {angebot} → `store.save_offer`,
   Response `{offer_id, angebotsnummer, kundennummer}`.
3. `GET /api/angebote` → `store.list_offers(owner)`.
4. `GET /api/angebot/{id}` → `store.get_offer(owner,id)` (404/403 wenn
   nicht eigenes).
5. `/api/angebot/pdf`: vor Render `save_offer` aufrufen, zugewiesene
   Nummern in `angebot` mergen (angebots_nr/kundennr) → erscheinen im
   PDF. Graceful: DB down → PDF trotzdem (ohne Persistenz, Warnung).
6. Alle neuen Endpoints scopen auf Cookie-User.

**Output:** `backend/app.py` (4 Endpoints + Auth-Helper + pdf-Hook)

**BDD:** → `BDD.md#us-005-api-endpoints-integration`
**Test-Stubs:** → `TEST.md#us-005-api-endpoints-integration`

**Verify:**
```bash
pytest backend/tests/test_api_angebot.py -q
# manuell: login → POST /api/angebot/save → GET /api/angebote zeigt es
```
**Blocked-by:** US-004

---

## Dependency-Graph / Waves

| Wave | Stories |
|------|---------|
| 1 | US-001 |
| 2 | US-002 |
| 3 | US-003 |
| 4 | US-004 |
| 5 | US-005 |

Inhärent sequenziell (DB-Fundament-Kette) — bewusst, kein Planungsfehler.
Headless: Pfad A (sequentiell) statt Agent-Teams sinnvoll (jede Story
baut auf der vorigen).
