"""Sprint 14 — US-069 render_notext TDD-Suite.

Nur DIESE Datei (Wave-Plan: keine andere Testdatei anfassen). Prüft:
  1. Filterfunktion strip_text() — Unit, DB-los: t=="text"-Elemente raus,
     Rest unverändert + Reihenfolge stabil.
  2. Artefakt: preview_notext/p1.png existiert + >5 KB (skipif ungerendert).
  3. Idempotenz: 2. render_single-Lauf gibt "skip" (Sample muss da sein).

render_notext importiert compose_offer (DSN/SPIKE) — das geht DB-los durch.
Echte soffice-Renders laufen nur im Container, daher Artefakt/Idempotenz
per skipif an die committeten Sample-PNGs gebunden.
"""
import os
import sys

import pytest

_TOOLING = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "engine", "tooling")
sys.path.insert(0, _TOOLING)

import render_notext as rn  # noqa: E402

_CACHE = rn.CACHE
_DECK = "kf-ausstattung-location"
_P1 = os.path.join(_CACHE, _DECK, "preview_notext", "p1.png")


# --- 1. Filterfunktion (Unit, DB-los) -------------------------------------

def test_strip_text_entfernt_textelemente():
    seq = [
        {"t": "rect", "x": 0},
        {"t": "text", "v": "Korpus-Text"},
        {"t": "image", "src": "a.png"},
        {"t": "text", "v": "noch ein Text"},
    ]
    out = rn.strip_text(seq)
    assert all(e.get("t") != "text" for e in out)
    assert [e["t"] for e in out] == ["rect", "image"]


def test_strip_text_laesst_nichttext_unveraendert():
    seq = [
        {"t": "rect", "x": 1, "y": 2},
        {"t": "image", "src": "foo.png", "w": 10},
    ]
    out = rn.strip_text(seq)
    assert out == seq  # identisch (Reihenfolge + Werte)


def test_strip_text_leere_sequenz():
    assert rn.strip_text([]) == []


def test_strip_text_nur_text():
    assert rn.strip_text([{"t": "text", "v": "x"}]) == []


# --- 2. Artefakt-Test (skipif solange nicht gerendert) --------------------

@pytest.mark.skipif(not os.path.isfile(_P1),
                    reason="Sample-PNG noch nicht gerendert (Container-Lauf)")
def test_sample_png_existiert_und_gross_genug():
    assert os.path.getsize(_P1) > 5 * 1024


# --- 3. Idempotenz (braucht gerendertes Sample) ---------------------------

@pytest.mark.skipif(not os.path.isfile(_P1),
                    reason="Sample-PNG noch nicht gerendert (Container-Lauf)")
def test_render_single_idempotent_skippt():
    # Ohne --force muss ein existierendes PNG geskippt werden (kein soffice
    # nötig — der Skip-Pfad greift vor jedem Render).
    assert rn.render_single(_DECK, 1, force=False) == "skip"
