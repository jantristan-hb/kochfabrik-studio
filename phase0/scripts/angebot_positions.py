"""US-013 — Positions-Repeater-Renderer (volle Tabellenregion).

Ersetzt im gefüllten Template die VERBATIM-Positionsdaten (Bezeichnungs-
+ Zahlenspalten + Zwischensummen je Block) durch per-Zeile aus dem
`Angebot`-Modell gerenderte Elemente — pixelnah am echten KOCHfabrik-
Layout (zeilenbasiert, Sub-Header fett inline, Zahlen rechtsbündig).

Invariant erhalten: Logo, Titel/ANGEBOT/Projekt, Gold-Header-Bars +
deren Spaltenüberschriften, Footer/Bankblock. Gold-Header je Block wird
auf die neue y-Position verschoben (Reflow nach Zeilenzahl).

Engine (extract.py/reconstruct.js) UNVERÄNDERT — nur Element-Ebene.
"""
import copy

DY = 0.162           # Zeilen-Pitch (aus Referenz: num-Spalte h/nlines)
HDR_OFF = 0.41       # Gold-Header-y → erste Datenzeile
GAP = 0.34           # Abstand Zwischensumme → nächster Block

# Pre-Wrap-Konstanten — Bezeichnungs-Spalte Word-Break vor Render
BEZ_W, BEZ_MAX = 3.7, 68          # 3.7in × 9pt × SIZE_K ≈ 68 chars
WRAP_PITCH = 1.7                  # Pitch-Multiplikator bei 2-Zeilen-Wrap


def _wrap_bez(t):
    """Word-Break der Bezeichnung auf max. 2 Zeilen (BEZ_MAX chars)."""
    t = str(t or "").strip()
    if len(t) <= BEZ_MAX:
        return [t]
    words, L1, idx = t.split(), "", 0
    for i, w in enumerate(words):
        if not L1:
            L1, idx = w, i + 1
        elif len(L1) + 1 + len(w) <= BEZ_MAX:
            L1 += " " + w; idx = i + 1
        else:
            break
    rest = " ".join(words[idx:])
    if not rest:
        return [L1]
    L2 = rest if len(rest) <= BEZ_MAX else rest[:BEZ_MAX - 1] + "…"
    return [L1, L2]


def _pos_lines(p):
    """Tatsächliche Zeilen-Höhe einer Position (1 oder WRAP_PITCH)."""
    if p.is_header:
        return 1.0
    return WRAP_PITCH if len(_wrap_bez(p.bezeichnung)) > 1 else 1.0


def _eur(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _line(txt, st, **ov):
    d = {k: st.get(k) for k in ("size", "color", "weight", "italic",
                                "font", "align")}
    d.update(ov)
    d["txt"] = txt
    return d


def _txt(x, y, w, st, txt, **ov):
    return {"t": "text", "x": round(x, 3), "y": round(y, 3),
            "w": round(w, 3), "h": 0.16,
            "lines": [_line(txt, st, **ov)]}


def render(el, angebot):
    """el = gefülltes Template (aus angebot_fill.fill). Gibt mutierte
    Kopie mit modell-gerenderten Positionen zurück."""
    el = copy.deepcopy(el)
    rep = el.get("_meta", {}).get("repeater") or {}
    pg = rep.get("positionen", {}).get("page", "2")
    seq = el[pg]

    # 1) Block-Header finden: Zeile mit 'Menge'+'Gesamt' + Titelzelle
    def first(e):
        ls = e.get("lines", [])
        return ls[0].get("txt", "") if ls else ""

    heads = []
    for e in seq:
        if e.get("t") == "text" and first(e).strip() == "Menge":
            y = e.get("y", 0)
            row = [o for o in seq if o.get("t") == "text"
                   and abs(o.get("y", -9) - y) < 0.05]
            tcell = min(row, key=lambda o: o.get("x", 9))   # x≈0.94
            g = next((o for o in row
                      if first(o).strip() == "Gesamt"), None)
            heads.append({"y": y, "title": tcell, "menge": e,
                          "gesamt": g, "row_y": y})
    heads.sort(key=lambda h: h["y"])

    # Spalten-Anker aus den (zu entfernenden) Datenspalten lesen
    def col_x(after_y, lo, hi):
        c = [o for o in seq if o.get("t") == "text"
             and after_y < o.get("y", 0) < after_y + 2.5
             and lo < o.get("x", 0) < hi
             and (o.get("lines", [{}])[0].get("color") == "666666")]
        return c[0].get("x") if c else None

    h0 = heads[0]["y"] if heads else 3.27
    X_BEZ = round(heads[0]["title"].get("x", 0.94), 3) if heads else 0.94
    X_MEN = col_x(h0, 4.6, 5.2) or 5.0
    X_EP = col_x(h0, 5.2, 6.0) or 5.48
    X_GES = col_x(h0, 6.4, 7.3) or 6.86
    body_st = {"size": 9.0, "color": "666666", "weight": "Regular",
               "italic": False, "font": None, "align": None}

    # 2) Header-Prototyp aus dem ERSTEN Template-Gold-Header klonen
    #    (Bar-Rects + Spaltenzellen). Wird je Modell-Block FRISCH
    #    emittiert → JEDER Block bekommt eine Gold-Bar (nicht nur die
    #    im Referenz-PDF physisch vorhandenen).
    h0y = heads[0]["y"] if heads else 3.27
    proto_rects, proto_cells = [], []
    for o in seq:
        oy = o.get("y", -9)
        if o.get("t") == "rect" and o.get("fill") == "977825" \
                and h0y - 0.30 < oy <= h0y + 0.02:
            proto_rects.append((copy.deepcopy(o), round(oy - h0y, 3)))
        elif o.get("t") == "text" and abs(oy - h0y) < 0.05:
            proto_cells.append(copy.deepcopy(o))
    title_proto = (min(proto_cells, key=lambda o: o.get("x", 9))
                   if proto_cells else None)
    tx = round(title_proto.get("x", 0.944), 3) if title_proto else None

    # 3) GESAMTE Positionsregion strippen: Datenzeilen (666666/sz9)
    #    UND alle Template-Gold-Header (Rects + Zellen). keep = Logo/
    #    Titel/ANGEBOT/Projekt + Footer/Bank + Rahmen (invariant).
    head_ys = [h["y"] for h in heads]
    y_top = (h0y - 0.3) if heads else 3.0
    y_foot = min((o.get("y", 99) for o in seq if o.get("t") == "text"
                  and o.get("lines", [{}])[0].get("size") == 5.0),
                 default=10.5)

    def _is_header_el(o):
        oy = o.get("y", -9)
        if o.get("t") == "rect" and o.get("fill") == "977825":
            return any(hy - 0.30 < oy <= hy + 0.02 for hy in head_ys)
        if o.get("t") == "text":
            return any(abs(oy - hy) < 0.05 for hy in head_ys)
        return False

    keep = []
    for e in seq:
        if e.get("t") == "text":
            st = e.get("lines", [{}])[0]
            y = e.get("y", 0)
            if (y_top < y < y_foot and st.get("size") in (9.0,)
                    and st.get("color") == "666666"):
                continue
        if _is_header_el(e):
            continue
        keep.append(e)

    # 4) Vertikal-Budget → adaptive Kompression. Kein Footer-Overlap
    #    ('Text ragt in den Fußraum'), Template-Folgeseiten (T&C)
    #    bleiben unangetastet. Pitch skaliert, Floor = Lesbarkeit.
    #    raw rechnet die ECHTE Zeilenzahl pro Position (inkl. WRAP_PITCH
    #    bei 2-Zeilen-Bezeichnungen) — sonst unterschätzt sie den Bedarf
    #    bei langen Speisenamen und scale wird zu optimistisch (Resultat:
    #    Positionen ragen in Footer).
    raw = sum(HDR_OFF + sum(_pos_lines(p) for p in b.positionen) * DY
              + (DY + GAP if b.zwischensumme else GAP)
              for b in angebot.bloecke) or 1.0
    budget = (y_foot - 0.28) - h0y
    # Floor 0.78 statt 0.55 → lesbarer Pitch (kein „Zeilen-Kleben").
    # Bei extrem vielen Positionen lieber etwas Pitch verlieren als
    # die Lesbarkeit aufgeben; echte Pagination ist nicht in dieser
    # Story.
    scale = 1.0 if raw <= budget else max(0.78, budget / raw)
    dy, hoff, gap = DY * scale, HDR_OFF * scale, GAP * scale

    # 5) Je Modell-Block: geklonte Gold-Bar + Positionszeilen
    cur_y = h0y
    out = []
    for blk in angebot.bloecke:
        for rect, ddy in proto_rects:
            r = copy.deepcopy(rect)
            r["y"] = round(cur_y + ddy, 3)
            out.append(r)
        for cell in proto_cells:
            c = copy.deepcopy(cell)
            c["y"] = round(cur_y, 3)
            if tx is not None and round(c.get("x", 0), 3) == tx \
                    and c.get("lines"):
                c["lines"][0]["txt"] = blk.titel or blk.typ.title()
            out.append(c)
        ry = cur_y + hoff
        # Bezeichnung kann lang sein („Gegrilltes Striploin … &
        # Sommerbohnen") → würde bei wrap:false in die Menge-Spalte
        # laufen. _wrap_bez (Modul-Ebene) bricht auf max 2 Zeilen,
        # _pos_lines spiegelt die echte Höhe für raw/scale (Schritt 4).
        for p in blk.positionen:
            if p.is_header:
                out.append(_txt(X_BEZ, ry, BEZ_W, body_st,
                                p.bezeichnung, weight="Bold"))
                ry = round(ry + dy, 3)
            else:
                lns = _wrap_bez(p.bezeichnung)
                bez_el = {"t": "text", "x": round(X_BEZ, 3),
                          "y": round(ry, 3), "w": round(BEZ_W, 3),
                          "h": 0.16 if len(lns) == 1 else 0.32,
                          "lines": [_line(s, body_st) for s in lns]}
                out.append(bez_el)
                out.append(_txt(X_MEN, ry, 0.4, body_st, f"{p.menge:g}"))
                out.append(_txt(X_EP, ry, 0.5, body_st,
                                _eur(p.einzelpreis)))
                out.append(_txt(X_GES, ry, 0.5, body_st,
                                _eur(p.gesamt)))
                ry = round(ry + dy * _pos_lines(p), 3)
        if blk.zwischensumme:
            ry = round(ry + dy, 3)
            out.append(_txt(X_GES - 0.12, ry, 0.6, body_st,
                            _eur(blk.zwischensumme), weight="Bold"))
        cur_y = round(ry + gap, 3)

    el[pg] = keep + out
    return el


if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from angebot_fill import fill
    from angebot_model import example
    r = render(fill(example()), example())
    seq = r[r["_meta"]["repeater"]["positionen"]["page"]]
    bez = [l.get("txt") for e in seq if e.get("t") == "text"
           for l in e.get("lines", [])]
    print("Positions-Zeilen gerendert:",
          [b for b in bez if "Grillequipment" in b or "Live Cooking" in b
           or "Gerüstbohlen" in b])
