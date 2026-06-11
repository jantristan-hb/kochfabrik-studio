"""bundle — EINE Lade-/Normalisier-/ANN-Schicht für pgbundle.npz.

US-055 / ADR-003 (Hybrid: vendortes numpy-Bundle statt pgvector). Vor
diesem Modul luden pg_shim.py UND slidesuche.py das Bundle je selbst per
np.load + eigener L2-Normalisierung — strukturell F-E-03 (zwei
Ladestellen, Drift-Risiko). Jetzt: `np.load` auf pgbundle existiert genau
EINMAL (hier); pg_shim und slidesuche nutzen load()/rank().

Ranking originaltreu (pgvector `<=>` = Cosinus-Distanz, ORDER BY asc ==
Cosinus-Sim desc == (norm.E)·(norm.q) desc). rank() bildet die bisherige
Sequenz `E[idx] @ qv` → `idx[np.argsort(-sim)][:k]` bit-identisch ab —
gleiche Float32-Arithmetik, gleiche argsort-Tie-Break-Semantik, gleicher
1e-9-Normalisierungs-Epsilon wie an den Altstellen.

Bundle: ../data/pgbundle.npz (emb float32 N×768 + deck/page/src_pdf/
module_type/module_label).
"""
import os

import numpy as np

_D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
_NPZ = os.path.join(_D, "pgbundle.npz")

_BUNDLE = None


def npz_path() -> str:
    return _NPZ


def available() -> bool:
    return os.path.isfile(_NPZ)


def load() -> dict:
    """Lädt + cached das Bundle als dict. `_normemb` = L2-normalisierte
    Embeddings (float32), 1e-9-Epsilon wie an den Altstellen. EINZIGE
    np.load-Stelle für pgbundle.npz (ADR-003 / FEATURE-006 EARS 2)."""
    global _BUNDLE
    if _BUNDLE is not None:
        return _BUNDLE
    z = np.load(_NPZ, allow_pickle=True)
    b = {k: z[k] for k in z.files}
    e = b["emb"].astype(np.float32)
    b["_normemb"] = e / (np.linalg.norm(e, axis=1, keepdims=True) + 1e-9)
    _BUNDLE = b
    return _BUNDLE


def normalize_query(vec) -> np.ndarray:
    """Query-Vektor → L2-normalisiert (float32, 1e-9-Epsilon)."""
    qv = np.asarray(vec, np.float32)
    return qv / (np.linalg.norm(qv) + 1e-9)


def rank(qv, idx=None, k=None) -> np.ndarray:
    """ANN gegen das normalisierte Bundle. `qv` ist BEREITS normalisiert
    (siehe normalize_query). `idx` schränkt die Kandidaten ein (None =
    global); `k` begrenzt das Ergebnis (None = alle). Gibt die geordneten
    Bundle-Indizes zurück — bit-identisch zur bisherigen Sequenz
    `E[idx] @ qv` → `idx[np.argsort(-sim)][:k]`."""
    E = load()["_normemb"]
    if idx is None:
        idx = np.arange(len(E))
    if len(idx) == 0:
        return idx[:0]
    sim = E[idx] @ qv
    order = idx[np.argsort(-sim)]
    return order if k is None else order[:k]
