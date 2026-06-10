# Sprint 1 — Retrospektive (Engine Phase A)

## Was lief gut
- Sequentielle, linear gestackte Branches → null Merge-Konflikte trotz
  geteilter Dateien (extract.py/reconstruct.js/convert.py).
- Spike-Kernlogik strikt unangetastet — jede Story nur parametrisieren/
  orchestrieren/absichern, jede Verify grün, keine Fidelity-Regression.
- Phase-B-Gate lieferte harte Daten statt Bauchgefühl: **25/25 clean**.

## Was lief schlecht / hätte besser sein können
- /sprint-plan, /sprint-execute, /sprint-review sind GitLab-/Astro-zentriert;
  mussten manuell auf GitHub + Python/JS adaptiert werden (Lean-Modus).
- Kein Test-Framework → Verify = Story-Einzeiler statt BDD/TEST (bewusst,
  ROI-getrieben für ~500-LOC-Konverter).

## Plan-vs-Reality

### Implementierungs-Matrix
| Story | Geplant | Status | Abweichung |
|-------|---------|--------|------------|
| US-001 | Input/Output parametrisieren, Maß aus PDF | ✅ DONE | — |
| US-002 | convert.py Orchestrator | ✅ DONE | — |
| US-005 | Override produktiv (deck-gekeyt + Readback) | ✅ DONE | — |
| US-003 | CLI + Batch | ✅ DONE | — |
| US-004 | Fehlerbehandlung + Fallbacks | ✅ DONE | — |
| US-006 | Phase-B Mess-Gate | ✅ DONE | — |

### Plan-Qualität
| Metrik | Plan | Realität |
|--------|------|----------|
| Umsetzungsrate | 6 Stories | 6/6 DONE (100%) |
| Effort-Schätzung | Phase A = L (8–13 SP) | akkurat |
| Dependencies | linearer Wave-Plan | korrekt, 0 Konflikte |
| Scope | 6 Stories | genau richtig |

## Learnings (übertragbar)
- Lineares Branch-Stacking ist bei stark geteilten Dateien dem
  Parallel-Agent-Teams-Default überlegen — Default situativ überstimmen.
- Skill-Adaption (GitLab→GitHub, kein Test-Framework) als Pushback früh
  ansagen statt blind abspulen.
- **Engine generalisiert breiter als konservativ angenommen** —
  Phase-C-Schätzung von „XL/unbekannt" auf **≈ M** revidiert.

## BDD/Tests
- Keine (bewusst, kein Framework). Verify-Einzeiler je Story als Gate.

## Offene technische Schulden / Phase C (aus Phase-B abgeleitet)
- Phase-B-Gate ist **coarse** (Slide-1-Diff, strukturelle Heuristik, keine
  Per-Slide-Vision). „100 % clean" ≠ pixel-perfekt garantiert.
- Phase C: optionaler Per-Slide-Fidelity-Feinpass + gezielte Härtung der
  (bisher: keiner) auffälligen Klassen. Scope ≈ M.
- Wingdings-Substitut (Icon-Glyphs) ungelöst, niedrige Prio.
