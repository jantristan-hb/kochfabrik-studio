"""US-002 — Idempotente Schema-Migration.

Greenfield-Schema (eine Revision) → `create_all` ist idempotent
(legt nur fehlende Tabellen an) und headless-robust. Echtes Alembic
wird eingeführt sobald der erste ALTER nötig ist (Sprint 2+, additiv).
Entrypoint ruft das vor uvicorn auf — Fehler NICHT fatal (graceful).
"""
import asyncio
import sys


async def _run() -> bool:
    from .db import DB_OK, engine
    if not DB_OK or engine is None:
        print("migrate: DB nicht verfügbar — übersprungen (graceful)")
        return False
    from .models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("migrate: Schema OK (create_all, idempotent)")
    return True


def main() -> int:
    try:
        ok = asyncio.run(_run())
        return 0 if ok else 0          # nie fatal: App soll trotzdem starten
    except Exception as e:             # noqa
        print(f"migrate: FEHLER (graceful, App startet trotzdem): {e}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
