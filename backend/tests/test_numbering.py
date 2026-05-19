"""Tests für numbering.py — atomare Nummern-Sequenzen.

Format-Tests + Atomicity-Check (UPSERT-then-UPDATE-RETURNING-Pattern):
- next_kundennummer → 100001-A, 100002-A, …
- next_angebotsnummer → KF-{Jahr}-{n:04d}
- mock-Session: verifiziert dass _next(name) den SQL atomar absetzt
  (INSERT ON CONFLICT + UPDATE RETURNING — kein read-then-write Race).
"""
import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")))

from backend import numbering


def _mk_session(return_value):
    """Async-Mock: execute() ist async und gibt ein Result-Like mit
    scalar_one()=return_value zurück."""
    sess = MagicMock()
    sess.execute = AsyncMock()
    result = MagicMock()
    result.scalar_one.return_value = return_value
    sess.execute.return_value = result
    return sess


class TestNext:
    @pytest.mark.asyncio
    async def test_next_returnt_int(self):
        sess = _mk_session(42)
        n = await numbering._next(sess, "kunde")
        assert n == 42

    @pytest.mark.asyncio
    async def test_next_setzt_zwei_queries_ab(self):
        """INSERT ON CONFLICT + UPDATE RETURNING — atomar."""
        sess = _mk_session(1)
        await numbering._next(sess, "angebot")
        assert sess.execute.call_count == 2
        # 1. Call = INSERT ON CONFLICT
        first_sql = str(sess.execute.call_args_list[0].args[0])
        assert "INSERT" in first_sql.upper()
        assert "CONFLICT" in first_sql.upper()
        # 2. Call = UPDATE RETURNING
        second_sql = str(sess.execute.call_args_list[1].args[0])
        assert "UPDATE" in second_sql.upper()
        assert "RETURNING" in second_sql.upper()


class TestKundennummer:
    @pytest.mark.asyncio
    async def test_format_100001_a(self):
        sess = _mk_session(1)
        n = await numbering.next_kundennummer(sess)
        assert n == "100001-A"

    @pytest.mark.asyncio
    async def test_format_100099_a(self):
        sess = _mk_session(99)
        n = await numbering.next_kundennummer(sess)
        assert n == "100099-A"

    @pytest.mark.asyncio
    async def test_format_immer_a_suffix(self):
        """A = AI — Suffix nicht verhandelbar."""
        sess = _mk_session(7)
        n = await numbering.next_kundennummer(sess)
        assert n.endswith("-A")

    @pytest.mark.asyncio
    async def test_format_6_stellig_padded(self):
        sess = _mk_session(1)
        n = await numbering.next_kundennummer(sess)
        # 100000 + 1 = 100001 → 6 Stellen davor
        assert len(n.split("-")[0]) == 6


class TestAngebotsnummer:
    @pytest.mark.asyncio
    async def test_format_kf_jahr_n(self):
        sess = _mk_session(1)
        n = await numbering.next_angebotsnummer(sess)
        jahr = datetime.now().year
        assert n == f"KF-{jahr}-0001"

    @pytest.mark.asyncio
    async def test_n_4stellig_padded(self):
        sess = _mk_session(5)
        n = await numbering.next_angebotsnummer(sess)
        parts = n.split("-")
        # KF-{jahr}-{n:04d}
        assert len(parts[2]) == 4
        assert parts[2] == "0005"

    @pytest.mark.asyncio
    async def test_grosse_zahl_bleibt_4_oder_mehr_stellig(self):
        sess = _mk_session(9999)
        n = await numbering.next_angebotsnummer(sess)
        assert n.endswith("-9999")

    @pytest.mark.asyncio
    async def test_format_ueber_9999(self):
        """Überschreitet 9999 — Format wächst auf 5 Stellen (Python
        :04d ist Mindest-Pad)."""
        sess = _mk_session(12345)
        n = await numbering.next_angebotsnummer(sess)
        assert n.endswith("-12345")

    @pytest.mark.asyncio
    async def test_jahr_aus_systemzeit(self):
        sess = _mk_session(1)
        n = await numbering.next_angebotsnummer(sess)
        # Jahr-Komponente = aktuelles Jahr
        assert str(datetime.now().year) in n
