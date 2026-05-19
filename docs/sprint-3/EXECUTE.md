# Sprint 3 — pptxgenerator_v2 (EPIC-001)

> Übergabe-Prompt für `/sprint-execute` nach `/clear`.
> Referenzieren mit: @docs/sprint-3/EXECUTE.md

**Pfad:** `/home/jrudat/work/03 AKARA Solutions GmbH/kochfabrik/pptxgenerator_v2`
**Sprint:** 3 · **Epic:** EPIC-001 Angebotsgenerator
**Erstellt:** 2026-05-19
**Build:** `python3 -m py_compile phase0/scripts/*.py`
**Test:** `cd phase0 && for t in tests/test_*.py; do python3 "$t"; done`
**Branch-Konvention:** `us-{NR}-{slug}` (GitHub, kein glab; NIE main pushen)
**Voraussetzung:** `main` @ 0e97e9c (Sprint 2 gemergt); `soffice`,
`pdftoppm`, `pdftotext` verfügbar; Korpus unter `~/Nextcloud/...`.

## Sprint-Docs

- Stories: `docs/sprint-3/USER-STORIES.md`
- Architektur: `docs/sprint-3/FEATURE-ARCH.md`
- Epic: `docs/epics/EPIC-001-angebotsgenerator.md`
- Engine-Regel: `extract.py`/`reconstruct.js`/`lib/` NICHT ändern

## Lean-Adaption (Projekt-CLAUDE.md)

GitHub/Python: **kein glab/Issues, kein BDD.md/TEST.md, kein 7-File.**
Tests = plain-assert (`tests/test_*.py`, Muster `test_angebot_template.py`).
Dependent Stories **linear stacken** (geteilte Dateien — wie Sprint 2).

## Waves

### Wave 1 (parallel)
| Story | Titel | Blocked-by |
|-------|-------|------------|
| US-013 | Positions-Repeater-Renderer | — |
| US-015 | PDF-Diff-Harness | — |
| US-017 | Muster→Angebot-Parser | — |

### Wave 2
| Story | Titel | Blocked-by |
|-------|-------|------------|
| US-014 | End-to-End Renderer-CLI (Angebot→PDF) | US-013 |

### Wave 3
| Story | Titel | Blocked-by |
|-------|-------|------------|
| US-016 | Pixel-Diff-Gate gegen ≥3 echte Muster | US-014, US-015, US-017 |

### Wave 4
| Story | Titel | Blocked-by |
|-------|-------|------------|
| US-019 | Regression — Render-Konformität + Diff | US-014, US-016 |

## Auftrag

/sprint-execute führt die Waves aus. Worktrees bei paralleler Arbeit.
Jede Story: Feature-Branch (dependent → auf Vorgänger stacken) → Verify
grün → Commit (`feat(angebot): US-NR …`, Co-Authored-By Claude Opus 4.7)
→ Push Feature-Branch (NIE main). Merge nur nach explizitem User-Approval
(/sprint-review → Integrate). Empfehlung: US-013 (Kern, L) als
Architektur-Gate zuerst — davon hängt US-014/016/019 ab.
Sequentiell-Fallback: `/sprint-execute pptxgenerator_v2 3 --sequential`.
