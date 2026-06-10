# Sprint 2 — Retrospektive (EPIC-001)

## Was lief gut
- Architektur-Gate vor US-009 (convert.py-Spike auf Referenz-Muster)
  räumte das zentrale Epic-Risiko mit Evidenz aus, bevor Template-Code
  gebaut wurde — 12/12 Schlüssel-Strings faithful rekonstruiert.
- Saubere Kopplung US-008 ↔ US-009: token_map aus `example()` →
  US-010-fill konnte exakt dasselbe Token-Set bedienen, keine Drift.
- End-to-end-Beleg in US-012 (7/7): Modell→fill→Template→reconstruct→
  kf_classify=='angebot'. Akzeptanzkriterium-1-Vorstufe erfüllt.
- Voll-Regression durchgehend grün (4 Suites), keine Altlast gebrochen.

## Was lief schlecht / hätte besser sein können
- US-011 hatte zwei unabhängige Eltern (US-007-Doc + US-008-Modell) →
  Cross-Branch-Konflikt. Planungs-Gap im Wave-Graph (geteilte Datei
  LAYOUT-ANALYSE.md nicht erkannt). Workaround: eigenes POSITIONSBLOCK.md.
- US-007-Sektions-Regex griff in `pdftotext -layout` nicht (rechts-
  bündige Preisspalten) — Geometrie korrekt nach US-009 verschoben,
  aber hätte im Plan antizipiert sein können.
- Story-Output-Pfad `phase0/data/` war gitignored → Fixture nach
  `phase0/fixtures/` umgezogen. Plan kannte die .gitignore-Regel nicht.

## Plan-vs-Reality

### Implementierungs-Matrix
| Story | Geplant | Status | Abweichung |
|-------|---------|--------|------------|
| US-007 | Korpus-Inventar & Layout | ✅ | Sektions-Geometrie → US-009 verschoben |
| US-008 | Datenmodell | ✅ | Fixture phase0/fixtures statt data (gitignore) |
| US-009 | Template-Extraktion | ✅ | — (Gate grün vorab) |
| US-010 | Felder-Mapping | ✅ | — |
| US-011 | Positionsblock | 🔄 | Modell schon in US-008; Doku eigenes Doc |
| US-012 | Konformitäts-Check | 🔄 | PPTX-Text-Proxy statt PDF→pdftotext (Sprint-3-Scope) |

### Plan-Qualität
| Metrik | Plan | Realität |
|--------|------|----------|
| Umsetzungsrate | 6 Stories | 6/6 DONE (100 %) |
| Effort-Schätzungen | US-009 L, Rest M/S | Akkurat; US-011 leicht überschätzt (US-008 pre-modelliert) |
| Dependencies | 4 Waves | Korrekt; aber geteilte-Datei-Stack (US-011) nicht im Graph |
| Scope | 6 Stories | Genau richtig (1 Session) |

## Learnings (übertragbar)
- **Wave-Graph muss geteilte Dateien erfassen**, nicht nur Blocked-by:
  Stories die dieselbe Datei ändern → linear stacken einplanen.
- Bei Brownfield-Spike: `.gitignore` vor Story-Output-Pfaden prüfen
  (Build-Artefakte vs. versionierte Fixtures trennen).
- Architektur-Gate vor dem teuersten Story (L) ist hoher ROI — als
  Muster für künftige Epics mit unverifizierten Annahmen.

## Tests
- Falsch herausgestellt: —
- Gefehlt: US-007 hat keinen automatischen Test (Verify = manueller
  scan_angebote-Lauf) — akzeptabel (Analyse-Story), aber Inventar-
  Zahlen sind nicht regressionsgesichert.

## Offene technische Schulden → Carry-Over Sprint 3
- Positions-Repeater RENDERN (Datenmodell→Zeilen) — EPIC-001 Sprint 3
- Pixel-Diff-Gate gegen ≥3 echte Muster — Akzeptanzkriterium 1
- Echte PDF-Render-Pipeline statt PPTX-Text-Proxy (US-012)
- Token-Mapping über GEN 1/3 generalisieren (Sprint 2 nur GEN 2)
