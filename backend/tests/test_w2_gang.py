"""W2-Regression: _gang_groups MUSS das gang-Objekt (label+dishes) in jeder
Gruppe mitliefern. Vorher fehlte es → im Wizard kam gang=null an →
_suggest_overrides lieferte keine angebotsbezogenen Texte. embed (Gemini) und
die bundle-Schicht werden gemockt (kein Netz/DB nötig)."""
import sys
import types

import numpy as np
import pytest


def _fake_bundle():
    m = types.ModuleType("bundle")
    emb = np.array([[1.0, 0.0], [0.0, 1.0]])
    m.load = lambda: {"_normemb": emb, "deck": ["deckA", "deckB"],
                      "page": [1, 2], "module_label": ["L1", "L2"]}
    m.normalize_query = lambda v: v / (np.linalg.norm(v) or 1.0)
    m.rank_mixed = lambda qv, n, alpha=0.7: list(range(min(n, 2)))
    return m


@pytest.mark.asyncio
async def test_gang_groups_includes_gang(monkeypatch):
    import backend.routers.designer as d
    monkeypatch.setattr(d, "embed",
                        lambda texts: [np.array([1.0, 0.0]) for _ in texts])
    monkeypatch.setitem(sys.modules, "bundle", _fake_bundle())

    gaenge = [{"label": "Vorspeise",
               "dishes": [{"name": "Süppchen", "desc": "warm"}]}]
    out = d._gang_groups(gaenge, 2)

    assert len(out) == 1
    g = out[0]
    assert g["kind"] == "gang"
    assert g["gang"]["label"] == "Vorspeise"           # W2: gang mitgeliefert
    assert g["gang"]["dishes"][0]["name"] == "Süppchen"
    assert len(g["candidates"]) == 2                    # Ranking unberührt


@pytest.mark.asyncio
async def test_gang_groups_empty(monkeypatch):
    import backend.routers.designer as d
    assert d._gang_groups([], 3) == []
