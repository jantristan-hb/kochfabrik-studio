"""Sprint-12-Tests — Code-Ordnung + Docs. EARS-Bindung in Kommentaren.

US-053 legt die ersten beiden Tests an:
- test_router_layout  (prüft in US-053 NUR auth.py + bildgenerator.py;
  US-054 erweitert um angebot.py/praesentation.py + app.py-<200-Z.-Grenze)
- test_routen_inventar_unveraendert

Die weiteren Tests aus docs/sprint-12/TEST.md (test_eine_bundle_ladestelle,
test_tooling_split, test_sim_gate_db_block, test_claude_md) kommen mit den
Folge-Stories US-055/056/057/059.

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
