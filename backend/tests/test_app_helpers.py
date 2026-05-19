"""Tests für app.py-Helpers — pure Funktionen ohne DB / HTTP.

Fokus:
- _today_de: korrektes Format mit deutschem Monatsnamen
- _ensure_correct_dates: Server-Zeit für datum, lieferdatum default
  aus v_datum, Idempotenz, defensives Verhalten bei nicht-dict
- valid_cookie: Signaturprüfung, Expiry, Unbekannte User
- _owner: Cookie → email extrahieren
"""
import base64
import hashlib
import hmac
import os
import sys
import time
from unittest.mock import MagicMock

import pytest

# PYTHONPATH-relative Imports
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")))

# KF_USERS muss gesetzt sein bevor app importiert wird.
# Format: email|salt|sha256(salt:pw).hexdigest()  separator ';'
import hashlib as _h
_salt = "s"
_hash = _h.sha256((_salt + ":secret").encode()).hexdigest()
os.environ["KF_USERS"] = f"test@example.com|{_salt}|{_hash}"
os.environ["KF_SESSION_SECRET"] = "test-secret-for-cookie-signing"

from backend import app


# ---------- _today_de ----------

class TestTodayDe:
    def test_format_deutscher_monat(self):
        s = app._today_de()
        # "{day}. {Monat} {year}" — Beispiel: "20. Mai 2026"
        parts = s.split(" ")
        assert len(parts) == 3
        assert parts[0].endswith(".")
        # Monat = deutsches Wort
        deutsche_monate = ("Januar", "Februar", "März", "April", "Mai",
                           "Juni", "Juli", "August", "September",
                           "Oktober", "November", "Dezember")
        assert parts[1] in deutsche_monate
        # Jahr 4-stellig
        assert parts[2].isdigit() and len(parts[2]) == 4

    def test_format_tag_ist_zahl_punkt(self):
        s = app._today_de()
        tag = s.split(".")[0]
        assert tag.isdigit()
        assert 1 <= int(tag) <= 31


# ---------- _ensure_correct_dates ----------

class TestEnsureCorrectDates:
    def test_datum_wird_immer_auf_heute_gesetzt(self):
        d = {"datum": "01. Januar 2020"}  # alt-Wert
        out = app._ensure_correct_dates(d)
        assert out["datum"] == app._today_de()

    def test_lieferdatum_default_aus_v_datum(self):
        d = {"veranstaltung": {"datum": "15. Juli 2026"}}
        out = app._ensure_correct_dates(d)
        assert out["lieferdatum"] == "15. Juli 2026"

    def test_lieferdatum_bleibt_wenn_schon_gesetzt(self):
        d = {"lieferdatum": "10. Juli 2026",
             "veranstaltung": {"datum": "15. Juli 2026"}}
        out = app._ensure_correct_dates(d)
        # lieferdatum NICHT überschrieben durch v_datum
        assert out["lieferdatum"] == "10. Juli 2026"

    def test_kein_lieferdatum_default_ohne_v_datum(self):
        d = {"veranstaltung": {}}
        out = app._ensure_correct_dates(d)
        # Bleibt undefined / not-set (kein willkürlicher Wert)
        assert "lieferdatum" not in out or not out.get("lieferdatum")

    def test_veranstaltung_datum_unveraendert(self):
        d = {"veranstaltung": {"datum": "15. Juli 2026"}}
        out = app._ensure_correct_dates(d)
        assert out["veranstaltung"]["datum"] == "15. Juli 2026"

    def test_defensiv_bei_string_input(self):
        """Soll keinen Crash bei ungültigem Input."""
        assert app._ensure_correct_dates("nope") == "nope"

    def test_defensiv_bei_none(self):
        assert app._ensure_correct_dates(None) is None

    def test_defensiv_bei_list(self):
        assert app._ensure_correct_dates([1, 2, 3]) == [1, 2, 3]

    def test_idempotent_doppelt_aufgerufen(self):
        d = {"veranstaltung": {"datum": "01. Juli 2026"}}
        a = app._ensure_correct_dates(dict(d))
        b = app._ensure_correct_dates(dict(a))
        # Datum bleibt heute, lieferdatum bleibt v_datum
        assert b["datum"] == app._today_de()
        assert b["lieferdatum"] == "01. Juli 2026"

    def test_leeres_veranstaltung_dict_kein_crash(self):
        d = {"veranstaltung": None}
        out = app._ensure_correct_dates(d)
        assert out["datum"] == app._today_de()


# ---------- valid_cookie + _owner ----------

def _sign(email, secret, exp):
    raw = f"{email}|{exp}"
    sig = hmac.new(secret.encode(), raw.encode(),
                   hashlib.sha256).hexdigest()[:32]
    tok = f"{email}|{exp}|{sig}"
    return base64.urlsafe_b64encode(tok.encode()).decode()


class TestValidCookie:
    def test_gueltiges_kf_users_cookie_ok(self):
        # KF_USERS enthält test@example.com (via setdefault)
        tok = _sign("test@example.com", app._secret(),
                    int(time.time()) + 3600)
        assert app.valid_cookie(tok) is True

    def test_abgelaufenes_cookie_invalid(self):
        tok = _sign("test@example.com", app._secret(),
                    int(time.time()) - 1)
        assert app.valid_cookie(tok) is False

    def test_falsche_signatur_invalid(self):
        tok = _sign("test@example.com", "anderes-secret",
                    int(time.time()) + 3600)
        assert app.valid_cookie(tok) is False

    def test_garbage_invalid(self):
        assert app.valid_cookie("nonsense") is False
        assert app.valid_cookie("") is False

    def test_unbekannter_user_invalid_ohne_db(self):
        """User nicht in KF_USERS, DB-Check schlägt fehl ohne DB →
        False."""
        tok = _sign("unbekannt@example.com", app._secret(),
                    int(time.time()) + 3600)
        # _db_user_ok ohne DB liefert False → Gesamt False
        assert app.valid_cookie(tok) is False


class TestOwner:
    def _mk_request(self, cookie_val):
        r = MagicMock()
        r.cookies = {app.COOKIE: cookie_val}
        return r

    def test_owner_aus_gueltigem_cookie(self):
        tok = _sign("test@example.com", app._secret(),
                    int(time.time()) + 3600)
        req = self._mk_request(tok)
        assert app._owner(req) == "test@example.com"

    def test_owner_none_ohne_cookie(self):
        req = self._mk_request("")
        assert app._owner(req) is None

    def test_owner_none_bei_invalid_cookie(self):
        req = self._mk_request("garbage")
        assert app._owner(req) is None

    def test_owner_lowercased(self):
        # capitalization sollte normalisiert werden
        tok = _sign("test@example.com", app._secret(),
                    int(time.time()) + 3600)
        req = self._mk_request(tok)
        assert app._owner(req) == "test@example.com"
