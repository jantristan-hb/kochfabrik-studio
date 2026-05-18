# next-step.md — Plan (Phase D: Angebot → maßgeschneidertes Deck)

> Stand 2026-05-18. Engine (faithful PDF→editierbares PPTX) = **Sprint 1
> integriert** (`main`). Phase D = die Generierungs-Brücke.

## ⏯️ Resume — exakter Arbeitsstand (2026-05-18, Cold-Start ZUERST lesen)

### Repo / Doku-Querverweise (alles hier verlinkt)
- Projekt: `~/work/03 AKARA Solutions GmbH/kochfabrik/pptxgenerator_v2`,
  GitHub `jantristan-hb/pptxgenerator_v2` (privat).
- `main` = **Sprint 1 integriert** (Engine fertig). Phase-D-WIP auf Branch
  **`phase-d-01-composition-ingest`** (committed+gepusht, Commit `853edf4`):
  `git checkout phase-d-01-composition-ingest`.
- Engine-Doku: `README.md`. Herleitung/Holzwege/pdfminer-Fallen:
  `~/work/Projects/claude-pptx/pptxGenJS/PDF-zu-PPTX Rekonstruktion — Learnings.md`.
  Memory-Index: `project_pptxgenerator_v2_spike.md`. Sprint-1:
  `docs/sprint-1/`, `PROGRESS.md`, `CLAUDE.md`.

### Daten / Infra
- Korpus (199 Präsentations-PDFs): `~/Nextcloud/Kochfabrik Dokumente/
  AKARA_Präsentationen/` (`Angebot #*` = A4-Text-Angebote, NICHT Menü-Korpus
  — aber das sind die **BANKETTprofi-Input-Beispiele**).
- Muster-Angebote (Input-Hälfte): `~/Nextcloud/Kochfabrik Dokumente/
  AKARA_Muster_Angebote/` (z.B. Risk_Ident, 4D-v20-Producer, gelabelter
  key:value-Textlayer).
- Postgres clean-room: Container **`pptxgen-pg`** (pgvector-Image, Port
  5434, db `pptxgen`, pw `pptxgen`). Falls aus: `podman start pptxgen-pg`.
  Schema: `phase0/sql/schema.sql` (zwei Tabellen `menu_composition` +
  `info_slide` + `image(slide_kind,slide_id)` + `src_pdf`).
- Tools: python3+pdfminer.six+Pillow+psycopg2, node+pptxgenjs
  (`spike-pptxgenjs/node_modules`, sonst `npm i`), poppler
  (pdftohtml/pdfimages/pdftoppm/pdfinfo), libreoffice. Open Sans systemweit
  installiert; **Wingdings fehlt** (Icon-Glyphs offen).

### Skript-Inventar (alle in `phase0/`)
| Datei | Zweck | Run |
|---|---|---|
| `spike-pptxgenjs/convert.py` | PDF→editierbares PPTX (volle Pipeline) | `convert.py <pdf> [out] / --batch DIR` |
| `spike-pptxgenjs/extract.py` | pdfminer→elements.json (+onpage-Filter) | `extract.py <pdf> [out.json]` |
| `spike-pptxgenjs/reconstruct.js` | elements.json→pptx | `node reconstruct.js <el.json> <out>` |
| `spike-pptxgenjs/readback_overrides.py` | Hand-Korrektur→overrides.json | `<pptx> <deck>` |
| `scripts/_deckpipe.py` | volle Per-Deck-Pipeline, deck-namespaced (Logo!) | import |
| `scripts/build_menu_deck.py` | EINE pptx aller Menü-Kandidaten (Kuratierung) | `build_menu_deck.py [out]` |
| `scripts/ingest_compositions.py` | classify() + (TODO) DB-Ingest | `--n N / --all` |
| `scripts/compose_demo.py` | Composer-Kern (hand-gefüttert) | `<out> "<pdf>::page" …` |
| `scripts/phase_b_gate.py` | Engine-Mess-Gate | `--n 25` |

### Status der Bausteine
- **Engine**: fertig, integriert, generalisiert (Sprint 1 + Phase-B 25/25).
- **Off-Page-Filter** (`extract.py onpage()`): committed, **verifiziert
  faithful** (Bechtle byte-identisch, „MIT ZWEITER ZEILE IN GOLD" weg).
- **`_deckpipe.py`**: behebt Logo-Regression (Demos/Composer müssen die
  volle Pipeline inkl. `extract_logos`+`apply_official_logo` fahren —
  bloßes pdftohtml+extract → opakes Logo). `build_menu_deck.py` nutzt es.
- **Klassifikator `classify()`**: strukturell, title-unabhängig. Empirisch
  **bewusst zu lose** (False Positives: Crew/Intro, Foto-Galerie, Getränke
  — strukturell wie Speisen-Menüs). Das ist OK für den gewählten Weg ↓.
- **`ingest_compositions.py main()`**: Insert noch ALTes Single-Table —
  **TODO**: auf curation-basierte Labels umbauen (s.u.), nicht auf
  classify() allein.

### Gewählter Ground-Truth-Weg (Jans Entscheidung — wichtig!)
Statt Klassifikator-Perfektion: **EINE pptx mit allen Menü-Kandidaten aus
allen 199 PDFs** → Jan löscht Falsch-Slides von Hand → die übrig
bleibenden Slides = Menü-Ground-Truth. classify() ist nur ein Wegwerf-
Vorfilter (inklusiv, lieber zu viel). Gemini-Check optional/sekundär,
nicht mehr zwingend.

### 🟡 LÄUFT beim Session-Ende
`build_menu_deck.py /tmp/all_menus.pptx` als Hintergrund-Job über alle
199 PDFs. Output: `/tmp/all_menus.pptx`, Log: `/tmp/allmenus.log`.
Nach Fertigstellung: Jan kuratiert (Falsch-Slides löschen).

### ‼️ KRITISCHE LÜCKE — vor DB-Ingest schließen
`build_menu_deck.py` schreibt **kein Manifest** `slide_no → (deck,page)`.
Ohne das kann die kuratierte pptx NICHT auf Quell-(Deck,Seite)
zurückgemappt werden → menu_composition nicht befüllbar.
**Nächste Aktion #1:** build_menu_deck.py um ein `manifest.json`
(`{slide_no:{deck,page,src_pdf}}`) erweitern, Deck NEU bauen (oder Mapping
nachträglich aus Reihenfolge rekonstruieren, falls Jan vorher kuratiert
hat). Dann: kuratierte pptx → überlebende slide_no → manifest → diese
(deck,page) als `menu_composition`, Rest als `info_slide` ingesten.

### Nächste konkrete Aktionen (Resume-Reihenfolge)
1. **Manifest in build_menu_deck.py** (s.o.) — Blocker für alles Weitere.
2. all_menus.pptx fertig? → Jan kuratieren lassen → curate-Mapping.
3. `ingest_compositions.py main()` auf curation-Labels + menu/info +
   src_pdf umbauen → Stichprobe → ganzer Korpus.
4. Composer-Kern (compose_demo.py generalisieren): menu_composition nach
   Form matchen → Foto-SET + Text → reconstruct → editierbar.
5. Input-Adapter: Angebot/Prompt → `model.json`.
6. Phase-C-Reste (s.u.) bei Gelegenheit.

**Verify-Befehle:** je Skript-Header. DB: `PGPASSWORD=pptxgen psql -h
localhost -p 5434 -U postgres -d pptxgen`. Engine: `cd
phase0/spike-pptxgenjs && python3 convert.py <pdf> out.pptx`.

## Wo wir stehen
- **Output-Hälfte fertig:** Konverter erzeugt aus jedem KOCHfabrik-PDF
  editierbare Slide-Elemente (Engine, bewiesen auf 3 ungesehenen Decks).
- **Phase D begonnen:** Kompositions-Ingestion. Erkenntnis: Slides müssen
  nach Rolle getrennt werden (Menü vs. Info) — sonst zieht der Composer
  Cover statt Menüs.

## Akzeptanztest (Nordstern)
„Bau mir eine pptx aus zwei Grillmahlzeiten" →
Prompt → `model.json` → `menu_composition`-Match (grill) → reales Foto-SET
(Harmonie geschenkt) + Gericht-Text → reconstruct.js → editierbares Deck.

## BANKETTprofi-Angebot → Präsentation (Kern-Pipeline, explizit)

**Eingabe:** ein BANKETTprofi-Angebots-PDF (z.B.
`AKARA_Muster_Angebote/# 9_062_Risk_Ident GmbH_…pdf`) — A4, sauberer
key:value-Textlayer (`Veranstaltungsanlass:`, `Personenanzahl:`,
`Veranstaltungsdatum:`, Ort, Ansprechpartner) + Menüfolge/Positionen.
**Ausgabe:** ein editierbares KOCHfabrik-Präsentations-Deck.

**Schritte:**
1. **Angebot → `model.json`** (Input-Adapter, „Input egal").
   Header/Eckdaten via Regex/Geometrie (Felder sind explizit gelabelt →
   robust), Menü/Positionen via LLM. Ergebnis: kanonisches
   `model.json = {event:{kunde,anlass,datum,gäste,ort,ansprechpartner},
   menu:[{gang,gerichte[]}], drinks[], agenda[]}`.
2. **Deck-Gerüst aus `info_slide`** wählen: Cover, Über-uns, Team, Agenda,
   Kontakt — rollenbasiert, mit `event`-Daten befüllt (Kunde/Anlass/Datum).
3. **Menü-Slides aus `menu_composition`** komponieren: pro Gang/Menü-Block
   eine Komposition wählen, deren **Form** passt (n_photos ≈ #Gerichte,
   Gang-Typ). Das kuratierte Foto-SET 1:1 übernehmen (Harmonie geschenkt),
   Gericht-Texte aus `model.json.menu` einsetzen.
4. **Foto-Feinabgleich** (nur bei echtem Mismatch): einzelnes Foto via
   pgvector kohärenz-nah zum Set ersetzen — nicht das ganze Set neu suchen.
5. **Emit** über `reconstruct.js` → natives editierbares `.pptx`.
6. **Mensch** finalisiert Resttext (das „~80 %-fertig"-Niveau).

**Reihenfolge real:** zuerst Slide-Rollen sauber trennen (Klassifikator →
DB), DANN Composer (3.), DANN Input-Adapter (1.). Akzeptanztest oben ist
der End-to-End-Beweis.

## Plan (Reihenfolge, de-risk-getrieben)

1. **Slide-Rollen-Klassifikator** (Wegwerf-Algo, nur DB sinnvoll strukturieren)
   - strukturell, **title-unabhängig**: `|`-Zutatenzeilen + Foto-Grid +
     Font-Größen-Profil (`classify()` in `phase0/scripts/ingest_compositions.py`)
   - Proof VOR DB: `build_menu_deck.py N` → Deck aus N **reinen Menü-Slides**
     → Jan sieht visuell ob Erkennung stimmt ← **HIER GERADE**
   - dann gegen **Gemini** (Vision ground-truth, Stichprobe) validieren →
     Accuracy/Confusion, bevor Korpus eingekippt wird
2. **DB strukturieren** (zwei Tabellen, `phase0/sql/schema.sql`)
   - `menu_composition` (Composer-Quelle) + `info_slide` + `image(slide_kind)`
   - `src_pdf`-Provenienz (Composer kann Deck re-extrahieren)
   - erst Stichprobe, dann ganzer Korpus (199), wenn Klassifikator trägt
3. **Composer-Kern**
   - `menu_composition` matchen (Menü-Form/Tags) → Foto-SET 1:1 übernehmen
     → Gericht-Text befüllen → reconstruct.js → editierbar
   - Foto-Teil-Tausch nur bei echtem Mismatch → pgvector (kohärenz-nah)
4. **Gericht/Tag-Normalisierung**
   - `dishes` ist aktuell Rohtext → normalisierte Gerichte/Tags (damit
     „Grillmahlzeit"-Query greift). pgvector (`image.embedding`) erst wenn
     semantischer Match nachweislich nötig
5. **Input-Adapter** („Input egal")
   - Angebot-PDF / Prompt / Formular → **ein kanonisches `model.json`**
   - Generierung sieht NUR `model.json`, nie den Input

## Prinzipien (hart, aus dieser Session)
- **Faithful 1:1** — reproduzieren, nicht verschönern.
- **Wegwerf-Algos ok** — Klassifikator dient nur der DB-Struktur.
- **Spike + Evidenz vor Infra/Commitment** (Proof vor DB-Kippen).
- Spike-Kernlogik (Paint-Order, `lib/`, Logo-Transparenz) unangetastet.
- Clean-room (kein v1-Bezug). GitHub/lean (Skills GitLab-zentriert → adaptieren).

## Infra
- Postgres clean-room: Container `pptxgen-pg`, pgvector-Image, Port **5434**,
  db `pptxgen`. Schema: `phase0/sql/schema.sql`.

## Phase-C-Reste (aus Sprint 1, parallel/später)
- Off-Page-Master-Text-Filter (#1, ~2 Zeilen `extract.py`: bbox komplett
  außerhalb `[0,PW]×[0,PH]` droppen).
- Mess-Gate-Feinpass (coarse), Wingdings-Substitut, Kalibrier-Konstanten
  (`SIZE_K/LINE_K/Y_OFF_K`) breiter validieren.
