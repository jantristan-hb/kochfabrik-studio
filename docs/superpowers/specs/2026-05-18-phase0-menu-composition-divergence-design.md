# Phase 0 — Menü-Kompositions-Divergenz (Decision-Gate-Spike)

**Datum:** 2026-05-18
**Projekt:** pptxgenerator_v2 (KOCHfabrik Präsentationsgenerator, Clean-Room-Neubau)
**Status:** Spec zur Review

---

## 1. Zweck

Phase 0 ist **kein** Generator. Es ist ein Mess-Spike, der **eine** Frage
evidenzbasiert beantwortet:

> Wie divergent sind die **Menü-/Speisen-Kompositions-Slides** in den echten
> KOCHfabrik-Decks — und wiederholen sich Layouts **und** Gerichte?

Das Ergebnis entscheidet die gesamte Phase-1-Architektur. Ohne diese Zahlen ist
jedes Generator-Design geraten.

## 2. Decision-Gate

Aus dem Aggregat-Report wird genau einer dieser Pfade gewählt:

| Befund (Menü-Slides) | Phase-1-Architektur |
|---|---|
| ≤ 10 Archetypen decken ≥ 80 %, Archetyp-Set sättigt bis ~25 Decks | **Ansatz D**: kleiner fester Master-Katalog, Klon + Befüllung |
| 10–25 Archetypen *oder* Deckung 60–80 % | **Hybrid**: wenige Master + parametrische Slots |
| > 25 Archetypen / Long-Tail / keine Sättigung | **Parametrische Layout-Engine** (feste Master skalieren nicht) |

Zusätzlich (Inhalts-Rekurrenz, unabhängig):

| Befund (Gerichte) | Konsequenz Bild-Pipeline |
|---|---|
| Top-Gerichte decken großen Anteil / Menüs wiederholen sich (hohe Jaccard-Überlappung) | Gericht↔Bild = **kuratierte Lookup-Tabelle** statt KI-Suche |
| Gerichte überwiegend unikal | KI-Bildauswahl aus dem kuratierten Pool nötig |

Schwellen sind Vorschläge; finale Werte legt Jan beim Report-Review fest.

## 3. Scope

**In:**
- Korpus: `/home/jrudat/Nextcloud/Kochfabrik Dokumente/AKARA_Präsentationen/`
  (199 PDF; die 4 großen `.pptx` sind in Phase 0 **out** — flache
  Layout-Analyse, separat als spätere Master-Kandidaten notieren).
- Nur **Menü-/Speisen-Kompositions-Slides**. Cover/„Über uns"/Team/Wein/Kontakt
  sind trivial-fix und hier irrelevant.
- Stratifizierte Stichprobe ~25 Decks (≈5 je Stratum) über die Dateinamen-Typen:
  **Foodkonzept/Speisenidee**, **Eventkonzept**, **Angebot #…**,
  **Hochzeit/Geburtstag/Jubiläum**, **Kunden-benannt** (z.B. „KF x …").
  Bei Sättigung Aussage; sonst eskalieren.

**Out:**
- Generator, Datenmodell, PPTX-Erzeugung, Templates bauen — alles Phase 1+.
- Bildgenerierung, Bild-Embedding, RAG.
- Jeglicher Bezug auf vorhandenen v1-Code/-Doku (Clean-Room, bewusst).

## 4. Methode (Variante b: Geometrie-Prefilter + Vision-Batch)

```
PDF (Stichprobe)
  → pro Seite: eingebettete Raster zählen + bboxen + Textlayer extrahieren   [PDF-Geometrie]
  → Heuristik Menü-Seite? (≥2 food-große Bilder ODER Gänge-Keywords im Text:
     Vorspeise|Hauptgang|Dessert|Menü|Flying|Buffet|Gang|Amuse|Snack)        [Prefilter]
  → Kandidatenseiten → PNG-Render → Anthropic Batch API (Vision)             [Feintagging]
  → Fingerprint-JSON pro Menü-Seite                                          [Output]
  → Clustering + Rekurrenz-Statistik                                         [Analyse]
  → REPORT.md (Aggregat)                                                     [Decision-Gate]
```

- **Batch API Pflicht** (CLAUDE.md): `client.messages.batches.create`, kein
  sequentielles Schleifen mit sleep. 50 % günstiger, parallel.
- Geometrie-Prefilter senkt die teuren Vision-Calls auf die echten Menü-Seiten.

## 5. Datenmodell — Fingerprint pro Menü-Seite

Strukturskelett, **kein** Pixelinhalt:

```json
{
  "deck": "12.09.2025_KF Bechtle.pdf",
  "seite": 4,
  "typ_stratum": "Foodkonzept",
  "food_bilder": 3,
  "bild_bboxen_norm": [[0.05,0.10,0.45,0.40], "..."],
  "text_block_pos": "rechts",
  "gaenge": 3,
  "gericht_namen": ["Rote-Bete-Carpaccio", "Short Rib", "Valrhona-Tarte"],
  "titel_pos": "oben-links"
}
```

bboxen normiert auf Seitenmaße (0–1), damit Format-unabhängig clusterbar.

## 6. Analyse

- **Struktur-Cluster:** Kanonische Signatur aus (gerundetes bbox-Raster,
  #Bilder, #Gänge, Text-Block-Region). Häufigkeit je Signatur → Archetyp-Katalog
  mit Deckungs-Kurve. Sättigung = Archetyp-Anzahl wächst bei weiteren Decks
  nicht mehr.
- **Inhalts-Rekurrenz:** Gerichtsnamen normalisieren (lowercase, Qualifier
  strippen) → Häufigkeitsliste; Menü als Multiset je Deck → paarweise
  Jaccard-Verteilung.

## 7. Outputs (ALLE im Projektordner — harte Regel)

Projekt-Root: `~/work/03 AKARA Solutions GmbH/kochfabrik/pptxgenerator_v2/`
Kein Artefakt außerhalb. Kein /tmp. Nichts in den Chat-Kontext rohgeladen.

| Pfad | Inhalt |
|---|---|
| `phase0/scripts/` | Prefilter + Batch-Submit + Analyse-Skripte |
| `phase0/index.json` | Fingerprints aller analysierten Menü-Seiten |
| `phase0/REPORT.md` | Aggregat: Archetyp-Katalog, Deckungs-/Sättigungskurve, Gericht-Rekurrenz, Decision-Gate-Empfehlung |
| `phase0/cache/` | Batch-Roh-Responses (gitignored) |

Ich (Claude) lese **nur** `REPORT.md` — niemals rohe Decks oder `index.json` am
Stück in den Kontext.

## 8. Constraints

- Clean-Room: kein v1-Bezug, keinerlei.
- Kein 199-Big-Bang: Stichprobe → Sättigungsprüfung → erst dann Vollkorpus,
  und nur falls der Report es rechtfertigt (eigene Folge-Entscheidung).
- Anthropic Batch API für alle Bulk-Vision-Calls.
- Keine Kunden-/PII-Daten in Logs/Report (Gericht-/Layout-Ebene reicht;
  Kundennamen aus Dateinamen nur als `typ_stratum`/anonymisiert).
- Alle Artefakte im Projektordner.

## 9. Erfolgskriterien

Phase 0 ist **done**, wenn:
1. ~25 stratifizierte Decks analysiert, Fingerprints in `phase0/index.json`.
2. `phase0/REPORT.md` liefert: Archetyp-Anzahl + Deckung %, Sättigungskurve,
   Top-Gericht-/Menü-Rekurrenz, **eine** klare Decision-Gate-Empfehlung.
3. Jan kann auf Basis des Reports den Phase-1-Pfad (D / Hybrid / parametrisch)
   und die Bild-Strategie (Lookup / KI-Suche) entscheiden.

Phase 0 trifft die Entscheidung **nicht** selbst — es liefert die Evidenz.

## 10. Nicht-Ziele

- Keine Templates bauen.
- Keine `.pptx` erzeugen.
- Keine Architektur für Phase 1 festschreiben (kommt im eigenen Brainstorm
  *nach* den Daten).
