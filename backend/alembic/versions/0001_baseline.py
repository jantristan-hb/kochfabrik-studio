"""0001 baseline — S1-Schema (leer; etabliert via create_all).

Das vollständige S1-Schema (app_user, customer, offer, chat_message,
seq_counter) wird von migrate.py per Base.metadata.create_all
idempotent angelegt (droppt NIE). Diese Baseline ist bewusst leer —
sie dient nur als Alembic-Anker; künftige Schema-ALTERs (S3+) werden
als FOLGE-Revisionen mit echten op.*-Schritten angehängt.

Live-DB (S1, Tabellen existieren bereits, kein alembic_version):
migrate.py STAMPT auf diese Revision (kein Re-Create).
"""

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
