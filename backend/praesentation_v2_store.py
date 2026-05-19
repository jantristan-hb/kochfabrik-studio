"""EPIC-002 Sprint 5 — Store-Layer für Präsentationsgenerator v2.

Strikt parallel zu store.py. Keine Mutation von Offer/Customer-Tabellen
(EPIC-001-Eigentum). Nur Read-Verweis auf `offer.id` für Kohärenz.

Funktionen:
- `suggestions(kategorie, limit=4)` → 3-4 Slide-Vorschläge je Kategorie
- `set_offer_slide(offer_id, position, kategorie, slide_id, overrides)`
- `get_offer_slides(offer_id)` → aktuelle Auswahl pro Offer
- `clear_offer_slides(offer_id)` → vor neuer Generierung leeren
"""
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.praesentation_v2_models import (
    KATEGORIEN, PraesV2OfferSlide, PraesV2Slide)


async def suggestions(session: AsyncSession, kategorie: str,
                      limit: int = 4) -> list[dict]:
    """3-4 Slide-Vorschläge für eine Kategorie. Liefert nüchterne dicts
    (kein ORM-Leak in die API)."""
    if kategorie not in KATEGORIEN:
        return []
    stmt = (select(PraesV2Slide)
            .where(PraesV2Slide.kategorie == kategorie)
            .order_by(PraesV2Slide.id.asc())
            .limit(limit))
    rows = (await session.execute(stmt)).scalars().all()
    return [{"id": r.id, "kategorie": r.kategorie, "titel": r.titel,
             "payload": r.payload, "preview_url": r.preview_url}
            for r in rows]


async def set_offer_slide(session: AsyncSession, offer_id: int,
                          position: int, kategorie: str,
                          slide_id: Optional[int],
                          overrides: Optional[dict] = None) -> int:
    """Upsert: existiert (offer_id, position) bereits → update, sonst
    insert. Gibt id des Datensatzes zurück."""
    if kategorie not in KATEGORIEN:
        raise ValueError(f"Unbekannte Kategorie: {kategorie}")
    stmt = select(PraesV2OfferSlide).where(
        PraesV2OfferSlide.offer_id == offer_id,
        PraesV2OfferSlide.position == position)
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is not None:
        existing.kategorie = kategorie
        existing.slide_id = slide_id
        existing.overrides = overrides or {}
        await session.flush()
        return existing.id
    row = PraesV2OfferSlide(
        offer_id=offer_id, position=position, kategorie=kategorie,
        slide_id=slide_id, overrides=overrides or {})
    session.add(row)
    await session.flush()
    return row.id


async def get_offer_slides(session: AsyncSession,
                           offer_id: int) -> list[dict]:
    """Aktuelle Slide-Auswahl der Offer, sortiert nach Position."""
    stmt = (select(PraesV2OfferSlide)
            .where(PraesV2OfferSlide.offer_id == offer_id)
            .order_by(PraesV2OfferSlide.position.asc()))
    rows = (await session.execute(stmt)).scalars().all()
    return [{"id": r.id, "offer_id": r.offer_id,
             "position": r.position, "kategorie": r.kategorie,
             "slide_id": r.slide_id, "overrides": r.overrides}
            for r in rows]


async def clear_offer_slides(session: AsyncSession,
                             offer_id: int) -> int:
    """Vor neuer Generierung Auswahl leeren. Returns deleted-count."""
    stmt = delete(PraesV2OfferSlide).where(
        PraesV2OfferSlide.offer_id == offer_id)
    result = await session.execute(stmt)
    return result.rowcount or 0


async def seed_default_slides(session: AsyncSession) -> int:
    """Idempotent: legt für jede Kategorie 3 Default-Slide-Karten an
    falls die Kategorie noch leer ist. Returns neu angelegte Anzahl.

    Dient als Sofort-Start: User sieht direkt nach Deploy 3 Vorschläge
    je Kategorie statt leerer Listen. Sprint 6+ kann das verfeinern
    (echte Kataloge aus Cache-Decks)."""
    created = 0
    for kat in KATEGORIEN:
        stmt = select(PraesV2Slide.id).where(
            PraesV2Slide.kategorie == kat).limit(1)
        has = (await session.execute(stmt)).scalar_one_or_none()
        if has is not None:
            continue
        for i in range(3):
            session.add(PraesV2Slide(
                kategorie=kat,
                titel=f"{kat.capitalize()} — Vorlage {i + 1}",
                payload={"untertitel": "", "bullets": [], "bild": ""},
                preview_url=""))
            created += 1
    if created:
        await session.flush()
    return created
