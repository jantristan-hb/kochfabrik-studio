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

    # 2) Alle Positions-DATEN-Elemente entfernen (zwischen erstem
    #    Gold-Header und Footer; color 666666 size~9, NICHT die
    #    Header-Zellen size 8 schwarz, NICHT Footer size 5)
    y_top = (heads[0]["y"] - 0.3) if heads else 3.0
    y_foot = min((o.get("y", 99) for o in seq if o.get("t") == "text"
                  and o.get("lines", [{}])[0].get("size") == 5.0),
                 default=10.5)
    keep = []
    for e in seq:
        if e.get("t") == "text":
            st = e.get("lines", [{}])[0]
            y = e.get("y", 0)
            is_data = (y_top < y < y_foot and st.get("size") in (9.0,)
                       and st.get("color") == "666666")
            if is_data:
                continue
        keep.append(e)

    # 3) Modell-Blöcke per Reihenfolge auf Gold-Header mappen + Reflow
    cur_y = heads[0]["y"] if heads else 3.27
    out_rows = []
    for bi, blk in enumerate(angebot.bloecke):
        hd = heads[bi] if bi < len(heads) else None
        if hd:                                  # Gold-Header (Bar+Zellen)
            shift = cur_y - hd["y"]
            for o in keep:
                if o.get("t") == "rect" and hd["y"] - 0.3 < \
                        o.get("y", -9) <= hd["y"] + 0.02:
                    o["y"] = round(o.get("y", 0) + shift, 3)
                elif o.get("t") == "text" and abs(
                        o.get("y", -9) - hd["y"]) < 0.05:
                    o["y"] = round(cur_y, 3)
            tcell = hd["title"]
            if tcell.get("lines"):
                tcell["lines"][0]["txt"] = blk.titel or blk.typ.title()
        ry = cur_y + HDR_OFF
        for p in blk.positionen:
            if p.is_header:
                out_rows.append(_txt(X_BEZ, ry, 3.4, body_st,
                                     p.bezeichnung, weight="Bold"))
            else:
                out_rows.append(_txt(X_BEZ, ry, 3.4, body_st,
                                     p.bezeichnung))
                out_rows.append(_txt(X_MEN, ry, 0.4, body_st,
                                     f"{p.menge:g}"))
                out_rows.append(_txt(X_EP, ry, 0.5, body_st,
                                     _eur(p.einzelpreis)))
                out_rows.append(_txt(X_GES, ry, 0.5, body_st,
                                     _eur(p.gesamt)))
            ry = round(ry + DY, 3)
        if blk.zwischensumme:
            ry = round(ry + DY, 3)
            out_rows.append(_txt(X_GES - 0.12, ry, 0.6, body_st,
                                 _eur(blk.zwischensumme), weight="Bold"))
        cur_y = round(ry + GAP, 3)

    el[pg] = keep + out_rows
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
