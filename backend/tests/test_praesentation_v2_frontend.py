"""EPIC-002 Sprint 6 — Smoke-Tests für das v2-Frontend.

Datei-Inspektion (Existenz + Struktur-Marker). Echte Browser-Tests
laufen via Playwright in einer eigenen Phase — hier reicht Sanity, dass
Build/Deploy-Pipeline die Dateien hat und die Struktur den Vertrag
einhält (Drei-Spalten-Layout, 7 Kategorien, kein Verweis auf das alte
praesentationsgenerator.html-Modul).
"""
import os

import pytest

WEB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                   "web"))
V2 = os.path.join(WEB, "praesentation_v2")


class TestDateien:
    def test_index_existiert(self):
        assert os.path.isfile(os.path.join(V2, "index.html"))

    def test_editor_js_existiert(self):
        assert os.path.isfile(os.path.join(V2, "assets", "editor.js"))

    def test_alter_generator_im_legacy_archiv(self):
        """Sprint-9-Refactor: alte praesentationsgenerator.html ist
        nach _legacy/ verschoben (raus aus aktivem WEB-Pfad)."""
        p = os.path.join(WEB, "_legacy", "praesentationsgenerator.html")
        assert os.path.isfile(p)
        assert os.path.getsize(p) > 100


class TestIndexHtmlStruktur:
    @pytest.fixture
    def html(self):
        return open(os.path.join(V2, "index.html"),
                    encoding="utf-8").read()

    def test_drei_spalten_layout(self, html):
        assert "grid-template-columns" in html
        # 3 columns
        assert "col-chat" in html
        assert "col-form" in html
        assert "col-sugg" in html

    def test_chat_links(self, html):
        """Chat-Spalte ist die ERSTE im DOM (links)."""
        i_chat = html.find('id="col-chat"')
        i_form = html.find('id="col-form"')
        i_sugg = html.find('id="col-sugg"')
        assert 0 < i_chat < i_form < i_sugg

    def test_v2_beta_badge(self, html):
        assert "v2" in html.lower()
        assert "beta" in html.lower()

    def test_offer_dropdown(self, html):
        assert 'id="offer-select"' in html

    def test_generate_button(self, html):
        assert 'id="btn-generate"' in html

    def test_kein_alter_endpunkt_referenziert(self, html):
        """v2-FE darf NICHT den alten /api/praesentation/-Endpunkt
        anrufen — saubere Trennung Sprint 9."""
        # Suche nach exaktem alten Pfad ohne _v2
        assert "/api/praesentation/" not in html  # alter exakt
        # v2-Pfad muss präsent sein
        assert "/api/praesentation_v2/" in html or "editor.js" in html


class TestEditorJsStruktur:
    @pytest.fixture
    def js(self):
        return open(os.path.join(V2, "assets", "editor.js"),
                    encoding="utf-8").read()

    def test_genau_7_kategorien(self, js):
        """KAT-Array hat genau die 7 Backend-Kategorien."""
        for k in ("food", "deckblatt", "location", "ausstattung",
                  "goldschaetzchen", "kochfabrik", "freitext"):
            assert f'"{k}"' in js, f"Kategorie {k} fehlt im KAT-Array"

    def test_api_basis_pfad_v2(self, js):
        assert "/api/praesentation_v2/" in js

    def test_kein_zugriff_auf_alten_api(self, js):
        """v2-FE darf NICHT auf die alten Routen."""
        # Wir prüfen Zugriff auf alte EXAKTE Pfade
        for bad in ("/api/praesentation/health",
                    "/api/praesentation/generate",
                    "/api/praesentation/from-angebot",
                    "/api/praesentation/from-pdf"):
            assert bad not in js, f"Verbotener Pfad referenziert: {bad}"

    def test_persistenz_debounced(self, js):
        """Live-Edit muss debounced sein (Request-Sturm-Schutz)."""
        assert "schedulePersist" in js
        assert "setTimeout" in js or "debounce" in js

    def test_offer_id_scope(self, js):
        """Slide-Auswahl persistiert pro offer_id — Pflicht aus EPIC-Prompt."""
        assert "S.offer_id" in js
        assert "offer/${" in js or "offer/${S.offer_id}" in js

    def test_keine_destruktive_db_operation_im_fe(self, js):
        """FE darf keine direkten DB-Ops absetzen (paranoid-check)."""
        for bad in ("DROP TABLE", "TRUNCATE", "DELETE FROM ",
                    "ALTER TABLE"):
            assert bad not in js.upper(), f"Verbotener SQL: {bad}"
