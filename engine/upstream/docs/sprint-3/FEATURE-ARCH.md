# Sprint 3 — FEATURE-ARCH (EPIC-001 · Renderer + Pixel-Diff-Gate)

## Scope

`Angebot`-Datenmodell → **pixelgenaues KOCHfabrik-Angebots-PDF**, plus
ein messbares Pixel-Diff-Gate gegen ≥3 echte Muster. Liefert das
Kernprodukt des Epics (Akzeptanzkriterium 1). Baut auf Sprint-2-
Artefakten (alle auf `main` @ 0e97e9c).

### Goals
- Positions-Repeater rendern (Zeilen/Sub-Header/Zwischensumme ins
  `_meta.repeater`-Band, pixelgenau im Referenz-Stil)
- Ein-Befehl-Renderer `angebot_render.py` (Angebot.json → PDF)
- PDF-Diff-Harness (per-Seite Pixel/SSIM, Schwellwert)
- Muster→Angebot-Parser (Round-Trip-Fähigkeit)
- Pixel-Diff-Gate über ≥3 echte GEN-2-Muster < kalibrierter Toleranz
- Echte PDF-Pipeline schließt die US-012-Proxy-Adaption

### Non-Goals (bewusst NICHT Sprint 3)
- **GEN-1/3-Token-Generalisierung** → Sprint 4 (Carry-Over bleibt
  DEFERRED; Sprint 3 fokussiert Renderer+Gate auf GEN 2)
- Echte KOCHfabrik-Preisliste/Kalkulation → Epic Non-Goal
- Chat-Flow → Sprint 5
- Änderungen an `extract.py`/`reconstruct.js`/`lib/` (Engine-Regel)
- Präsentationsgenerator (Freeze bleibt grün)

## Architektur

```
angebot.json ─ angebot_model.load
                    │
        angebot_fill.fill (Skalar-Tokens)        ← Sprint 2
                    │
        angebot_positions.render (Repeater-Band) ← US-013 (neu)
                    │
        elements.json + logos → reconstruct.js → pptx
                    │  soffice --convert-to pdf
                    ▼
                 out.pdf  ── angebot_render.py (US-014)
                    │
   echtes Muster ─ angebot_parse (US-017) ─┐
                    │                        │ Round-Trip
   pdf_diff (US-015) ◄── angebot_gate (US-016) ◄┘  ≥3 Muster
                    ▼
              PIXEL-GATE.md  +  test_angebot_render (US-019)
```

Engine bleibt unverändert (nur darüberliegende Skripte). Render-Weg
pptx→pdf via `soffice` ist bereits CLAUDE.md-Standard (Render/Verify).

## Datenfluss (Round-Trip-Gate)

`echtes Muster.pdf → angebot_parse → Angebot → angebot_render → out.pdf
→ pdf_diff(out.pdf, Muster.pdf) → Score < Toleranz`. Toleranz wird in
US-016 datenbasiert kalibriert (Startwert + Begründung in PIXEL-GATE.md).

## Entscheidungen / Risiken

| Punkt | Entscheidung / Mitigation |
|---|---|
| Render-Ziel PDF | pptx→pdf via `soffice` (CLAUDE.md-Standard, kein neuer Stack) |
| Repeater-Zeilen-Vorlage | aus Referenz-Template-Bbox abgeleitet (US-013), nicht hardcoded |
| Pixel-Toleranz unklar | US-016 kalibriert datenbasiert über ≥3 Muster, Wert dokumentiert |
| soffice-Varianz (Font/Layout) | Diff per-Seite + Toleranz; bei Ausreißer Region-Diff, dokumentiert |
| GEN 1/3 weicht ab | bewusst Non-Goal → Sprint 4 (kein Scope-Creep) |

## Epic-Alignment

**Epic:** EPIC-001. **Adressiert:** Sprint-3-Zeile (Renderer Daten→PDF +
Pixel-Diff-Gate) = **Akzeptanzkriterium 1**. **Nächste Iteration:**
Sprint 4 = Fiktiv-Korpus-Generator (20–30 PDFs) + GEN-1/3-
Generalisierung; Sprint 5 = Chat-Flow.
