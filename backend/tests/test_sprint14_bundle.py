"""Sprint-14-Tests — US-073 Bild-Embeddings + rank_mixed (imgbundle).

EARS (FEATURE-013 §8 Nr. 2+3):
- WHEN embed_images.py für eine Sample-Menge läuft THE SYSTEM SHALL
  imgbundle.npz mit L2-normierten 768er-Vektoren je Slide erzeugen.
- WHEN rank_mixed mit alpha=1.0 läuft THE SYSTEM SHALL exakt die
  rank-Reihenfolge liefern; IF imgbundle fehlt THEN Fallback text-only.

Pitfall 4 (FEATURE-013 §12): Slides ohne Foto/img-Vektor in rank_mixed
neutral (text-only), nicht 0. ADR-003: np.load auf Bundles NUR in
bundle.py — die Tests monkeypatchen das Modulattribut bundle._IMG, laden
also selbst NIE per np.load.
"""
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
_ENG = os.path.join(ROOT, "engine", "scripts")
_TOOLING = os.path.join(ROOT, "engine", "tooling")
for _p in (_ENG, _TOOLING):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import bundle  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_img_cache():
    """imgbundle-Cache vor + nach jedem Test neutralisieren — kein Leak
    zwischen Tests (load_img cached in bundle._IMG)."""
    bundle._IMG = None
    bundle._IMG_LOADED = False
    yield
    bundle._IMG = None
    bundle._IMG_LOADED = False


def _skip_if_no_bundle():
    if not bundle.available():
        pytest.skip("pgbundle.npz nicht vorhanden")


def test_rank_mixed_alpha1_equals_rank(monkeypatch):
    """alpha=1.0 → reine Text-Ähnlichkeit == rank() (bit-identisch).
    img-Beitrag wird mit (1-alpha)=0 ausmultipliziert, daher selbst mit
    geladenem imgbundle identisch zur Text-Reihenfolge."""
    _skip_if_no_bundle()
    b = bundle.load()
    _, D = b["emb"].shape
    qv = bundle.normalize_query(
        np.random.default_rng(7).standard_normal(D))
    # auch mit vorhandenem (Fake-)imgbundle muss alpha=1.0 == rank sein
    N = len(b["emb"])
    monkeypatch.setattr(bundle, "_IMG", {
        "deck": b["deck"], "page": b["page"],
        "imgemb": np.zeros((N, D), np.float32),
    })
    monkeypatch.setattr(bundle, "_IMG_LOADED", True)
    assert list(bundle.rank_mixed(qv, 20, alpha=1.0)) == \
        list(bundle.rank(qv, None, 20))


def test_rank_mixed_fallback_without_imgbundle(monkeypatch):
    """Fehlt das imgbundle, fällt rank_mixed graceful auf text-only
    zurück == rank() — auch bei alpha<1 (EARS Nr. 3 IF-Klausel)."""
    _skip_if_no_bundle()
    monkeypatch.setattr(bundle, "load_img", lambda: None)
    b = bundle.load()
    _, D = b["emb"].shape
    qv = bundle.normalize_query(
        np.random.default_rng(11).standard_normal(D))
    assert list(bundle.rank_mixed(qv, 8, alpha=0.3)) == \
        list(bundle.rank(qv, None, 8))


def test_rank_mixed_image_match_lifts_slide(monkeypatch):
    """Mit Fake-imgbundle: eine Slide mit hohem img-Match steigt im
    gemischten Ranking gegenüber text-only auf. Konstruiert: img-Vektor
    EINER Slide == qv (Cosinus 1.0), alle anderen orthogonal/0."""
    _skip_if_no_bundle()
    b = bundle.load()
    N, D = b["emb"].shape
    qv = bundle.normalize_query(
        np.random.default_rng(3).standard_normal(D))
    # text-only-Reihenfolge: wähle ein Ziel, das NICHT vorne steht
    text_order = list(bundle.rank(qv, None, N))
    target = text_order[N // 2]              # mittiges Slide
    imgemb = np.zeros((N, D), np.float32)
    imgemb[target] = qv                       # perfekter img-Match
    monkeypatch.setattr(bundle, "_IMG", {
        "deck": b["deck"], "page": b["page"], "imgemb": imgemb,
    })
    monkeypatch.setattr(bundle, "_IMG_LOADED", True)
    mixed = list(bundle.rank_mixed(qv, N, alpha=0.3))
    assert mixed.index(target) < text_order.index(target)


def test_rank_mixed_neutral_for_imageless_slides(monkeypatch):
    """Pitfall 4: Slides OHNE img-Vektor (NaN-Marker) zählen text-only,
    nicht img_sim=0. Eine sonst top-rankende Text-Slide ohne Foto darf
    durch alpha-Mischung nicht nach hinten fallen, als hätte sie
    img_sim=0."""
    _skip_if_no_bundle()
    b = bundle.load()
    N, D = b["emb"].shape
    qv = bundle.normalize_query(
        np.random.default_rng(5).standard_normal(D))
    text_order = list(bundle.rank(qv, None, N))
    top = text_order[0]                       # beste Text-Slide, kein Foto
    imgemb = np.full((N, D), np.nan, np.float32)  # alle ohne Foto-Vektor
    monkeypatch.setattr(bundle, "_IMG", {
        "deck": b["deck"], "page": b["page"], "imgemb": imgemb,
    })
    monkeypatch.setattr(bundle, "_IMG_LOADED", True)
    # alle img-los → komplett text-only == rank()
    assert list(bundle.rank_mixed(qv, N, alpha=0.3)) == text_order
    assert list(bundle.rank_mixed(qv, 5, alpha=0.3))[0] == top


def test_embed_images_writes_l2_normed_npz(tmp_path, monkeypatch):
    """WHEN embed_images läuft (Beschreibung gemockt) THE SYSTEM SHALL
    imgbundle.npz mit L2-normierten 768er-Vektoren je Slide erzeugen.
    Echte Gemini-Calls (Vision + embed) sind gemockt — kein Netz."""
    import importlib
    ei = importlib.import_module("embed_images")

    # Vision-Beschreibung + Embedding deterministisch mocken
    monkeypatch.setattr(
        ei, "describe_image",
        lambda png, key: "Ein elegant angerichteter Teller, warmes Licht.")

    def _fake_embed(texts):
        # 768er, nicht normiert (Norm != 1) → npz MUSS normieren
        return np.tile(np.arange(1, 769, dtype=np.float64), (len(texts), 1))
    monkeypatch.setattr(ei, "embed", _fake_embed)

    out = tmp_path / "imgbundle.npz"
    # 2 Fake-Slides mit Foto
    slides = [("deckA", 2, "/x/p2.png"), ("deckA", 3, "/x/p3.png")]
    monkeypatch.setattr(ei, "collect_image_slides", lambda decks=None: slides)
    monkeypatch.setattr(ei, "preview_png",
                        lambda deck, page: f"/x/p{page}.png")
    monkeypatch.setattr(os.path, "isfile",
                        lambda p: True if str(p).endswith(".png") else
                        os.path.exists(p))

    n = ei.run(out_path=str(out), limit=None, force=True, key="k")
    assert n == 2
    z = np.load(out, allow_pickle=True)
    assert z["imgemb"].shape == (2, 768)
    norms = np.linalg.norm(z["imgemb"].astype(np.float32), axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)
    assert list(z["deck"]) == ["deckA", "deckA"]
    assert list(z["page"].astype(int)) == [2, 3]
    assert all(z["desc"])


def test_embed_images_idempotent_skips_existing(tmp_path, monkeypatch):
    """idempotent: vorhandene (deck,page)-Einträge werden übersprungen,
    nur neue Slides embedded."""
    import importlib
    ei = importlib.import_module("embed_images")
    monkeypatch.setattr(ei, "describe_image", lambda png, key: "desc")
    calls = {"n": 0}

    def _fake_embed(texts):
        calls["n"] += len(texts)
        return np.ones((len(texts), 768), dtype=np.float64)
    monkeypatch.setattr(ei, "embed", _fake_embed)
    monkeypatch.setattr(ei, "preview_png",
                        lambda deck, page: f"/x/p{page}.png")
    monkeypatch.setattr(os.path, "isfile",
                        lambda p: True if str(p).endswith(".png") else
                        os.path.exists(p))

    out = tmp_path / "imgbundle.npz"
    monkeypatch.setattr(ei, "collect_image_slides",
                        lambda decks=None: [("d", 1, "/x/p1.png")])
    ei.run(out_path=str(out), limit=None, force=False, key="k")
    assert calls["n"] == 1
    # zweiter Lauf mit derselben + einer neuen Slide → nur die neue embedden
    monkeypatch.setattr(ei, "collect_image_slides",
                        lambda decks=None: [("d", 1, "/x/p1.png"),
                                            ("d", 2, "/x/p2.png")])
    ei.run(out_path=str(out), limit=None, force=False, key="k")
    assert calls["n"] == 2          # nur +1 (die neue Slide)
    z = np.load(out, allow_pickle=True)
    assert len(z["deck"]) == 2
