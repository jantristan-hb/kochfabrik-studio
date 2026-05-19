"""US-004 — Owner-scoped Repository/Service-Layer.

Alle Operationen STRIKT auf owner_email gescoped (Multi-Tenant —
keine Cross-Tenant-Leaks). Vollständiger Angebot-State wird als JSONB
persistiert → S2 kann den Chatbot-Editor 1:1 rekonstruieren.
"""
from sqlalchemy import select

from .db import Session
from .models import AppUser, ChatMessage, Customer, Offer
from .numbering import next_angebotsnummer, next_kundennummer


class TenantError(PermissionError):
    """Zugriff auf fremdes Offer (Multi-Tenant-Verletzung) — US-009."""


def _kunde_name(angebot: dict) -> str:
    return (str(angebot.get("kunde") or "").strip()
            or "Unbekannter Kunde")


async def _ensure_user(s, email: str):
    if not await s.get(AppUser, email):
        s.add(AppUser(email=email))
        await s.flush()


async def save_offer(owner_email: str, angebot: dict) -> dict:
    """Angebot persistieren. Customer (name+owner) upsert; bei
    Erstanlage Kunden-/Angebotsnummer atomar zuweisen. Idempotent pro
    bestehender offer_id im angebot['_offer_id']."""
    async with Session() as s:
        async with s.begin():
            await _ensure_user(s, owner_email)
            name = _kunde_name(angebot)
            offer = None
            oid = angebot.get("_offer_id")
            if oid:
                offer = await s.get(Offer, int(oid))
                if offer and offer.owner_email != owner_email:
                    offer = None                       # fremd -> neu
            if offer is None:
                cust = (await s.execute(
                    select(Customer).where(
                        Customer.owner_email == owner_email,
                        Customer.name == name))).scalars().first()
                if cust is None:
                    cust = Customer(
                        kundennummer=await next_kundennummer(s),
                        name=name, owner_email=owner_email)
                    s.add(cust)
                    await s.flush()
                offer = Offer(
                    angebotsnummer=await next_angebotsnummer(s),
                    customer_id=cust.id, owner_email=owner_email,
                    state={}, status="draft")
                s.add(offer)
                await s.flush()
            else:
                cust = await s.get(Customer, offer.customer_id)
            angebot = dict(angebot)
            angebot["angebots_nr"] = offer.angebotsnummer
            angebot["kundennr"] = cust.kundennummer
            angebot["_offer_id"] = offer.id
            offer.state = angebot
            return {"offer_id": offer.id,
                    "angebotsnummer": offer.angebotsnummer,
                    "kundennummer": cust.kundennummer}


async def get_offer(owner_email: str, offer_id: int) -> dict | None:
    async with Session() as s:
        o = await s.get(Offer, int(offer_id))
        if not o or o.owner_email != owner_email:       # Tenant-Isolation
            return None
        return o.state


async def list_offers(owner_email: str, q: str = "",
                      status: str = "") -> list[dict]:
    """US-014: optionale Filter q (kunde/anlass/angebotsnummer,
    case-insensitiv) + status (exakt). Leere Filter = alles
    (abwärtskompat zu S1)."""
    async with Session() as s:
        rows = (await s.execute(
            select(Offer, Customer)
            .join(Customer, Offer.customer_id == Customer.id)
            .where(Offer.owner_email == owner_email)
            .order_by(Offer.updated.desc()))).all()
        out = []
        for o, c in rows:
            st = o.state or {}
            out.append({
                "offer_id": o.id,
                "angebotsnummer": o.angebotsnummer,
                "kundennummer": c.kundennummer,
                "kunde": c.name,
                "anlass": (st.get("veranstaltung") or {}).get("anlass", ""),
                "status": o.status,
                "updated": o.updated.isoformat() if o.updated else None,
            })
        ql = (q or "").strip().lower()
        st_f = (status or "").strip()
        if ql:
            out = [r for r in out if ql in (
                f"{r['kunde']} {r['anlass']} "
                f"{r['angebotsnummer']}").lower()]
        if st_f:
            out = [r for r in out if r["status"] == st_f]
        return out


async def _owned_offer(s, owner_email: str, offer_id: int):
    """Offer laden + Owner verifizieren (US-009). Fremd → TenantError,
    fehlt → None."""
    o = await s.get(Offer, int(offer_id))
    if o is None:
        return None
    if o.owner_email != owner_email:
        raise TenantError(f"offer {offer_id} gehört nicht {owner_email}")
    return o


async def add_chat(owner_email: str, offer_id: int, role: str,
                   content: str) -> None:
    """US-006/009 — einen Chat-Turn offer-scoped persistieren.
    Owner-Check vor jedem Write (kein Cross-Tenant)."""
    if not content:
        return
    async with Session() as s:
        async with s.begin():
            o = await _owned_offer(s, owner_email, offer_id)
            if o is None:
                raise TenantError(f"offer {offer_id} fehlt")
            s.add(ChatMessage(offer_id=o.id, role=str(role)[:16],
                              content=str(content)))


async def get_offer_full(owner_email: str,
                         offer_id: int) -> dict | None:
    """US-007/009 — Angebot-State + Chat-Verlauf (chronologisch),
    strikt owner-scoped. Fremd/fehlt → None."""
    async with Session() as s:
        try:
            o = await _owned_offer(s, owner_email, offer_id)
        except TenantError:
            return None
        if o is None:
            return None
        msgs = (await s.execute(
            select(ChatMessage)
            .where(ChatMessage.offer_id == o.id)
            .order_by(ChatMessage.ts.asc(),
                      ChatMessage.id.asc()))).scalars().all()
        return {
            "angebot": o.state,
            "chat": [{"role": m.role, "content": m.content,
                      "ts": m.ts.isoformat() if m.ts else None}
                     for m in msgs],
        }


async def stats(owner_email: str) -> dict:
    """US-012 — owner-scoped Kennzahlen: #Angebote, #Kunden,
    Volumen (Σ aller block.zwischensumme), letzte ≤5."""
    async with Session() as s:
        rows = (await s.execute(
            select(Offer, Customer)
            .join(Customer, Offer.customer_id == Customer.id)
            .where(Offer.owner_email == owner_email)
            .order_by(Offer.updated.desc()))).all()
    kunden, vol, letzte = set(), 0.0, []
    for o, c in rows:
        kunden.add(c.kundennummer)
        st = o.state or {}
        for b in (st.get("bloecke") or []):
            try:
                vol += float(b.get("zwischensumme") or 0)
            except (TypeError, ValueError):
                pass
        if len(letzte) < 5:
            letzte.append({
                "offer_id": o.id, "angebotsnummer": o.angebotsnummer,
                "kunde": c.name,
                "anlass": (st.get("veranstaltung") or {}).get("anlass", ""),
                "status": o.status,
                "updated": o.updated.isoformat() if o.updated else None,
            })
    return {"angebote": len(rows), "kunden": len(kunden),
            "volumen": round(vol, 2), "letzte": letzte}


async def list_customers(owner_email: str) -> list[dict]:
    """US-013 — Kundenliste owner-scoped (mit #Angebote, letztem
    Datum)."""
    async with Session() as s:
        rows = (await s.execute(
            select(Offer, Customer)
            .join(Customer, Offer.customer_id == Customer.id)
            .where(Offer.owner_email == owner_email)
            .order_by(Offer.updated.desc()))).all()
    by: dict = {}
    for o, c in rows:
        e = by.setdefault(c.id, {
            "customer_id": c.id, "kundennummer": c.kundennummer,
            "name": c.name, "angebote": 0, "letztes": None})
        e["angebote"] += 1
        u = o.updated.isoformat() if o.updated else None
        if u and (e["letztes"] is None or u > e["letztes"]):
            e["letztes"] = u
    return sorted(by.values(), key=lambda x: x["letztes"] or "",
                  reverse=True)


async def get_customer(owner_email: str,
                       customer_id: int) -> dict | None:
    """US-013 — Kunde + dessen Angebote, strikt owner-scoped
    (fremd/fehlt → None)."""
    async with Session() as s:
        c = await s.get(Customer, int(customer_id))
        if not c or c.owner_email != owner_email:
            return None
        rows = (await s.execute(
            select(Offer)
            .where(Offer.customer_id == c.id,
                   Offer.owner_email == owner_email)
            .order_by(Offer.updated.desc()))).scalars().all()
        angebote = []
        for o in rows:
            st = o.state or {}
            angebote.append({
                "offer_id": o.id, "angebotsnummer": o.angebotsnummer,
                "kunde": c.name, "kundennummer": c.kundennummer,
                "anlass": (st.get("veranstaltung") or {}).get("anlass", ""),
                "status": o.status,
                "updated": o.updated.isoformat() if o.updated else None,
            })
        return {"kunde": {"customer_id": c.id,
                          "kundennummer": c.kundennummer,
                          "name": c.name},
                "angebote": angebote}


async def ensure_user(email: str) -> bool:
    """US-019 — app_user-Row für OAuth-Login sicherstellen.
    Graceful: DB-Fehler → False (kein Raise)."""
    e = (email or "").strip().lower()
    if not e:
        return False
    try:
        async with Session() as s:
            async with s.begin():
                await _ensure_user(s, e)
        return True
    except Exception:                                           # noqa
        return False
