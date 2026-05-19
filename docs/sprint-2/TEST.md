# TEST — Sprint 2 (pytest)

> `backend/tests/test_sprint2.py`. DB-Tests via `TEST_DATABASE_URL`
> (US-011 conftest-Fixture). Graceful/JS-Checks laufen ohne DB.

## US-006 {#us-006-chat-turns-persistieren}
**Datei:** `backend/tests/test_sprint2.py`
```python
@needs_db
@pytest.mark.asyncio
async def test_chat_persists_turns_and_creates_offer():
    from backend.store import add_chat, get_offer_full, save_offer
    r = await save_offer("a@x.de", {"kunde":"K","veranstaltung":{}})
    await add_chat("a@x.de", r["offer_id"], "me", "Hallo")
    await add_chat("a@x.de", r["offer_id"], "bot", "Moin")
    full = await get_offer_full("a@x.de", r["offer_id"])
    assert [m["role"] for m in full["chat"]] == ["me","bot"]
def test_chat_endpoint_graceful_without_db(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    import backend.app                       # async chat-Endpoint, kein Crash
    assert hasattr(backend.app,"app")
```

## US-007 {#us-007-angebot-chat-laden}
```python
@needs_db
@pytest.mark.asyncio
async def test_get_offer_full_shape_and_owner():
    from backend.store import get_offer_full, save_offer, add_chat
    r = await save_offer("a@x.de", {"kunde":"K","veranstaltung":{}})
    await add_chat("a@x.de", r["offer_id"], "me", "x")
    full = await get_offer_full("a@x.de", r["offer_id"])
    assert "angebot" in full and "chat" in full
    assert await get_offer_full("b@x.de", r["offer_id"]) is None
```

## US-008 {#us-008-chat-html-wiederoeffnen}
```bash
# JS-Syntax + Marker (kein DB):
node --check /tmp/c.js
grep -q "URLSearchParams\|location.search" web/chat.html
grep -q "history.replaceState" web/chat.html
```

## US-009 {#us-009-tenant-haertung}
```python
@needs_db
@pytest.mark.asyncio
async def test_chat_tenant_isolation():
    from backend.store import add_chat, get_offer_full, save_offer
    r = await save_offer("a@x.de", {"kunde":"K","veranstaltung":{}})
    await add_chat("a@x.de", r["offer_id"], "me", "geheim")
    assert await get_offer_full("b@x.de", r["offer_id"]) is None
    import pytest
    with pytest.raises(Exception):
        await add_chat("b@x.de", r["offer_id"], "me", "inject")
```

## US-010 {#us-010-alembic-setup}
```bash
alembic -c alembic.ini heads | wc -l        # == 1
alembic -c alembic.ini upgrade head
alembic -c alembic.ini upgrade head         # 2x = no-op, kein Fehler
```

## US-011 {#us-011-pytest-test-pg}
```bash
# ohne Var -> skip, mit Var -> grün
pytest backend/tests -q
TEST_DATABASE_URL=postgresql+asyncpg://postgres:x@localhost:5599/test pytest backend/tests -q
```
**Fixtures (conftest.py, US-011):** async `session`/`session_factory`
gegen `TEST_DATABASE_URL`, Transaktion+Rollback je Test; `needs_db`
skip-marker (aus S1) bleibt.
