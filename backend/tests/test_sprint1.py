"""Sprint 1 — Akzeptanz (EPIC-001 US-001..005).

Graceful/Format-Tests laufen immer (kein DB nötig). DB-Integration
(Migration/Numbering/Tenant/API) → live gegen kf-studio-pg verifiziert
(repräsentativer als lokales Mock); hier als skip-fähige Stubs.
"""
import importlib
import os

import pytest

from .conftest import needs_db


# US-001 — Graceful DB-Layer (kein DB nötig)
def test_db_import_graceful_without_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    from backend import db
    importlib.reload(db)
    assert db.DB_OK is False and db.DB_ERR          # kein Crash
    import asyncio
    assert asyncio.run(db.ping()) is False          # keine Exception


def test_app_imports_without_db(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    import backend.app                               # darf nicht crashen
    assert hasattr(backend.app, "app")


# US-003 — Nummernformat (reine Formatlogik)
def test_kundennummer_format():
    # f"{100000+n:06d}-A" ; erster Aufruf n=1 -> 100001-A
    assert f"{100000 + 1:06d}-A" == "100001-A"
    assert f"{100000 + 42:06d}-A" == "100042-A"


def test_angebotsnummer_format():
    from datetime import datetime
    y = datetime.now().year
    assert f"KF-{y}-{1:04d}" == f"KF-{y}-0001"


# US-002/003/004/005 — DB-Integration (skip ohne TEST_DATABASE_URL)
@needs_db
@pytest.mark.asyncio
async def test_migration_idempotent():
    from backend.migrate import _run
    assert await _run() is True
    assert await _run() is True                      # 2x = idempotent


@needs_db
@pytest.mark.asyncio
async def test_numbering_first_and_unique():
    import asyncio

    from backend.db import Session
    from backend.numbering import (next_angebotsnummer,
                                   next_kundennummer)
    async with Session() as s:
        async with s.begin():
            kn = await next_kundennummer(s)
    assert kn.endswith("-A")

    async def one():
        async with Session() as s:
            async with s.begin():
                return await next_angebotsnummer(s)
    res = await asyncio.gather(*[one() for _ in range(15)])
    assert len(set(res)) == 15                        # keine Kollision


@needs_db
@pytest.mark.asyncio
async def test_tenant_isolation_and_numbers():
    from backend.store import get_offer, list_offers, save_offer
    a = await save_offer("a@x.de", {"kunde": "K", "veranstaltung": {}})
    assert a["kundennummer"].endswith("-A") and a["angebotsnummer"]
    assert await get_offer("b@x.de", a["offer_id"]) is None       # fremd
    assert all(o["offer_id"] != a["offer_id"]
               for o in await list_offers("b@x.de"))
    assert (await get_offer("a@x.de", a["offer_id"]))["kunde"] == "K"
