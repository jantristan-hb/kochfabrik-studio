"""EPIC-002 Sprint 8 — Switch-Tests: v2 ist neue Default-Route im FE,
alter Generator ist deprecated im FE markiert.

Backend bleibt voll erreichbar (Rollback-fähig) → kein Test gegen
Backend-Routes. Nur Frontend-Markup-Inspektion.
"""
import os

import pytest

WEB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                   "web"))


NAV_FILES = ("client.html", "bibliothek.html", "chat.html",
             "index.html", "kunden.html", "gen.html",
             "bildgenerator.html", "vorschau.html", "upload.html")


@pytest.fixture
def web_files():
    return {f: open(os.path.join(WEB, f), encoding="utf-8").read()
            for f in NAV_FILES}


class TestNavRedirected:
    def test_alle_nav_items_zeigen_auf_v2(self, web_files):
        """Alle FE-Seiten haben Nav-Link auf /praesentation_v2/, NICHT
        mehr auf praesentationsgenerator.html."""
        for fname, src in web_files.items():
            # Nav-Items
            assert 'href="/praesentation_v2/"' in src, (
                f"{fname} hat keinen v2-Link in der Nav")

    def test_keine_nav_items_zeigen_auf_alten_pfad(self, web_files):
        for fname, src in web_files.items():
            # nav-item klasse darf nicht auf alte URL zeigen
            assert ('nav-item" href="praesentationsgenerator.html"'
                    not in src), (
                f"{fname} hat noch alten Nav-Link")
            assert ('nav-item active" href="praesentationsgenerator.html"'
                    not in src)


class TestLegacyBanner:
    def test_alte_seite_ist_legacy_markiert(self):
        p = os.path.join(WEB, "praesentationsgenerator.html")
        src = open(p, encoding="utf-8").read()
        assert "LEGACY" in src
        # Banner mit Link zur neuen Version
        assert "/praesentation_v2/" in src
        assert "Neue Version" in src or "neuen Editor" in src

    def test_alte_seite_bleibt_funktional(self):
        """Backend-Calls in der alten Seite sind unverändert (Rollback-
        fähig). Wir prüfen die fetch-Pfade."""
        p = os.path.join(WEB, "praesentationsgenerator.html")
        src = open(p, encoding="utf-8").read()
        assert "/api/praesentation/health" in src
        assert "/api/praesentation/generate" in src or \
               "/api/praesentation/from-pdf" in src


class TestV2DefaultRoute:
    def test_v2_index_existiert(self):
        assert os.path.isfile(os.path.join(WEB, "praesentation_v2",
                                           "index.html"))

    def test_v2_link_aus_chat_html(self):
        src = open(os.path.join(WEB, "chat.html"),
                   encoding="utf-8").read()
        # chat.html hat den Button "→ Präsentation"; bleibt erreichbar
        # via /api/praesentation/from-angebot (Backend bleibt aktiv).
        # Aber Nav-Link in chat.html geht auf v2.
        assert 'href="/praesentation_v2/"' in src

    def test_v2_route_klar_unterscheidbar(self):
        """Sprint-9-Refactor-Vertrag: v2 ist ein eigenes Verzeichnis,
        kein File namens 'praesentationsgenerator_v2.html'."""
        # Verzeichnis exists
        assert os.path.isdir(os.path.join(WEB, "praesentation_v2"))
        # KEIN Verwechslungs-File
        assert not os.path.isfile(os.path.join(
            WEB, "praesentationsgenerator_v2.html"))
