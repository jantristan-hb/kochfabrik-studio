# Sprint 2 — pptxgenerator_v2 (EPIC-001)

> Übergabe-Prompt für `/sprint-execute` nach `/clear`.
> Referenzieren mit: @docs/sprint-2/EXECUTE.md

**Pfad:** `/home/jrudat/work/03 AKARA Solutions GmbH/kochfabrik/pptxgenerator_v2`
**Sprint:** 2 · **Epic:** EPIC-001 Angebotsgenerator
**Erstellt:** 2026-05-19
**Build:** `python3 -m py_compile phase0/scripts/*.py`
**Test:** `cd phase0 && for t in tests/test_*.py; do python3 "$t"; done`
**Branch-Konvention:** `us-{NR}-{slug}` (GitHub, kein glab; NIE main pushen)
**Voraussetzung:** DB `pptxgen-pg` :5434 läuft; Korpus unter
`~/Nextcloud/Kochfabrik Dokumente/` erreichbar.

## Sprint-Docs

- Stories: `docs/sprint-2/USER-STORIES.md`
- Architektur: `docs/sprint-2/FEATURE-ARCH.md`
- Epic: `docs/epics/EPIC-001-angebotsgenerator.md`
- Engine-Regel: Projekt-`CLAUDE.md` — `extract.py`/`reconstruct.js`/`lib/` NICHT ändern

## Lean-Adaption (Projekt-CLAUDE.md)

GitHub/Python-Projekt: **kein glab/Issues, kein BDD.md/TEST.md, kein
7-File-Spec.** Tests = plain-assert in `phase0/tests/test_*.py` (Muster:
`test_kf_classify.py`). Verify-Befehle stehen je Story in USER-STORIES.md.

## Waves

### Wave 1 (parallel)
| Story | Titel | Blocked-by |
|-------|-------|------------|
| US-007 | Angebots-Korpus inventarisieren & Layout vermessen | — |
| US-008 | Angebots-Datenmodell definieren | — |

### Wave 2 (parallel, nach Wave 1)
| Story | Titel | Blocked-by |
|-------|-------|------------|
| US-009 | Template aus Referenz-Muster pixelgenau extrahieren | US-007 |
| US-011 | Positionsblock-Struktur modellieren | US-007, US-008 |

### Wave 3 (nach Wave 2)
| Story | Titel | Blocked-by |
|-------|-------|------------|
| US-010 | Datenmodell → Template Felder-Mapping | US-008, US-009 |

### Wave 4 (nach Wave 3)
| Story | Titel | Blocked-by |
|-------|-------|------------|
| US-012 | kf_classify-Konformitäts-Check | US-009, US-010, US-011 |

## Auftrag

/sprint-execute liest diese Datei und führt die Waves aus. Worktrees bei
paralleler Arbeit (Hooks erzwingen das). Jede Story: Feature-Branch →
Verify grün → Commit (`feat|chore(scope): US-NR …`, Co-Authored-By
Claude Opus 4.7) → Push Feature-Branch (NIE main). Merge nur nach
explizitem User-Approval (Stack/Integrate am Sprint-Ende).
Sequentiell-Fallback: `/sprint-execute pptxgenerator_v2 2 --sequential`.
