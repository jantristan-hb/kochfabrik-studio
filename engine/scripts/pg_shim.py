"""pg_shim — DB-freier psycopg2-Ersatz für assemble.py.

Bedient EXAKT die 4 Query-Shapes aus assemble.py aus einem vendorten
numpy-Bundle (statt Postgres/pgvector). assemble.py-Matching-Logik
bleibt unverändert — nur connect() wird getauscht. Ranking originaltreu:
pgvector `<=>` = Cosinus-Distanz, ORDER BY asc == Cosinus-Sim desc
== (norm.E)·(norm.q) desc.

US-055/ADR-003: Bundle-Laden + ANN laufen über die gemeinsame Schicht
`bundle` (die einzige Ladestelle) — kein eigener Bundle-Load mehr.
Ranking bleibt bit-identisch (bundle.rank bildet die bisherige Sequenz
ab). Zusätzlich: ../data/static_slide.json.
"""
import json
import os
import re

import numpy as np

import bundle as _bundle

_D = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "..", "data")
_SS = os.path.join(_D, "static_slide.json")


def available():
    return _bundle.available() and os.path.isfile(_SS)


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
            qv = _bundle.normalize_query(json.loads(p[-1]))
            if "module_type=%s" in s:                  # restringiert
                idx = np.where(self._b["module_type"] == p[0])[0]
            else:                                      # global
                idx = None                             # global (alle)
            order = _bundle.rank(qv, idx, 8)           # <=> asc, top-8
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
        self._b = _bundle.load()                       # EINE Ladestelle
        self._ss = json.load(open(_SS, encoding="utf-8"))

    def cursor(self):
        return _Cur(self._b, self._ss)

    def close(self):
        pass


def connect(**_):
    return _Conn()
