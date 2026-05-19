"""US-003 — Atomare, kollisionsfreie Nummernsequenzen.

Kundennummer: 100001-A, 100002-A … (A = AI).
Angebotsnummer: KF-{Jahr}-{n:04d}, global fortlaufend (Jahr nur Präfix).
Atomar via UPDATE … RETURNING (row-lock, kein read-then-write-Race).
"""
from datetime import datetime

from sqlalchemy import text


async def _next(session, name: str) -> int:
    """Inkrementiert seq_counter[name] atomar, gibt neuen Wert zurück.
    Lazy-Init der Zeile falls fehlt."""
    await session.execute(
        text("INSERT INTO seq_counter(name, value) VALUES (:n, 0) "
             "ON CONFLICT (name) DO NOTHING"), {"n": name})
    row = await session.execute(
        text("UPDATE seq_counter SET value = value + 1 "
             "WHERE name = :n RETURNING value"), {"n": name})
    return int(row.scalar_one())


async def next_kundennummer(session) -> str:
    n = await _next(session, "kunde")
    return f"{100000 + n:06d}-A"            # erster Aufruf -> 100001-A


async def next_angebotsnummer(session) -> str:
    n = await _next(session, "angebot")
    return f"KF-{datetime.now().year}-{n:04d}"
