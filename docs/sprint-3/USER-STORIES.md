# Sprint 3 — USER-STORIES (EPIC-001 · Renderer + Pixel-Diff-Gate)

**Projekt:** pptxgenerator_v2 · **Epic:** EPIC-001 Angebotsgenerator
**Ziel:** Aus einem `Angebot`-Datenmodell ein **pixelgenaues** KOCHfabrik-
Angebots-PDF rendern (Positions-Repeater + Skalar-Fill + invariante
Blöcke) und gegen ≥3 echte Muster per Pixel-Diff absichern
(Epic-Akzeptanzkriterium 1).

Format: Context/Input/Task/Output/Verify/Blocked-by. Tests = projekt-
üblich plain-assert (`phase0/tests/test_*.py`), kein BDD/glab.
Engine-Regel (CLAUDE.md): `extract.py`/`reconstruct.js`/`lib/` UNVERÄNDERT.

Carry-Over → Sprint 3 (aus PROGRESS.md): Positions-Rendering ✓ (US-013/014),
Pixel-Diff-Gate ✓ (US-015/016), echte PDF-Pipeline ✓ (US-014, schließt
US-012-Proxy). GEN-1/3-Generalisierung → bewusst **Sprint 4** (FEATURE-ARCH Non-Goal).

---

### US-013: Positions-Repeater-Renderer

**Context:** Sprint 2 vermaß das `_meta.repeater`-Band, rendert die
Positionen aber nicht. Kern dieses Sprints: `Angebot.bloecke` als
Zeilen ins Band schreiben (pixelgenau im Referenz-Stil).

**Input:**
- `phase0/scripts/angebot_model.py` (Positionsblock/Position/is_header)
- `phase0/data/angebot_template.elements.json` (`_meta.repeater`-Band)
- `phase0/scripts/angebot_fill.py` (Skalar-Fill als Muster)

**Task:**
1. Aus dem Referenz-Template eine **Zeilen-Vorlage** ableiten (eine
   Positions-Element-Gruppe an der Band-y0, Spalten Bezeichnung|Menge|
   Einzelpreis|Gesamt aus den Bbox-x der getroffenen Elemente).
2. Pro `Position` die Zeilen-Vorlage klonen, y += row_h, Werte einsetzen;
   `is_header=True` → ohne Menge/Preis-Spalten; pro Block Titel +
   `zwischensumme`-Zeile.
3. In die gefüllte elements.json einsetzen (Band-Bereich ersetzen).

**Output:** `phase0/scripts/angebot_positions.py`

**Verify:**
```bash
cd phase0/scripts && python3 -c "import angebot_positions as P, angebot_fill as F, angebot_model as M; el=P.render(F.fill(M.example()), M.example()); n=sum(1 for pg,s in el.items() if pg!='_meta' and isinstance(s,list) for e in s if e.get('t')=='text' and any('Grillequipment' in (l.get('txt','')) for l in e.get('lines',[]))); assert n>=1, 'Positionszeile fehlt'"
```

**Blocked-by:** —

---

### US-015: PDF-Diff-Harness

**Context:** Pixel-Treue braucht ein messbares Gate (analog Phase-B des
Präsentationsgenerators, aber per-Seite/Region).

**Input:** `pdftoppm`, `python3` (PIL), zwei PDFs

**Task:**
1. `pdf_diff.py`: beide PDFs via `pdftoppm` → PNG je Seite (gleiche DPI),
   Seiten paaren, pixelweise Differenz + Score (Anteil abweichender
   Pixel ODER SSIM falls verfügbar) pro Seite + Gesamt.
2. CLI: `pdf_diff.py a.pdf b.pdf [--dpi N] [--max DELTA]` → Exit≠0 wenn
   Score > Toleranz; Report je Seite.

**Output:** `phase0/scripts/pdf_diff.py`

**Verify:**
```bash
cd phase0/scripts && python3 pdf_diff.py /tmp/ref_angebot.pdf /tmp/ref_angebot.pdf --max 0.001
# Identisches PDF gegen sich selbst → Score 0, Exit 0
```

**Blocked-by:** —

---

### US-017: Muster→Angebot-Parser

**Context:** Für das Pixel-Diff-Gate (Round-Trip) muss ein echtes
Muster-PDF in ein `Angebot` überführbar sein, um es dann zu rendern und
gegen das Original zu diffen.

**Input:** `phase0/scripts/kf_classify.py` (extract_event), `angebot_model.py`

**Task:**
1. `angebot_parse.py`: PDF → `Angebot`. Kopf/Veranstaltungsinformationen
   via `kf_classify.extract_event` + Label-Regex; Positionsblöcke aus
   den Positions-Zeilen (Bezeichnung + Menge/EP/Gesamt-Spalten,
   `is_header` für preislose Zeilen).
2. Footer = invariante Defaults (nicht parsen).

**Output:** `phase0/scripts/angebot_parse.py`

**Verify:**
```bash
cd phase0/scripts && python3 -c "import angebot_parse as A; a=A.parse('/home/jrudat/Nextcloud/Kochfabrik Dokumente/AKARA_Muster_Angebote/# 10_182_RAUMKARUSSELL GmbH_12_09_2026.pdf'); assert a.kunde and a.veranstaltung.anlass and a.bloecke"
```

**Blocked-by:** —

---

### US-014: End-to-End Renderer-CLI (Angebot → PDF)

**Context:** Ein Befehl Datenmodell → pixelgenaues PDF — das
Kernprodukt des Sprints. Schließt die US-012-Adaption (echte PDF-
Pipeline statt PPTX-Text-Proxy).

**Input:** US-013 (`angebot_positions`), `angebot_fill`, `angebot_model`,
`reconstruct.js`, `soffice` (pptx→pdf, wie in CLAUDE.md Render/Verify)

**Task:**
1. `angebot_render.py <angebot.json> -o out.pdf`: load → fill (Skalar)
   → render Positionen (US-013) → elements.json + logos in Workdir →
   `reconstruct.js` → pptx → `soffice --convert-to pdf` → out.pdf.
2. Fehlerpfade: fehlendes Template → `build_angebot_template.py`
   triggern; soffice fehlt → klare Meldung + Exit≠0.

**Output:** `phase0/scripts/angebot_render.py`

**Verify:**
```bash
cd phase0/scripts && python3 angebot_render.py ../fixtures/angebot_example.json -o /tmp/ang.pdf && python3 -c "import os;assert os.path.getsize('/tmp/ang.pdf')>10000"
```

**Blocked-by:** US-013

---

### US-016: Pixel-Diff-Gate gegen ≥3 echte Muster

**Context:** Epic-Akzeptanzkriterium 1: gerendertes PDF entspricht 1:1
echten KOCHfabrik-Angeboten. Round-Trip: echtes Muster → parse → render
→ diff vs Original < Toleranz.

**Input:** US-014 (`angebot_render`), US-015 (`pdf_diff`),
US-017 (`angebot_parse`), ≥3 GEN-2-Muster (RAUMKARUSSELL/HOWDENRE/INBOUND)

**Task:**
1. `angebot_gate.py`: für jedes der ≥3 Muster: `parse` → `render` →
   `pdf_diff` vs Original; aggregiere Scores; Exit≠0 wenn ein Muster >
   Toleranz. Toleranz datenbasiert kalibrieren (Startwert dokumentieren).
2. Report je Muster + Gesamt nach `docs/sprint-3/PIXEL-GATE.md`.

**Output:** `phase0/scripts/angebot_gate.py`, `docs/sprint-3/PIXEL-GATE.md`

**Verify:**
```bash
cd phase0/scripts && python3 angebot_gate.py
# ≥3 Muster, jedes Score < kalibrierter Toleranz → Exit 0; PIXEL-GATE.md geschrieben
```

**Blocked-by:** US-014, US-015, US-017

---

### US-019: Regression — Render-Konformität + Diff

**Context:** US-012 prüfte nur PPTX-Text-Proxy. Jetzt echtes PDF:
`kf_classify`-Konformität + Pixel-Gate regressionssicher.

**Input:** US-014, US-016, `kf_classify`

**Task:**
1. `test_angebot_render.py` (plain-assert): `angebot_render(example)` →
   PDF; `pdftotext` → `kf_classify` `is_kochfabrik` + `classify=='angebot'`
   + 6 Labels + Bankblock; `angebot_gate` Gesamtscore < Toleranz.

**Output:** `phase0/tests/test_angebot_render.py`

**Verify:**
```bash
cd phase0 && python3 tests/test_angebot_render.py   # ALLE TESTS GRÜN
```

**Blocked-by:** US-014, US-016

---

## Dependency-Graph / Waves

```
Wave 1 (parallel):  US-013   US-015   US-017
Wave 2:             US-014 (←013)
Wave 3:             US-016 (←014,015,017)
Wave 4:             US-019 (←014,016)
```
