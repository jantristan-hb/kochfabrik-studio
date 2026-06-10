"""Regression: assemble.py darf bei 0 erkannten Gängen NICHT crashen
(kaufmännisches Angebots-PDF ohne Speisen → embed()-Batch leer →
np.asarray([]) ist 1-D → norm(axis=1) AxisError). Bildet die gefixte
Ln-Konstruktion 1:1 ab. Run: python3 test_empty_courses.py"""
import numpy as np

f = 0


def chk(name, cond):
    global f
    print(("  ok  " if cond else "  FAIL") + " " + name)
    f += 0 if cond else 1


def build_Ln(allv, nL):
    """Exakt der gefixte Pfad aus assemble.py."""
    if nL and len(allv) >= nL:
        Ln = np.asarray(allv[:nL], float)
        Ln = Ln / (np.linalg.norm(Ln, axis=1, keepdims=True) + 1e-9)
    else:
        Ln = np.zeros((0, 768))
    return Ln


# 1) 0 Gänge: allv leer, nL>0 (DB-Labels da) → kein Crash, leere Matrix
try:
    Ln = build_Ln([], 30)
    crash = False
except Exception:
    crash = True
chk("leeres allv crasht nicht", not crash)
chk("leeres allv -> Shape (0,768)", build_Ln([], 30).shape == (0, 768))

# 2) allv kürzer als nL (Teil-Embed) → ebenfalls sicher leer
chk("zu kurzes allv -> (0,768)",
    build_Ln([[0.1] * 768] * 5, 30).shape == (0, 768))

# 3) Normalfall: nL Vektoren → (nL,768), zeilenweise normiert (||·||≈1)
Ln = build_Ln([[float(i + 1)] * 768 for i in range(4)], 4)
chk("voller Fall -> (4,768)", Ln.shape == (4, 768))
chk("zeilen-normiert (norm≈1)",
    np.allclose(np.linalg.norm(Ln, axis=1), 1.0, atol=1e-3))

# 4) nL==0 (keine DB-Labels) → auch (0,768), kein Crash
chk("nL=0 -> (0,768)", build_Ln([], 0).shape == (0, 768))

print(f"\n{'ALLE TESTS GRÜN' if f == 0 else str(f)+' FEHLER'}")
raise SystemExit(1 if f else 0)
