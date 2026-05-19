"""US-001 — Graceful Async-DB-Layer (Postgres kf-studio-pg).

Muster analog ENGINE_OK (app.py): Import/Boot bricht NIE wenn die DB
fehlt. DB_OK/DB_ERR werden gemeldet; Endpoints degradieren graceful.
"""
import os

DB_OK: bool = False
DB_ERR: str = ""
engine = None
Session = None


def _normalize(url: str) -> str:
    # Coolify liefert postgres://… ; SQLAlchemy-async braucht asyncpg.
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]
    return url


try:
    _raw = os.environ.get("DATABASE_URL", "").strip()
    if not _raw:
        raise RuntimeError("DATABASE_URL nicht gesetzt")
    from sqlalchemy.ext.asyncio import (create_async_engine,        # noqa
                                        async_sessionmaker)
    engine = create_async_engine(_normalize(_raw), pool_pre_ping=True,
                                  pool_size=5, max_overflow=5)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    DB_OK = True
except Exception as e:                                              # noqa
    engine = None
    Session = None
    DB_ERR = f"{type(e).__name__}: {e}"


async def ping() -> bool:
    """True wenn eine triviale Query durchgeht. Nie Exception nach außen."""
    if not DB_OK or engine is None:
        return False
    try:
        from sqlalchemy import text
        async with engine.connect() as c:
            await c.execute(text("SELECT 1"))
        return True
    except Exception as e:                                          # noqa
        global DB_ERR
        DB_ERR = f"ping: {type(e).__name__}: {e}"
        return False
