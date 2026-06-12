"""Sprint 15 — US-081: Treue-Metrik fidelity.py (FEATURE-016 §3/§4).

Diese Datei ist die Ketten-Test-Datei der Treue-Kette (US-081…084).

EARS (FEATURE-016 §8 Nr. 1):
- WHEN compare eine Seite mit sich selbst vergleicht THE SYSTEM SHALL
  total >= 0.99 liefern.
- WHEN Texte/Fonts manipuliert sind THE SYSTEM SHALL messbar niedrigere
  Teil-Scores liefern (Monotonie, kein absoluter Anspruch).

fitz/PyMuPDF ist eine explizit freigegebene Analyse-Dependency (NICHT Runtime),
die Tests skippen sauber, falls sie fehlt.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

fitz = pytest.importorskip("fitz", reason="PyMuPDF (fitz) ist Analyse-Dep, nicht im Runtime-Stack")

REPO_ROOT = Path(__file__).resolve().parents[2]
FIDELITY_PY = REPO_ROOT / "engine" / "tooling" / "fidelity.py"
SAMPLE_REF = (
    REPO_ROOT
    / "engine"
    / "data"
    / "cache"
    / "10-182-raumkarussell-gmbh-12-09-2026"
    / "assets"
    / "ref.pdf"
)


def _load_fidelity():
    spec = importlib.util.spec_from_file_location("fidelity", FIDELITY_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def fid():
    assert FIDELITY_PY.exists(), f"fidelity.py fehlt: {FIDELITY_PY}"
    return _load_fidelity()


@pytest.fixture(scope="module")
def sample_ref():
    if not SAMPLE_REF.exists():
        pytest.skip(f"Sample-Deck-ref.pdf fehlt: {SAMPLE_REF}")
    return SAMPLE_REF


def test_version_konstante(fid):
    assert getattr(fid, "FIDELITY_VERSION", None) == "1.0"


def test_selbstvergleich_total_min_099(fid, sample_ref):
    """EARS Nr. 1: Seite vs. sich selbst → total >= 0.99."""
    res = fid.compare(str(sample_ref), 1, str(sample_ref), 1)
    assert set(res) >= {"text", "geometry", "font", "pixel", "total"}
    assert res["total"] >= 0.99, res
    # Teil-Scores ebenfalls sehr hoch beim Identitätsvergleich.
    assert res["text"] >= 0.99
    assert res["geometry"] >= 0.99
    assert res["font"] >= 0.99
    assert res["pixel"] >= 0.99


def _copy_first_page(src_pdf: Path, dst_pdf: Path):
    src = fitz.open(src_pdf)
    out = fitz.open()
    out.insert_pdf(src, from_page=0, to_page=0)
    out.save(dst_pdf)
    out.close()
    src.close()


def test_text_score_sinkt_bei_textmanipulation(fid, sample_ref, tmp_path):
    """Monotonie: zusätzlich eingefügter Text senkt den text-Score."""
    base_copy = tmp_path / "text_base.pdf"
    _copy_first_page(sample_ref, base_copy)
    manipulated = tmp_path / "text_changed.pdf"
    doc = fitz.open(base_copy)
    page = doc[0]
    # Großzügig Fremdtext einfügen → Token-F1 muss sinken.
    page.insert_text(
        fitz.Point(40, 40),
        "VOELLIG FREMDER TEXT BLOCK ZUR STOERUNG DES TOKEN F1 SCORES XYZ QWERTZ",
        fontsize=11,
    )
    doc.save(str(manipulated))
    doc.close()

    base = fid.compare(str(sample_ref), 1, str(sample_ref), 1)
    changed = fid.compare(str(sample_ref), 1, str(manipulated), 1)
    assert changed["text"] < base["text"], (base, changed)


def test_font_score_sinkt_bei_groessenaenderung(fid, sample_ref, tmp_path):
    """Monotonie: geänderte Font-Größen senken den font-Score.

    Wir rendern dieselben Tokens an denselben Positionen, aber mit anderer
    Größe, sodass Text-/Geometrie-Score stabil bleiben und der font-Score
    isoliert fällt.
    """
    src = fitz.open(sample_ref)
    page0 = src[0]
    rect = fitz.Rect(page0.rect)
    spans = []
    for block in page0.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                if span.get("text", "").strip():
                    spans.append(
                        {
                            "text": span["text"],
                            "size": float(span["size"]),
                            "origin": tuple(span.get("origin"))
                            if span.get("origin")
                            else (span["bbox"][0], span["bbox"][3]),
                        }
                    )
    src.close()
    assert spans, "Sample-Seite hat keine Text-Spans"
    resized = tmp_path / "font_resized.pdf"
    out = fitz.open()
    pg = out.new_page(width=rect.width, height=rect.height)
    for s in spans:
        origin = s["origin"]
        # Größe deutlich verändern (+6pt) → font-Teil-Score muss fallen.
        pg.insert_text(
            fitz.Point(origin[0], origin[1]),
            s["text"],
            fontsize=s["size"] + 6.0,
        )
    out.save(str(resized))
    out.close()

    # Selbe Spans in Originalgröße als Kontroll-PDF.
    control = tmp_path / "font_control.pdf"
    out2 = fitz.open()
    pg2 = out2.new_page(width=rect.width, height=rect.height)
    for s in spans:
        origin = s["origin"]
        pg2.insert_text(
            fitz.Point(origin[0], origin[1]),
            s["text"],
            fontsize=s["size"],
        )
    out2.save(str(control))
    out2.close()

    # Kontroll-PDF mit sich selbst: gleiche Familie + Größe → font == 1.0.
    base = fid.compare(str(control), 1, str(control), 1)
    # Kontroll- vs. vergrößertes PDF: gleiche Familie/Position, andere Größe.
    changed = fid.compare(str(control), 1, str(resized), 1)
    assert changed["font"] < base["font"], (base, changed)


def test_a4_vs_169_crasht_nicht(fid, sample_ref, tmp_path):
    """Pitfall §12.2: unterschiedliche Seitenmaße dürfen nicht crashen.

    Koordinaten werden auf Seitenmaße normalisiert → ein 16:9-Deck vs. A4-Hochkant
    liefert ein valides Resultat statt einer Exception.
    """
    wide = tmp_path / "wide_169.pdf"
    out = fitz.open()
    pg = out.new_page(width=1280, height=720)  # 16:9
    pg.insert_text(fitz.Point(60, 60), "Titel auf 16:9 Folie", fontsize=28)
    pg.insert_text(fitz.Point(60, 120), "Untertitel Inhalt", fontsize=14)
    out.save(str(wide))
    out.close()

    res = fid.compare(str(sample_ref), 1, str(wide), 1)
    assert set(res) >= {"text", "geometry", "font", "pixel", "total"}
    for k in ("text", "geometry", "font", "pixel", "total"):
        assert 0.0 <= res[k] <= 1.0, res


# ---------------------------------------------------------------------------
# US-082: Korpus-Harness fidelity_run (FEATURE-016 §8 Nr. 2)
#
# Der Lauf rekonstruiert Sample-Slides (reconstruct.js + soffice) und misst sie
# gegen ref.pdf. Render läuft NUR im Container (kf-studio-sim: node + soffice;
# fitz wird dort on-demand bereitgestellt). Diese Tests sind docker-gated und
# skippen sauber, wenn kein docker da ist (CI ohne docker, FEATURE-016 §12.5).
# ---------------------------------------------------------------------------
import json
import shutil
import subprocess

SAMPLE_DECK = "10-182-raumkarussell-gmbh-12-09-2026"


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        subprocess.run(
            ["docker", "image", "inspect", "kf-studio-sim"],
            check=True,
            capture_output=True,
            timeout=30,
        )
        return True
    except Exception:
        return False


docker_gate = pytest.mark.skipif(
    not _docker_available(),
    reason="docker / kf-studio-sim Image fehlt — Render-Pipeline nur im Container",
)


def _run_in_container(args: list[str]) -> dict:
    """fidelity_run.py im kf-studio-sim-Container fahren → geparstes JSON."""
    proc = subprocess.run(
        [
            "docker", "run", "--rm",
            "-v", f"{REPO_ROOT}/engine/data:/app/engine/data",
            "-v", f"{REPO_ROOT}/engine/tooling:/app/engine/tooling",
            "kf-studio-sim",
            "python3", "engine/tooling/fidelity_run.py",
            *args,
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"
    return json.loads(proc.stdout)


@docker_gate
def test_fidelity_run_liefert_je_slide_scores():
    """EARS Nr. 2: Lauf über das Sample → JSON mit je-Slide scores.total + Version."""
    rep = _run_in_container(["--deck", SAMPLE_DECK])
    assert "metrik_version" in rep
    assert rep["slides"], "keine Slides gerendert"
    for slide in rep["slides"]:
        assert slide["deck"] == SAMPLE_DECK
        assert isinstance(slide["page"], int)
        assert set(slide["scores"]) >= {"text", "geometry", "font", "pixel", "total"}
        assert 0.0 <= slide["scores"]["total"] <= 1.0, slide


@docker_gate
def test_fidelity_run_reproduzierbar():
    """EARS Nr. 2: zweiter Lauf liefert identische Scores ±0.005 (Render-Determinismus)."""
    rep_a = _run_in_container(["--deck", SAMPLE_DECK, "--limit", "2"])
    rep_b = _run_in_container(["--deck", SAMPLE_DECK, "--limit", "2"])
    scores_a = {s["page"]: s["scores"] for s in rep_a["slides"]}
    scores_b = {s["page"]: s["scores"] for s in rep_b["slides"]}
    assert scores_a.keys() == scores_b.keys()
    assert scores_a, "kein Slide gerendert"
    for page, sa in scores_a.items():
        sb = scores_b[page]
        for k in ("text", "geometry", "font", "pixel", "total"):
            assert abs(sa[k] - sb[k]) <= 0.005, (page, k, sa[k], sb[k])
