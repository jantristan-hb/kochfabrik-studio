# TEST — Sprint 1 (pytest, initial rot)

> `backend/tests/`. DB-Tests gegen lokale Postgres (Docker) oder
> `pytest`-Fixture mit `DATABASE_URL` env. Async: `pytest-asyncio`
> (zu requirements-dev hinzufügen).

## US-001 {#us-001-postgres-graceful-db-layer}
**Datei:** `backend/tests/test_db_graceful.py`
```python
def test_import_does_not_crash_without_db(monkeypatch):
    monkeypatch.setenv("DATABASE_URL","postgresql+asyncpg://x:x@127.0.0.1:1/none")
    import importlib, backend.db as db; importlib.reload(db)
    assert db.DB_OK in (True, False)          # kein Crash
def test_health_reports_db_field():
    from fastapi.testclient import TestClient
    from backend.app import app
    j = TestClient(app).get("/api/health").json()
    assert "db" in j
```

## US-002 {#us-002-db-schema-migrationen}
**Datei:** `backend/tests/test_schema.py`
```python
def test_models_importable():
    from backend.models import AppUser,Customer,Offer,ChatMessage,SeqCounter
    assert Offer.__tablename__ == "offer"
# Migration-Idempotenz: CI/Skript `alembic upgrade head` 2x (Verify-Cmd)
```

## US-003 {#us-003-atomare-nummernsequenzen}
**Datei:** `backend/tests/test_numbering.py`
```python
import asyncio, pytest
@pytest.mark.asyncio
async def test_first_kundennummer(session):
    from backend.numbering import next_kundennummer
    assert await next_kundennummer(session) == "100001-A"
@pytest.mark.asyncio
async def test_concurrent_unique(session_factory):
    from backend.numbering import next_angebotsnummer
    res = await asyncio.gather(*[_one(session_factory) for _ in range(20)])
    assert len(set(res)) == 20                # keine Kollision
```

## US-004 {#us-004-owner-scoped-store}
**Datei:** `backend/tests/test_store.py`
```python
@pytest.mark.asyncio
async def test_tenant_isolation(session):
    from backend.store import save_offer, get_offer, list_offers
    a = await save_offer("a@x.de", {"kunde":"K","veranstaltung":{}})
    assert await get_offer("b@x.de", a["offer_id"]) is None
    assert all(o["offer_id"]!=a["offer_id"] for o in await list_offers("b@x.de"))
@pytest.mark.asyncio
async def test_save_assigns_numbers(session):
    from backend.store import save_offer
    r = await save_offer("a@x.de", {"kunde":"K","veranstaltung":{}})
    assert r["kundennummer"] == "100001-A" and r["angebotsnummer"]
```

## US-005 {#us-005-api-endpoints-integration}
**Datei:** `backend/tests/test_api_angebot.py`
```python
def test_save_then_list(client_authed):           # Cookie-Fixture
    sid = client_authed.post("/api/angebot/save",
        json={"angebot":{"kunde":"K","veranstaltung":{}}}).json()
    assert sid["angebotsnummer"]
    lst = client_authed.get("/api/angebote").json()
    assert any(o["offer_id"]==sid["offer_id"] for o in lst)
def test_foreign_offer_404(client_authed, client_authed_b):
    sid = client_authed.post("/api/angebot/save",
        json={"angebot":{"kunde":"K"}}).json()
    assert client_authed_b.get(f"/api/angebot/{sid['offer_id']}").status_code==404
```

**Fixtures:** `session`/`session_factory` (async, test-DB, rollback je
Test), `client_authed`/`client_authed_b` (TestClient + gültiges
`kf_sess`-Cookie zweier User) — in `backend/tests/conftest.py`.
