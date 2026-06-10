# Sprint 2 — USER-STORIES (EPIC-001 · Template-Extraktion + Datenmodell)

**Projekt:** pptxgenerator_v2 · **Epic:** EPIC-001 Angebotsgenerator
**Ziel:** Aus einem echten KOCHfabrik-Muster-Angebot ein pixelgenaues,
parametrisierbares Template extrahieren + striktes Angebots-Datenmodell.
Renderer (Daten→PDF) + Pixel-Diff-Gate = Sprint 3.

Format: Context/Input/Task/Output/Verify/Blocked-by (LLM-Agent-optimiert).
Tests = projektüblich plain-assert (`phase0/tests/test_*.py`), kein BDD.

---

### US-007: Angebots-Korpus inventarisieren & Layout vermessen

**Context:** Vor der Template-Extraktion muss feststehen, welche echten
Angebots-PDFs existieren, wie viele Layout-Generationen es gibt (Estimate:
„Templates über Jahre variierend") und welches Muster als pixelgenaue
Referenz dient.

**Input:**
- `phase0/scripts/kf_classify.py` (classify → `angebot`)
- Korpus `~/Nextcloud/Kochfabrik Dokumente/{AKARA_Präsentationen,AKARA_Muster_Angebote}`
- `phase0/spike-pptxgenjs/extract.py` (Element-/Bbox-Extraktion)

**Task:**
1. Alle Korpus-PDFs via `kf_classify` klassifizieren, alle `angebot`-Typen sammeln.
2. Pro PDF die invarianten Blöcke vermessen: Letterhead-Box,
   Veranstaltungsinformationen-Label-Block, Positionsblöcke (Speisen/
   Getränke/Personal/Logistik), Bankblock/Footer (Bbox aus elements.json).
3. Layout-Generationen clustern (Bbox-/Label-Signatur); 1 Referenz-Muster
   wählen (jüngste, vollständigste Generation).

**Output:**
- `phase0/scripts/scan_angebote.py`
- `docs/sprint-2/LAYOUT-ANALYSE.md` (Generationen, Block-Geometrie, Referenz-Wahl + Begründung)

**Verify:**
```bash
cd phase0/scripts && python3 scan_angebote.py
# listet N angebot-PDFs + K Generationen; LAYOUT-ANALYSE.md nennt
# genau 1 Referenz-Muster + dessen Block-Bboxes
```

**Blocked-by:** —

---

### US-008: Angebots-Datenmodell definieren

**Context:** Striktes Schema als Single Source für Renderer (Sprint 3)
und Chat (Sprint 5). Muss alle Felder echter KOCHfabrik-Angebote abbilden.

**Input:**
- `kf_classify.extract_event` (bekannte Label-Felder)
- bekannter Angebots-Aufbau (Kopf, Veranstaltungsinformationen, Positionsblöcke, Bank)

**Task:**
1. `@dataclass`-Modell (stdlib): `Angebot` (Kopf: Kunde/Adresse/Angebots-Nr/
   Datum/Kundennr/Lieferdatum/Ansprechpartner), `Veranstaltung` (Anlass/
   Datum/Beginn/Personen/Ort/Konzept), `Positionsblock`/`Position`
   (Bezeichnung/Menge/Einzelpreis/Gesamt), `Pauschale`, invarianter Footer.
2. JSON dump/load (roundtrip-stabil).
3. Eine vollständige Beispiel-Instanz aus einem echten Muster (INBOUND) von Hand.

**Output:**
- `phase0/scripts/angebot_model.py`
- `phase0/data/angebot_example.json`

**Verify:**
```bash
cd phase0/scripts && python3 -c "from angebot_model import load,dump; a=load('../data/angebot_example.json'); assert a.kunde and a.veranstaltung.anlass; assert dump(load('../data/angebot_example.json'))==open('../data/angebot_example.json').read().strip()"
```

**Blocked-by:** —

---

### US-009: Template aus Referenz-Muster pixelgenau extrahieren

**Context:** Die bestehende Faithful-Extraktion rückwärts nutzen: das
Referenz-Angebot zu einem parametrisierbaren Template ableiten — analog
`cover_template`/`ausstattung_template`.

**Input:**
- Referenz-Muster aus US-007
- `phase0/spike-pptxgenjs/extract.py`, `phase0/scripts/build_cover_template.py` (Vorlage-Muster)

**Task:**
1. `extract` auf das Referenz-PDF → `elements.json`.
2. Build-Skript leitet daraus `angebot_template.elements.json` ab:
   Skalar-Tokens (`{KUNDE}`,`{ADRESSE}`,`{ANGEBOTS_NR}`,`{DATUM}`,
   `{ANLASS}`,`{PERSONEN}`,`{ORT}`,`{KONZEPT}`,`{LIEFERDATUM}`,
   `{ANSPRECHPARTNER}`) + Positionszeilen-Repeater-Marker; invarianter
   Letterhead/Bank/Footer verbatim.

**Output:**
- `phase0/scripts/build_angebot_template.py`
- `phase0/data/angebot_template.elements.json`

**Verify:**
```bash
cd phase0/scripts && python3 build_angebot_template.py
node ../spike-pptxgenjs/reconstruct.js ../data/angebot_template.elements.json /tmp/tmpl.pptx
# Element-Count == Referenz-Muster; visueller Spot-Check Layout deckungsgleich
```

**Blocked-by:** US-007

---

### US-011: Positionsblock-Struktur modellieren

**Context:** Speisen/Getränke/Personal/Logistik sind wiederholbare
Positionszeilen (Bezeichnung, Menge, Einzelpreis, Gesamt, Zwischensummen).
Template + Modell brauchen einen Zeilen-Repeater.

**Input:** US-007 (Block-Geometrie), US-008 (Modell-Basis)

**Task:**
1. Positionszeilen-Vorlage im Template als Repeater-Spec (eine Zeilen-
   Element-Gruppe + Wiederhol-/Offset-Regel).
2. `angebot_model.py` um `Positionsblock`/`Position` erweitern (Spalten +
   Zwischensumme); Preislogik nur strukturell (Felder), KEINE echte
   KOCHfabrik-Kalkulation (Scope-Grenze, siehe FEATURE-ARCH Non-Goals).

**Output:**
- Erweiterung `phase0/scripts/angebot_model.py`
- Repeater-Spec in `angebot_template.elements.json` + Doku in `LAYOUT-ANALYSE.md`

**Verify:**
```bash
cd phase0/scripts && python3 -c "from angebot_model import load; a=load('../data/angebot_example.json'); assert sum(len(b.positionen) for b in a.bloecke)>0"
```

**Blocked-by:** US-007, US-008

---

### US-010: Datenmodell → Template Felder-Mapping

**Context:** Statische Skalar-Felder (Kopf/Veranstaltungsinformationen)
aus dem Modell in die Template-Tokens einsetzen. Positionszeilen-Rendering
= Sprint 3.

**Input:** US-008 (Modell), US-009 (Template+Tokens), `compose_offer.swap_ph` (Muster)

**Task:**
1. `angebot_fill.py`: nimmt `Angebot` + `angebot_template.elements.json`,
   ersetzt alle Skalar-Tokens, lässt Positions-Repeater-Marker unberührt,
   invariante Blöcke verbatim.

**Output:** `phase0/scripts/angebot_fill.py`

**Verify:**
```bash
cd phase0/scripts && python3 -c "import json,angebot_fill; from angebot_model import load; el=angebot_fill.fill(load('../data/angebot_example.json')); s=json.dumps(el); import re; assert not re.search(r'\{[A-Z_]+\}',s.replace('{POSITIONEN}','')), 'offene Skalar-Tokens'"
```

**Blocked-by:** US-008, US-009

---

### US-012: kf_classify-Konformitäts-Check für generierte Templates

**Context:** Akzeptanzkriterium 1 des Epics (Vorstufe zum Pixel-Diff-Gate
in Sprint 3): ein aus Template+Modell befülltes PDF muss strukturell ein
echtes KOCHfabrik-Angebot sein.

**Input:** US-009, US-010, US-011, `kf_classify`

**Task:**
1. `verify_angebot.py`: `angebot_fill(example)` → reconstruct.js → PDF →
   `pdftotext` → `kf_classify`: `is_kochfabrik`==True, `classify`==`angebot`,
   alle Label-Felder + Bankblock vorhanden.
2. Plain-assert Regression-Test.

**Output:**
- `phase0/scripts/verify_angebot.py`
- `phase0/tests/test_angebot_template.py`

**Verify:**
```bash
cd phase0 && python3 tests/test_angebot_template.py   # ALLE TESTS GRÜN
```

**Blocked-by:** US-009, US-010, US-011

---

## Dependency-Graph / Waves

```
Wave 1 (parallel):  US-007  US-008
Wave 2 (parallel):  US-009 (←007)   US-011 (←007,008)
Wave 3:             US-010 (←008,009)
Wave 4:             US-012 (←009,010,011)
```
