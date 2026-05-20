"""0003 — EPIC-002 Cleanup: praes_v2_*-Tabellen + Indexes droppen.

Nach POC-Abnahme entfernen wir den Präsi-V2-Editor komplett: Code,
Tests, FE, DB-Tabellen. Die Tabellen sind komplett isoliert (kein
Cross-Modul-Zugriff via grep verifiziert) — Drop ist risikofrei.

Idempotent: Tabellen werden nur gedroppt wenn vorhanden (für DBs die
nie auf 0002 waren).

Revision-ID: 0003
Down-Revision: 0002
"""
from alembic import op
import sqlalchemy as sa


revision = "0003_drop_praesentation_v2"
down_revision = "0002_praesentation_v2"
branch_labels = None
depends_on = None


def _table_exists(name: str) -> bool:
    bind = op.get_bind()
    return name in sa.inspect(bind).get_table_names()


def upgrade():
    if _table_exists("praes_v2_offer_slide"):
        op.drop_index("ix_praes_v2_offer_slide_offer_id",
                      table_name="praes_v2_offer_slide")
        op.drop_table("praes_v2_offer_slide")
    if _table_exists("praes_v2_slide"):
        op.drop_index("ix_praes_v2_slide_kategorie",
                      table_name="praes_v2_slide")
        op.drop_table("praes_v2_slide")


def downgrade():
    """Wiederherstellung — identisch zu 0002.upgrade()."""
    from sqlalchemy.dialects import postgresql
    op.create_table(
        "praes_v2_slide",
        sa.Column("id", sa.BigInteger, primary_key=True,
                  autoincrement=True),
        sa.Column("kategorie", sa.String(32), nullable=False),
        sa.Column("titel", sa.String(255), nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("preview_url", sa.Text, nullable=False,
                  server_default=""),
        sa.Column("created", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_praes_v2_slide_kategorie",
                    "praes_v2_slide", ["kategorie"])

    op.create_table(
        "praes_v2_offer_slide",
        sa.Column("id", sa.BigInteger, primary_key=True,
                  autoincrement=True),
        sa.Column("offer_id", sa.BigInteger,
                  sa.ForeignKey("offer.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("position", sa.Integer, nullable=False,
                  server_default="0"),
        sa.Column("kategorie", sa.String(32), nullable=False),
        sa.Column("slide_id", sa.BigInteger,
                  sa.ForeignKey("praes_v2_slide.id",
                                ondelete="SET NULL"),
                  nullable=True),
        sa.Column("overrides", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("created", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_praes_v2_offer_slide_offer_id",
                    "praes_v2_offer_slide", ["offer_id"])
