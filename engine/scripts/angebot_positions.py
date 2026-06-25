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

# A1 — globale Schrift-Vergrößerung. EIN Knopf: skaliert am Ende von
# render() ALLE Text-Größen uniform (Proportionen bleiben exakt), und
# zieht Zeilen-Pitch (DY) + Umbruch-Schwelle (BEZ_MAX) konsistent mit.
# Die "faithful"-Engine-Konstante SIZE_K (lib/text.js) bleibt unberührt.
FONT_SCALE = 1.3

DY = round(0.162 * FONT_SCALE, 4)   # Zeilen-Pitch, skaliert mit Schrift
HDR_OFF = 0.55       # Gold-Header-y → erste Datenzeile (Atem-Margin)
GAP = 0.55           # Abstand Zwischensumme → nächster Block (Atem)
SUBHEAD_LEAD = 0.5   # Zusatz-Luft VOR Sub-Header (× DY, ab 2. SubHd)
ZSUM_LEAD = 2.0      # Luft zwischen letzter Position und Zwischensumme
PAGE_RESERVE = 0.30  # Safety-Margin oberhalb Footer (in)

# Pre-Wrap-Konstanten — Bezeichnungs-Spalte Word-Break vor Render.
# BEZ_MAX schrumpft mit FONT_SCALE (größere Schrift → weniger Zeichen
# passen in die 3.7in-Spalte), sonst läuft der Text in die Mengenspalte.
BEZ_W = 3.7
BEZ_MAX = int(68 / FONT_SCALE)
WRAP_PITCH = 1.7                  # Pitch-Multiplikator bei 2-Zeilen-Wrap


def _scale_fonts(el, k):
    """A1 — letzter Schritt in render(): skaliert JEDE Text-Zeilen-Größe
    über alle Seiten uniform mit k. Läuft NACH den größen-basierten
    Heuristiken (Strip size==9.0, Footer/Pagenum size==5.0), damit die
    unberührt bleiben."""
    if k == 1.0:
        return el
    for key, seq in el.items():
        if key == "_meta":
            continue
        for e in seq:
            if e.get("t") != "text":
                continue
            for ln in e.get("lines", []):
                s = ln.get("size")
                if isinstance(s, (int, float)):
                    ln["size"] = round(s * k, 1)
    return el


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

    # 4) Block-Höhe pro Block (echte Höhe, KEINE Kompression mehr —
    #    bei Overflow wird auf neue Seite umbrochen statt zu quetschen).
    def _blk_height(blk):
        h = HDR_OFF
        sub_count = 0
        for p in blk.positionen:
            if p.is_header:
                if sub_count > 0:
                    h += DY * SUBHEAD_LEAD
                sub_count += 1
                h += DY
            else:
                h += DY * _pos_lines(p)
        if blk.zwischensumme:
            h += DY * ZSUM_LEAD
        return h

    # 5) Einen Block bei start_y emittieren (Gold-Bar + Positionen +
    #    Zwischensumme). Gibt (out_elements, end_y) zurück.
    def _emit_block(blk, start_y):
        out = []
        for rect, ddy in proto_rects:
            r = copy.deepcopy(rect)
            r["y"] = round(start_y + ddy, 3)
            out.append(r)
        for cell in proto_cells:
            c = copy.deepcopy(cell)
            c["y"] = round(start_y, 3)
            if tx is not None and round(c.get("x", 0), 3) == tx \
                    and c.get("lines"):
                c["lines"][0]["txt"] = blk.titel or blk.typ.title()
            out.append(c)
        ry = start_y + HDR_OFF
        sub_count = 0
        for p in blk.positionen:
            if p.is_header:
                if sub_count > 0:
                    ry = round(ry + DY * SUBHEAD_LEAD, 3)
                sub_count += 1
                out.append(_txt(X_BEZ, ry, BEZ_W, body_st,
                                p.bezeichnung, weight="Bold"))
                ry = round(ry + DY, 3)
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
                ry = round(ry + DY * _pos_lines(p), 3)
        if blk.zwischensumme:
            ry = round(ry + DY * ZSUM_LEAD, 3)
            out.append(_txt(X_GES - 0.12, ry, 0.6, body_st,
                            _eur(blk.zwischensumme), weight="Bold"))
        return out, ry

    # 6) Pagination: Blöcke auf Position-Seiten verteilen. Bei Overflow
    #    neue Seite (Klon der Page-Frame: Logo/Titel/Footer/Bank-Block),
    #    nicht quetschen. AGB-Seiten werden danach re-numbered.
    y_avail = y_foot - PAGE_RESERVE
    pages_blocks = [[]]                          # Liste je Page: Elemente
    cur_y = h0y
    for blk in angebot.bloecke:
        bh = _blk_height(blk)
        # Wenn nicht erster Block auf der Seite UND Block läuft in Footer:
        # neue Seite. Einzelner Block größer als Page-Budget → läuft trotzdem
        # (echte Multi-Page-Block-Split wäre eigener Sprint).
        if pages_blocks[-1] and cur_y + bh > y_avail:
            pages_blocks.append([])
            cur_y = h0y
        block_out, end_y = _emit_block(blk, cur_y)
        pages_blocks[-1].extend(block_out)
        cur_y = round(end_y + GAP, 3)

    # 7) Seiten in el einbauen — keep auf Seite 1 ist Original (mit
    #    ANGEBOT-Titel/Projekt-Zeile/Footer/Bank/Logo). Folgeseiten
    #    klonen die SAME keep (auch Titel/Projekt — minimaler Schaden
    #    und maximale Konsistenz; echte „nur Footer auf Folgeseiten"
    #    wäre Style-Variante). AGB-Pages danach.
    pg_int = int(pg)
    # AGB-Pages (alles nach der ursprünglichen Positionsseite) puffern
    agb_pages = []
    for k in sorted([k for k in el if k != "_meta" and int(k) > pg_int],
                    key=int):
        agb_pages.append(el[k])
        del el[k]

    def _set_page_num(seq, n):
        """Page-Number-Textbox (rechts unten, sz=5.0, rein numerisch).
        Im Template auf x≈6.58 y≈11.32 — eindeutig über size 5.0."""
        for e in seq:
            if e.get("t") != "text":
                continue
            for ln in e.get("lines", []):
                if ln.get("size") != 5.0:
                    continue
                t = (ln.get("txt") or "").strip()
                if t.isdigit():
                    ln["txt"] = str(n)
                    return

    el[pg] = keep + pages_blocks[0]
    _set_page_num(el[pg], pg_int)
    for i, page_elements in enumerate(pages_blocks[1:], start=1):
        new_pg = str(pg_int + i)
        new_keep = copy.deepcopy(keep)
        el[new_pg] = new_keep + page_elements
        _set_page_num(el[new_pg], pg_int + i)
    offset = len(pages_blocks) - 1                 # extra Position-Seiten
    for j, agb_seq in enumerate(agb_pages, start=1):
        new_pg = str(pg_int + offset + j)
        el[new_pg] = agb_seq
        _set_page_num(agb_seq, pg_int + offset + j)
    return _scale_fonts(el, FONT_SCALE)            # A1 — uniforme Skalierung


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
