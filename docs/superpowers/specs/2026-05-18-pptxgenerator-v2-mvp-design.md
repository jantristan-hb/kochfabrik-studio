# pptxgenerator_v2 — MVP-Design

**Datum:** 2026-05-18
**Status:** Spec zur Review
**Ersetzt:** `2026-05-18-phase0-menu-composition-divergence-design.md`
(Vision-Batch-Divergenzmessung — durch die Recon billiger beantwortet, verworfen)

---

## 1. Evidenzbasis (Recon, 29-Deck-Stichprobe, committed)

| Befund | Wert | Quelle |
|---|---|---|
| Decks individuell gebaut? | **Nein** — template-/bibliotheksgetrieben | recon v1/v2/v3 |
| Foto-Reuse **instanz-gewichtet** (furniture-bereinigt, sha256) | 72 % | recon v3 / 50 Decks — *Furniture/Ambiente-dominiert, irreführend* |
| Foto-Reuse **unique-gewichtet** | nur **31 % der distinkten Fotos in ≥2 Decks** (362 unique → **69 % bespoke**) | recon v3 / 50 Decks |
| Menü-/Gericht-Kompositionen | **bespoke pro Kundenmenü** (Daten unique-gewichtet **+** manuelle Slide-Durchsicht) | recon + Augenschein |
| Universelle Furniture-Hashes (Logo/Badge-Set) | 6, in ~allen Decks | recon v3 |
| Fixe Rollen-Slides „über uns"/„team" | 92 % / 96 % byte-identisch | recon v2 |
| Seitenzahl je Deck | 6–31, ~63 % bei 9–13, Gipfel 11 (nicht fix) | pdfinfo/199 |
| Stabiles Skelett | S1 = 6 Furniture (+ ggf. 1 Hero); Menü-Slides 1–6 Fotos; Schluss furniture-only | recon v3 Profil |

**Konsequenz:** Gericht-Fotos sind überwiegend bespoke → der Generator kann sie
**nicht** aus einem Deck erben. Foto-*Auswahl pro Gericht aus dem kuratierten
384-Pool* ist echte MVP-Arbeit (Selektion, nicht Generierung). Furniture/
Branding dagegen statisches Bibliotheks-Asset.

## 2. Architektur-Entscheidung

Differenziert nach Slide-Ebene (Recon + manuelle Slide-Durchsicht):

- **Fix-Rollen** (Cover-Furniture, Über uns, Team, Kontakt): wiederholen sich
  quasi-ganz (92–96 % byte-identisch) → wholesale Template-Reuse.
- **Menü-Slides**: das **Layout/Template** wiederkehrend (wenige
  Foto-Anzahl-Varianten), aber die **Foto-Komposition ist bespoke pro
  Kundenmenü** (manuell verifiziert). → Template wird **befüllt, nicht
  fertig geklont**.

MVP = **editierbare Template-Bibliothek (pptxgenjs-rekonstruiert) +
Compose-Fill**: leeres Template klonen, mit N Gericht-Fotos aus dem Pool +
Texten befüllen. Ergebnis: natives, in PowerPoint editierbares `.pptx`.
Das frühere „Slides ganz konkatenieren" war ein Overclaim (Instanz-gewichtete
Reuse-Metrik, Furniture/Ambiente-dominiert — sagt nichts über
Menü-Kompositionen).

**HARTE BEDINGUNG:** Das finale `.pptx` MUSS in PowerPoint editierbar sein
(echte Text/Shapes). Damit: naives „PDF→Flachbild-PPTX" tot; primär =
pptxgenjs-Rekonstruktion (§6b); (C)-Hybrid nur **letzter Ausweg** für Slides,
die pptxgenjs physisch nicht erreicht — Anzahl zu minimieren, nicht Default.

**Explizit OUT (YAGNI, evidenzgestützt):** Bildgenerierung; bbox-/parametrischer
Layout-Solver; Vision-Batch-Korpusanalyse; RAG/Embedding-Bildpipeline (erst
naiver Pool-Match, später messen/iterieren).

## 3. Eingaben → ein Datenmodell

Beide Eingabewege münden in **ein** Zod-validiertes, PII-gefiltertes Modell:

```
Event   { kunde, anlass, datum, gäste?, location? }
Menu    { gänge: [ { name, gerichte: [ { name, beschreibung? } ] } ] }
Drinks  [ ... ]
Flags   { team?, location?, referenzen?, … }   // optionale Slides an/aus
```

- **PDF-Adapter:** Angebots-/BANKETTprofi-PDF → Geometrie + LLM-Extraktion → Modell.
- **Briefing-Adapter:** Freitext → LLM → Modell.

## 4. Komponenten (isoliert, je eine Aufgabe)

| Modul | Aufgabe | Abhängigkeit |
|---|---|---|
| `model/` | Zod-Schema = Single Source of Truth | — |
| `input/pdf` | PDF → model | model |
| `input/briefing` | Freitext → model | model |
| `library/` | editierbare Master-Slides je Rolle + Manifest (Rolle → Datei + Platzhalter-Map) | — |
| `images/` | Pool-Index (kuratierte 384) + Selektor hinter Interface (naiver Name/Tag-Match, austauschbar) | — |
| `compose/` | Sequenz planen (Fix-Slides + N Menü-Slides; Menü-Variante nach #Gerichten/#Fotos), Slide + Foto wählen | model, library, images |
| `assemble/` | OOXML-Klon + Platzhalter-Befüllung → editierbares .pptx (Spike-Technik) | library |
| `cli/` | dünner Orchestrator | alle |

## 5. Datenfluss

```
PDF | Freitext
  → input-Adapter → model (Zod, PII-gefiltert)
  → compose: Slide-Sequenz [Cover, ÜberUns, …, MenüxN, Getränke, Kontakt]
             je Menü-Slide Variante nach #Gerichten; Foto je Gericht aus Pool
  → assemble: pro Slide Master klonen, Text-/Foto-Platzhalter füllen, konkatenieren
  → natives editierbares .pptx
```

## 6. Erste Aufgabe: Template-Bibliothek per pptxgenjs-Rekonstruktion

**6a. Slide-Index (Katalog).**
Aus dem Korpus jede Slide indizieren → `{rolle, archetyp, #fotos,
wiederkehrend?, text-skelett, quelle}`. PDF reicht, billig — die Recon-Skripte
sind ~80 % davon. Liefert die **endliche distinkte Template-Menge** (~10–20,
nicht 2000 — Recon: Fix-Rollen 92–96 % identisch, Menü-Varianten nach #Fotos)
und Häufigkeiten.

**6b. Distinkte Templates per pptxgenjs nachbauen (Refine-Loop).**
Nicht „alle Slides" — nur die ~15 distinkten Templates aus 6a. Je Template:

```
Assets extrahieren (Fotos, Text, Font) + Original-Slide rendern
→ Claude generiert pptxgenjs-Code (pptxGenJS-Handbuch = API-Referenz)
→ LibreOffice rendert → visueller Diff gegen Original
→ Refine-Loop bis Toleranz  (claude-pptx-Spike kann render+compare bereits)
→ editierbares Master-Template
```

**6c. Fidelity-Ceiling + Fallback (Pushback, ehrlich).**
pptxgenjs = Ansatz A: editierbar ja, **nicht gratis pixelgenau**. Harte Wände
(MIT-Typdef verifiziert): kein Gradient, nur kreisförmiges Image-Rounding,
Font-Metrik-Drift, z-Order/Full-Bleed. „genau" = *nach Refine nah genug*,
nicht bytegleich. Design-schwere Slides (Cover/Vollbild/Goldrahmen-Verlauf),
die pptxgenjs nicht erreicht → **(C)-Hybrid-Fallback**: Original-PDF-Render
als vollflächiger Hintergrund + editierbare Textboxen nur über den
index-erkannten Text-Slots. KOCHfabrik-Quelldateien sind in **keinem** Pfad
nötig.

PDF → *sauberer klonbarer Master* direkt ist **nicht** möglich (Spike
bewiesen) — darum Rekonstruktion (6b) bzw. Hybrid-Fallback (6c), nie naives
„PDF→PPTX".

Master-Rollen (aus Recon-Skelett): Cover · Über uns · Team · Menü {1,2,3,4,6
Fotos} · Getränke · Location · Referenzen · Kontakt.

Master-Rollen (aus Recon-Skelett): Cover · Über uns · Team · Menü {1,2,3,4,6
Fotos} · Getränke · Location · Referenzen · Kontakt.

## 7. Fehlerbehandlung

- Kein Pool-Foto für ein Gericht → Platzhalter-Asset, Deck bricht **nicht** ab.
- PDF-Parse-Fehler → strukturierter Fehler, Fallback auf Briefing/Manuell.
- Zod-Validierung ist das Gate vor `compose`.

## 8. Hauptrisiko (Pushback)

Der einzige Sargnagel für Ansatz D ist **Text-Overflow**, wenn Gericht-Namen/
-Beschreibungen die Master-Box sprengen (im claude-pptx-Spike als
`generated-3` exakt demonstriert). Mitigation: Box-Kapazitätsprüfung +
Autosize/Varianten-Fallback in `assemble/`. Pflicht, nicht optional.

## 9. Tests

- `assemble/`: Unit — Klon erhält Geometrie byte-genau; Platzhalter-Fill korrekt.
- `compose/`: Golden-File — Beispiel-Modell → erwartete Slide-Sequenz.
- `input/`: je 1–2 echte PDFs / Briefings → erwartetes Modell.
- E2E: Output rendert in LibreOffice ohne Defekt (Spike-Render-Check).

## 10. Scope-Grenze / Folgephasen

MVP = Pfad PDF/Briefing → editierbares Deck mit Fix-Slides + Menü-Slides +
Pool-Fotos. **Danach** (eigener Spec): besseres Dish↔Foto-Matching, Dish-vs-
Venue-Nachtest, mehr Menü-Varianten, Live-Editing-UI.

## 11. Erfolgskriterien

1. Ein realer Angebots-PDF **und** ein Freitext-Briefing erzeugen je ein
   natives, in PowerPoint editierbares, KOCHfabrik-gebrandetes `.pptx`.
2. Fix-Slides byte-stabil; Menü-Slides korrekt nach #Gerichten variiert;
   Fotos aus Pool zugewiesen.
3. Output rendert ohne Layout-Defekt; Overflow-Fälle abgefangen.
4. Alles im Projektordner, keine Bildgenerierung, kein v1-Bezug.
