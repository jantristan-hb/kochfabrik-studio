# TEST.md — kochfabrik Sprint 12 (TDD-Stubs aus EARS)

> Stubs aus FEATURE-006/007/008 — initial ROT. **Test-Runner:** pytest
> (synchron, KEIN Async-Plugin nötig — keine async-Stubs in diesem
> Sprint). Ablage: `backend/tests/test_sprint12.py` — entsteht auf dem
> Ketten-Branch MIT US-053 und wächst pro Ketten-Story (sequentiell,
> keine Fixture-Konflikte; alle Fixtures lokal in der Datei).
> Doc-/Ops-Stories (US-052/058/060) nutzen ihre Verify-Blöcke als Gate
> (SSH/GitHub-abhängig — nicht suite-fähig).

```python
"""Sprint-12-Tests — Code-Ordnung + Docs. EARS-Bindung in Kommentaren."""
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


# FEATURE-006 EARS 1 — Routen identisch + app.py ist Komposition (US-053/054)
def test_router_layout():
    for f in ("auth.py", "bildgenerator.py", "angebot.py",
              "praesentation.py"):
        assert os.path.isfile(os.path.join(ROOT, "backend", "routers", f)), f
    assert sum(1 for _ in open(os.path.join(ROOT, "backend", "app.py"),
                               encoding="utf-8")) < 200


def test_routen_inventar_unveraendert():
    # Vorher-Inventar wird von US-053 als Fixture-Datei committet:
    # backend/tests/fixtures/routes_baseline.txt (aus master-Stand)
    import sys
    sys.path.insert(0, ROOT)
    from backend.app import app
    rs = sorted(f"{sorted(r.methods or ['GET'])} {r.path}"
                for r in app.routes)
    base = open(os.path.join(ROOT, "backend", "tests", "fixtures",
                             "routes_baseline.txt"),
                encoding="utf-8").read().splitlines()
    assert rs == sorted(base)


# FEATURE-006 EARS 2 — genau EINE pgbundle-Ladestelle (US-055)
def test_eine_bundle_ladestelle():
    out = subprocess.run(
        ["grep", "-rl", "pgbundle", "--include=*.py",
         "backend", "engine/scripts"],
        cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
    loaders = [f for f in out if "np.load" in open(
        os.path.join(ROOT, f), encoding="utf-8").read()]
    assert loaders == ["engine/scripts/bundle.py"], loaders


# FEATURE-006 EARS 3 — Tooling-Split (US-056)
def test_tooling_split():
    assert os.path.isdir(os.path.join(ROOT, "engine", "tooling"))
    # Stichprobe: reine Build-Tools sind NICHT mehr unter scripts/
    for tool in ("build_korpus.py", "gen_fiktiv.py", "recon_food_reuse.py"):
        assert not os.path.exists(
            os.path.join(ROOT, "engine", "scripts", tool)), tool
        assert os.path.exists(
            os.path.join(ROOT, "engine", "tooling", tool)), tool
    # Runtime-Kern bleibt:
    for rt in ("assemble.py", "compose_offer.py", "pg_shim.py",
               "bundle.py", "_deckpipe.py"):
        assert os.path.exists(
            os.path.join(ROOT, "engine", "scripts", rt)), rt


# FEATURE-006 EARS 4 — Sim-Gate hat DB-Block (US-057)
def test_sim_gate_db_block():
    src = open(os.path.join(ROOT, "tools", "sim_gate.sh"),
               encoding="utf-8").read()
    assert "SIM_GATE_DB" in src
    assert "timeout " not in src


# FEATURE-008 EARS 1 — CLAUDE.md vollständig (US-059)
def test_claude_md():
    p = os.path.join(ROOT, "CLAUDE.md")
    assert os.path.getsize(p) > 1000
    md = open(p, encoding="utf-8").read()
    assert "{…}" not in md
    for marker in ("sim_gate.sh", "live_verify.sh", "backend/routers"):
        assert marker in md, marker
```

**Fixture-Ownership (Wave-konform):** `routes_baseline.txt` erzeugt
US-053 (erste Ketten-Story) aus dem unveränderten master-Stand —
alle Konsumenten laufen später in derselben sequentiellen Kette.
US-052/058/060 (SSH/GitHub-gebunden) bleiben außerhalb der Suite.
