# USER-STORIES.md — pptxgenerator_v2 · Sprint 1 (Engine Phase A)

> ## Projekt: pptxgenerator_v2
> Technische Stories für LLM-Code-Agents. Atomar, mit Verify.
> Basis: verifizierter Spike `phase0/spike-pptxgenjs/` (konvertiert Bechtle-Deck
> faithful + editierbar). Scope = Estimate Phase A. **Phase C (Korpus-Härtung)
> explizit NICHT in diesem Sprint** — wird aus US-006-Daten geschätzt.

## Phase 1: Parametrisierung

### US-001: Input/Output parametrisieren, Seitenmaß aus PDF

**Context:** Spike ist auf `assets/ref.pdf` + Seitenmaß 960×540 hardcoded.
Engine muss beliebiges PDF verarbeiten.

**Input:**
- Spike lauffähig (`extract.py`, `reconstruct.js`, `lib/*`)
- `pdfinfo`, `pdftohtml`, `pdfimages`, python3+pdfminer, node+pptxgenjs vorhanden

**Task:**
1. `extract.py`: PDF-Pfad + Output-JSON-Pfad als CLI-Args (argparse); `assets/ref.xml`-Hardcode → aus dem übergebenen PDF ableiten.
2. Seitenmaß (`PAGE_W/PAGE_H`) via `pdfinfo`/pdfminer `page.bbox` aus dem PDF lesen statt 960/540.
3. `reconstruct.js`: elements.json-Pfad + Output-PPTX-Pfad + Seitenmaß als Args/aus elements.json (Maß in elements.json mitschreiben).
4. Keine funktionale Änderung am Rekonstruktions-Verhalten.

**Output:**
- `phase0/spike-pptxgenjs/extract.py` — parametrisiert, Seitenmaß dynamisch
- `phase0/spike-pptxgenjs/reconstruct.js` — parametrisiert

**Verify:**
```bash
cd phase0/spike-pptxgenjs && python3 extract.py assets/ref.pdf /tmp/e.json && node reconstruct.js /tmp/e.json /tmp/out.pptx && python3 -c "from pptx import Presentation as P;print(len(P('/tmp/out.pptx').slides),'Slides')"
```

**Blocked-by:** —

---

## Phase 2: Orchestrierung

### US-002: convert.py — Asset-Pipeline als ein Lauf

**Context:** Die Schritte pdftohtml-xml / pdfimages / extract_logos /
apply_official_logo / extract / reconstruct werden heute manuell per bash
gefahren. Engine braucht einen deterministischen Orchestrator.

**Input:** US-001 erledigt (parametrisierte Tools)

**Task:**
1. Neu `convert.py`: nimmt `<input.pdf> <output.pptx>`, legt ein temporäres Work-Dir an.
2. Führt in Reihenfolge aus: pdftohtml -xml, pdfimages (-list/-png), `extract_logos.py`, `apply_official_logo.py`, `extract.py`, `reconstruct.js`.
3. Reicht `overrides.json` (falls für das Deck vorhanden, s. US-005) durch.
4. Räumt Work-Dir auf (außer `--keep`).

**Output:**
- `phase0/spike-pptxgenjs/convert.py` — Orchestrator

**Verify:**
```bash
cd phase0/spike-pptxgenjs && python3 convert.py assets/ref.pdf /tmp/bechtle.pptx && python3 -c "from pptx import Presentation as P;s=P('/tmp/bechtle.pptx').slides;print(len(s),'Slides, runs S4=',sum(len(p.runs) for sh in s[3].shapes if sh.has_text_frame for p in sh.text_frame.paragraphs))"
```

**Blocked-by:** US-001

---

### US-005: Override-Workflow produktiv (Readback pro Deck)

**Context:** Hand-Korrekturen (`lib/overrides.js`) sind aktuell für ein Deck
gekeyt. Produktiv: pro Deck eindeutiger Key + Readback aus editiertem PPTX.

**Input:** US-001 erledigt

**Task:**
1. Deck-Key = stabiler Hash/Basename des Input-PDF; `overrides.json` als `{ deckKey: { page: [...] } }`.
2. `lib/overrides.js`: Lookup nach deckKey (Fallback: kein Override).
3. Neu `readback_overrides.py`: nimmt editiertes `.pptx` + Deck-Key, liest geänderte Shape-Geometrien aus, schreibt/merged in `overrides.json`.
4. `convert.py` reicht deckKey an `reconstruct.js` durch.

**Output:**
- `phase0/spike-pptxgenjs/lib/overrides.js` — deckKey-fähig
- `phase0/spike-pptxgenjs/readback_overrides.py` — Readback

**Verify:**
```bash
cd phase0/spike-pptxgenjs && python3 readback_overrides.py reconstructed.pptx bechtle && python3 -c "import json;d=json.load(open('overrides.json'));print('bechtle' in d or list(d)[:1])"
```

**Blocked-by:** US-001

---

## Phase 3: CLI, Robustheit

### US-003: CLI + Batch über Ordner

**Context:** Engine muss einzeln und über einen Ordner laufen können.

**Input:** US-002 erledigt

**Task:**
1. `convert.py` argparse: `convert.py <in.pdf> [out.pptx]`, `--batch <dir> [--out <dir>]`, `--keep`.
2. Batch: alle `*.pdf` im Ordner → `<name>.pptx`, fortschritt + Summary (ok/fehler je Deck).
3. Exit-Code ≠ 0 bei ≥1 Fehler im Batch.

**Output:**
- `phase0/spike-pptxgenjs/convert.py` — CLI + Batch

**Verify:**
```bash
cd phase0/spike-pptxgenjs && mkdir -p /tmp/in && cp assets/ref.pdf /tmp/in/ && python3 convert.py --batch /tmp/in --out /tmp/outb && ls /tmp/outb/*.pptx
```

**Blocked-by:** US-002

---

### US-004: Fehlerbehandlung + Fallbacks

**Context:** Über 199 heterogene Decks darf ein kaputtes Deck/Element den
Lauf nicht killen.

**Input:** US-002 erledigt

**Task:**
1. `reconstruct.js`: try/catch pro Element + pro Slide; fehlendes Bild-File → Platzhalter-Rect, weiter.
2. `convert.py`: kaputtes/leeres PDF → skip + Eintrag in `convert-report.json` (deck, stufe, fehler), nicht abbrechen.
3. Batch-Summary nutzt `convert-report.json`.

**Output:**
- `phase0/spike-pptxgenjs/reconstruct.js` — defensive Emission
- `phase0/spike-pptxgenjs/convert.py` — Skip + Report

**Verify:**
```bash
cd phase0/spike-pptxgenjs && printf '%%PDF-1.4 broken' > /tmp/bad.pdf && python3 convert.py /tmp/bad.pdf /tmp/bad.pptx; test -f convert-report.json && python3 -c "import json;print(json.load(open('convert-report.json')))"
```

**Blocked-by:** US-002

---

## Phase 4: Mess-Gate (Sprint-Abschluss)

### US-006: Phase-B Mess-Gate — Korpus-Stichprobe + Fehlerrate

**Context:** Kalibrier-Konstanten (SIZE_K/LINE_K/Y_OFF_K) und Regeln
(band/frame/backing) sind nur an 1 Deck validiert. Vor jeder Korpus-Zusage:
Fehlerrate über eine stratifizierte Stichprobe messen. **Liefert die Daten zur
Schätzung von Phase C — KEINE Härtung in diesem Sprint.**

**Input:** US-003, US-004 erledigt

**Task:**
1. Neu `phase0/scripts/phase_b_gate.py`: ~25 stratifizierte Decks (über Dateinamen-Typen, kein „Angebot #") aus dem KOCHfabrik-Korpus.
2. Pro Deck `convert.py` laufen lassen + Original- vs. Recon-Render (pdftoppm) erzeugen.
3. Fehlerklassen je Slide grob klassifizieren (Vision-Light oder Heuristik): Text-Position, fehlender Frame/Banner, Logo, Bild-Platzierung, Overflow.
4. `phase0/REPORT-phase-b.md`: Fehlerrate je Regelklasse + Decks die clean durchlaufen + Decision-Empfehlung für Phase C.

**Output:**
- `phase0/scripts/phase_b_gate.py` — Mess-Skript
- `phase0/REPORT-phase-b.md` — Aggregat + Decision-Empfehlung

**Verify:**
```bash
cd phase0/spike-pptxgenjs && python3 ../scripts/phase_b_gate.py --n 25 && test -f ../REPORT-phase-b.md && grep -qi "Fehlerrate\|Decision" ../REPORT-phase-b.md && echo GATE-OK
```

**Blocked-by:** US-003, US-004

---

## Dependency-Graph / Waves

```
Wave 1: US-001
Wave 2: US-002, US-005      (blocked-by US-001)
Wave 3: US-003, US-004      (blocked-by US-002)
Wave 4: US-006              (blocked-by US-003, US-004)
```
