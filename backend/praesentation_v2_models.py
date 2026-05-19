"""EPIC-002 Sprint 5 — Datenmodelle für Präsentationsgenerator v2.

STRIKT additiv zu den S1-Modellen (models.py). Eigene Tabellen, eigene
Klassen — KEIN Touch der bestehenden offer/customer/chat_message/...-
Tabellen oder ihrer SQLAlchemy-Definitionen.

Tabellen:
- `praes_v2_slide`              — Slide-Vorschläge-Katalog (3-4 pro
                                  Kategorie für die 7 Kategorien)
- `praes_v2_offer_slide`        — Slide-Auswahl pro Offer (1:n)

Schneidbarkeit (Sprint 9): beide Tabellen können später per `DROP TABLE`
entfernt werden, ohne die EPIC-001-Tabellen zu beeinflussen — keine FKs
außer auf `offer.id` (Read-only-Referenz).
"""
from datetime import datetime

from sqlalchemy import (BigInteger, DateTime, ForeignKey, Integer, String,
                        Text)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models import Base


# Die 7 Slide-Kategorien aus dem EPIC-Prompt (Single Source).
KATEGORIEN = (
    "food", "deckblatt", "location", "ausstattung",
    "goldschaetzchen", "kochfabrik", "freitext",
)


class PraesV2Slide(Base):
    """Slide-Vorschlag aus dem Katalog (eine Karte rechts im Editor).

    `kategorie` ist eines aus `KATEGORIEN`. `payload` ist das JSONB-
    Schema das die Engine braucht um diesen Slide zu rendern (Titel,
    Untertitel, Bilder-URLs, ggf. Bullet-Points). Schema ist
    laufzeit-flexibel, weil sich pro Kategorie unterscheidet."""
    __tablename__ = "praes_v2_slide"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True,
                                    autoincrement=True)
    kategorie: Mapped[str] = mapped_column(String(32), index=True)
    titel: Mapped[str] = mapped_column(String(255))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    preview_url: Mapped[str] = mapped_column(Text, default="")  # cached PNG
    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow)


class PraesV2OfferSlide(Base):
    """Welcher Slide-Vorschlag wurde für welche Position im Deck
    welcher Offer ausgewählt? `position` ist die 0-basierte Reihen-
    folge im finalen Deck. `overrides` enthält die nutzer-editierten
    Texte (überschreiben `slide.payload`-Defaults beim Rendern)."""
    __tablename__ = "praes_v2_offer_slide"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True,
                                    autoincrement=True)
    offer_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("offer.id", ondelete="CASCADE"),
        index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    kategorie: Mapped[str] = mapped_column(String(32))
    slide_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("praes_v2_slide.id", ondelete="SET NULL"),
        nullable=True)
    overrides: Mapped[dict] = mapped_column(JSONB, default=dict)
    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow)
    updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow,
        onupdate=datetime.utcnow)
