# Changelog — pptxgenerator_v2

Format: [Keep a Changelog](https://keepachangelog.com/de/1.1.0/)

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
