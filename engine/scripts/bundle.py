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

# US-073 / FEATURE-013: Bild-Embedding-Bundle (imgbundle.npz). Optional —
# fehlt es, fällt rank_mixed graceful auf text-only zurück. `np.load` auf
# Bundles existiert weiterhin NUR in diesem Modul (ADR-003).
_IMG_NPZ = os.path.join(_D, "imgbundle.npz")
_IMG = None
_IMG_LOADED = False


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


def load_img():
    """Lädt + cached das imgbundle (US-073). Gibt ein dict mit
    `imgemb` (float32 N×768, L2-normiert, NaN-Zeile = Slide ohne
    Foto-Vektor), `deck`, `page` zurück — oder None, wenn das Bundle
    fehlt (graceful, EARS Nr. 3 IF-Klausel). EINZIGE np.load-Stelle für
    imgbundle.npz (ADR-003, analog load())."""
    global _IMG, _IMG_LOADED
    if _IMG_LOADED:
        return _IMG
    _IMG_LOADED = True
    if not os.path.isfile(_IMG_NPZ):
        _IMG = None
        return None
    z = np.load(_IMG_NPZ, allow_pickle=True)
    _IMG = {k: z[k] for k in z.files}
    _IMG["imgemb"] = _IMG["imgemb"].astype(np.float32)
    return _IMG


def rank_mixed(qv, k=None, alpha=0.7) -> np.ndarray:
    """Gemischtes ANN: score = alpha*text_sim + (1-alpha)*img_sim über
    das globale Bundle. `qv` ist BEREITS normalisiert (normalize_query).

    - imgbundle fehlt → graceful text-only (== rank(qv, None, k)).
    - alpha == 1.0 → reine Text-Reihenfolge (img-Beitrag *0), == rank.
    - Slides OHNE Foto-Vektor (NaN-Zeile im imgbundle bzw. nicht im
      imgbundle enthalten) zählen NEUTRAL text-only: ihr Mischscore ist
      alpha*text + (1-alpha)*text == text_sim, NICHT (1-alpha)*0
      (Pitfall 4). Das hält sie auf ihrem Text-Rang statt sie wegen
      fehlendem Foto künstlich nach hinten zu schieben.

    imgemb wie text-emb L2-normiert (in embed_images erzeugt), die
    Cosinus-Mischung ist damit auf gleicher Skala wie text_sim.
    """
    E = load()["_normemb"]
    text_sim = E @ qv
    img = load_img()
    if img is None or alpha >= 1.0:
        order = np.argsort(-text_sim)
        return order if k is None else order[:k]
    # img_sim je Bundle-Slide über (deck,page)-Join; Default = text_sim
    # (neutral: Slides ohne Foto behalten ihren Text-Score).
    img_sim = text_sim.copy()
    b = load()
    key2row = {}
    idecks, ipages = img["deck"], img["page"]
    iemb = img["imgemb"]
    for r in range(len(idecks)):
        vec = iemb[r]
        if np.isnan(vec).any():          # Slide ohne Foto-Vektor
            continue
        key2row[(str(idecks[r]), int(ipages[r]))] = r
    if key2row:
        bd, bp = b["deck"], b["page"]
        for i in range(len(text_sim)):
            r = key2row.get((str(bd[i]), int(bp[i])))
            if r is not None:
                img_sim[i] = float(iemb[r] @ qv)
    score = alpha * text_sim + (1.0 - alpha) * img_sim
    order = np.argsort(-score)
    return order if k is None else order[:k]
