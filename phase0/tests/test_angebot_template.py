"""US-012 — Regression: aus Template+Modell erzeugtes Angebot ist
strukturell ein echtes KOCHfabrik-Angebot (kf_classify == 'angebot',
invariante Blöcke + Labels erhalten, Modellwerte injiziert).
Run: python3 tests/test_angebot_template.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from verify_angebot import verify                              # noqa

f = 0
ok, checks, err = verify()
for name, cond in checks.items():
    print(("  ok  " if cond else "  FAIL") + " " + name)
    f += 0 if cond else 1
if f and err:
    print("stderr:", err)
print(f"\n{'ALLE TESTS GRÜN' if f == 0 else str(f)+' FEHLER'}")
raise SystemExit(1 if f else 0)
