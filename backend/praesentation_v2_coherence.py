"""EPIC-002 Sprint 7 — Kohärenz-Layer + LLM-Chat für Präsi-v2.

Strikt getrennt von Engine angebot_*.py und backend/store.py. Liest
Offer-Felder read-only via SQLAlchemy → mappt sie auf Slide-Default-
Overrides.

Akzeptanzkriterium 5: "Generierte Präsentation matched das verknüpfte
Angebot (Kunde, Datum, Konzept, Block-Themen)". Dafür braucht das FE
einen Endpoint der OFFER → SLIDE-DEFAULTS liefert.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Offer


# Mapping: Kategorie → welche Felder vom Offer als Default-Overrides
# eingespielt werden sollen. Sprint 7+ feiner ausgestalten.
_DEFAULT_TEMPLATE = {
    "deckblatt": lambda o: {
        "titel": (o.get("veranstaltung", {}).get("anlass")
                  or "Präsentation"),
        "untertitel": _kunde_und_datum(o),
        "bullets": [],
    },
    "food": lambda o: {
        "titel": "Speisen",
        "untertitel": o.get("veranstaltung", {}).get("konzept", ""),
        "bullets": _bullets_aus_block(o, "speisen"),
    },
    "location": lambda o: {
        "titel": "Location",
        "untertitel": o.get("veranstaltung", {}).get("ort", ""),
        "bullets": [],
    },
    "ausstattung": lambda o: {
        "titel": "Ausstattung & Technik",
        "untertitel": "",
        "bullets": _bullets_aus_block(o, "logistik"),
    },
    "goldschaetzchen": lambda o: {
        "titel": "Restaurant Goldschätzchen",
        "untertitel": "Unser Standort in Schleswig-Holstein",
        "bullets": [],
    },
    "kochfabrik": lambda o: {
        "titel": "Die KOCHfabrik",
        "untertitel": "Über uns",
        "bullets": [],
    },
    "freitext": lambda o: {
        "titel": "",
        "untertitel": "",
        "bullets": [],
    },
}


def _kunde_und_datum(o: dict) -> str:
    k = (o.get("kunde") or "").strip()
    d = (o.get("veranstaltung") or {}).get("datum", "")
    if k and d:
        return f"{k} — {d}"
    return k or d or ""


def _bullets_aus_block(o: dict, typ: str) -> list[str]:
    """Erste 4 Positionen eines Blocks als Bullets — knapp + kohärent."""
    for b in (o.get("bloecke") or []):
        if b.get("typ") == typ:
            return [p.get("bezeichnung", "")
                    for p in (b.get("positionen") or [])
                    if p.get("bezeichnung") and not p.get("is_header")][:4]
    return []


async def offer_context(session: AsyncSession, owner: str,
                        offer_id: int) -> Optional[dict]:
    """Liefert das (read-only) Offer-Dict gescoped auf owner. None
    wenn Offer nicht existiert ODER nicht owner gehört."""
    stmt = select(Offer.state, Offer.owner_email).where(
        Offer.id == offer_id)
    row = (await session.execute(stmt)).first()
    if row is None:
        return None
    state, oe = row
    if oe != owner:
        return None
    return state or {}


def defaults_for(kategorie: str, offer_dict: dict) -> dict:
    """Mappt Offer-Felder auf sinnvolle Slide-Override-Defaults für
    die Kategorie. Idempotent + side-effect-frei."""
    fn = _DEFAULT_TEMPLATE.get(kategorie)
    if not fn:
        return {}
    return fn(offer_dict or {})


def merge_overrides(defaults: dict, user_overrides: dict) -> dict:
    """User-Overrides haben Vorrang. Felder die im user-dict EXPLIZIT
    leer sind ('' / []) bleiben leer — nicht durch Defaults überschrieben.
    Felder die FEHLEN werden mit Defaults gefüllt."""
    out = dict(defaults)
    for k, v in (user_overrides or {}).items():
        out[k] = v
    return out
