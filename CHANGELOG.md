# Changelog — pptxgenerator_v2

Format: [Keep a Changelog](https://keepachangelog.com/de/1.1.0/)

## [Sprint 3] — 2026-05-19 — EPIC-001 Angebotsgenerator (Renderer + Pixel-Gate)

### Hinzugefügt
- **US-013: Positions-Repeater-Renderer** — `angebot_positions.py`:
  per-Zeile aus Modell (Sub-Header/Zeilen/Zwischensumme), volle
  Tabellenregion, Reflow; Gold-Header/Footer invariant.
- **US-015: PDF-Diff-Harness** — `pdf_diff.py` (pdftoppm + PIL,
  per-Seite Score, CLI/Exit-Code).
- **US-017: Muster→Angebot-Parser** — `angebot_parse.py` (PDF →
  Angebot, selbst-enthalten).
- **US-014: End-to-End Renderer-CLI** — `angebot_render.py`
  (Angebot-JSON → PDF via fill→positions→reconstruct→soffice).
- **US-016: Pixel-Diff-Gate** — `angebot_gate.py` + `PIXEL-GATE.md`:
  Round-Trip, Referenz-Self-Round-Trip max 0.1656 ≤ TOL 0.25.
- **US-019: Render-Regression** — `test_angebot_render.py`: echtes PDF
  → kf_classify + Pixel-Gate (schließt US-012-Proxy).

## [Sprint 2] — 2026-05-19 — EPIC-001 Angebotsgenerator (Fundament)

### Hinzugefügt
- **US-007: Korpus-Inventar & Layout-Analyse** — `scan_angebote.py`
  klassifiziert 207 PDFs → 34 Angebote, 3 Layout-Generationen,
  Referenzwahl (GEN-2 RAUMKARUSSELL). `docs/sprint-2/LAYOUT-ANALYSE.md`.
- **US-008: Angebots-Datenmodell** — `angebot_model.py` (dataclasses,
  JSON-roundtrip-stabil) + Referenz-Fixture `phase0/fixtures/angebot_example.json`.
- **US-009: Pixelgenaues Template** — `build_angebot_template.py`:
  Faithful-Extraktion → Skalar-Tokens + Positions-Repeater-Band,
  invariante Blöcke verbatim.
- **US-010: Felder-Mapping** — `angebot_fill.py` setzt Modellwerte in
  alle 15 Template-Tokens.
- **US-011: Positionsblock-Struktur** — `Position.is_header` (preislose
  Sub-Header), `docs/sprint-2/POSITIONSBLOCK.md`.
- **US-012: Konformitäts-Check** — `verify_angebot.py` +
  `test_angebot_template.py`: end-to-end Modell→Template→Render→
  `kf_classify == 'angebot'` (7/7).

## [Unreleased]

### Hinzugefügt
- **Robuste KOCHfabrik-PDF-Pipeline** (`kf_classify.py`) — Identify
  (invariante Letterhead/Domain-Signatur, empirisch 33/33) ·
  deterministischer Footer-Strip · Classify (angebot/menue/kontext) ·
  Label-basierte Event-Extraktion · Ableitung von Gang-Headlines aus
  Cateringkonzept/Anlass/Empfang, wenn das PDF kein Menü listet. Die
  abgeleiteten Headlines laufen durch den bestehenden Kategorie-Lock →
  der 1010-Korpus liefert echte passende KOCHfabrik-Speisen. Robustheit
  durch sichere Dokument-Klassifikation statt fragilem Inhalts-Parsen.
  Regression: `tests/test_kf_classify.py`.

### Behoben
- **assemble.py crasht bei 0 erkannten Gängen** — kaufmännische
  Angebots-PDFs ohne Speisen (z.B. INBOUND/RAUMKARUSSELL/HOWDENRE)
  führten im Category-Lock zu `numpy.AxisError` (leeres `embed()`-
  Batch → 1-D-Array → `norm(axis=1)`). Jetzt: Food-Block wird leer
  gelassen, Deck ohne Food gebaut (Cover + Frame + Ausstattung) plus
  Klartext-Hinweis. Regression: `tests/test_empty_courses.py`.

## [Sprint 1 — Engine Phase A] — 2026-05-18

Aus dem Ein-Deck-Spike eine parametrisierte, orchestrierte, robuste
Engine. Spike-Kernlogik (pdfminer-Paint-Order, z-Order-Regeln,
Logo-Transparenz) bewusst unverändert — nur parametrisieren/
orchestrieren/absichern.

### Hinzugefügt
- **US-002: convert.py** — Ein-Lauf-Orchestrator (pdftohtml → extract_logos
  → apply_official_logo → extract → reconstruct) in isoliertem Work-Dir.
- **US-003: CLI + Batch** — `convert.py <pdf> [out]` und `--batch DIR`
  mit Summary + Exit-Code.
- **US-005: readback_overrides.py** — Hand-Korrekturen aus editiertem
  PPTX pro Deck zurücklesen.
- **US-006: phase_b_gate.py** — stratifiziertes Mess-Gate über den Korpus
  → `REPORT-phase-b.md`.

### Geändert
- **US-001:** `extract.py`/`reconstruct.js` parametrisiert; Seitenmaß aus
  PDF (`_meta`) statt hardcoded 960×540.
- **US-005:** `overrides.json` pro Deck gekeyt; `lib/overrides.js`
  deckKey-aware (+ Legacy-Fallback).

### Behoben
- **US-004:** defensive Emission in `reconstruct.js` (try/catch je
  Element/Slide, fehlendes Bild → Platzhalter); `convert.py`
  pdfinfo-Frühvalidierung + `convert-report.json`.

### Mess-Ergebnis (US-006)
25/25 Decks clean, 0 Pipeline-Fails, 0 Flags (stratifiziert) →
Phase-C-Scoping: **≈ M** (Engine generalisiert breit). Limitierung:
coarse Heuristik (Slide-1-Diff, keine Vision).
