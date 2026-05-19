"""Sprint 2 — Akzeptanz (EPIC-001 US-006..011).

Graceful-Tests laufen immer. DB-Integration → live gegen kf-studio-pg
verifiziert (binding gate) + via TEST_DATABASE_URL/DATABASE_URL in CI.
store.* binden zur Importzeit an DATABASE_URL → CI: beide Vars auf die
Test-PG zeigen lassen.
"""
import os

import pytest

from .conftest import needs_db


# US-006 — chat-Endpoint async, kein Crash ohne DB
def test_chat_endpoint_graceful_without_db(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    import backend.app as a
    assert any(getattr(r, "path", "") == "/api/angebot/chat"
               for r in a.app.routes)


# US-010 — Alembic-Artefakte vorhanden + Baseline leer (kein DROP)
def test_alembic_baseline_present_and_empty():
    import backend.alembic.versions as _v  # noqa
    p = os.path.join(os.path.dirname(_v.__file__), "0001_baseline.py")
    src = open(p).read()
    assert "revision = \"0001_baseline\"" in src
    assert "down_revision = None" in src
    # Baseline tut NICHTS (Schema via create_all, droppt nie)
    assert "def upgrade() -> None:\n    pass" in src


@needs_db
@pytest.mark.asyncio
async def test_chat_persist_and_full(session_factory):
    from backend.store import (add_chat, get_offer_full, save_offer)
    o = "a@s2.de"
    r = await save_offer(o, {"kunde": "S2K", "veranstaltung": {}})
    oid = r["offer_id"]
    await add_chat(o, oid, "me", "Hallo <b>")
    await add_chat(o, oid, "bot", "Angebot aktualisiert.")
    full = await get_offer_full(o, oid)
    assert full["angebot"]["kunde"] == "S2K"
    assert [m["role"] for m in full["chat"]] == ["me", "bot"]
    assert full["chat"][0]["content"] == "Hallo <b>"


@needs_db
@pytest.mark.asyncio
async def test_chat_tenant_isolation(session_factory):
    from backend.store import (TenantError, add_chat, get_offer_full,
                               save_offer)
    r = await save_offer("a@s2.de", {"kunde": "X", "veranstaltung": {}})
    await add_chat("a@s2.de", r["offer_id"], "me", "geheim")
    assert await get_offer_full("b@s2.de", r["offer_id"]) is None
    with pytest.raises(TenantError):
        await add_chat("b@s2.de", r["offer_id"], "me", "inject")
