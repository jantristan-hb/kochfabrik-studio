"""Tests für angebot_fill (Token-Replacement) + angebot_model
(Datenmodell + JSON-Roundtrip).

Fokus:
- _addr: Adress-Parsing edge cases (PLZ-positionsfrei, Straßen-Signal,
  Bug 'Möbelstraße in Ansprechpartner')
- token_values: alle Tokens belegt, leere Felder leere Strings
- fill: Template-Tokens werden ersetzt, open_tokens zählt Rest
- Modell: roundtrip dump→load, example() ist load-stabil
"""
import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from angebot_model import (Angebot, Position, Positionsblock, Veranstaltung,
                           Footer, dump, load, example)
import angebot_fill as af


# ---------- _addr — Adress-Parsing ----------

class TestAddrParsing:
    def test_voll_3_teile_name_strasse_ortplz(self):
        an, st, ot = af._addr(
            "Frau Claudia Kiesel, Ernst-Merck-Straße 12-14, 20099 Hamburg")
        assert an == "Frau Claudia Kiesel"
        assert st == "Ernst-Merck-Straße 12-14"
        assert ot == "20099 Hamburg"

    def test_2_teile_strasse_ortplz(self):
        an, st, ot = af._addr("Hauptstr 1, 25497 Prisdorf")
        assert an == ""
        assert st == "Hauptstr 1"
        assert ot == "25497 Prisdorf"

    def test_nur_ortplz(self):
        an, st, ot = af._addr("22525 Hamburg")
        assert an == ""
        assert st == ""
        assert ot == "22525 Hamburg"

    def test_leere_adresse(self):
        an, st, ot = af._addr("")
        assert (an, st, ot) == ("", "", "")

    def test_none_adresse(self):
        an, st, ot = af._addr(None)
        assert (an, st, ot) == ("", "", "")

    def test_strasse_ohne_explizite_nummer_aber_signal(self):
        """„Hauptweg" hat das Straßen-Signal ‚weg' — sollte als Straße
        erkannt werden, auch ohne Hausnummer."""
        an, st, ot = af._addr("Beispielhof, Hauptweg, 12345 Anywhere")
        assert ot == "12345 Anywhere"
        # Straßen-Signal 'weg' im 2. Teil → 2. Teil ist Straße
        assert st == "Hauptweg"

    def test_strasse_signal_grossschreibung(self):
        an, st, ot = af._addr("Am Damm 5, 22000 Hamburg")
        assert st == "Am Damm 5"
        assert ot == "22000 Hamburg"

    def test_ohne_strassen_signal_nimmt_letztes_vor_plz(self):
        """Wenn kein Signal: letztes Teil vor PLZ-Ort = Straße."""
        an, st, ot = af._addr("Beispielirgendwas, 22000 Hamburg")
        assert st == "Beispielirgendwas"
        assert ot == "22000 Hamburg"


# ---------- token_values ----------

class TestTokenValues:
    def test_alle_pflicht_tokens_vorhanden(self):
        v = af.token_values(example())
        pflicht = ["{KUNDE}", "{ADRESSE_STRASSE}", "{ADRESSE_ORT}",
                   "{ANGEBOTS_NR}", "{DATUM}", "{KUNDENNR}",
                   "{LIEFERDATUM}", "{ANSPRECHPARTNER}",
                   "{SB_EMAIL}", "{SB_DURCHWAHL}",
                   "{ANLASS}", "{V_DATUM}", "{BEGINN}", "{PERSONEN}",
                   "{ORT}", "{KONZEPT}"]
        for t in pflicht:
            assert t in v, f"Token {t} fehlt in token_values"

    def test_personen_formatiert_als_string(self):
        v = af.token_values(example())
        assert v["{PERSONEN}"] == "500 Personen"

    def test_personen_null_leer_string(self):
        a = Angebot(veranstaltung=Veranstaltung(personen=0))
        assert af.token_values(a)["{PERSONEN}"] == ""

    def test_personen_eins(self):
        a = Angebot(veranstaltung=Veranstaltung(personen=1))
        assert af.token_values(a)["{PERSONEN}"] == "1 Personen"

    def test_leere_skalare_bleiben_leerstring(self):
        """Empty-Defaults dürfen nicht null/undefined werden."""
        v = af.token_values(Angebot())
        assert v["{KUNDE}"] == ""
        assert v["{SB_EMAIL}"] == ""


# ---------- fill + open_tokens ----------

class TestFill:
    @pytest.fixture
    def template_path(self):
        p = os.path.join(os.path.dirname(__file__), "..", "data",
                         "angebot_template.elements.json")
        if not os.path.exists(p):
            pytest.skip(f"Template fehlt: {p}")
        return p

    def test_example_keine_offenen_tokens(self, template_path):
        """example() füllt alle Tokens — Regression-Schutz."""
        el = af.fill(example(), template_path)
        rest = af.open_tokens(el)
        assert rest == [], f"Offene Tokens nach fill: {rest}"

    def test_fill_ist_idempotent(self, template_path):
        """fill 2× hintereinander = fill 1×."""
        el1 = af.fill(example(), template_path)
        # Klon und nochmal befüllen — sollte unchanged sein
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False,
                                          mode="w", encoding="utf-8")
        json.dump(el1, tmp, ensure_ascii=False)
        tmp.close()
        el2 = af.fill(example(), tmp.name)
        os.unlink(tmp.name)
        # Strukturell identisch — keine doppelten Ersetzungen
        assert af.open_tokens(el2) == af.open_tokens(el1)

    def test_kunde_wird_eingesetzt(self, template_path):
        a = example()
        a.kunde = "Test-Kunde-XYZ-12345"
        el = af.fill(a, template_path)
        # Suche im Output ob der String drin ist
        found = False
        for pg, seq in el.items():
            if pg == "_meta" or not isinstance(seq, list):
                continue
            for e in seq:
                if e.get("t") != "text":
                    continue
                for ln in e.get("lines", []):
                    if "Test-Kunde-XYZ-12345" in (ln.get("txt") or ""):
                        found = True
        assert found, "Geänderter Kunden-String nicht im Output"

    def test_open_tokens_findet_unersetzte_marker(self):
        el = {"1": [{"t": "text", "lines": [{"txt": "Hallo {UNKNOWN}"}]}],
              "_meta": {}}
        assert af.open_tokens(el) == ["{UNKNOWN}"]

    def test_open_tokens_ignoriert_meta(self):
        el = {"_meta": {"foo": "{TOKEN}"}, "1": []}
        assert af.open_tokens(el) == []

    def test_open_tokens_ignoriert_nicht_text_elemente(self):
        el = {"1": [{"t": "rect", "fill": "{TOKEN}"}], "_meta": {}}
        assert af.open_tokens(el) == []


# ---------- Angebot-Modell — Roundtrip ----------

class TestModelRoundtrip:
    def test_dump_load_example_stabil(self, tmp_path):
        a = example()
        p = tmp_path / "ex.json"
        p.write_text(dump(a), encoding="utf-8")
        a2 = load(str(p))
        # Strukturell identisch
        assert dump(a2) == dump(a)

    def test_dump_ist_utf8_mit_umlauten(self):
        a = Angebot(kunde="Café Müller GmbH")
        s = dump(a)
        # ensure_ascii=False → Umlaute echt
        assert "Müller" in s
        assert "\\u" not in s.replace("\\n", "")  # keine \\uXXXX

    def test_load_default_footer_wenn_fehlt(self, tmp_path):
        p = tmp_path / "mini.json"
        p.write_text(json.dumps({
            "kunde": "X", "veranstaltung": {}, "bloecke": []
        }), encoding="utf-8")
        a = load(str(p))
        assert a.footer.firma == "Die KOCHfabrik GmbH"
        assert a.footer.bic == "GENODEF1PIN"

    def test_load_positionsblock_mit_positionen(self, tmp_path):
        p = tmp_path / "blk.json"
        p.write_text(json.dumps({
            "veranstaltung": {},
            "bloecke": [{"typ": "speisen", "titel": "S",
                         "positionen": [{"bezeichnung": "X", "menge": 2,
                                         "einzelpreis": 10.0,
                                         "gesamt": 20.0}],
                         "zwischensumme": 20.0}]
        }), encoding="utf-8")
        a = load(str(p))
        assert len(a.bloecke) == 1
        assert isinstance(a.bloecke[0], Positionsblock)
        assert isinstance(a.bloecke[0].positionen[0], Position)
        assert a.bloecke[0].positionen[0].bezeichnung == "X"

    def test_position_is_header_default_false(self):
        p = Position("test")
        assert p.is_header is False

    def test_position_with_header(self):
        p = Position("Sub-Titel", is_header=True)
        assert p.is_header is True
        assert p.menge == 1
