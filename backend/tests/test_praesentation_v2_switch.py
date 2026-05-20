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


class TestLegacyArchive:
    """Sprint 9: alter FE-View ist nach web/_legacy/ verschoben.
    Datei bleibt im Repo als historischer Anker + Rollback-Quelle."""

    def test_alte_seite_aus_dem_aktiven_pfad_raus(self):
        # Datei darf NICHT mehr unter web/ direkt erreichbar sein
        # (FastAPI StaticFiles würde sie sonst weiter ausliefern)
        p = os.path.join(WEB, "praesentationsgenerator.html")
        assert not os.path.exists(p), (
            "Alter FE muss aus dem aktiven web/-Pfad raus sein")

    def test_alte_seite_im_legacy_archiv(self):
        p = os.path.join(WEB, "_legacy", "praesentationsgenerator.html")
        assert os.path.isfile(p), "Legacy-Archiv-Datei fehlt"

    def test_backend_routes_unangetastet(self):
        """Akzeptanzkriterium 6: /api/angebot/* bit-identisch — und
        /api/praesentation/* (alt) bleibt für Rollback erreichbar."""
        src = open(os.path.join(
            os.path.dirname(__file__), "..", "app.py"),
            encoding="utf-8").read()
        # Alte Backend-Routes sind weiterhin registriert
        assert "/api/praesentation/health" in src
        assert "/api/praesentation/generate" in src
        assert "/api/praesentation/from-angebot" in src
        assert "/api/praesentation/from-pdf" in src


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
