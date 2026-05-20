"""EPIC-002 Sprint 7 — Kohärenz-Layer + Chat-Endpoint Tests.

Schwerpunkt:
- defaults_for: pro Kategorie sinnvolle Defaults aus Offer-Felder
- merge_overrides: user-overrides haben Vorrang
- _bullets_aus_block: erste 4 Positionen eines Blocks
- _kunde_und_datum: Format mit Trenner / leerer Fallback
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")))

# KF_USERS / KF_SESSION_SECRET vor app-Import setzen
import hashlib as _h
os.environ.setdefault("KF_USERS",
                      f"test@example.com|s|{_h.sha256(b's:pw').hexdigest()}")
os.environ.setdefault("KF_SESSION_SECRET", "x")

from backend import praesentation_v2_coherence as co


# ---------- defaults_for ----------

class TestDefaultsFor:
    def test_unbekannte_kategorie_leer(self):
        assert co.defaults_for("nope", {}) == {}

    def test_deckblatt_titel_aus_anlass(self):
        d = co.defaults_for("deckblatt", {
            "kunde": "Firma X",
            "veranstaltung": {"anlass": "Sommerfest", "datum": "01.07.2026"}
        })
        assert d["titel"] == "Sommerfest"
        assert "Firma X" in d["untertitel"]
        assert "01.07.2026" in d["untertitel"]
        assert d["bullets"] == []

    def test_deckblatt_fallback_titel_wenn_kein_anlass(self):
        d = co.defaults_for("deckblatt", {})
        assert d["titel"] == "Präsentation"

    def test_food_bullets_aus_speisen_block(self):
        d = co.defaults_for("food", {
            "veranstaltung": {"konzept": "4-Gang"},
            "bloecke": [
                {"typ": "speisen", "positionen": [
                    {"bezeichnung": "Suppe", "is_header": False},
                    {"bezeichnung": "Vorspeise", "is_header": True},
                    {"bezeichnung": "Hauptgang", "is_header": False},
                    {"bezeichnung": "Dessert", "is_header": False},
                    {"bezeichnung": "Extra", "is_header": False},
                    {"bezeichnung": "Noch eins", "is_header": False},
                ]}
            ]
        })
        # Headers werden gefiltert, max 4
        assert "Suppe" in d["bullets"]
        assert "Vorspeise" not in d["bullets"]   # is_header → out
        assert len(d["bullets"]) <= 4

    def test_food_leere_bullets_ohne_block(self):
        d = co.defaults_for("food", {})
        assert d["bullets"] == []

    def test_location_titel_und_untertitel(self):
        d = co.defaults_for("location", {
            "veranstaltung": {"ort": "Hamburg"}
        })
        assert d["titel"] == "Location"
        assert d["untertitel"] == "Hamburg"

    def test_ausstattung_bullets_aus_logistik(self):
        d = co.defaults_for("ausstattung", {
            "bloecke": [{"typ": "logistik",
                         "positionen": [
                             {"bezeichnung": "Grill", "is_header": False},
                             {"bezeichnung": "Tisch", "is_header": False},
                         ]}]
        })
        assert "Grill" in d["bullets"]

    def test_goldschaetzchen_static_defaults(self):
        d = co.defaults_for("goldschaetzchen", {})
        assert "Goldschätzchen" in d["titel"]

    def test_freitext_leer(self):
        d = co.defaults_for("freitext", {})
        assert d["titel"] == ""
        assert d["bullets"] == []

    def test_alle_7_kategorien_haben_template(self):
        """Garantie: jede Kategorie aus KATEGORIEN hat defaults_for-Mapping.
        Schützt vor Drift wenn KATEGORIEN erweitert wird."""
        from backend.praesentation_v2_models import KATEGORIEN
        for k in KATEGORIEN:
            d = co.defaults_for(k, {})
            assert "titel" in d, f"Kategorie {k} hat kein titel-default"


# ---------- merge_overrides ----------

class TestMergeOverrides:
    def test_user_uebersteuert_default(self):
        out = co.merge_overrides(
            {"titel": "Default", "bullets": []},
            {"titel": "User"})
        assert out["titel"] == "User"
        assert out["bullets"] == []  # aus default

    def test_leerer_user_wert_bleibt(self):
        """User EXPLICIT leer setzen darf nicht vom Default überschrieben
        werden (User wollte das so)."""
        out = co.merge_overrides({"titel": "Default"}, {"titel": ""})
        assert out["titel"] == ""

    def test_user_fehlend_default_greift(self):
        out = co.merge_overrides({"titel": "D"}, {})
        assert out["titel"] == "D"

    def test_zusatz_user_felder(self):
        out = co.merge_overrides({}, {"foo": "bar"})
        assert out["foo"] == "bar"


# ---------- _kunde_und_datum ----------

class TestKundeUndDatum:
    def test_voll(self):
        assert co._kunde_und_datum({
            "kunde": "X GmbH",
            "veranstaltung": {"datum": "01.07.2026"}
        }) == "X GmbH — 01.07.2026"

    def test_nur_kunde(self):
        assert co._kunde_und_datum({"kunde": "X"}) == "X"

    def test_nur_datum(self):
        assert co._kunde_und_datum({
            "veranstaltung": {"datum": "01.07.2026"}
        }) == "01.07.2026"

    def test_leer(self):
        assert co._kunde_und_datum({}) == ""

    def test_kunde_whitespace_strip(self):
        assert co._kunde_und_datum({"kunde": "  X  "}) == "X"


# ---------- Route-Existenz Sprint 7 ----------

class TestRoutesSprint7:
    def test_context_route_registriert(self):
        from backend.praesentation_v2 import router
        paths = {r.path for r in router.routes}
        assert "/api/praesentation_v2/offer/{offer_id}/context" in paths

    def test_chat_route_registriert(self):
        from backend.praesentation_v2 import router
        paths = {r.path for r in router.routes}
        assert "/api/praesentation_v2/chat" in paths

    def test_chat_body_validation(self):
        from backend.praesentation_v2 import ChatBody
        b = ChatBody(message="Test")
        assert b.overrides is None
        assert b.kategorie is None
        assert b.offer_id is None
