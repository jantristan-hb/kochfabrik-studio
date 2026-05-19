# Sprint 4 — USER-STORIES (EPIC-001 · Fiktiv-Korpus + Generalisierung)

**Projekt:** pptxgenerator_v2 · **Epic:** EPIC-001 Angebotsgenerator
**Ziel:** Das ursprüngliche Kern-Deliverable — **20–30 fiktive
KOCHfabrik-Angebots-PDFs im Original-Stil** — plus Template-
Generalisierung über Layout-Generationen und die zwei RETRO-Carry-Overs.

Baut auf `main` @ `79b1b7e` (Sprint 2+3 gemergt: angebot_model/
_fill/_positions/_render/_gate, build_angebot_template, kf_classify).
Format: Context/Input/Task/Output/Verify/Blocked-by. Tests = plain-
assert. Engine (`extract.py`/`reconstruct.js`/`lib/`) UNVERÄNDERT.
Bulk-LLM: **Anthropic Batch API** (CLAUDE.md-Pflicht), Key aus
`~/work/.env` (`ANTHROPIC_API_KEY`).

---

### US-020: Fiktiv-Event-Generator (LLM, Batch)

**Context:** Kern des Sprints — realistische fiktive KOCHfabrik-Events
als `Angebot`-JSONs (Anlass/Datum/Personen/Ort/Cateringkonzept +
plausible Positionsblöcke/Preise im KF-Duktus).

**Input:**
- `phase0/scripts/angebot_model.py` (Zielschema)
- `~/work/.env` → `ANTHROPIC_API_KEY`; Modell `claude-opus-4-6` o. `sonnet-4-6`

**Task:**
1. `gen_fiktiv.py`: N Event-Specs (variierende Anlässe/Größen/Konzepte)
   → **Anthropic Batch API** (`messages.batches.create`, NICHT
   sequentiell) → je ein valides `Angebot`-JSON (Schema-geprüft via
   `angebot_model.load`).
2. KF-typische Positionen/Preise (Streetfood/Flying Dinner/BBQ/Buffet,
   Sub-Header, Logistik) — plausibel, keine echte Preisliste (Non-Goal).

**Output:** `phase0/scripts/gen_fiktiv.py`, `phase0/data/fiktiv/*.json` (gitignored)

**Verify:**
```bash
cd phase0/scripts && python3 gen_fiktiv.py --n 3 --out ../data/fiktiv && python3 -c "import glob,sys;sys.path.insert(0,'.');from angebot_model import load; fs=glob.glob('../data/fiktiv/*.json'); assert len(fs)>=3; [load(f) for f in fs]"
```

**Blocked-by:** —

---

### US-022: GEN-1/3-Template-Generalisierung

**Context:** Sprint 2/3 = GEN-2-Template-only. Korpus-Realismus +
Carry-Over: Token-Detection muss auch GEN 1 (ohne Beginn) und GEN 3
(spärlich) abdecken; ≥2 Referenz-Templates.

**Input:** `build_angebot_template.py`, `angebot_fill.py`,
`scan_angebote.py` (GEN-Cluster), Korpus GEN-1/GEN-3-Muster

**Task:**
1. Je 1 Referenz-Muster pro Generation wählen (GEN-1 + GEN-3, via
   `scan_angebote`), Template extrahieren → `angebot_template_gen1/
   gen3.elements.json`.
2. `build_angebot_template`/`angebot_fill` generationen-parametrisiert
   (Token-Map robust, fehlende Felder tolerant).

**Output:** `phase0/scripts/build_angebot_template.py` (erweitert),
`phase0/data/angebot_template_gen{1,3}.elements.json`

**Verify:**
```bash
cd phase0/scripts && python3 build_angebot_template.py --gen 1 && python3 build_angebot_template.py --gen 3 && python3 -c "import os;[os.path.getsize(f) for f in ['../data/angebot_template_gen1.elements.json','../data/angebot_template_gen3.elements.json']]"
```

**Blocked-by:** —

---

### US-023: _kunde + Sub-Header-Robustheit (RETRO-Carry-Over)

**Context:** Zwei dokumentierte Schulden aus Sprint 3: `_kunde`
verfehlt Namen ohne Rechtsform-Token (z.B. HOWDENRE); Sub-Header nur
fett statt unterstrichen.

**Input:** `angebot_parse.py` (`_kunde`), `angebot_positions.py` (Sub-Header)

**Task:**
1. `_kunde`: Fallback auf Empfänger-Block-Erkennung (Zeile nach
   Letterhead, vor Adresse) wenn kein Rechtsform-Token.
2. Sub-Header: Unterstreichung via Element-Modell prüfen — falls
   `lines[].underline`/Deko unterstützt: setzen; sonst dokumentieren
   warum nicht (kein Workaround-Hack).

**Output:** `phase0/scripts/angebot_parse.py`, `phase0/scripts/angebot_positions.py`

**Verify:**
```bash
cd phase0/scripts && python3 -c "import angebot_parse as A; a=A.parse('/home/jrudat/Nextcloud/Kochfabrik Dokumente/AKARA_Muster_Angebote/# 9_745_HOWDENRE_11_06_2025.pdf'); assert a.kunde, 'HOWDENRE kunde leer'"
```

**Blocked-by:** —

---

### US-021: Korpus-Batch-Renderer

**Context:** Die generierten `Angebot`-JSONs → 20–30 Original-Stil-PDFs
(das Kern-Deliverable des ursprünglichen Riesenfeature-Wunsches).

**Input:** US-020 (`gen_fiktiv` JSONs), `angebot_render.py`,
optional US-022 (GEN-Varianz)

**Task:**
1. `build_korpus.py`: alle `data/fiktiv/*.json` → `angebot_render` →
   `data/fiktiv_korpus/*.pdf`; Generation pro Angebot variieren falls
   US-022 verfügbar; Fehler pro Datei isoliert + Report.

**Output:** `phase0/scripts/build_korpus.py`, `phase0/data/fiktiv_korpus/*.pdf` (gitignored)

**Verify:**
```bash
cd phase0/scripts && python3 gen_fiktiv.py --n 20 --out ../data/fiktiv && python3 build_korpus.py && python3 -c "import glob;assert 20<=len(glob.glob('../data/fiktiv_korpus/*.pdf'))<=30"
```

**Blocked-by:** US-020

---

### US-024: Korpus-Konformitäts-Gate

**Context:** Jedes generierte PDF muss strukturell ein echtes
KOCHfabrik-Angebot sein (sonst taugt der Korpus nicht als Referenz).

**Input:** US-021 (Korpus), `kf_classify`

**Task:**
1. `korpus_gate.py`: jedes `fiktiv_korpus/*.pdf` → `pdftotext` →
   `kf_classify` `is_kochfabrik` + `classify=='angebot'` + Label-/
   Bankblock-Check; Aggregat + `docs/sprint-4/KORPUS-GATE.md`.

**Output:** `phase0/scripts/korpus_gate.py`, `docs/sprint-4/KORPUS-GATE.md`

**Verify:**
```bash
cd phase0/scripts && python3 korpus_gate.py
# alle PDFs is_kochfabrik + 'angebot' → Exit 0; KORPUS-GATE.md geschrieben
```

**Blocked-by:** US-021

---

### US-025: Regression — Korpus + GEN-1/3

**Context:** Korpus-Generierung + Generalisierung regressionssicher.

**Input:** US-021, US-022, US-024

**Task:**
1. `test_korpus.py` (plain-assert): Mini-Batch (n=3) gen→render→gate
   alle 'angebot'; GEN-1 + GEN-3 Template-Build + Fill ohne Fehler.

**Output:** `phase0/tests/test_korpus.py`

**Verify:**
```bash
cd phase0 && python3 tests/test_korpus.py   # ALLE TESTS GRÜN
```

**Blocked-by:** US-021, US-022, US-024

---

## Dependency-Graph / Waves

```
Wave 1 (parallel):  US-020   US-022   US-023
Wave 2:             US-021 (←020)
Wave 3:             US-024 (←021)
Wave 4:             US-025 (←021,022,024)
```
