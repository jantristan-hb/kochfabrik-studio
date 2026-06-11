"""Sprint-12-Tests — Code-Ordnung + Docs. EARS-Bindung in Kommentaren.

US-053 legt die ersten beiden Tests an:
- test_router_layout  (prüft in US-053 NUR auth.py + bildgenerator.py;
  US-054 erweitert um angebot.py/praesentation.py + app.py-<200-Z.-Grenze)
- test_routen_inventar_unveraendert

US-055 ergänzt test_eine_bundle_ladestelle (TEST.md) + test_bundle_ranking_gold
(Gold-Diff gegen ranking_gold.json — bit-identisches Ranking, Pitfall 4).
Die restlichen TEST.md-Tests (test_tooling_split, test_sim_gate_db_block,
test_claude_md) kommen mit US-056/057/059.

HINWEIS Mount-Route: Die StaticFiles-Mount-Route (StaticFiles auf "/") ist
ein starlette.routing.Mount und hat KEIN .methods-Attribut. Der TEST.md-
Ausdruck `r.methods or [...]` würde darauf mit AttributeError abbrechen,
darum hier (und in der Baseline-Fixture) konsistent
`getattr(r, "methods", None) or ["GET"]` — verhaltensneutral, Mount → GET.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


# FEATURE-006 EARS 1 — Routen identisch + app.py ist Komposition (US-053/054)
def test_router_layout():
    # US-053: auth + bildgenerator. US-054: angebot + praesentation +
    # app.py-<200-Z.-Grenze (app.py ist reine Komposition).
    for f in ("auth.py", "bildgenerator.py", "angebot.py",
              "praesentation.py"):
        assert os.path.isfile(os.path.join(ROOT, "backend", "routers", f)), f
    assert sum(1 for _ in open(os.path.join(ROOT, "backend", "app.py"),
                               encoding="utf-8")) < 200


def test_routen_inventar_unveraendert():
    # Vorher-Inventar von US-053 als Fixture committet (master-Stand):
    # backend/tests/fixtures/routes_baseline.txt
    import sys
    sys.path.insert(0, ROOT)
    from backend.app import app
    rs = sorted(f"{sorted(getattr(r, 'methods', None) or ['GET'])} {r.path}"
                for r in app.routes)
    base = open(os.path.join(ROOT, "backend", "tests", "fixtures",
                             "routes_baseline.txt"),
                encoding="utf-8").read().splitlines()
    assert rs == sorted(base)


# FEATURE-006 EARS 2 — genau EINE pgbundle-Ladestelle (US-055)
def test_eine_bundle_ladestelle():
    # HINWEIS: Die Testdatei selbst nennt sowohl "pgbundle" (grep-Arg)
    # als auch den Filter-String "np.load" und würde sich sonst selbst
    # matchen — Tests werden daher ausgeschlossen (verhaltensneutral,
    # gemeint sind Produktionsmodule unter backend/ + engine/scripts/).
    import subprocess
    out = subprocess.run(
        ["grep", "-rl", "pgbundle", "--include=*.py",
         "backend", "engine/scripts"],
        cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
    out = [f for f in out if "tests/" not in f]
    loaders = [f for f in out if "np.load" in open(
        os.path.join(ROOT, f), encoding="utf-8").read()]
    assert loaders == ["engine/scripts/bundle.py"], loaders


# FEATURE-006 EARS 2 — Ranking bit-identisch (Pitfall 4, Gold-Diff).
# ranking_gold.json wurde aus dem Pre-Refactor-Stand (zwei getrennte
# Loader) erzeugt; bundle.rank() muss byte-gleiche Reihenfolgen liefern
# für slidesuche- (global top-20) UND pg_shim-Pfad (global + restringiert
# top-8). Fixe Seed-Query (kein Gemini-Call) → reproduzierbar.
def test_bundle_ranking_gold():
    import json
    import sys
    import numpy as np
    eng = os.path.join(ROOT, "engine", "scripts")
    if eng not in sys.path:
        sys.path.insert(0, eng)
    import bundle
    if not bundle.available():
        import pytest
        pytest.skip("pgbundle.npz nicht vorhanden")
    gold = json.load(open(os.path.join(
        ROOT, "backend", "tests", "fixtures", "ranking_gold.json"),
        encoding="utf-8"))
    b = bundle.load()
    _, D = b["emb"].shape
    qv = bundle.normalize_query(
        np.random.default_rng(gold["seed"]).standard_normal(D))
    ss = [[str(b["deck"][i]), int(b["page"][i]),
           str(b["module_label"][i])] for i in bundle.rank(qv, None, 20)]
    pg = [[str(b["deck"][j]), int(b["page"][j]),
           str(b["src_pdf"][j])] for j in bundle.rank(qv, None, 8)]
    idx = np.where(b["module_type"] == gold["module_type_pick"])[0]
    rr = [[str(b["deck"][j]), int(b["page"][j]),
           str(b["src_pdf"][j])] for j in bundle.rank(qv, idx, 8)]
    assert ss == [list(x) for x in gold["slidesuche_top20"]]
    assert pg == [list(x) for x in gold["pg_shim_global_top8"]]
    assert rr == [list(x) for x in gold["pg_shim_restr_top8"]]


# FEATURE-006 EARS 3 — Tooling-Split (US-056)
# Klassifikation per Import-Graph (US-056), NICHT per Namen — gen_fiktiv
# ist Runtime (engine_glue:349, angebot_chat:18), build_angebot_template
# ist Runtime (subprocess aus angebot_render). TEST.md-Sample wurde per
# Namensraten geschrieben (selbst das Pitfall-3-Beispiel) → hier korrigiert
# auf die EARS-Wahrheit (Option A, vom team-lead genehmigt).
def test_tooling_split():
    assert os.path.isdir(os.path.join(ROOT, "engine", "tooling"))
    # Stichprobe: reine Build-Tools sind NICHT mehr unter scripts/
    for tool in ("build_korpus.py", "recon_food_reuse.py",
                 "embed_cluster.py"):
        assert not os.path.exists(
            os.path.join(ROOT, "engine", "scripts", tool)), tool
        assert os.path.exists(
            os.path.join(ROOT, "engine", "tooling", tool)), tool
    # Runtime-Kern bleibt scripts/ — inkl. gen_fiktiv + build_angebot_template
    # (Anti-Namensraten: beide trotz Build-Anmutung Runtime-Dependencies).
    for rt in ("assemble.py", "compose_offer.py", "pg_shim.py",
               "bundle.py", "_deckpipe.py", "gen_fiktiv.py",
               "build_angebot_template.py"):
        assert os.path.exists(
            os.path.join(ROOT, "engine", "scripts", rt)), rt
