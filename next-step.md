# next-step.md — Plan (Phase D: Angebot → maßgeschneidertes Deck)

> Stand 2026-05-18. Engine (faithful PDF→editierbares PPTX) = **Sprint 1
> integriert** (`main`). Phase D = die Generierungs-Brücke.

## ⏯️ Resume — exakter Arbeitsstand (2026-05-18, Cold-Start lesen!)

**Branch `phase-d-01-composition-ingest`** (off `main`), teils gepusht.
**Uncommittet/zu verifizieren** (Stand Session-Ende):
- `phase0/sql/schema.sql` — neu: **zwei Tabellen** `menu_composition` +
  `info_slide` + `image(slide_kind,slide_id)` + `src_pdf`. (Postgres
  `pptxgen-pg`, Port 5434, db `pptxgen` läuft.)
- `phase0/scripts/ingest_compositions.py` — Klassifikator auf **strukturell**
  umgestellt (`classify()`), aber main()-Insert noch auf ALTE eine-Tabelle
  → **muss auf menu/info+src_pdf umgebaut werden** bevor Reingest.
- `phase0/scripts/build_menu_deck.py` — Proof „N reine Menüs".
- `phase0/scripts/compose_demo.py` — Composer-Kern (hand-gefüttert).
- `phase0/scripts/_deckpipe.py` — **NEU**: volle Per-Deck-Pipeline inkl.
  Logo-Transparenz + Gold-Logo, deck-genamespaced. **build_menu_deck.py &
  compose_demo.py müssen darauf umgestellt werden** (sie skippen aktuell
  die Logo-Schritte → Logo-Regression, von Jan moniert).
- `phase0/spike-pptxgenjs/extract.py` — **Off-Page-Filter eingebaut**
  (`onpage()` droppt Elemente komplett außerhalb der Mediabox → killt
  „MIT ZWEITER ZEILE IN GOLD"). **Verify offen:** Bechtle weiter 8 Slides
  faithful + Stray-Text weg.

**Empirisches Ergebnis (wichtig):** Struktur-Klassifikator getestet via
`build_menu_deck.py 30` → **zu lose**: echte Speisen-Menüs erkannt (gut),
aber False Positives: Crew-/Intro-Slide, Foto-Galerie, Getränke-Slides
(strukturell identisch zu Speisen-Menüs). → **Gemini-Ground-Truth-Check
ist zwingend** (nicht optional) zum Kalibrieren/Verschärfen, BEVOR Korpus
in die DB. Getränke evtl. eigene Rolle.

**Nächste konkrete Aktion (Resume hier):**
1. extract.py-Off-Page-Fix verifizieren (`convert.py assets/ref.pdf` →
   8 Slides, kein „ZWEITER ZEILE"), committen+pushen.
2. build_menu_deck.py + compose_demo.py auf `_deckpipe.process_deck`
   umstellen (Logo-Transparenz zurück), gemergte `logos.json` schreiben.
3. Gemini-Validierungs-Skript: ~25 Decks Slide-Render → „Speisen-Menü?
   Rolle?" → Accuracy/Confusion vs. `classify()` → `classify()` schärfen.
4. ingest_compositions.py main() auf menu/info-Tabellen + src_pdf umbauen,
   Stichprobe → erst dann Korpus.

**Verify-Befehle:** je Skript Header. DB: `PGPASSWORD=pptxgen psql -h
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
