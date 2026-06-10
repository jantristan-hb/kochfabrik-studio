"""Sprint-11-Tests — Monorepo-Layout + Gates. EARS-Bindung in Kommentaren."""
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


# FEATURE-004 EARS 3 — Engine-Historie + flaches Layout (US-047)
def test_monorepo_layout():
    for d in ("engine/scripts", "engine/spike-pptxgenjs",
              "engine/tests", "engine/data"):
        assert os.path.isdir(os.path.join(ROOT, d)), d
    assert not os.path.isdir(os.path.join(ROOT, "engine", "phase0"))


# FEATURE-004 EARS 5 — gerettete Artefakte (US-047)
def test_engine_data_und_node_modules_gerettet():
    assert os.path.getsize(os.path.join(ROOT, "engine", "data",
                                        "pgbundle.npz")) > 1_000_000
    assert os.path.isdir(os.path.join(
        ROOT, "engine", "spike-pptxgenjs", "node_modules", "pptxgenjs"))


# FEATURE-004 EARS 4 — keine Alt-Pfade mehr in backend/ (US-048)
def test_keine_phase0_referenzen_im_backend():
    out = subprocess.run(
        ["grep", "-rlE", "phase0|pptxgenerator_v2", "backend"],
        cwd=ROOT, capture_output=True, text=True)
    hits = [l for l in out.stdout.splitlines()
            if not l.startswith("backend/tests/")]
    assert hits == [], hits
    assert not os.path.exists(os.path.join(ROOT, "vendor.sh"))


# FEATURE-005 EARS 2/3 — Dockerfile- + Sim-Gate-Tests (test_dockerfile_monorepo,
# test_sim_gate_vorhanden aus TEST.md) gehören zu US-049/US-050 und werden mit
# diesen Folge-Stories ergänzt (Dockerfile-COPY + tools/sim_gate.sh existieren
# hier noch nicht).
