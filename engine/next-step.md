# next-step.md — Plan (Phase D: Angebot → maßgeschneidertes Deck)

> Stand 2026-05-18. Engine (faithful PDF→editierbares PPTX) = **Sprint 1
> integriert** (`main`). Phase D = die Generierungs-Brücke.

## ✅ STAND 2026-05-19 — DATENBANK FERTIG + END-TO-END LÄUFT

**Die Datenbank ist fertig und produktiv nutzbar bewiesen.**

- **`menu_composition`**: 1010 kuratierte Food-Slides, alle embedded
  (`vector(768)`, pgvector hnsw), 296 Module. Ground-Truth = Jans
  Hand-Kuration.
- **`static_slide`**: 16 Zeilen / 6 Kategorien, skel_pos-geordnet,
  kohärent — COVER(T/0.0) · CREW(B/0.10) · PERSONAL(B/0.76) ·
  AUSSTATTUNG(T/0.78) · WERTSCHÄTZUNG(B/0.89) · KONTAKT(B/1.00),
  je golden + freigegebene Alternativen. Gegroundet auf Jans Kuration
  (`category_samples.pptx`) — keine Korpus-Artefakte.
- **2 Templates** (tier T, `phase0/data/`): `cover_template` +
  `ausstattung_template` (Text-Platzhalter + leerer Bild-Slot für
  späteres Bildgenerator-Projekt).
- **Element-Cache** `phase0/data/cache/` (199 Decks) warm.

**`assemble.py` = hocheffizienter End-to-End-Assembler — verifiziert:**
Risk.Ident-Angebot → **9 Slides in 0,7 s** im exakten kanonischen
Skelett (Cover→Crew→Food→Personal→Ausstattung→Wertschätzung→Kontakt).
1 Embed-Batch, DB-ANN, nur Cache-Reads, 1 reconstruct. Doku:
**`docs/ASSEMBLER-WORKFLOW.md`** (prominent, vollständig).
Beispiel-Output: `phase0/data/assembled_risk_ident.pptx`.

**Doku prominent in `docs/`:** ASSEMBLER-WORKFLOW · PRESENTATION-
BLUEPRINT · REPORT-structure · INFO-TOP20-METHOD. Golden-Datasets je
Kategorie zum Versand: `docs/samples/Golden_*.pptx` + `Food_Sample.pptx`.

**Nächste Ausbaustufen (optional, kein Blocker):** Food-Modul-
Sortierung im Block · Ausstattung-Text feiner aus „Event Ausstattung"
· Bildgenerator-Projekt (Hero/Ausstattung-Bilder) · Frontend Design 2
anbinden · phase0/data Snapshots aufräumen (5,5 G).

---

> _(Historie unten — Stand vor 2026-05-19)_

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
| `scripts/curate.py` | regelbasiert Slides löschen (Headline-Block/`--drop`), notiz-erhaltend+gehärtet | `curate.py <pptx> --block "..." [--dry]` |
| `scripts/slide_text.py` | pro Slide deck/page/headline/body→JSON | `slide_text.py <pptx> [out.json]` |
| `scripts/embed_cluster.py` | Gemini-Embed (headline-only,gecacht)+Cluster→tags.json | `embed_cluster.py embed\|cluster <slides.json> [--th]` |
| `scripts/resort_pptx.py` | pptx nach Cluster umsortieren (gehärteter Save) | `resort_pptx.py <pptx>` |
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

### ✅ Manifest-Lücke GESCHLOSSEN (Commit `7e5107b`)
`build_menu_deck.py` schreibt jetzt `<out>.manifest.json`
(`{slide_no:{deck,page,src_pdf}}`) UND jede Slide trägt eine unsichtbare
Notiz `"<deck-slug>::<page>"` (via additivem `reconstruct.js`-Hook
`meta.notes`). Notizen überstehen Löschen/Umsortieren in PowerPoint.
Slides sind **ähnlichkeits-sortiert** (Struktur-Signatur: #Fotos +
Foto-Grid + Textblöcke) → gleiche Archetypen am Stück → Block-Löschen.
Smoke (5 Decks) verifiziert: Manifest+Notizen+Sort ok.

### ✅ Vollauf fertig + kuratiert + cluster-sortiert (2026-05-18 spät)
`build_menu_deck.py` Vollauf: **1546 Kandidaten / 171 Decks / 0 Fehler**.
Dann `curate.py` (Headline-Blockliste, notiz-erhaltend, gehärtet —
droppt Slide-Part-Rel + kompaktiert Alt-Waisen):
- Runde 1: `WERTSCHÄTZUNG IST DER SCHLÜSSEL`+`PERSONAL` → 1546→1238
- Runde 2: `CREW`+`IM NORDEN`+`IN THE NORTH`+`STATTUNG` → 1238→**1050**
(Logistik/Personal/Crew/Equipment raus — Jans Keep-Scope: **Essen +
Getränke + Mahlzeiten behalten**, nur Logistik/Deko/Personal löschen.
Getränke-Slides bleiben! SOFTES&HOPFIGES NICHT gelöscht.)
Backup: `/tmp/all_menus_1050_<ts>.pptx` (+manifest).

**Tagging = Embedding-Cluster (Jans Wahl, nicht classify/Fold-Map):**
`slide_text.py`→`embed_cluster.py`→`resort_pptx.py`. Gemini
`gemini-embedding-001`, **headline-only** (Body fragmentiert gleichen
Modultyp!), taskType SEMANTIC_SIMILARITY, dim 768, gecacht in
`/tmp/all_menus.slides.json.emb.npz`. mean-zentrieren+L2 →
AgglomerativeClustering(cosine, average), **th=0.12**: wiederkehrende
Module je 1 Cluster (SWEET DREAMS 115, SOFTES&HOPFIGES 98, WINE TIME 94,
SO EMPFANGEN 71, BIG BBQ 47, LIVE COOKING 41, …), 323 Cluster, 226
Singletons (= individuelle Event-Menüs). `/tmp/all_menus.tags.json`
(no,deck,page,headline,cluster). pptx in-place nach Cluster umsortiert
(247 MB), 1050 Notizen erhalten, in Impress offen.

### Curation→DB Rückmapping (Rezept, unverändert gültig)
Nach finaler Kuratierung (Cluster-weise Falsch-Slides gelöscht):
```python
from pptx import Presentation
keep = {s.notes_slide.notes_text_frame.text.strip()
        for s in Presentation("all_menus.pptx").slides
        if s.has_notes_slide}            # {"deck::page", ...}
```
→ diese (deck,page) = `menu_composition` MIT Cluster als `module_type`
(aus tags.json joinen); Rest des Korpus = `info_slide`.

### Nächste konkrete Aktionen (Resume-Reihenfolge)
1. Jan kuratiert cluster-sortiertes Deck (ganze Cluster keep/drop, da
   semantisch gruppiert). curate.py `--block`/`--drop` weiter nutzbar;
   ggf. `--drop-cluster <id>` ergänzen (tags.json-aware).
2. **Postgres/pgvector laden** (Container `pptxgen-pg` Up:5434): Tabelle
   `slide_embed(slide_no,deck,page,headline,cluster,embedding vector(768))`
   aus npz+tags.json. = die DB die Jan wollte; pgvector für späteres
   Composition-Matching/teilweisen Foto-Swap.
3. `ingest_compositions.py main()` umbauen: Labels aus überlebenden
   Slide-Notizen (Rezept oben) + Cluster als module_type; Tabellen
   `menu_composition`/`info_slide` + `src_pdf`.
4. Composer-Kern (compose_demo.py generalisieren, auf `_deckpipe`):
   menu_composition nach Cluster/Form matchen → Foto-SET → reconstruct.
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
