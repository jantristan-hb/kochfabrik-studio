"""pg_shim — DB-freier psycopg2-Ersatz für assemble.py.

Bedient EXAKT die 4 Query-Shapes aus assemble.py aus einem vendorten
numpy-Bundle (statt Postgres/pgvector). assemble.py-Matching-Logik
bleibt unverändert — nur connect() wird getauscht. Ranking originaltreu:
pgvector `<=>` = Cosinus-Distanz, ORDER BY asc == Cosinus-Sim desc
== (norm.E)·(norm.q) desc.

Bundle: ../data/pgbundle.npz (emb float32 N×768 + deck/page/src_pdf/
module_type/module_label) + ../data/static_slide.json.
"""
import json
import os
import re

import numpy as np

_D = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "..", "data")
_NPZ = os.path.join(_D, "pgbundle.npz")
_SS = os.path.join(_D, "static_slide.json")


def available():
    return os.path.isfile(_NPZ) and os.path.isfile(_SS)


class _Cur:
    def __init__(self, b, ss):
        self._b, self._ss, self._r = b, ss, []

    def execute(self, sql, params=None):
        s = re.sub(r"\s+", " ", sql).strip()
        p = params or ()
        if "DISTINCT module_type, module_label" in s:
            seen, out = set(), []
            mt, ml = self._b["module_type"], self._b["module_label"]
            for i in range(len(mt)):
                a, b = mt[i], ml[i]
                if a and b and a != "None" and b != "None" \
                        and (a, b) not in seen:
                    seen.add((a, b))
                    out.append((str(a), str(b)))
            self._r = out
        elif "FROM static_slide" in s:
            self._r = [(r["deck"], r["page"], r["src_pdf"],
                        r["category"], r["skel_pos"]) for r in self._ss
                       if r.get("inclusion") == "pflicht"
                       and r.get("category") != "COVER"]
        elif "FROM menu_composition" in s and "embedding<=>" in s:
            qv = np.asarray(json.loads(p[-1]), np.float32)
            qv = qv / (np.linalg.norm(qv) + 1e-9)
            E = self._b["_normemb"]
            if "module_type=%s" in s:                  # restringiert
                idx = np.where(self._b["module_type"] == p[0])[0]
            else:                                      # global
                idx = np.arange(len(E))
            if len(idx) == 0:
                self._r = []
                return
            sim = E[idx] @ qv                          # cos-sim
            order = idx[np.argsort(-sim)][:8]          # <=> asc
            self._r = [(str(self._b["deck"][j]),
                        int(self._b["page"][j]),
                        str(self._b["src_pdf"][j])) for j in order]
        else:
            self._r = []

    def fetchall(self):
        return self._r

    def fetchone(self):
        return self._r[0] if self._r else None

    def close(self):
        pass


class _Conn:
    def __init__(self):
        z = np.load(_NPZ, allow_pickle=True)
        b = {k: z[k] for k in z.files}
        e = b["emb"].astype(np.float32)
        b["_normemb"] = e / (np.linalg.norm(e, axis=1,
                                            keepdims=True) + 1e-9)
        self._b = b
        self._ss = json.load(open(_SS, encoding="utf-8"))

    def cursor(self):
        return _Cur(self._b, self._ss)

    def close(self):
        pass


def connect(**_):
    return _Conn()
