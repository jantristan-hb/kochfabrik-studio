# PROGRESS.md — pptxgenerator_v2

**Projekt:** pptxgenerator_v2 (KOCHfabrik PDF→PPTX-Konverter, Clean-Room)
**Aktueller Sprint:** EPIC-001 Angebotsgenerator DONE (Sprint 2–5)
**Status:** 5 Sprints done · EPIC-001 DONE (AK1–4 erfüllt)
**Repo:** github.com/jantristan-hb/pptxgenerator_v2 (privat)

## Compact-Recovery

> Kontext verloren? Lies:
> 1. `CLAUDE.md` — Regeln, Stack, Sprint-Tabelle
> 2. **Diese Datei** — Status, was existiert
> 3. `docs/sprint-1/{USER-STORIES,FEATURE-ARCH,RETRO}.md` — Sprint 1
> 4. `~/work/Projects/claude-pptx/pptxGenJS/PDF-zu-PPTX Rekonstruktion — Learnings.md`
> 5. `phase0/REPORT-phase-b.md` — Korpus-Mess-Ergebnis

---

## Sprint 1 — Engine Phase A (2026-05-18)

| Story | Titel | Status |
|-------|-------|--------|
| US-001 | Input/Output parametrisieren, Maß aus PDF | DONE |
| US-002 | convert.py Orchestrator | DONE |
| US-003 | CLI + Batch | DONE |
| US-004 | Fehlerbehandlung + Fallbacks | DONE |
| US-005 | Override produktiv (deck-gekeyt + Readback) | DONE |
| US-006 | Phase-B Mess-Gate | DONE |

**Ergebnis:** Engine konvertiert beliebiges KOCHfabrik-PDF (einzeln/Batch)
→ faithful, editierbares PPTX. Phase-B: 25/25 Decks clean, 0 Fails.

## Sprint 2 — EPIC-001 Template-Extraktion + Datenmodell (2026-05-19)

| Story | Titel | Status |
|-------|-------|--------|
| US-007 | Angebots-Korpus inventarisieren & Layout vermessen | DONE |
| US-008 | Angebots-Datenmodell definieren | DONE |
| US-009 | Template aus Referenz-Muster pixelgenau extrahieren | DONE |
| US-010 | Datenmodell → Template Felder-Mapping | DONE |
| US-011 | Positionsblock-Struktur modellieren | DONE |
| US-012 | kf_classify-Konformitäts-Check | DONE |

**Docs:** `docs/sprint-2/{USER-STORIES,FEATURE-ARCH,EXECUTE}.md`
**Neue Dateien:** `phase0/scripts/{scan_angebote,angebot_model,build_angebot_template,angebot_fill,verify_angebot}.py`, `phase0/data/angebot_template.elements.json`, `phase0/tests/test_angebot_template.py`
**Waves:** W1{007,008} W2{009,011} W3{010} W4{012}
**Ergebnis:** 6/6 DONE. End-to-end belegt: angebot_model → angebot_fill
→ angebot_template → reconstruct.js → kf_classify == 'angebot' (7/7).
Referenz GEN-2 RAUMKARUSSELL aus 34 Angebots-PDFs / 3 Generationen.

## Sprint 3 — EPIC-001 Renderer + Pixel-Diff-Gate (2026-05-19)

| Story | Titel | Status |
|-------|-------|--------|
| US-013 | Positions-Repeater-Renderer | DONE |
| US-014 | End-to-End Renderer-CLI (Angebot→PDF) | DONE |
| US-015 | PDF-Diff-Harness | DONE |
| US-016 | Pixel-Diff-Gate gegen ≥3 echte Muster | DONE |
| US-017 | Muster→Angebot-Parser | DONE |
| US-019 | Regression — Render-Konformität + Diff | DONE |

**Docs:** `docs/sprint-3/{USER-STORIES,FEATURE-ARCH,EXECUTE}.md`
**Neue Dateien:** `phase0/scripts/{angebot_positions,angebot_render,pdf_diff,angebot_parse,angebot_gate}.py`, `phase0/tests/test_angebot_render.py`, `docs/sprint-3/PIXEL-GATE.md`
**Waves:** W1{013,015,017} W2{014} W3{016} W4{019}
**Ergebnis:** 6/6 DONE. `angebot_render.py` (Angebot→PDF) end-to-end;
Referenz-Self-Round-Trip Pixel-Gate **max-score 0.1656 ≤ TOL 0.25**
(8/8 Seiten). US-012-Proxy geschlossen (echte PDF-Pipeline). Carry-Over
Sprint-3 (Positions-Rendering · Pixel-Gate · echte PDF-Pipeline) ✓
abgedeckt.

## Sprint 4 — EPIC-001 Fiktiv-Korpus (2026-05-19) — DONE

| Story | Titel | Status |
|-------|-------|--------|
| US-020 | Fiktiv-Event-Generator (Anthropic Batch API) | DONE |
| US-021 | Korpus-Batch-Renderer | DONE |
| US-024 | Korpus-Konformitäts-Gate | DONE |
| US-022/023/025 | GEN-1/3 + RETRO-Polish | DEFERRED → Post-Epic |

**Ergebnis (AK2):** `gen_fiktiv.py`→`build_korpus.py`→`korpus_gate.py`.
**20/20 valide JSONs → 20/20 PDFs → 20/20 konform** (is_kochfabrik +
classify=='angebot' + Labels + Bankblock). `docs/sprint-4/KORPUS-GATE.md`.

## Sprint 5 — EPIC-001 Angebotsgenerator-Frontend (2026-05-19) — DONE

| Story | Titel | Status |
|-------|-------|--------|
| US-026 | Studio-Modul: Chat + Hand-Edit + PDF (verdrahtet) | DONE |

**Ergebnis (AK3):** Cross-Repo-Integration in **KOCHfabrik Studio**
(`kochfabrik-studio` @ master `74f7bf9`): `web/chat.html`
(Angebotsgenerator: Chatbot + editierbares Formular/Positionen + PDF
jederzeit, Design-2), `backend/app.py` `/api/angebot/{health,chat,pdf}`
graceful, Engine als ~9 MB vendored Bundle, Dockerfile nodejs+
LibreOffice, Coolify-ENV `ANTHROPIC_API_KEY`. **Lokal end-to-end
verifiziert** (engine:true, PDF ok). Live-Deploy: Coolify-Build
angestoßen. `angebot_chat.py` (Engine-CLI). Pattern:
`reference_studio_engine_integration_pattern`.

## EPIC-001 — DONE (2026-05-19)

AK1 ✅ Renderer+Pixel-Gate (0.1656≤0.25, Sprint 3) · AK2 ✅ 20/20
Fiktiv-Korpus konform (Sprint 4) · AK3 ✅ Chat+Edit+PDF in Studio
(Sprint 5) · AK4 ✅ Präsentationsgenerator-Freeze unberührt.

## Post-Epic-Backlog
<!-- nach EPIC-001-Abschluss, keine AK -->
| ID | Titel | Typ |
|----|-------|-----|
| — | GEN-1/3-Token-Generalisierung (alle Template-Generationen) | DEFERRED |
| — | Cross-Template-Treue / mehrere Templates (Fremd-Muster Pixel-Gate) | DEFERRED |
| — | `_kunde`-Heuristik: Namen ohne Rechtsform-Token (HOWDENRE) | DEFERRED |
| — | Sub-Header-Unterstreichung (Element-Modell-Limit) | DEFERRED |
| — | Präsentationsgenerator in Studio integrieren (Pattern; DB-Caveat pptxgen-pg) | DEFERRED |
| — | Engine-Container-Verifikation live (LibreOffice/node Build) | DEFERRED |

## Carry-Over → Sprint 3
<!-- auto-generated by /sprint-review 2026-05-19 — INPUT für /sprint-plan -->
| ID | Titel | Typ | Quelle |
|----|-------|-----|--------|
| — | Positions-Repeater RENDERN (Datenmodell→Zeilen ins _meta.repeater-Band) | DEFERRED | EPIC-001 Sprint 3 (geplant, kein Defizit) |
| — | Pixel-Diff-Gate gegen ≥3 echte Muster | DEFERRED | EPIC-001 Sprint 3 (Akzeptanzkriterium 1) |
| — | PDF-Render-Pipeline (statt PPTX-Text-Proxy in US-012) | DEFERRED | Sprint-2-Adaption, Sprint-3-Scope |
| — | Token-Mapping über GEN 1/3 generalisieren (Sprint 2 nur GEN 2) | DEFERRED | LAYOUT-ANALYSE.md |

## Carry-Over → Sprint 2
<!-- auto-generated by /sprint-review 2026-05-18 — INPUT für /sprint-plan -->
| ID | Titel | Typ | Quelle |
|----|-------|-----|--------|
| — | Phase C: Per-Slide-Fidelity-Feinpass + gezielte Härtung (≈ M) | DEFERRED | RETRO.md / Phase-B |
| — | Wingdings-Icon-Substitut | DEFERRED | RETRO.md (niedrige Prio) |
| — | Eingabe-Kapselung: Prompt/Formular statt Kunden-PDF | DEFERRED | Architektur-Richtung (FEATURE-ARCH) |

**Disposition (2026-05-19, /sprint-plan):**
- *Phase C* + *Wingdings-Substitut* → bleiben DEFERRED: gehören zum
  eingefrorenen Präsentationsgenerator (`freeze/praesentationsgenerator-
  2026-05-19`, Out-of-Scope laut Freeze-Bericht). Nicht in Sprint 2.
- *Eingabe-Kapselung Prompt/Formular* → **absorbiert von EPIC-001**
  (Angebotsgenerator-Kern; Chat-Flow = Sprint 5). Nicht verloren.

## Aktueller Zustand (2026-05-18)

| Metrik | Wert |
|--------|------|
| Sprints done | 1 |
| Stories | 6 |
| Engine-Einstieg | `phase0/spike-pptxgenjs/convert.py <pdf> [out]` / `--batch DIR` |
| Korpus-Clean-Rate (Phase-B, n=25) | 100% |

### Bekannte Lücken
- Phase-B-Gate coarse (Slide-1-Diff, keine Per-Slide-Vision) → echte
  Pixel-Fidelity nicht garantiert, nur „keine groben Defekte".
- Phase C noch nicht geplant (erst nach diesem Sprint, Scope ≈ M).

## Freeze

- **`freeze/praesentationsgenerator-2026-05-19`** @ `6d218bc` —
  Präsentationsgenerator v1 eingefroren. Bericht:
  `docs/FREEZE-praesentationsgenerator-2026-05-19.md`.

## Epics

| ID | Titel | Status | Sprints |
|----|-------|--------|---------|
| EPIC-001 | KOCHfabrik Angebotsgenerator (Chat → pixelgenaues Angebots-PDF) | DONE | Sprint 2–5 DONE (AK1–4) |
