"""US-010 — Alembic env (sync/psycopg2, entkoppelt vom async App-Engine).

URL aus DATABASE_URL → psycopg2-Form. Robuster als async-Alembic.
Baseline (0001) ist leer: das Schema wird per Base.metadata.create_all
(migrate.py, idempotent, droppt NIE) etabliert; Alembic trägt nur die
Versionshistorie für künftige ALTER-Revisionen.
"""
import os
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

sys.path.insert(0, os.getcwd())
from backend.models import Base                                   # noqa


def _sync_url() -> str:
    u = os.environ.get("DATABASE_URL", "").strip()
    if u.startswith("postgres://"):
        u = "postgresql+psycopg2://" + u[len("postgres://"):]
    elif u.startswith("postgresql://"):
        u = "postgresql+psycopg2://" + u[len("postgresql://"):]
    elif u.startswith("postgresql+asyncpg://"):
        u = "postgresql+psycopg2://" + u[len("postgresql+asyncpg://"):]
    return u


target_metadata = Base.metadata
config = context.config
config.set_main_option("sqlalchemy.url", _sync_url())


def run_migrations_offline() -> None:
    context.configure(url=_sync_url(), target_metadata=target_metadata,
                       literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    cfg = config.get_section(config.config_ini_section) or {}
    cfg["sqlalchemy.url"] = _sync_url()
    eng = engine_from_config(cfg, prefix="sqlalchemy.",
                             poolclass=pool.NullPool)
    with eng.connect() as conn:
        context.configure(connection=conn, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
