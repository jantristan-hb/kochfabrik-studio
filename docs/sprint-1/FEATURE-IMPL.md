# FEATURE-IMPL — Sprint 1

## Stack-Ergänzungen
`requirements.txt`: `sqlalchemy[asyncio]>=2`, `asyncpg>=0.29`,
`alembic>=1.13`. Dev: `pytest`, `pytest-asyncio`.

## Dateien (neu)
```
backend/db.py          # async engine + sessionmaker + DB_OK/ping (graceful)
backend/models.py      # SQLAlchemy 2 declarative (5 Tabellen)
backend/numbering.py   # atomare seq_counter-Zähler
backend/store.py       # owner-scoped save/get/list
backend/alembic/ + alembic.ini   # Migrationen (rev1 = ganzes Schema)
backend/entrypoint.sh  # alembic upgrade head (graceful) → uvicorn
backend/tests/{conftest,test_db_graceful,test_schema,test_numbering,test_store,test_api_angebot}.py
```
Geändert: `requirements.txt`, `Dockerfile` (entrypoint), `backend/app.py`
(health db-Feld, Auth-Helper owner_email, 4 Endpoints, pdf-Hook).

## Graceful-Muster (Pflicht, analog ENGINE_OK app.py:266ff)
```python
DB_OK, DB_ERR = False, ""
try:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    _url = os.environ.get("DATABASE_URL","").replace(
        "postgresql://","postgresql+asyncpg://")
    engine = create_async_engine(_url, pool_pre_ping=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    DB_OK = True
except Exception as e:                      # noqa
    engine = Session = None
    DB_ERR = f"{type(e).__name__}: {e}"
```
`ping()` macht `SELECT 1`; Endpoints prüfen `DB_OK and await ping()`,
sonst graceful (save/list → 503-JSON, /pdf → render ohne Persistenz).

## Daten-Flows
**Save:** Cookie→owner_email → `save_offer` → customer upsert (name+owner)
→ falls neu: `next_kundennummer`/`next_angebotsnummer` → offer.state=JSON
→ commit → {ids,nummern}.
**PDF (Happy):** /pdf → save_offer → Nummern in angebot mergen → engine
render → PDF mit Nummern.
**PDF (DB-Fehler):** save_offer wirft → fangen, Warnung loggen, render
ohne Nummern/Persistenz (kein 500).
**Load:** /angebot/{id} → get_offer(owner,id) → state | 404.

## Phasen
1 Foundation (US-001 db.py+Coolify-PG+health) → 2 Schema (US-002
models+alembic+entrypoint) → 3 Numbering (US-003) → 4 Service (US-004
store) → 5 API (US-005 endpoints+pdf-hook). Sequenziell.

## Pitfalls
- `postgresql://` → `postgresql+asyncpg://` URL normalisieren.
- asyncpg + SQLAlchemy: kein psycopg-Mix; JSONB via `sqlalchemy.JSON`/`JSONB`.
- seq_counter Race: nur `UPDATE … RETURNING` (kein read-then-write).
- Entrypoint-Migration darf Boot nicht fatal brechen (try, log, weiter).
- Coolify-Postgres interne URL (Service-Name), nicht Public.
