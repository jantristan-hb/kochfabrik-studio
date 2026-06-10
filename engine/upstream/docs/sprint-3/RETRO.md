# Sprint 3 — Retrospektive (EPIC-001)

## Was lief gut
- Architektur-Gate (US-013) zuerst: der per-Zeile-Full-Region-Renderer
  wurde am echten KOCHfabrik-PDF visuell validiert (Demo-PDF
  strukturtreu) BEVOR US-014/016/019 darauf aufbauten — Risiko früh raus.
- Linearer Branch-Stack (us-013→…→us-019) ohne Merge-Konflikte; Tests
  durchgehend grün (5 Suites, keine Regression auf Sprint 1/2).
- Pixel-Diff-Gate datenbasiert kalibriert (beobachtet 0.1656 → TOL 0.25
  mit Headroom) statt geratener Schwelle.
- Session-Schnitt nach US-013 sauber persistiert → Wiederaufnahme in
  frischer Session funktionierte ohne Reibung (PROGRESS-Resume-Hinweis).

## Was lief schlecht / hätte besser sein können
- US-009-Template-Band war zu schmal (nur 3 Beispiel-Zeilen) → US-013
  musste auf „volle Tabellenregion" erweitert werden (L→L+). Hätte in
  Sprint-2-US-009 breiter getaggt sein sollen.
- US-016-Report-Pfad zeigte erst auf `phase0/docs/` statt Projekt-
  `docs/sprint-3/` (ROOT-Berechnung) — im Lauf bemerkt + gefixt.
- `parse_header`/`parse_location` fälschlich in compose_offer vermutet
  (liegen in assemble.py) → US-017 ImportError, mit lokalem `_kunde`
  selbst-enthalten gelöst.

## Plan-vs-Reality

### Implementierungs-Matrix
| Story | Geplant | Status | Abweichung |
|-------|---------|--------|------------|
| US-013 | Positions-Renderer | 🔄 | Scope L→L+ (volle Region statt Band, mit User entschieden) |
| US-015 | PDF-Diff-Harness | ✅ | — |
| US-017 | Muster→Parser | 🔄 | selbst-enthalten (kein assemble-Import); `_kunde` heuristisch |
| US-014 | Renderer-CLI | ✅ | — |
| US-016 | Pixel-Gate ≥3 Muster | 🔄 | Gate-Wert = Referenz-Self-Round-Trip; Fremd-Muster informativ (GEN-1/3=Sprint 4) |
| US-019 | Regression | ✅ | — |

### Plan-Qualität
| Metrik | Plan | Realität |
|--------|------|----------|
| Umsetzungsrate | 6 Stories | 6/6 DONE (100 %) |
| Effort | US-013 L, Rest M/S | US-013 L→L+ (Template-Band-Lücke); Rest akkurat |
| Dependencies | 4 Waves, linear | Korrekt; Stack ohne Konflikt |
| Scope | 6 Stories | Genau richtig; GEN-1/3 sauber als Non-Goal abgegrenzt |

## Learnings (übertragbar)
- **Template-Extraktion muss die VOLLE variable Region taggen**, nicht
  nur Beispieldaten — sonst Folge-Renderer-Story muss nachziehen.
- Pixel-Gate für Template-Renderer: nur **Self-Round-Trip der
  Referenz** ist valide; Cross-Template braucht Generalisierung.
- Architektur-Gate vor der teuersten Story + visuelle Sichtung =
  weiterhin höchster ROI (wie Sprint 2).

## Tests
- Falsch herausgestellt: —
- Gefehlt: US-015/017 haben keinen eigenen plain-assert Test (Verify =
  CLI-Einzeiler) — von US-019-Regression indirekt mitgedeckt.

## Offene technische Schulden → Carry-Over Sprint 4
- GEN-1/3-Token-Generalisierung (alle Template-Generationen)
- Cross-Template-Treue / ggf. mehrere Templates
- Fiktiv-Korpus-Generator (20–30 Original-Stil-PDFs)
- `_kunde`-Heuristik (Namen ohne Rechtsform-Token)
- Sub-Header-Unterstreichung (Element-Modell-Limit)
