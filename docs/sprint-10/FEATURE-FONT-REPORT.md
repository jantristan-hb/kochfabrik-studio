---
key: KOCHFABRIK-FEATURE-002
status: approved
title: "Font-/Größen-Report über die 200 Referenz-PDFs"
created: 2026-06-09
project: kochfabrik
---

# KOCHFABRIK-FEATURE-002: Font-/Größen-Report

> **Typ:** FEATURE (Brownfield-Delta). Sprint 10 / EPIC-003, WP Q3.
> Liefert das Daten-Fundament für EPIC-005 (Font-Treue) und die
> Metrik-Definition in EPIC-007 (V1).

## 1. Vision

Ein reproduzierbarer Extraktor liest alle 200 Referenz-PDFs und
liefert exakte Font-Fakten (Familie, Face/Weight, pt-Größe, Farbe,
Häufigkeit) maschinenlesbar (JSON) + als lesbaren Report. „Open Sans
kanonisch, exakte Größen" (R-FONT-1/2) bekommt damit Zahlen statt
Stichproben — inkl. Wingdings-Glyphen-Inventar für das Bullet-Mapping.

## 3. Datenmodell (font-report.json)

| Feld | Typ | Beschreibung |
|---|---|---|
| `generated_for` | `string` | Korpus-Pfad + Commit-Stand |
| `pdf_count` | `int` | MUSS 200 sein (Vollständigkeits-Zähler) |
| `pdfs` | `array[{…}]` | ein Eintrag pro PDF (slug, pages, spans) |
| `pdfs[].spans` | `array[{…}]` | pro Text-Span: `font` (string), `size_pt` (decimal, exakt), `color` (hex), `bold`/`italic` (bool), `count` (int) |
| `aggregate.fonts` | `object` | Familie→Vorkommen (korpusweit) |
| `aggregate.sizes_pt` | `object` | pt-Wert→Vorkommen (Histogramm-Basis) |
| `aggregate.wingdings_glyphs` | `object` | Unicode-Codepoint→Vorkommen |

## 4. Flow

```
cache/*/assets/*.pdf (read-only) → Span-Extraktion (exakte pt aus
Text-Rendering-Matrix, NICHT Glyph-Bbox) → pro PDF aggregieren →
korpusweit aggregieren → font-report.json → FONT-REPORT.md (Mensch)
```

## 7. API-Skizze

Entfällt — CLI: `python3 tools/font_report.py [--out …] [--verify]`.

## 8. Akzeptanzkriterien (EARS)

1. WHEN der Extraktor über den Korpus läuft THE SYSTEM SHALL ein
   `font-report.json` mit `pdf_count == 200` und genau 200
   `pdfs`-Einträgen erzeugen.
2. THE SYSTEM SHALL pt-Größen als exakte Werte aus der
   Text-Rendering-Matrix liefern (kein Korrekturfaktor im Extraktor).
3. WHEN der Report generiert wird THE SYSTEM SHALL in FONT-REPORT.md
   die Abdeckung `200/200`, ein pt-Histogramm, die Font-Verteilung
   und das Wingdings-Glyphen-Inventar ausweisen.
4. IF ein PDF nicht lesbar ist THEN THE SYSTEM SHALL es im JSON unter
   `errors` mit Grund führen statt es still zu überspringen
   (Zähler bleibt nachvollziehbar).

## 9. Abgrenzung (Nicht-Teil)

- Keine Änderung an `extract.py`/`text.js` (→ EPIC-005/T1–T2)
- Keine Treue-Metrik/Diffs (→ EPIC-007/V1)

## 9a. Boundaries (3-Tier)

- ✅ **Always:** `tools/` + `docs/sprint-10/` anlegen/schreiben;
  Analyse-venv unter `tools/.venv` mit `pymupdf` (reine
  Analyse-Dependency, NICHT in requirements.txt)
- ⚠️ **Ask-first:** Runtime-Dependency in `requirements.txt`;
  Änderungen im Engine-Repo
- 🚫 **Never:** `data/cache/` schreiben/löschen (R-NF-3)

## 10. Abgrenzung zum Ist

- Heute: ein pdffonts-Stichproben-Sweep (Ideation 2026-06-09, nur
  Font-Namen) → Soll: vollständige Span-Daten inkl. exakter pt-Größen
  und Farben, reproduzierbar per Skript.

## 11. Implementierungs-Anker (Ist)

Korpus: `../pptxgenerator_v2/phase0/data/cache/{slug}/assets/*.pdf`
(200 Stück, read-only). Referenz für das Span-Format:
`pptxgenerator_v2/phase0/spike-pptxgenjs/extract.py` (Ist-Extraktion
mit Glyph-Bbox — der Report macht es exakt, als Vorlage für T1).

## 12. Bekannte Pitfalls

1. **Glyph-Bbox als Größe** — genau der Fehler, der SIZE_K=0.78
   erzwang; pt MUSS aus der Rendering-Matrix kommen (PyMuPDF
   `span["size"]`).
2. **Subset-Font-Präfixe** (`ABCDEF+OpenSans-Bold`) — vor der
   Aggregation strippen, sonst zerfällt die Verteilung.
3. **Stilles Überspringen kaputter PDFs** — bricht den
   200/200-Nachweis; immer in `errors` ausweisen.

## Referenzen
- implements → REQUIREMENTS R-QA-2 (Daten für R-FONT-1/2/5, R-FID-1)
- relates_to → [[EPIC-003]] WP Q3 · [[EPIC-005]] T1/T4 · [[EPIC-007]] V1

## Referenziert von
— USER-STORIES Sprint 10 (US-038, US-039)
