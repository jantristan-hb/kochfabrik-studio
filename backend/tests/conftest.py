"""US-011 — Test-Fixtures (Carry-Over S1).

DB-Tests laufen gegen TEST_DATABASE_URL (Docker-Postgres in CI);
ohne die Var sauber geskippt (`needs_db`). `session`/`session_factory`
= async, je Test eigene DB-Session; Schema via models.create_all
(idempotent) auf die Test-DB. Binding-Gate bleibt zusätzlich die
Live-Smoke gegen kf-studio-pg.
"""
import os

import pytest

DB_URL = os.environ.get("TEST_DATABASE_URL")
needs_db = pytest.mark.skipif(not DB_URL,
                              reason="TEST_DATABASE_URL nicht gesetzt")


def _norm(u: str) -> str:
    for pre in ("postgres://", "postgresql://"):
        if u.startswith(pre):
            return "postgresql+asyncpg://" + u[len(pre):]
    return u


@pytest.fixture(scope="session")
def _engine():
    if not DB_URL:
        pytest.skip("TEST_DATABASE_URL nicht gesetzt")
    from sqlalchemy.ext.asyncio import create_async_engine
    eng = create_async_engine(_norm(DB_URL), pool_pre_ping=True)
    yield eng


@pytest.fixture
async def session_factory(_engine):
    """Schema (idempotent) + async sessionmaker. Tests räumen via
    eindeutige Owner/Namen selbst ab (Rollback-frei, da store eigene
    Sessions/Commits nutzt)."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from backend.models import Base
    async with _engine.begin() as c:
        await c.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(_engine, expire_on_commit=False)


@pytest.fixture
async def session(session_factory):
    async with session_factory() as s:
        yield s
