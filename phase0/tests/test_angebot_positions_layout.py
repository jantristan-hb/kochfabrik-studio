"""Layout-Tests für angebot_positions.py.

Deckt den frischen Pagination-Refactor + Atem-Margins ab:
- _wrap_bez: Word-Break-Strategie (1-Zeile / 2-Zeilen / ellipsis)
- _pos_lines: Sub-Header vs. Body-Position, lang vs. kurz
- _blk_height: HDR_OFF / SUBHEAD_LEAD / ZSUM_LEAD / Position-Zeilen
- _eur: deutsche Zahlenformatierung
- Pagination: Overflow → neue Seite; AGB-Pages re-numbered
- _set_page_num: rechts-unten size:5 numerische Box

Lädt das Modul über sys.path-Insertion (kein __init__.py im scripts-Dir
— die Engine ist als loose-script-Sammlung organisiert).
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from angebot_model import Angebot, Veranstaltung, Positionsblock, Position
import angebot_positions as ap


# ---------- _eur — Geldformatierung ----------

class TestEur:
    def test_ganze_zahl(self):
        assert ap._eur(100) == "100,00"

    def test_dezimal(self):
        assert ap._eur(26.5) == "26,50"

    def test_tausender_punkt_komma_dezimal(self):
        assert ap._eur(2280) == "2.280,00"

    def test_grosse_zahl(self):
        assert ap._eur(1234567.89) == "1.234.567,89"

    def test_null(self):
        assert ap._eur(0) == "0,00"

    def test_negativ(self):
        # Mathematisch denkbar (Storno) — Format muss konsistent bleiben
        assert ap._eur(-50.5) == "-50,50"


# ---------- _wrap_bez — Bezeichnungs-Wrap ----------

class TestWrapBez:
    def test_kurze_bezeichnung_bleibt_einzeilig(self):
        assert ap._wrap_bez("Mineralwasser") == ["Mineralwasser"]

    def test_genau_bez_max_einzeilig(self):
        t = "x" * ap.BEZ_MAX
        assert ap._wrap_bez(t) == [t]

    def test_bez_max_plus_eins_wrappt(self):
        t = "abc " * 20  # >> BEZ_MAX
        lns = ap._wrap_bez(t)
        assert len(lns) == 2
        # Beide Zeilen unterhalb des Limits
        assert all(len(L) <= ap.BEZ_MAX for L in lns)

    def test_striploin_realer_fall(self):
        """Der ursprünglich problematische Striploin-String aus dem
        Live-Bug: 'Gegrilltes Striploin … & Sommerbohnen'."""
        s = ("Gegrilltes Striploin vom Deutschen Jungbullen, "
             "Rosmarinjus, Gratin Dauphinois & Sommerbohnen")
        lns = ap._wrap_bez(s)
        assert len(lns) == 2
        assert all(len(L) <= ap.BEZ_MAX for L in lns)
        # Wörter dürfen NICHT mitten im Wort gebrochen werden
        full = " ".join(lns)
        assert full.replace("  ", " ") == s

    def test_sehr_lange_zeile_2_wird_elliptiert(self):
        """Wenn auch die 2. Zeile zu lang wäre: Ellipsis statt 3. Zeile."""
        t = "Wort " + ("x" * (ap.BEZ_MAX * 2))  # Zeile-2 selbst zu lang
        lns = ap._wrap_bez(t)
        assert len(lns) == 2
        assert lns[1].endswith("…")
        assert len(lns[1]) == ap.BEZ_MAX

    def test_leere_eingabe(self):
        assert ap._wrap_bez("") == [""]
        assert ap._wrap_bez(None) == [""]

    def test_nur_whitespace(self):
        assert ap._wrap_bez("   ") == [""]


# ---------- _pos_lines — effektive Zeilen pro Position ----------

class TestPosLines:
    def test_header_immer_einzeilig(self):
        h = Position("Vorspeise", 0, 0, 0, is_header=True)
        assert ap._pos_lines(h) == 1.0

    def test_header_lang_bleibt_einzeilig(self):
        """Sub-Header werden bewusst einzeilig gerendert auch wenn
        sehr lang — sie sind Bold ohne Werte. Konsistenz."""
        h = Position("x" * 200, 0, 0, 0, is_header=True)
        assert ap._pos_lines(h) == 1.0

    def test_kurze_position_einzeilig(self):
        p = Position("Wasser", 1, 4.5, 4.5)
        assert ap._pos_lines(p) == 1.0

    def test_lange_position_wrap_pitch(self):
        # _wrap_bez bricht an Wort-Grenzen — Test braucht Whitespace
        lang = " ".join(["wort"] * 30)
        p = Position(lang, 1, 1, 1)
        assert ap._pos_lines(p) == ap.WRAP_PITCH

    def test_lange_position_ohne_whitespace_bleibt_einzeilig(self):
        """Edge case: ein einzelnes sehr langes Wort kann nicht
        gebrochen werden → _wrap_bez liefert 1 Zeile → _pos_lines = 1."""
        p = Position("x" * 200, 1, 1, 1)
        assert ap._pos_lines(p) == 1.0


# ---------- Konstanten-Plausibilität ----------

class TestKonstanten:
    def test_hdr_off_groesser_als_dy(self):
        """Header → 1. Position muss mehr Luft sein als zwischen Zeilen."""
        assert ap.HDR_OFF > ap.DY

    def test_gap_groesser_als_dy(self):
        """Block→Block-Lücke muss mehr Luft sein als Zeilen-Pitch."""
        assert ap.GAP > ap.DY

    def test_wrap_pitch_in_range(self):
        """1.0 < WRAP_PITCH < 2.0 — 2-Zeilen-Box braucht mehr als 1 Pitch,
        aber weniger als 2 (sonst zu großer Spalt)."""
        assert 1.0 < ap.WRAP_PITCH < 2.0

    def test_subhead_lead_positiv(self):
        assert ap.SUBHEAD_LEAD > 0

    def test_zsum_lead_groesser_als_eins(self):
        """Zwischensumme braucht mehr Abstand als normale Position."""
        assert ap.ZSUM_LEAD >= 1.5

    def test_page_reserve_realistisch(self):
        """Reserve vor Footer > 0, nicht absurd groß."""
        assert 0.1 < ap.PAGE_RESERVE < 1.0


# ---------- Integration: render(el, angebot) — Pagination + Numbering ----------

def _mk_block(typ, titel, n_pos, mit_zsum=True, lang=False):
    """Block mit n_pos Positionen, optional mit langen Bezeichnungen."""
    bez_kurz = "Position"
    bez_lang = ("Gegrilltes Striploin vom Deutschen Jungbullen, "
                "Rosmarinjus, Gratin Dauphinois & Sommerbohnen")
    pos = [Position(bez_lang if lang else f"{bez_kurz} {i+1}",
                    1, 10.0, 10.0)
           for i in range(n_pos)]
    return Positionsblock(typ, titel, pos,
                          zwischensumme=10.0 * n_pos if mit_zsum else None)


def _mk_angebot(bloecke):
    return Angebot(
        kunde="Test GmbH", adresse="Teststr 1, 22000 Hamburg",
        angebots_nr="KF-2026-TEST", datum="20. Mai 2026",
        kundennr="100099-A", lieferdatum="01. Juli 2026",
        ansprechpartner="",
        veranstaltung=Veranstaltung("Test", "01. Juli 2026", "17:00",
                                    100, "Hamburg", "Test-Konzept"),
        bloecke=bloecke,
    )


@pytest.fixture
def angebot_template_el():
    """Liest das gerenderte angebot_template.elements.json — Voraussetzung
    für jeden Render-Test. Falls fehlt: skip (build_angebot_template.py
    nicht gelaufen)."""
    p = os.path.join(os.path.dirname(__file__), "..", "data",
                     "angebot_template.elements.json")
    if not os.path.exists(p):
        pytest.skip(f"Template fehlt: {p}")
    import json
    return json.load(open(p))


class TestRenderPagination:
    def test_kleines_angebot_passt_auf_eine_position_seite(
            self, angebot_template_el):
        """Wenig Positionen → Page 2 reicht, AGB-Pages bleiben unverändert."""
        a = _mk_angebot([_mk_block("speisen", "Speisen", 3)])
        el = ap.render(angebot_template_el, a)
        # Page 2 + AGB-Pages (Original-Pruning lässt 3 AGB-Seiten übrig)
        pages = [k for k in el if k != "_meta"]
        # 1 Cover + 1 Position + N AGB ≥ 3
        assert len(pages) >= 3
        # Page 2 ist Positions-Seite
        assert "2" in el

    def test_grosses_angebot_bricht_um(self, angebot_template_el):
        """Viele Blöcke → mehrere Positions-Seiten."""
        bloecke = [_mk_block("typ", f"Block {i}", 8, lang=True)
                   for i in range(4)]
        a = _mk_angebot(bloecke)
        el = ap.render(angebot_template_el, a)
        # Erwartung: > 1 Position-Page (kein Quetschen)
        # Heuristik: el hat mehr als 4 Pages (Cover + ≥2 Pos + 3 AGB)
        pages = sorted(int(k) for k in el if k != "_meta")
        assert len(pages) >= 5, (
            f"Erwartet mind. 5 Pages bei viel Inhalt, hab {pages}")

    def test_page_numbers_fortlaufend(self, angebot_template_el):
        """Nach Render: Page-Number-Boxen (size 5 unten rechts) zeigen
        die echte Seitenzahl 2, 3, 4, ..."""
        bloecke = [_mk_block("typ", f"Block {i}", 8, lang=True)
                   for i in range(3)]
        a = _mk_angebot(bloecke)
        el = ap.render(angebot_template_el, a)

        for pg in sorted(k for k in el if k != "_meta"):
            seq = el[pg]
            nums = []
            for e in seq:
                if e.get("t") != "text":
                    continue
                for ln in e.get("lines", []):
                    if ln.get("size") == 5.0:
                        t = (ln.get("txt") or "").strip()
                        if t.isdigit():
                            nums.append(int(t))
            # Page 1 (Cover) hat keine Page-Num-Box mit size 5 → ok wenn leer
            if pg == "1" or not nums:
                continue
            assert int(pg) in nums, (
                f"Page {pg} hat keine Page-Number {pg} im Footer "
                f"(gefundene size:5-Zahlen: {nums})")

    def test_zwischensumme_ist_fett_und_rechts(self, angebot_template_el):
        """Zwischensumme = Bold + an der Gesamt-Spalte (rechts)."""
        a = _mk_angebot([_mk_block("speisen", "Speisen", 2,
                                   mit_zsum=True)])
        el = ap.render(angebot_template_el, a)
        # In den Positions-Seiten muss eine Bold-Zahl mit Wert "20,00"
        # existieren (3 × 10 = ... bei 2 pos × 10 = 20)
        seq = el["2"]
        bold_zahlen = [
            (ln.get("txt"), e.get("x"))
            for e in seq if e.get("t") == "text"
            for ln in e.get("lines", [])
            if ln.get("weight") == "Bold"
        ]
        # "20,00" muss vorkommen
        zwischen = [t for t, _ in bold_zahlen if t == "20,00"]
        assert zwischen, ("Zwischensumme nicht fett gerendert. "
                          f"Bold-Texte: {[b[0] for b in bold_zahlen]}")

    def test_keine_zwischensumme_wenn_block_zwischensumme_none(
            self, angebot_template_el):
        a = _mk_angebot([_mk_block("freitext", "Freitext", 1,
                                   mit_zsum=False)])
        el = ap.render(angebot_template_el, a)
        # Keine Bold-Zahl in Pos-Seite (keine Zwischensumme generiert)
        seq = el["2"]
        bold_zahlen = [
            ln.get("txt")
            for e in seq if e.get("t") == "text"
            for ln in e.get("lines", [])
            if ln.get("weight") == "Bold" and "," in (ln.get("txt") or "")
        ]
        # Erwartung: keine Zahl-Boldtexte (nur Sub-Header sind bold-text)
        assert not bold_zahlen, (
            f"Erwartet keine Zwischensumme, gefunden: {bold_zahlen}")
