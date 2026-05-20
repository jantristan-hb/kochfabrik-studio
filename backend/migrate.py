"""US-010 — Schema-Migration: idempotente Baseline + Alembic-Versionierung.

Reihenfolge (alles graceful — nie fatal, App startet immer):
 1. Base.metadata.create_all (async, idempotent, legt NUR fehlende
    Tabellen an, droppt NIE) → etabliert das S1-Baseline-Schema.
 2. Alembic-Versionstracking (psycopg2 sync):
    - alembic_version leer/fehlt  → STAMP auf '0001_baseline'
      (kein Re-Create; passt zur S1-Live-DB deren Tabellen schon da
      sind und zu frischen DBs nach create_all).
    - alembic_version vorhanden   → `alembic upgrade head` (wendet
      künftige ALTER-Revisionen an; no-op wenn auf head).
"""
import asyncio
import os
import subprocess
import sys

HEAD = "0003_drop_praesentation_v2"


def _sync_url() -> str:
    u = os.environ.get("DATABASE_URL", "").strip()
    for pre in ("postgres://", "postgresql://", "postgresql+asyncpg://"):
        if u.startswith(pre):
            return "postgresql+psycopg2://" + u[len(pre):]
    return u


async def _create_all() -> bool:
    from .db import DB_OK, engine
    if not DB_OK or engine is None:
        print("migrate: DB nicht verfügbar — übersprungen (graceful)")
        return False
    from .models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("migrate: Schema OK (create_all, idempotent)")
    return True


def _alembic_sync() -> None:
    """Versionstracking. psycopg2; jeder Fehler graceful geschluckt."""
    try:
        import psycopg2
        from psycopg2 import sql                                  # noqa
        url = _sync_url()
        # psycopg2 versteht 'postgresql+psycopg2://' nicht → strippen
        dsn = url.replace("postgresql+psycopg2://", "postgresql://", 1)
        cx = psycopg2.connect(dsn)
        cx.autocommit = True
        cu = cx.cursor()
        cu.execute("SELECT to_regclass('public.alembic_version')")
        has_tbl = cu.fetchone()[0] is not None
        row = None
        if has_tbl:
            cu.execute("SELECT version_num FROM alembic_version LIMIT 1")
            r = cu.fetchone()
            row = r[0] if r else None
        if not row:                                   # STAMP (nie re-create)
            cu.execute("CREATE TABLE IF NOT EXISTS alembic_version ("
                       "version_num VARCHAR(32) NOT NULL "
                       "CONSTRAINT alembic_version_pkc PRIMARY KEY)")
            cu.execute("DELETE FROM alembic_version")
            cu.execute("INSERT INTO alembic_version(version_num) "
                       "VALUES (%s)", (HEAD,))
            print(f"migrate: Alembic gestampt auf {HEAD} (kein Re-Create)")
        else:
            r = subprocess.run(["alembic", "-c", "alembic.ini",
                                 "upgrade", "head"],
                                capture_output=True, text=True,
                                timeout=120)
            print(f"migrate: alembic upgrade head rc={r.returncode} "
                  f"(at {row})")
        cu.close()
        cx.close()
    except Exception as e:                                        # noqa
        print(f"migrate: Alembic übersprungen (graceful): "
              f"{type(e).__name__}: {e}")


def main() -> int:
    try:
        if asyncio.run(_create_all()):
            _alembic_sync()
    except Exception as e:                                        # noqa
        print(f"migrate: FEHLER (graceful, App startet trotzdem): {e}")
    return 0                                          # nie fatal


if __name__ == "__main__":
    sys.exit(main())
