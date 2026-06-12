# Sprint 14 — Retrospektive (2026-06-12)

## Was lief gut
- **Reibungslosester Sprint bisher:** 9 Stories, 4 parallele Stränge,
  2 Lead-Wartepunkt-Merges — null Incidents, null Merge-Konflikte,
  null Fehlrouting. Die Sprint-13-Gegenmittel (Board-Ignorier-Klausel
  in jedem Prompt, Tasks nach TeamCreate, Ketten-Ownership komplett
  vorab) haben den Auto-Dispatcher vollständig neutralisiert.
- **Planungs-Validierung zahlte aus:** Der „kein soffice auf dem Mac"-
  Fund VOR der Execution (Container-Render-Umstellung) und die
  vorab dokumentierte Symlink-Falle verhinderten zwei sichere
  Mid-Sprint-Eskalationen. Der API-Agent verifizierte die Symlink-
  Lösung sogar gegen lib/logos.js-Resolve-Verhalten.
- **Beweisqualität:** E2E lief REAL (nicht geskippt) — Override-Text
  im Slide-XML + Bild in ppt/media; Live-Smoke des Gesamtflows mit
  echtem Angebots-PDF; Formulieren-Tonprobe („Firmen-Catering, das
  sitzt. Erfahren, norddeutsch, ohne Schnickschnack."); Bild-Ranking-
  Stichprobe semantisch plausibel.
- Gold-Test-Disziplin: rank()/load() unangetastet, rank_mixed additiv —
  Sprint-12-Regressionsschutz hat den Design-Druck richtig gelenkt.

## Was lief schlecht / hätte besser sein können
- Stacked-Branch-Sichtprüfung: der „vollständigste" Branch (wizard)
  enthielt die US-069-Artefakte NICHT (Solo-Branch nie eingemergt) —
  R1-Spotcheck musste auf zwei Branches prüfen; endgültiger Beweis
  erst auf dem gemergten master (bekannte Apollo-Lehre, kein Schaden).
- zsh-Wortsplitting-Falle beim Lead (`set -- $w` splittet nicht) —
  Worktree-Anlage schlug einmal still fehl; Lehre: keine kompakten
  Shell-Tricks in Orchestrierungs-Befehlen, explizit ausschreiben.

## Plan-vs-Reality

### Implementierungs-Matrix
| Story | Geplant | Status | Abweichung |
|-------|---------|--------|------------|
| US-069 | Notext-Renders | ✅ | raumkarussell p1 = reine Textseite → korrekt leerer Render (dokumentiert) |
| US-073 | imgbundle + rank_mixed | ✅ | Vision-Quelle: preview-PNG bevorzugt, Fallback größtes Asset (soffice-frei) |
| US-070 | Geometrie-API + Notext-Route | ✅ | — |
| US-071 | Bild-Overrides | ✅ | — (Symlink-Falle sauber umschifft) |
| US-072 | Formulieren + Mix | ✅ | Graceful-Pfad via monkeypatch bewiesen (imgbundle ist committet → im Image vorhanden) |
| US-074 | Wizard-Gerüst | ✅ | — |
| US-075 | Alternativen | ✅ | — |
| US-076 | Overlay-Editor | ✅ | — |
| US-077 | Filmstreifen + E2E | ✅ | Cover-Deck 12-09-2025-kf-bechtle nicht im committeten Cache (Prod-Volume hat es) — Smoke übersprang es korrekt |

### Plan-Qualität
| Metrik | Plan | Realität |
|--------|------|----------|
| Umsetzungsrate | 9 Stories | 9/9 (100%) |
| Effort | 2×S-Solo, Ketten M/L | Akkurat |
| Dependencies | 4 Stränge, 2 Wartepunkte | Exakt wie geplant, 0 Konflikte |
| Scope | 9 (Obergrenze) | Passend — Wizard komplett in einem Sprint |

## Learnings (übertragbar)
- Die Prompt-Klausel „nur Lead-Briefings, Board ignorieren" gehört
  jetzt fest in jedes EXECUTE.md-Template (hat 100% gewirkt).
- Read-before-write in der PLANUNG (soffice-Check, Symlink-Analyse,
  elements-Shape) ist der größte Hebel gegen Mid-Sprint-Eskalationen —
  die Minuten beim Planen sparen Stunden in der Execution.
- Stacked-Verifies: bei Multi-Strang-Sprints Spotchecks IMMER je
  Strang-Branch fahren, nicht nur auf dem „letzten".

## Spec-Erfüllung (EARS/Tests)
- EARS ohne grünen Verify: — (14/14 über alle drei Specs)
- Pitfalls-Gegenprobe: sauber (kein np.load außerhalb bundle.py,
  _overrides statt Symlink-Schreiben, ResizeObserver/Maßstab,
  Bilder nicht in sessionStorage, Gold-Test grün, kein timeout-Binary)
- Tests falsch/fehlend: — (Suite 153→206, +53)

## Spec-Sync (Code → Spec, aus E8.0)
- Specs auf `implemented`: KOCHFABRIK-FEATURE-013/014/015
- Abweichungen: Vision-Fallback-Quelle (US-073) + Smoke-Befunde in
  RETRO dokumentiert; Spec-Flows decken den Ist-Stand
- TRACEABILITY (Sprint + Projekt) nachgezogen

## Offene technische Schulden
- **Voll-Korpus-Batches + Volume-Sync (Betriebs-Schritt, Jan-Go):**
  ohne sie Fallback-Previews mit Texten + text-only-Ranking in Prod
- EPIC-007/008 (CI + Treue) → Sprint 15 (2× geschoben — jetzt fällig)
- Vertrag-Rest: Dialog-Nachbearbeitung, DNA-Doku, Font-Treue (EPIC-005)
- Alt-Ordner-Entscheid (seit S12)
