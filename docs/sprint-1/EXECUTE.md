# Sprint 1 — pptxgenerator_v2 (Engine Phase A)

> Übergabe-Prompt für `/sprint-execute` nach `/clear`.
> Referenzieren mit: `@docs/sprint-1/EXECUTE.md`

**Pfad:** `~/work/03 AKARA Solutions GmbH/kochfabrik/pptxgenerator_v2`
**Sprint:** 1
**Erstellt:** 2026-05-18
**Repo:** github.com/jantristan-hb/pptxgenerator_v2 (privat, Branch `main`)
**Workdir:** `phase0/spike-pptxgenjs/`
**Build/Run:** `python3 convert.py <in.pdf> <out.pptx>` (entsteht in US-002/003)
**Verify je Story:** siehe `USER-STORIES.md` (jede Story hat Verify-Block)
**Branch-Konvention:** `<us-nr>-<slug>` (z.B. `001-input-parametrisieren`)

## Sprint-Docs

- Stories: `docs/sprint-1/USER-STORIES.md`
- Architektur: `docs/sprint-1/FEATURE-ARCH.md`
- Referenz-Spec: `docs/superpowers/specs/2026-05-18-pptxgenerator-v2-mvp-design.md`
- Learnings: `~/work/Projects/claude-pptx/pptxGenJS/PDF-zu-PPTX Rekonstruktion — Learnings.md`

## Waves

### Wave 1
| Story | Titel |
|---|---|
| US-001 | Input/Output parametrisieren, Seitenmaß aus PDF |

### Wave 2 (nach Wave 1, parallel)
| Story | Titel | Blocked-by |
|---|---|---|
| US-002 | convert.py — Asset-Pipeline als ein Lauf | US-001 |
| US-005 | Override-Workflow produktiv (Readback pro Deck) | US-001 |

### Wave 3 (nach Wave 2, parallel)
| Story | Titel | Blocked-by |
|---|---|---|
| US-003 | CLI + Batch über Ordner | US-002 |
| US-004 | Fehlerbehandlung + Fallbacks | US-002 |

### Wave 4 (Sprint-Abschluss)
| Story | Titel | Blocked-by |
|---|---|---|
| US-006 | Phase-B Mess-Gate — Korpus-Stichprobe + Fehlerrate | US-003, US-004 |

## Auftrag

`/sprint-execute` liest diese Datei und führt die Waves aus.
**Harte Regel:** Kernlogik der verifizierten Spike-Bausteine
(`extract.py`-Extraktion, `reconstruct.js`-z-Order, `lib/*`) NICHT verändern —
nur parametrisieren/orchestrieren/absichern. US-006 ist ein **Mess-Gate**,
keine Härtung — Phase C wird erst aus dessen Report geschätzt.

Sequentiell-Fallback: `/sprint-execute pptxgenerator_v2 1 --sequential`
