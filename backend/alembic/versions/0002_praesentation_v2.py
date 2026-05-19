"""0002 — EPIC-002 Sprint 5: additive Tabellen für Präsi-v2.

Strikt additiv (CREATE TABLE only). Keine bestehende Tabelle wird
angefasst. `praes_v2_slide` (Vorschlagskatalog) + `praes_v2_offer_slide`
(Auswahl pro Offer). FK auf `offer.id` ist read-only Verweis; CASCADE-
DELETE auf der v2-Seite — bei Offer-Löschung werden v2-Auswahl-Rows
mitgelöscht, EPIC-001-Tabellen unverändert.

Schneidbarkeit Sprint 9: `op.drop_table` in einer späteren Migration
entfernt beide Tabellen sauber.

Revision-ID: 0002
Down-Revision: 0001
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0002_praesentation_v2"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def _table_exists(name: str) -> bool:
    """Idempotenz-Guard: Base.metadata.create_all (migrate.py) legt im
    Boot-Schritt 1 die v2-Tabellen bereits an — wenn Alembic im Schritt 2
    dann hier nochmal create_table absetzt, kracht es („relation already
    exists"). Inspector-Check schützt davor."""
    bind = op.get_bind()
    return name in sa.inspect(bind).get_table_names()


def upgrade():
    if _table_exists("praes_v2_slide"):
        return
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


def downgrade():
    op.drop_index("ix_praes_v2_offer_slide_offer_id",
                  table_name="praes_v2_offer_slide")
    op.drop_table("praes_v2_offer_slide")
    op.drop_index("ix_praes_v2_slide_kategorie",
                  table_name="praes_v2_slide")
    op.drop_table("praes_v2_slide")
