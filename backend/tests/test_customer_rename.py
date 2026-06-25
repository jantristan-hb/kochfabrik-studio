"""Regression — Kundenname-Update beim Re-Save (Bug: "Unbekannter Kunde"
ließ sich nie korrigieren, weil save_offer im else-Zweig angebot["kunde"]
ignorierte). Owner-scoped, eindeutige Owner-Mails wie die übrigen DB-Tests.
"""
import pytest

from .conftest import needs_db


@needs_db
@pytest.mark.asyncio
async def test_rename_unbekannter_kunde_on_resave(session_factory):
    from backend.store import list_offers, save_offer

    owner = "rename@cr.de"
    # 1) Angebot OHNE Kundennamen -> Fallback "Unbekannter Kunde".
    r = await save_offer(owner, {"kunde": "", "veranstaltung": {}})
    oid = r["offer_id"]
    offers = {o["offer_id"]: o for o in await list_offers(owner)}
    assert offers[oid]["kunde"] == "Unbekannter Kunde"

    # 2) Denselben Datensatz mit echtem Namen erneut speichern.
    r2 = await save_offer(owner, {"_offer_id": oid, "kunde": "Echte Firma GmbH",
                                  "veranstaltung": {}})
    assert r2["offer_id"] == oid                      # gleiche Offer
    offers = {o["offer_id"]: o for o in await list_offers(owner)}
    assert offers[oid]["kunde"] == "Echte Firma GmbH"  # Name übernommen


@needs_db
@pytest.mark.asyncio
async def test_unbekannt_bucket_bleibt_fuer_andere(session_factory):
    """Re-Link darf den geteilten 'Unbekannter Kunde'-Sammeleintrag nicht
    umbenennen — ein zweites namenloses Angebot bleibt unverändert."""
    from backend.store import list_offers, save_offer

    owner = "bucket@cr.de"
    a = await save_offer(owner, {"kunde": "", "veranstaltung": {}})
    b = await save_offer(owner, {"kunde": "", "veranstaltung": {}})
    # beide hängen am selben Sammel-Customer
    assert a["kundennummer"] == b["kundennummer"]

    # a bekommt echten Namen -> re-link, b bleibt "Unbekannter Kunde".
    await save_offer(owner, {"_offer_id": a["offer_id"], "kunde": "Kunde A",
                             "veranstaltung": {}})
    offers = {o["offer_id"]: o for o in await list_offers(owner)}
    assert offers[a["offer_id"]]["kunde"] == "Kunde A"
    assert offers[b["offer_id"]]["kunde"] == "Unbekannter Kunde"
    # a hat jetzt eine eigene Kundennummer (eigener Customer).
    assert offers[a["offer_id"]]["kundennummer"] != b["kundennummer"]


@needs_db
@pytest.mark.asyncio
async def test_rename_to_existing_customer_dedupes(session_factory):
    """Umbenennen auf einen bereits existierenden Kundennamen verlinkt auf
    denselben Customer (keine Dublette)."""
    from backend.store import list_offers, save_offer

    owner = "dedupe@cr.de"
    existing = await save_offer(owner, {"kunde": "Sammel GmbH",
                                        "veranstaltung": {}})
    blank = await save_offer(owner, {"kunde": "", "veranstaltung": {}})
    await save_offer(owner, {"_offer_id": blank["offer_id"],
                             "kunde": "Sammel GmbH", "veranstaltung": {}})
    offers = {o["offer_id"]: o for o in await list_offers(owner)}
    # gleiche Kundennummer = derselbe Customer-Record.
    assert (offers[blank["offer_id"]]["kundennummer"]
            == offers[existing["offer_id"]]["kundennummer"])
